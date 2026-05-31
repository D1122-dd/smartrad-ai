from flask import Blueprint, request, jsonify, session
from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.jwt_handler import JWTHandler
from app import mail
from flask_mail import Message
import logging
import random
import string
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
logger = logging.getLogger(__name__)

# ============================================================
# ENDPOINT 1: REGISTER
# ============================================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register new user for AqarBot
    
    Expected JSON: {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123",
        "phone_number": "0551234567"  // optional
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        phone_number = data.get('phone_number', '').strip()
        
        # Call service
        result = AuthService.register(name, email, password, phone_number if phone_number else None)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Register error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error during registration: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 2: LOGIN
# ============================================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user
    
    Expected JSON: {
        "email": "john@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Call service
        result = AuthService.login(email, password)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error during login: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 3: VERIFY TOKEN
# ============================================================

@auth_bp.route('/verify-token', methods=['GET'])
def verify_token():
    """
    Verify if token is valid
    
    Expected header: Authorization: Bearer <token>
    """
    try:
        # Extract token
        token = JWTHandler.extract_token_from_header(request)
        
        # Call service
        result = AuthService.verify_token(token)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error verifying token: {str(e)}'
        }), 500
        

# ============================================================
# ENDPOINT 4: VERIFY EMAIL FOR PASSWORD RESET
# ============================================================

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Step 1: Verify email and send OTP
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400

        user = User.get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'message': 'No account found with this email'}), 404

        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Store in session
        session['reset_email'] = email
        session['reset_otp'] = otp
        session['reset_otp_expiry'] = (datetime.now() + timedelta(minutes=10)).timestamp()
        session['otp_verified'] = False

        # Send Email
        try:
            msg = Message(
                subject='Password Reset Code - SmartRAD AI',
                recipients=[email]
            )
            msg.body = f"Hello {user['name']},\n\nYour password reset code is: {otp}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this, please ignore this email.\n\nBest regards,\nSmartRAD AI Team"
            mail.send(msg)
            
            return jsonify({
                'success': True, 
                'message': 'Verification code sent to your email'
            }), 200
        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            return jsonify({
                'success': False, 
                'message': 'Failed to send verification email. Please check configuration.'
            }), 500

    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """
    Step 2: Verify the OTP sent to email
    """
    try:
        data = request.get_json()
        otp_input = data.get('otp', '').strip()
        email = data.get('email', '').strip().lower()

        if not otp_input or not email:
            return jsonify({'success': False, 'message': 'OTP and email are required'}), 400

        # Check session data
        stored_otp = session.get('reset_otp')
        stored_email = session.get('reset_email')
        expiry = session.get('reset_otp_expiry')

        if not stored_otp or stored_email != email:
            return jsonify({'success': False, 'message': 'Invalid session. Please request a new code.'}), 400

        if datetime.now().timestamp() > expiry:
            return jsonify({'success': False, 'message': 'OTP has expired. Please request a new code.'}), 400

        if stored_otp == otp_input:
            session['otp_verified'] = True
            return jsonify({'success': True, 'message': 'OTP verified successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid verification code'}), 400

    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Step 3: Reset password after successful OTP verification
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()
        new_password = data.get('new_password', '')

        # SECURITY CHECK: Must have verified OTP for this email
        if not session.get('otp_verified') or session.get('reset_email') != email:
            return jsonify({'success': False, 'message': 'Unauthorized. Please verify your email first.'}), 401

        if not email or not new_password:
            return jsonify({'success': False, 'message': 'Email and new password are required'}), 400

        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400

        # Verify user still exists
        user = User.get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'message': 'Account not found'}), 404

        success, message = User.update_password(email, new_password)

        if success:
            # Clear session after successful reset
            session.pop('reset_email', None)
            session.pop('reset_otp', None)
            session.pop('reset_otp_expiry', None)
            session.pop('otp_verified', None)
            return jsonify({'success': True, 'message': 'Password reset successfully'}), 200
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500