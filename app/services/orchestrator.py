"""
app/services/orchestrator.py
-----------------------------
The core "brain" of SmartRAD AI.

Responsibilities:
  1. Priority Scoring  → Score = (Urgency * 0.7) + (WaitTime_normalized * 0.3)
  2. Room Dispatch     → Find the best idle room for the highest-priority patient
  3. Auto-dispatch loop → Runs every DISPATCH_INTERVAL seconds as a background thread

Called from create_app() just like the RIS watcher.
"""

import time
import logging
import threading
from datetime import datetime

from app.models.room import (
    get_idle_rooms,
    get_waiting_patients,
    assign_patient_to_room,
)

logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
DISPATCH_INTERVAL = 5       # seconds between dispatch cycles
MAX_WAIT_MINUTES  = 120     # wait time that maps to a normalized score of 1.0

# Priority weight constants (from development plan)
W_URGENCY  = 0.7
W_WAIT     = 0.3

# ── Thread state ───────────────────────────────────────────────────────────────
_dispatch_thread: threading.Thread | None = None
_running = False


# ── Priority Logic ─────────────────────────────────────────────────────────────

def calculate_priority_score(urgency_score: int, wait_minutes: int) -> float:
    """
    Compute a priority score in range [0, 10].

    Formula:
        normalized_urgency  = urgency_score / 10          (scale 0-1)
        normalized_wait     = min(wait_minutes / MAX_WAIT_MINUTES, 1.0)
        score = (normalized_urgency * W_URGENCY + normalized_wait * W_WAIT) * 10

    Higher score → higher priority → dispatched first.
    """
    norm_urgency = urgency_score / 10.0
    norm_wait    = min(wait_minutes / MAX_WAIT_MINUTES, 1.0)
    score = (norm_urgency * W_URGENCY + norm_wait * W_WAIT) * 10
    return round(score, 3)


def rank_waiting_patients(patients: list) -> list:
    """
    Return the patient list sorted by strict urgency first, then by priority score.
    Injects a `priority_score` key into each dict for the frontend.
    """
    for p in patients:
        wait = p.get('wait_minutes') or 0
        p['priority_score'] = calculate_priority_score(
            urgency_score = p.get('urgency_score', 5),
            wait_minutes  = wait,
        )
    # Sort by is_urgent (DESC), then by priority_score (DESC)
    return sorted(patients, key=lambda x: (x.get('is_urgent', 0), x['priority_score']), reverse=True)


# ── Auto Completion Logic ──────────────────────────────────────────────────────

def check_and_complete_scans():
    """Check all rooms for all users."""
    from app.database import db
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM users")
            users = cursor.fetchall()
            for user in users:
                _check_user_scans(user['id'])
    except Exception as e:
        logger.error(f"[Orchestrator] global completion check error: {e}")

def _check_user_scans(user_id: int):
    """Check rooms for a specific user."""
    from app.models.room import get_all_rooms, set_room_cleaning, set_room_idle
    from app.models.history import log_completed_scan
    from app.services.pacs_handler import process_scan_completion
    from app.database import db
    from datetime import timedelta
    
    rooms = get_all_rooms(user_id)
    now = datetime.now()
    
    for room in rooms:
        status = room.get('status')
        if status == 'SCANNING' and room.get('predicted_end_time'):
            if now >= room['predicted_end_time']:
                room_id = room['id']
                logger.info(f"[Orchestrator-U{user_id}] ⏰ Scan complete for Room {room_id} -> Cleaning")
                
                # Fetch scan details for history & PACS logging before cleaning
                try:
                    with db.cursor() as cursor:
                        cursor.execute("""
                            SELECT p.id, p.name, p.exam_type, p.modality_type,
                                   p.is_urgent, p.predicted_duration,
                                   r.predicted_end_time, r.name AS room_name
                            FROM rooms r
                            JOIN patients p ON r.current_patient_id = p.id
                            WHERE r.id = %s
                        """, (room_id,))
                        scan_data = cursor.fetchone()
                        
                        if scan_data:
                            pred_dur = scan_data.get('predicted_duration') or 15
                            end_time = scan_data.get('predicted_end_time')
                            if end_time:
                                start_time = end_time - timedelta(minutes=pred_dur)
                                actual_dur = max(1, int((now - start_time).total_seconds() / 60))
                            else:
                                actual_dur = pred_dur
                                
                            # Log history
                            log_completed_scan(
                                patient_id=scan_data['id'],
                                patient_name=scan_data['name'],
                                room_id=room_id,
                                room_name=scan_data['room_name'],
                                exam_type=scan_data['exam_type'],
                                modality_type=scan_data['modality_type'],
                                predicted_duration=pred_dur,
                                actual_duration=actual_dur,
                                user_id=user_id,
                                is_urgent=scan_data.get('is_urgent', 0),
                            )
                            
                            # Run PACS integration
                            process_scan_completion(
                                patient_name=scan_data['name'],
                                exam_type=scan_data['exam_type'],
                                modality=scan_data['modality_type'],
                            )
                except Exception as e:
                    logger.error(f"[Orchestrator-U{user_id}] History/PACS error on auto-completion: {e}")
                
                # Now set the room cleaning state
                set_room_cleaning(room_id)
        elif status == 'CLEANING':
            logger.info(f"[Orchestrator-U{user_id}] ✨ Room {room['id']} is ready -> Idle")
            set_room_idle(room['id'])


