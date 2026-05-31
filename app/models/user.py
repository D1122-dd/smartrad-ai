from app.database import db
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import logging

logger = logging.getLogger(__name__)

class User:
    """User model"""
    
    @staticmethod
    def create_user(name, email, password, phone_number=None):
        """
        Create a new user for AqarBot
        
        Args:
            name: User's full name (required)
            email: User's email address (required)
            password: User's password (required)
            phone_number: User's phone number (optional, for agent contact)
        
        Returns: 
            (user_id, message) - user_id if success, None if failed
        """
        try:
            with db.cursor() as cursor:
                # Check if email already exists
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                existing_email = cursor.fetchone()
                
                if existing_email:
                    return None, "Email already exists"
                
                # Validate phone_number if provided
                if phone_number and len(phone_number) < 7:
                    return None, "Phone number must be at least 7 characters"
                
                # Hash password
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
                
                # Insert user
                cursor.execute("""
                    INSERT INTO users (name, email, password, phone_number, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (name, email, hashed_password, phone_number, datetime.datetime.now()))
                
                db.commit()
                
                # Get the newly created user ID
                cursor.execute("SELECT LAST_INSERT_ID() as id")
                result = cursor.fetchone()
                user_id = result['id'] if result else None
                
                logger.info(f"User created successfully: {user_id}")
                return user_id, "User created successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            return None, f"Error creating user: {str(e)}"
    
    @staticmethod
    def get_user_by_email(email):
        """
        Get user by email
        Returns: user dict or None
        """
        try:
            with db.cursor() as cursor:
                cursor.execute("SELECT id, name, email, password, profile_image FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                return user
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id):
        """
        Get user by ID
        Returns: user dict or None
        """
        try:
            with db.cursor() as cursor:
                cursor.execute("SELECT id, name, email, phone_number, profile_image FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                return user
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None
    
    @staticmethod
    def verify_password(stored_password_hash, provided_password):
        """
        Verify password
        Returns: True if password matches, False otherwise
        """
        try:
            return check_password_hash(stored_password_hash, provided_password)
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False
        
        
    @staticmethod
    def update_password(email, new_password):
        try:
            with db.cursor() as cursor:
                hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
                cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
                db.commit()
                logger.info(f"Password updated for email: {email}")
                return True, "Password updated successfully"
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating password: {str(e)}")
            return False, f"Error updating password: {str(e)}"