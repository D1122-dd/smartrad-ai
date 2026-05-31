from functools import wraps
from flask import request, jsonify
from app.utils.jwt_handler import JWTHandler

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = JWTHandler.extract_token_from_header(request)
        if not token:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        user_id = JWTHandler.verify_token(token)
        if not user_id:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401
        
        # Pass user_id to the decorated function
        return f(user_id, *args, **kwargs)
    
    return decorated_function