# ── Room Selection ─────────────────────────────────────────────────────────────

def _pick_best_room(idle_rooms: list, patient: dict) -> dict | None:
    """
    Given a list of idle rooms and a patient, pick the best fit.

    Strategy:
      1. Prefer a room whose modality_type matches the patient's modality.
      2. If none match, pick the lowest-id idle room as a fallback.
    """
    modality = patient.get('modality_type')
    matching = [r for r in idle_rooms if r['modality_type'] == modality]

    if matching:
        return matching[0]           # first matching room (stable ordering by id)
    return idle_rooms[0] if idle_rooms else None


# ── Dispatch Cycle ─────────────────────────────────────────────────────────────

def run_dispatch_cycle(user_id: int = None) -> list:
    """
    Execute dispatch cycle.
    If user_id is provided, runs for that user.
    If user_id is None, runs for ALL users (global background task).
    """
    if user_id is not None:
        return _run_user_dispatch_cycle(user_id)
    
    # Global background run
    from app.database import db
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM users")
            users = cursor.fetchall()
            
            all_assignments = []
            for user in users:
                all_assignments.extend(_run_user_dispatch_cycle(user['id']))
            return all_assignments
    except Exception as e:
        logger.error(f"[Orchestrator] global dispatch error: {e}")
        return []

def _run_user_dispatch_cycle(user_id: int) -> list:
    """Internal user-specific dispatch logic."""
    assignments = []

    idle_rooms = get_idle_rooms(user_id)
    if not idle_rooms:
        return assignments

    waiting = get_waiting_patients(user_id)
    if not waiting:
        return assignments

    ranked = rank_waiting_patients(waiting)

    # Work through idle rooms, consuming the ranked list
    remaining_patients = list(ranked)
    for room in idle_rooms:
        if not remaining_patients:
            break

        # Find the highest-priority patient compatible with this room's modality
        chosen_idx  = None
        chosen_patient = None
        for idx, patient in enumerate(remaining_patients):
            if patient.get('modality_type') == room['modality_type']:
                chosen_idx    = idx
                chosen_patient = patient
                break

        # Fallback: if no modality match, take the absolute top patient
        if chosen_patient is None:
            chosen_idx    = 0
            chosen_patient = remaining_patients[0]

        duration = chosen_patient.get('predicted_duration') or 15  # safe default
        success  = assign_patient_to_room(room['id'], chosen_patient['id'], duration)

        if success:
            assignment = {
                'room_id':       room['id'],
                'room_name':     room['name'],
                'patient_id':    chosen_patient['id'],
                'patient_name':  chosen_patient['name'],
                'exam_type':     chosen_patient['exam_type'],
                'priority_score': chosen_patient['priority_score'],
                'estimated_min': duration,
            }
            assignments.append(assignment)
            logger.info(
                f"[Orchestrator] ✅ Assigned {chosen_patient['name']} "
                f"(score={chosen_patient['priority_score']}) → {room['name']}"
            )
            remaining_patients.pop(chosen_idx)

    return assignments


# ── Background Loop ─────────────────────────────────────────────────────────────

def _dispatch_loop():
    """Runs continuously in a daemon thread."""
    logger.info("[Orchestrator] Dispatch loop started.")
    from app.database import db
    while _running:
        try:
            check_and_complete_scans()
            run_dispatch_cycle()
        except Exception as e:
            logger.error(f"[Orchestrator] Cycle error: {e}")
        finally:
            try:
                db.close()
            except Exception as dbe:
                logger.error(f"[Orchestrator] DB close error: {dbe}")
        time.sleep(DISPATCH_INTERVAL)


def start_orchestrator():
    """Start the background dispatch thread (called once from create_app)."""
    global _dispatch_thread, _running
    if _dispatch_thread and _dispatch_thread.is_alive():
        return
    _running = True
    _dispatch_thread = threading.Thread(
        target=_dispatch_loop,
        daemon=True,
        name='Orchestrator'
    )
    _dispatch_thread.start()


def stop_orchestrator():
    """Gracefully stop the dispatch loop."""
    global _running
    _running = False
