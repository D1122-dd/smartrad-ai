"""
app/models/history.py
----------------------
Database helpers for the `history` table.
Called when a scan is completed (SCANNING → CLEANING transition).
"""

import logging
from datetime import datetime
from app.database import db

logger = logging.getLogger(__name__)


def log_completed_scan(
    patient_id:         int,
    patient_name:       str,
    room_id:            int,
    room_name:          str,
    exam_type:          str,
    modality_type:      str,
    predicted_duration: int,
    actual_duration:    int,
    user_id:            int,
    is_urgent:          int = 0,
) -> int | None:
    """
    Insert a record into the history table when a scan is marked Finished.
    Returns the new history record id, or None on failure.
    """
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO history
                    (patient_id, patient_name, room_id, room_name,
                     exam_type, modality_type, predicted_duration,
                     actual_duration, user_id, is_urgent, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                patient_id, patient_name, room_id, room_name,
                exam_type, modality_type, predicted_duration,
                actual_duration, user_id, is_urgent, datetime.now()
            ))
            db.commit()
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            row = cursor.fetchone()
            hid = row['id'] if row else None
            logger.info(
                f"[History] Scan logged → patient={patient_name} | "
                f"predicted={predicted_duration}m actual={actual_duration}m | id={hid}"
            )
            return hid
    except Exception as e:
        logger.error(f"[History] log_completed_scan error: {e}")
        db.rollback()
        return None


def get_history_records(user_id: int, limit: int = 100) -> list:
    """Return the most recent completed scan records for a specific user."""
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id, patient_name, room_name, exam_type, modality_type,
                    predicted_duration, actual_duration, is_urgent, completed_at,
                    (actual_duration - predicted_duration) AS duration_error
                FROM history
                WHERE user_id = %s
                ORDER BY completed_at DESC
                LIMIT %s
            """, (user_id, limit))
            rows = cursor.fetchall()
            for r in rows:
                if r.get('completed_at'):
                    r['completed_at'] = r['completed_at'].isoformat()
            return rows
    except Exception as e:
        logger.error(f"[History] get_history_records error: {e}")
        return []


def get_analytics_summary(user_id: int) -> dict:
    """
    Aggregate stats for the Performance dashboard (user-specific).
    """
    try:
        with db.cursor() as cursor:
            # 1. Overview stats
            cursor.execute("""
                SELECT
                    COUNT(*)                                          AS total_scans,
                    ROUND(AVG(predicted_duration), 1)                AS avg_predicted,
                    ROUND(AVG(actual_duration), 1)                   AS avg_actual,
                    ROUND(AVG(ABS(actual_duration-predicted_duration)),1) AS avg_error,
                    ROUND(
                      IFNULL(100.0 * SUM(ABS(actual_duration-predicted_duration) <= 3) / COUNT(*), 0),
                      1
                    )                                                AS accuracy_pct
                FROM history
                WHERE user_id = %s
            """, (user_id,))
            summary = cursor.fetchone() or {}

            # 2. Room utilization
            cursor.execute("""
                SELECT r.name AS room_name, COUNT(h.id) AS scans
                FROM rooms r
                LEFT JOIN history h ON r.id = h.room_id AND h.user_id = %s
                WHERE r.user_id = %s
                GROUP BY r.id, r.name
                ORDER BY r.id
            """, (user_id, user_id))
            summary['room_utilization'] = cursor.fetchall()

            # 3. Modality split
            cursor.execute("""
                SELECT modality_type, COUNT(*) AS scans
                FROM history
                WHERE user_id = %s
                GROUP BY modality_type
            """, (user_id,))
            summary['modality_split'] = cursor.fetchall()

            # 4. Daily trend
            cursor.execute("""
                SELECT
                    DATE(completed_at)               AS scan_date,
                    ROUND(AVG(actual_duration), 1)   AS avg_actual,
                    ROUND(AVG(predicted_duration), 1) AS avg_predicted,
                    COUNT(*)                          AS total
                FROM history
                WHERE user_id = %s
                GROUP BY DATE(completed_at)
                ORDER BY scan_date DESC
                LIMIT 14
            """, (user_id,))
            summary['daily_trend'] = cursor.fetchall()
            for row in summary['daily_trend']:
                if row.get('scan_date'):
                    row['scan_date'] = str(row['scan_date'])

            return summary
    except Exception as e:
        logger.error(f"[History] get_analytics_summary error: {e}")
        return {}
