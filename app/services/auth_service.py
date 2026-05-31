from app.models.user import User
from app.models.user_profile import UserProfile
from app.utils.jwt_handler import JWTHandler
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service - business logic"""
    
    @staticmethod
    def register(name, email, password, phone_number=None):
        """
        Register new user for SmartRAD AI
        
        Args:
            name: User's full name (required)
            email: User's email address (required)
            password: User's password (required)
            phone_number: User's phone number (optional)
        
        Returns: 
            dict with success status and data
        """
        try:
            # Validate inputs
            if not name or len(name) < 2:
                return {
                    'success': False,
                    'message': 'Name must be at least 2 characters'
                }
            
            if not email or '@' not in email:
                return {
                    'success': False,
                    'message': 'Valid email is required'
                }
            
            if not password or len(password) < 6:
                return {
                    'success': False,
                    'message': 'Password must be at least 6 characters'
                }
            
            # Validate phone_number if provided
            if phone_number and len(phone_number) < 7:
                return {
                    'success': False,
                    'message': 'Phone number must be at least 7 characters'
                }
            
            # Create user
            user_id, user_message = User.create_user(name, email, password, phone_number)
            
            if user_id is None:
                return {
                    'success': False,
                    'message': user_message
                }
            
            # Create user profile
            profile_id, profile_message = UserProfile.create_profile(user_id)
            
            # Initialize dedicated rooms for this user
            from app.models.room import initialize_user_rooms
            initialize_user_rooms(user_id)
            
            # Generate token
            token = JWTHandler.generate_token(user_id)
            
            if token is None:
                logger.error(f"Failed to generate token for user {user_id}")
                return {
                    'success': False,
                    'message': 'Failed to generate authentication token'
                }
            
            return {
                'success': True,
                'message': 'User registered successfully',
                'user_id': user_id,
                'user_name': name,
                'profile_image': None,
                'token': token
            }
        
        except Exception as e:
            logger.error(f"Register error: {str(e)}")
            return {
                'success': False,
                'message': f'Error during registration: {str(e)}'
            }
    
    @staticmethod
    def login(email, password):
        """
        Login user
        
        Returns: 
            dict with success status and data
        """
        try:
            # Validate inputs
            if not email or not password:
                return {
                    'success': False,
                    'message': 'Email and password are required'
                }
            
            # Get user
            user = User.get_user_by_email(email)
            
            if not user:
                return {
                    'success': False,
                    'message': 'Invalid email or password'
                }
            
            # Verify password
            if not User.verify_password(user['password'], password):
                return {
                    'success': False,
                    'message': 'Invalid email or password'
                }
            
            # Generate token
            token = JWTHandler.generate_token(user['id'])
            
            if token is None:
                logger.error(f"Failed to generate token for user {user['id']}")
                return {
                    'success': False,
                    'message': 'Failed to generate authentication token'
                }
            
            return {
                'success': True,
                'message': 'Login successful',
                'user_id': user['id'],
                'user_name': user['name'],
                'profile_image': user.get('profile_image'),
                'token': token
            }
        
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return {
                'success': False,
                'message': f'Error during login: {str(e)}'
            }
    
    @staticmethod
    def verify_token(token):
        """
        Verify JWT token
        
        Returns: 
            dict with user info or error
        """
        try:
            if not token:
                return {
                    'success': False,
                    'message': 'No token provided'
                }
            
            # Verify token
            user_id = JWTHandler.verify_token(token)
            
            if user_id is None:
                return {
                    'success': False,
                    'message': 'Invalid or expired token'
                }
            
            # Get user info
            user = User.get_user_by_id(user_id)
            
            if not user:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            return {
                'success': True,
                'message': 'Token is valid',
                'user_id': user_id,
                'user_name': user['name'],
                'profile_image': user.get('profile_image')
            }
        
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return {
                'success': False,
                'message': f'Error verifying token: {str(e)}'
            }