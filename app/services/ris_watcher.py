"""
app/services/ris_watcher.py
---------------------------
Background thread that polls mock_ris/incoming/ for new JSON order files.
When a file appears:
  1. Parses the patient data
  2. Calls prediction_service to get estimated duration
  3. Inserts the patient into the `patients` DB table
  4. Moves the file to mock_ris/processed/ (prevents re-processing)
  5. Stores a notification in a shared in-memory queue (polled by frontend)

Started once from create_app() using threading.Thread.
"""

import os
import json
import time
import shutil
import logging
import threading
from datetime import datetime
from collections import deque

from app.database import db
from app.services.prediction_service import predict_duration

logger = logging.getLogger(__name__)

# ── Folder paths ───────────────────────────────────────────────────────────────
_BASE        = os.path.join(os.path.dirname(__file__), '..', '..', 'mock_ris')
INCOMING_DIR  = os.path.join(_BASE, 'incoming')
PROCESSED_DIR = os.path.join(_BASE, 'processed')

os.makedirs(INCOMING_DIR,  exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# ── Shared notification queue (max 20 entries, FIFO) ─────────────────────────
# Frontend polls /api/ris/notifications to read these.
notification_queue: deque = deque(maxlen=20)
_lock = threading.Lock()

# ── Watcher state ─────────────────────────────────────────────────────────────
_watcher_thread: threading.Thread | None = None
_running = False
POLL_INTERVAL = 3  # seconds


def _insert_patient(order: dict, predicted_duration: int) -> int | None:
    """Insert a parsed order into the patients table. Returns new patient id."""
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO patients
                    (name, patient_age_group, exam_type, body_part,
                     modality_type, is_urgent, urgency_score, predicted_duration, status, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'WAITING', %s)
            """, (
                order.get('patient_name'),
                order.get('patient_age_group', 'Adult'),
                order.get('exam_type'),
                order.get('body_part'),
                order.get('modality_type'),
                int(order.get('is_urgent', 0)),
                int(order.get('urgency_score', 5)),
                predicted_duration,
                order.get('user_id'), # New field
            ))
            db.commit()
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            row = cursor.fetchone()
            return row['id'] if row else None
    except Exception as e:
        logger.error(f"[RIS Watcher] DB insert error: {e}")
        db.rollback()
        return None


def _process_file(filepath: str):
    """Parse one order file, run prediction, insert to DB, move to processed."""
    filename = os.path.basename(filepath)
    processed_path = os.path.join(PROCESSED_DIR, filename)

    try:
        # ── ATOMIC LOCK ──────────────────────────────────
        # Move the file immediately. If another thread already moved it,
        # this will throw FileNotFoundError and we simply return.
        shutil.move(filepath, processed_path)
        
        # Now we read from the SAFE processed location
        with open(processed_path, 'r') as f:
            order = json.load(f)

        # ── DYNAMIC FEATURE CALCULATION ──────────────────
        try:
            with db.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as busy FROM rooms WHERE status != 'IDLE'")
                room_load = cursor.fetchone()['busy']
        except:
            room_load = 0

        # Run AI prediction using the .pkl model
        duration, status = predict_duration(
            exam_type             = order.get('exam_type', 'Chest'),
            modality_type         = order.get('modality_type', 'DX'),
            patient_age_group     = order.get('patient_age_group', 'Adult'),
            body_part             = order.get('body_part', 'Thorax'),
            is_urgent             = int(order.get('is_urgent', 0)),
            room_load_at_request  = room_load
        )

        patient_id = _insert_patient(order, duration)

        if patient_id:
            notification = {
                'id':               patient_id,
                'user_id':          order.get('user_id'),
                'patient':          order.get('patient_name', 'Unknown'),
                'mrn':              order.get('mrn', 'N/A'),
                'accession':        order.get('accession_number', 'N/A'),
                'exam':             order.get('exam_type'),
                'modality':         order.get('modality_type'),
                'urgent':           bool(order.get('is_urgent', 0)),
                'duration':         duration,
                'physician':        order.get('physician', 'Unknown'),
                'history':          order.get('history', ''),
                'hl7_raw':          order.get('hl7_raw', ''),
                'received_at':      datetime.now().strftime('%H:%M:%S'),
            }
            with _lock:
                notification_queue.appendleft(notification)
            logger.info(f"[RIS Watcher] Patient {patient_id} added → {notification['patient']} | Est. {duration} min")

    except FileNotFoundError:
        # File was already moved by another thread
        return
    except json.JSONDecodeError:
        logger.error(f"[RIS Watcher] Invalid JSON in {filename}")
    except Exception as e:
        logger.error(f"[RIS Watcher] Error processing {filename}: {e}")


def _watch_loop():
    """Main polling loop — runs in a background thread."""
    logger.info("[RIS Watcher] Started — watching mock_ris/incoming/")
    while _running:
        try:
            files = [
                f for f in os.listdir(INCOMING_DIR)
                if f.endswith('.json')
            ]
            for filename in files:
                _process_file(os.path.join(INCOMING_DIR, filename))
        except Exception as e:
            logger.error(f"[RIS Watcher] Loop error: {e}")
        time.sleep(POLL_INTERVAL)


def start_watcher():
    """Start the background watcher thread (call once from create_app)."""
    global _watcher_thread, _running
    if _watcher_thread and _watcher_thread.is_alive():
        return  # already running
    _running = True
    _watcher_thread = threading.Thread(target=_watch_loop, daemon=True, name='RIS-Watcher')
    _watcher_thread.start()


def stop_watcher():
    """Gracefully stop the watcher (useful for testing)."""
    global _running
    _running = False


def get_notifications(user_id: int) -> list:
    """Return notifications for the specific user (newest first)."""
    with _lock:
        return [n for n in list(notification_queue) if n.get('user_id') == user_id]


def clear_notifications():
    """Clear all pending notifications."""
    with _lock:
        notification_queue.clear()
