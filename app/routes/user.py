from flask import Blueprint, jsonify, request
from app.models.user import User
from app.models.user_profile import UserProfile
from app.utils.jwt_handler import JWTHandler
import logging
import os
from werkzeug.utils import secure_filename
from flask import current_app

user_bp = Blueprint('user', __name__, url_prefix='/api/users')
logger = logging.getLogger(__name__)

# ============================================================
# ENDPOINT: GET USER PROFILE (API ONLY)
# ============================================================

@user_bp.route('/profile', methods=['GET'])
def user_profile():
    """
    GET: Get logged-in user's profile information
    
    URL: GET /api/users/profile
    Auth: Required (Bearer token)
    
    Returns: User name, email, phone
    """
    try:
        # Verify token and get user_id
        token = JWTHandler.extract_token_from_header(request)
        if not token:
            return jsonify({
                'success': False,
                'message': 'No token provided'
            }), 401
        
        user_id = JWTHandler.verify_token(token)
        if user_id is None:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token'
            }), 401
        
        # Get user basic info
        user = User.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get user profile (phone, etc.)
        profile = UserProfile.get_profile_by_user(user_id)
        
        logger.info(f"Profile retrieved for user: {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Profile retrieved successfully',
            'data': {
                'user_id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'phone_number': user.get('phone_number'),
                'profile_image': user.get('profile_image'),
                'profile': profile if profile else None
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error in user profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@user_bp.route('/upload-avatar', methods=['POST'])
def upload_avatar():
    """Upload a profile image for the user."""
    try:
        token = JWTHandler.extract_token_from_header(request)
        user_id = JWTHandler.verify_token(token)
        if not user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if file:
            filename = secure_filename(f"user_{user_id}_{file.filename}")
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
            os.makedirs(upload_dir, exist_ok=True)
            
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            # Update DB
            from app.database import db
            with db.cursor() as cursor:
                image_url = f"/static/uploads/avatars/{filename}"
                cursor.execute("UPDATE users SET profile_image = %s WHERE id = %s", (image_url, user_id))
                db.commit()
                
            return jsonify({
                'success': True,
                'message': 'Avatar uploaded successfully',
                'image_url': image_url
            }), 200
            
    except Exception as e:
        logger.error(f"Avatar upload error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/change-password', methods=['POST'])
def change_password():
    """
    POST: Change password for logged-in user
    
    URL: POST /api/users/change-password
    Auth: Required (Bearer token)
    Expected JSON: {
        "current_password": "old_password",
        "new_password": "new_password"
    }
    """
    try:
        token = JWTHandler.extract_token_from_header(request)
        user_id = JWTHandler.verify_token(token)
        if not user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'message': 'Current and new password are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'New password must be at least 6 characters'}), 400

        from app.database import db
        with db.cursor() as cursor:
            cursor.execute("SELECT email, password FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            stored_hash = user['password']
            email = user['email']
            
        if not User.verify_password(stored_hash, current_password):
            return jsonify({'success': False, 'message': 'Incorrect current password'}), 400
            
        success, msg = User.update_password(email, new_password)
        if success:
            return jsonify({'success': True, 'message': 'Password changed successfully'}), 200
        else:
            return jsonify({'success': False, 'message': msg}), 400
            
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500