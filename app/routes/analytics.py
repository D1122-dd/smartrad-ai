"""
app/routes/analytics.py
------------------------
Analytics API endpoints for the Performance page.

Endpoints:
  GET /api/analytics/summary   → KPIs (total scans, accuracy %, avg duration)
  GET /api/analytics/history   → last 100 completed scan records
"""

import logging
from flask import Blueprint, jsonify, request
from app.models.history import get_analytics_summary, get_history_records
from app.utils.auth_decorator import login_required

logger = logging.getLogger(__name__)
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


@analytics_bp.route('/summary', methods=['GET'])
@login_required
def summary(user_id):
    """
    Returns aggregate KPIs for the Performance dashboard (user-specific).
    """
    data = get_analytics_summary(user_id)
    return jsonify({'success': True, 'data': data}), 200


@analytics_bp.route('/history', methods=['GET'])
@login_required
def history(user_id):
    """Returns the last 100 completed scan records for the current user."""
    records = get_history_records(user_id, limit=100)
    return jsonify({'success': True, 'count': len(records), 'history': records}), 200


@analytics_bp.route('/history/<int:record_id>', methods=['DELETE'])
@login_required
def delete_history_record(user_id, record_id):
    """Delete a specific history record from the database (scoped to user)."""
    try:
        from app.database import db
        with db.cursor() as cursor:
            # Check if record exists AND belongs to this user
            cursor.execute("SELECT id FROM history WHERE id = %s AND user_id = %s", (record_id, user_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': 'Record not found or unauthorized'}), 404
            
            cursor.execute("DELETE FROM history WHERE id = %s", (record_id,))
            db.commit()
            
        return jsonify({'success': True, 'message': 'History record deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting history record {record_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@analytics_bp.route('/history/clear', methods=['DELETE'])
@login_required
def clear_history(user_id):
    """Clear all records from the history table for the current user."""
    try:
        from app.database import db
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM history WHERE user_id = %s", (user_id,))
            db.commit()
            
        return jsonify({'success': True, 'message': 'Your history has been cleared successfully'}), 200
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
