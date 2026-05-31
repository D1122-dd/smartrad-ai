import jwt
from datetime import datetime, timedelta
from app.config import Config
import logging

logger = logging.getLogger(__name__)

class JWTHandler:
    """JWT token handler"""
    
    @staticmethod
    def generate_token(user_id, expires_in_days=30):
        """
        Generate JWT token
        Returns: token string or None if failed
        """
        try:
            payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(days=expires_in_days),
                'iat': datetime.utcnow()
            }
            token = jwt.encode(
                payload,
                Config.JWT_SECRET_KEY,
                algorithm='HS256'
            )
            return token
        except Exception as e:
            logger.error(f"Error generating token: {str(e)}")
            return None
    
    @staticmethod
    def verify_token(token):
        """
        Verify JWT token
        Returns: user_id if valid, None if invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                Config.JWT_SECRET_KEY,
                algorithms=['HS256']
            )
            return payload.get('user_id')
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None
    
    @staticmethod
    def extract_token_from_header(request):
        """
        Extract token from Authorization header
        Expected format: "Bearer <token>"
        Returns: token string or None
        """
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
        return None