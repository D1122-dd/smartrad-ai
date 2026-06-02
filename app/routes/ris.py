"""
app/routes/ris.py
-----------------
API endpoints consumed by the frontend dashboard for:
  - GET /api/ris/notifications  → poll for new patient arrivals
  - POST /api/ris/generate      → trigger a test order (dev only)
  - DELETE /api/ris/notifications → clear notification badge
"""

from flask import Blueprint, jsonify, request
import logging
import os
import sys
import json
from app.services.ris_watcher import get_notifications, clear_notifications
from app.utils.auth_decorator import login_required

ris_bp = Blueprint('ris', __name__, url_prefix='/api/ris')
logger = logging.getLogger(__name__)

@ris_bp.route('/notifications', methods=['GET'])
@login_required
def list_notifications(user_id):
    """Return new order notifications for the current user."""
    notifs = get_notifications(user_id)
    return jsonify({
        'success': True,
        'notifications': notifs,
        'count': len(notifs)
    })

@ris_bp.route('/notifications', methods=['DELETE'])
@login_required
def clear(user_id):
    """Clear all notifications (called when user opens the notification panel)."""
    # Note: Currently clearing is global, but filtered display handles isolation.
    clear_notifications()
    return jsonify({'success': True, 'message': 'Notifications cleared'}), 200

@ris_bp.route('/manual', methods=['POST'])
@login_required
def add_manual_patient(user_id):
    """Directly add a patient via the frontend form."""
    try:
        data = request.get_json(silent=True) or {}
        
        name      = data.get('name', 'Manual Patient')
        exam      = data.get('exam_type', 'Chest')
        modality  = data.get('modality_type', 'DX')
        age_group = data.get('patient_age_group', 'Adult')
        body_part = data.get('body_part', 'Thorax')
        urgency   = int(data.get('urgency_score', 5))
        is_urgent = 1 if urgency >= 8 else 0

        # 1. Run AI Prediction
        from app.services.prediction_service import predict_duration
        duration, status = predict_duration(
            exam_type=exam,
            modality_type=modality,
            patient_age_group=age_group,
            body_part=body_part,
            is_urgent=is_urgent
        )

        # 2. Insert into DB
        from app.database import db
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO patients
                    (name, patient_age_group, exam_type, body_part,
                     modality_type, is_urgent, urgency_score, predicted_duration, status, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'WAITING', %s)
            """, (name, age_group, exam, body_part, modality, is_urgent, urgency, duration, user_id))
            db.commit()
            
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            patient_id = cursor.fetchone()['id']

        # 3. Add to notifications queue
        from app.services.ris_watcher import notification_queue, _lock
        from datetime import datetime
        notification = {
            'id':         patient_id,
            'user_id':    user_id,
            'patient':    name,
            'exam':       exam,
            'modality':   modality,
            'urgent':     bool(is_urgent),
            'duration':   duration,
            'received_at': datetime.now().strftime('%H:%M:%S'),
        }
        with _lock:
            notification_queue.appendleft(notification)

        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'predicted_duration': duration
        }), 201

    except Exception as e:
        logger.error(f"Manual entry error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@ris_bp.route('/patient/<int:patient_id>', methods=['DELETE'])
@login_required
def delete_patient(user_id, patient_id):
    """Delete a patient record from the database."""
    try:
        from app.database import db
        with db.cursor() as cursor:
            # Check if patient exists AND belongs to this user
            cursor.execute("SELECT id FROM patients WHERE id = %s AND user_id = %s", (patient_id, user_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': 'Patient not found or unauthorized'}), 404
            
            cursor.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
            db.commit()
            
        return jsonify({'success': True, 'message': 'Patient deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting patient {patient_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@ris_bp.route('/generate', methods=['POST'])
@login_required
def generate(user_id):
    """Trigger the Mock-RIS to generate a batch of 5 cases, process them, and auto-dispatch them immediately."""
    try:
        data = request.get_json(silent=True) or {}
        urgent = data.get('urgent', False)
        
        # ── CLEANUP INCOMING FOLDER FIRST ──────────────────
        from app.services.ris_watcher import INCOMING_DIR, _process_file
        for f in os.listdir(INCOMING_DIR):
            if f.endswith('.json'):
                try: os.remove(os.path.join(INCOMING_DIR, f))
                except: pass

        # Import generator
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
        from mock_ris.generate_order import generate_order
        
        # Generate exactly 5 cases with the correct user_id from the start
        count = 5
        filepaths = generate_order(force_urgent=urgent, count=count, user_id=user_id)
        
        # Process the newly generated files synchronously
        for filepath in filepaths:
            _process_file(filepath)
            
        # Trigger an immediate orchestration dispatch cycle
        from app.services.orchestrator import run_dispatch_cycle
        assignments = run_dispatch_cycle(user_id=user_id)
        
        return jsonify({
            'success': True,
            'message': f'Fetched {count} orders and successfully auto-assigned {len(assignments)} rooms.',
            'files_count': count,
            'assignments_made': len(assignments)
        }), 200
    except Exception as e:
        logger.error(f"Error generating and processing mock orders: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
