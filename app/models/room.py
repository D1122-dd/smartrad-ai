"""
app/models/room.py
------------------
Database helpers for the `rooms` and `patients` tables.
Provides clean query functions used by the orchestrator and the rooms API.
"""

import logging
from datetime import datetime, timedelta
from app.database import db

logger = logging.getLogger(__name__)


# ── Room Queries ────────────────────────────────────────────────────────────────

def get_all_rooms(user_id: int) -> list:
    """Return all rooms for a specific user with their current state."""
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT
                    r.id,
                    r.name,
                    r.modality_type,
                    r.status,
                    r.current_patient_id,
                    r.predicted_end_time,
                    p.name           AS patient_name,
                    p.exam_type      AS patient_exam,
                    p.urgency_score  AS patient_urgency
                FROM rooms r
                LEFT JOIN patients p ON r.current_patient_id = p.id
                WHERE r.user_id = %s
                ORDER BY r.id
            """, (user_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"[RoomModel] get_all_rooms error: {e}")
        return []


def get_room_by_id(room_id: int) -> dict | None:
    """Return a single room record."""
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"[RoomModel] get_room_by_id error: {e}")
        return None


def get_idle_rooms(user_id: int) -> list:
    """Return all rooms currently in IDLE state for a specific user."""
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM rooms
                WHERE status = 'IDLE' AND user_id = %s
                ORDER BY id
            """, (user_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"[RoomModel] get_idle_rooms error: {e}")
        return []


def assign_patient_to_room(room_id: int, patient_id: int, predicted_duration: int) -> bool:
    """
    Atomically mark a room as SCANNING and record the predicted end time.
    Also flips the patient status to SCANNING.
    """
    try:
        with db.cursor() as cursor:
            end_time = datetime.now() + timedelta(minutes=predicted_duration)

            cursor.execute("""
                UPDATE rooms
                SET status              = 'SCANNING',
                    current_patient_id  = %s,
                    predicted_end_time  = %s
                WHERE id = %s AND status = 'IDLE'
            """, (patient_id, end_time, room_id))

            if cursor.rowcount == 0:
                # Room was grabbed by another thread
                db.rollback()
                return False

            cursor.execute("""
                UPDATE patients
                SET status          = 'SCANNING',
                    assigned_room_id = %s
                WHERE id = %s AND status IN ('WAITING', 'ASSIGNED')
            """, (room_id, patient_id))

            db.commit()
            logger.info(f"[RoomModel] Patient {patient_id} → Room {room_id} | ETA {end_time.strftime('%H:%M')}")
            return True

    except Exception as e:
        logger.error(f"[RoomModel] assign_patient_to_room error: {e}")
        db.rollback()
        return False


def set_room_cleaning(room_id: int) -> bool:
    """Transition a SCANNING room to CLEANING state and detach the patient."""
    try:
        with db.cursor() as cursor:
            # First, mark the patient as COMPLETED
            cursor.execute("""
                UPDATE patients p
                JOIN rooms r ON r.current_patient_id = p.id
                SET p.status = 'COMPLETED'
                WHERE r.id = %s
            """, (room_id,))

            # Then clear the room
            cursor.execute("""
                UPDATE rooms
                SET status              = 'CLEANING',
                    current_patient_id  = NULL,
                    predicted_end_time  = NULL
                WHERE id = %s
            """, (room_id,))

            db.commit()
            return True
    except Exception as e:
        logger.error(f"[RoomModel] set_room_cleaning error: {e}")
        db.rollback()
        return False


def set_room_idle(room_id: int) -> bool:
    """Transition a CLEANING room back to IDLE state."""
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE rooms
                SET status = 'IDLE',
                    current_patient_id = NULL,
                    predicted_end_time = NULL
                WHERE id = %s
            """, (room_id,))
            db.commit()
            return True
    except Exception as e:
        logger.error(f"[RoomModel] set_room_idle error: {e}")
        db.rollback()
        return False


# ── Patient Queue Queries ────────────────────────────────────────────────────────

def get_waiting_patients(user_id: int) -> list:
    """Return all patients in WAITING state for a specific user, oldest first."""
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    name,
                    exam_type,
                    body_part,
                    modality_type,
                    is_urgent,
                    urgency_score,
                    predicted_duration,
                    request_time,
                    TIMESTAMPDIFF(MINUTE, request_time, NOW()) AS wait_minutes
                FROM patients
                WHERE status = 'WAITING' AND user_id = %s
                ORDER BY request_time ASC
            """, (user_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"[RoomModel] get_waiting_patients error: {e}")
        return []


def get_active_queue(user_id: int) -> list:
    """Return all WAITING + ASSIGNED patients for the queue display for a specific user."""
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    name,
                    exam_type,
                    modality_type,
                    is_urgent,
                    urgency_score,
                    predicted_duration,
                    status,
                    assigned_room_id,
                    request_time,
                    TIMESTAMPDIFF(MINUTE, request_time, NOW()) AS wait_minutes
                FROM patients
                WHERE status IN ('WAITING', 'ASSIGNED', 'SCANNING') AND user_id = %s
                ORDER BY request_time ASC
            """, (user_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"[RoomModel] get_active_queue error: {e}")
        return []

def initialize_user_rooms(user_id: int):
    """Create the standard 4 rooms for a new user."""
    rooms = [
        ('X-Ray-1 - Room 1A', 'DX'),
        ('X-Ray-2 - Room 2B', 'CR'),
        ('X-Ray-3 - Room 1C', 'CR'),
        ('X-Ray-4 - Room 3D', 'DX'),
    ]
    try:
        with db.cursor() as cursor:
            # Check if user already has rooms
            cursor.execute("SELECT id FROM rooms WHERE user_id = %s", (user_id,))
            if cursor.fetchone():
                return True # Already has rooms
                
            for name, mod in rooms:
                cursor.execute("""
                    INSERT INTO rooms (name, modality_type, status, user_id)
                    VALUES (%s, %s, 'IDLE', %s)
                """, (name, mod, user_id))
            db.commit()
            logger.info(f"Initialized 4 rooms for user {user_id}")
            return True
    except Exception as e:
        logger.error(f"Error initializing rooms for user {user_id}: {e}")
        db.rollback()
        return False
