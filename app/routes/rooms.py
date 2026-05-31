"""
app/routes/rooms.py
-------------------
REST API for room state management and the patient queue.

Endpoints:
  GET  /api/rooms                    → live status of all 4 rooms
  GET  /api/rooms/queue              → active patient queue with priority scores
  POST /api/rooms/<id>/status        → manually update room status
  POST /api/rooms/dispatch           → manually trigger one dispatch cycle (demo)
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request

from app.models.room import (
    get_all_rooms,
    get_active_queue,
    get_room_by_id,
    set_room_cleaning,
    set_room_idle,
    initialize_user_rooms,
)
from app.services.orchestrator import run_dispatch_cycle
from app.models.room import get_waiting_patients
from app.models.history import log_completed_scan
from app.services.pacs_handler import process_scan_completion
from app.database import db
from app.utils.auth_decorator import login_required

logger = logging.getLogger(__name__)
rooms_bp = Blueprint('rooms', __name__, url_prefix='/api/rooms')


# ── GET /api/rooms ──────────────────────────────────────────────────────────────

@rooms_bp.route('', methods=['GET'])
@login_required
def list_rooms(user_id):
    """
    Returns live status of all 4 rooms.
    The dashboard polls this every 3 seconds.

    Response shape:
    {
        "success": true,
        "rooms": [
            {
                "id": 1,
                "name": "X-Ray-1 - Room 1A",
                "modality_type": "DX",
                "status": "SCANNING",
                "current_patient_id": 7,
                "patient_name": "Ahmed Ali",
                "patient_exam": "Chest",
                "patient_urgency": 8,
                "predicted_end_time": "2026-05-07T22:45:00"
            },
            ...
        ]
    }
    """
    initialize_user_rooms(user_id)
    rooms = get_all_rooms(user_id)

    # Serialize datetime to ISO string for JSON
    for room in rooms:
        if room.get('predicted_end_time'):
            room['predicted_end_time'] = room['predicted_end_time'].isoformat()

    return jsonify({'success': True, 'rooms': rooms}), 200


# ── GET /api/rooms/queue ────────────────────────────────────────────────────────

@rooms_bp.route('/queue', methods=['GET'])
@login_required
def patient_queue(user_id):
    """
    Returns all active (WAITING/ASSIGNED/SCANNING) patients ranked by
    priority score. Used to render the Case Queue table.

    Response shape:
    {
        "success": true,
        "count": 5,
        "queue": [
            {
                "id": 3,
                "name": "Sara Hassan",
                "exam_type": "Spine",
                "modality_type": "CR",
                "urgency_score": 9,
                "priority_score": 7.23,
                "wait_minutes": 14,
                "status": "WAITING",
                ...
            },
            ...
        ]
    }
    """
    patients = get_active_queue(user_id)

    # Inject priority scores for the display
    for p in patients:
        from app.services.orchestrator import calculate_priority_score
        wait = p.get('wait_minutes') or 0
        p['priority_score'] = calculate_priority_score(
            urgency_score=p.get('urgency_score', 5),
            wait_minutes=wait,
        )
        # Serialize datetimes
        if p.get('request_time'):
            p['request_time'] = p['request_time'].isoformat()

    # Sort by priority descending
    patients.sort(key=lambda x: x['priority_score'], reverse=True)

    return jsonify({'success': True, 'count': len(patients), 'queue': patients}), 200


# ── POST /api/rooms/<id>/status ─────────────────────────────────────────────────

@rooms_bp.route('/<int:room_id>/status', methods=['POST'])
@login_required
def update_room_status(user_id, room_id: int):
    """
    Manually transition a room's status.

    Request body:
        { "status": "CLEANING" }   or   { "status": "IDLE" }

    Allowed transitions:
        SCANNING → CLEANING   (technician marks scan done)
        CLEANING → IDLE       (room is prepped for next patient)

    The orchestrator will then automatically assign the next patient
    on its next cycle.
    """
    data   = request.get_json(silent=True) or {}
    new_status = (data.get('status') or '').upper()

    if new_status not in ('CLEANING', 'IDLE'):
        return jsonify({
            'success': False,
            'message': "Invalid status. Allowed transitions: SCANNING→CLEANING or CLEANING→IDLE"
        }), 400

    room = get_room_by_id(room_id)
    if not room:
        return jsonify({'success': False, 'message': f'Room {room_id} not found'}), 404

    current = room.get('status', '')

    # Validate transition
    valid_transitions = {
        'SCANNING': 'CLEANING',
        'CLEANING': 'IDLE',
    }
    if valid_transitions.get(current) != new_status:
        return jsonify({
            'success': False,
            'message': f"Cannot transition room from {current} → {new_status}."
        }), 409

    if new_status == 'CLEANING':
        # ── Phase 5: Log history + run PACS before clearing room ──
        try:
            # Fetch current patient from the room
            cursor = db.get_cursor()
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
                # Compute actual duration: time elapsed since scan started
                pred_dur = scan_data.get('predicted_duration') or 15
                end_time = scan_data.get('predicted_end_time')
                if end_time:
                    start_time   = end_time - timedelta(minutes=pred_dur)
                    actual_dur   = max(1, int((datetime.now() - start_time).total_seconds() / 60))
                else:
                    actual_dur   = pred_dur  # fallback

                # Log to history table
                log_completed_scan(
                    patient_id         = scan_data['id'],
                    patient_name       = scan_data['name'],
                    room_id            = room_id,
                    room_name          = scan_data['room_name'],
                    exam_type          = scan_data['exam_type'],
                    modality_type      = scan_data['modality_type'],
                    predicted_duration = pred_dur,
                    actual_duration    = actual_dur,
                    user_id            = user_id,
                    is_urgent          = scan_data.get('is_urgent', 0),
                )

                # Run mock PACS ingestion
                process_scan_completion(
                    patient_name = scan_data['name'],
                    exam_type    = scan_data['exam_type'],
                    modality     = scan_data['modality_type'],
                )
        except Exception as e:
            logger.error(f"[Rooms API] Phase 5 history/PACS error: {e}")
            # Non-fatal — still proceed to set_room_cleaning

        ok = set_room_cleaning(room_id)
    else:
        ok = set_room_idle(room_id)

    if not ok:
        return jsonify({'success': False, 'message': 'Database update failed'}), 500

    logger.info(f"[Rooms API] Room {room_id} manually set to {new_status}")
    return jsonify({
        'success': True,
        'message': f'Room {room_id} is now {new_status}',
        'room_id': room_id,
        'new_status': new_status,
    }), 200


@rooms_bp.route('/<int:room_id>/force-idle', methods=['POST'])
def force_idle_room(room_id: int):
    """
    Forcefully mark a room as IDLE, clearing any current patient.
    Useful for 'stuck' rooms or demo resets.
    """
    try:
        from app.database import db
        with db.cursor() as cursor:
            # 1. If there's a patient, mark them as COMPLETED so they leave the queue
            cursor.execute("""
                UPDATE patients p
                JOIN rooms r ON r.current_patient_id = p.id
                SET p.status = 'COMPLETED', p.assigned_room_id = NULL
                WHERE r.id = %s
            """, (room_id,))
            
            # 2. Reset the room to IDLE
            cursor.execute("""
                UPDATE rooms
                SET status = 'IDLE',
                    current_patient_id = NULL,
                    predicted_end_time = NULL
                WHERE id = %s
            """, (room_id,))
            db.commit()
            
        logger.info(f"[Rooms API] Room {room_id} was FORCE-IDLED")
        return jsonify({'success': True, 'message': f'Room {room_id} forced to IDLE'}), 200
    except Exception as e:
        logger.error(f"[Rooms API] Force idle error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@rooms_bp.route('/dispatch', methods=['POST'])
@login_required
def trigger_dispatch(user_id):
    """
    Manually trigger one orchestration dispatch cycle.
    Useful during demos to immediately assign waiting patients
    without waiting for the 5-second background loop.

    Response:
    {
        "success": true,
        "assignments_made": 2,
        "assignments": [ ... ]
    }
    """
    try:
        assignments = run_dispatch_cycle(user_id=user_id)
        return jsonify({
            'success': True,
            'assignments_made': len(assignments),
            'assignments': assignments,
        }), 200
    except Exception as e:
        logger.error(f"[Rooms API] Manual dispatch error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
