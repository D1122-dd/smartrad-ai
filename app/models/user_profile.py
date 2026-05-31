from app.database import db
import datetime
import logging

logger = logging.getLogger(__name__)

class UserProfile:
    """User Profile model"""
    
    @staticmethod
    def create_profile(user_id):
        """
        Create a new user profile
        Returns: (profile_id, message)
        """
        try:
            with db.cursor() as cursor:
                # Insert profile
                cursor.execute("""
                    INSERT INTO user_profile (user_id, created_at)
                    VALUES (%s, %s)
                """, (user_id, datetime.datetime.now()))
                
                db.commit()
                
                # Get the newly created profile ID
                cursor.execute("SELECT LAST_INSERT_ID() as id")
                result = cursor.fetchone()
                profile_id = result['id'] if result else None
                
                logger.info(f"Profile created successfully: {profile_id}")
                return profile_id, "Profile created successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating profile: {str(e)}")
            return None, f"Error creating profile: {str(e)}"
    
    @staticmethod
    def get_profile_by_user(user_id):
        """
        Get user profile by user_id
        Returns: profile dict or None
        """
        try:
            with db.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        id, user_id, profile_picture, bio, phone_number
                    FROM user_profile 
                    WHERE user_id = %s
                """, (user_id,))
                profile = cursor.fetchone()
                return profile
        except Exception as e:
            logger.error(f"Error getting profile: {str(e)}")
            return None
    
    @staticmethod
    def update_profile(user_id, **kwargs):
        """
        Update user profile (phone, bio only - no picture)
        Returns: (success, message)
        """
        try:
            with db.cursor() as cursor:
                # Build dynamic update query
                allowed_fields = ['bio', 'phone_number']
                updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
                
                if not updates:
                    return False, "No valid fields to update"
                
                set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
                values = list(updates.values()) + [user_id]
                
                query = f"UPDATE user_profile SET {set_clause}, updated_at = NOW() WHERE user_id = %s"
                cursor.execute(query, values)
                
                db.commit()
                
                logger.info(f"Profile updated successfully for user: {user_id}")
                return True, "Profile updated successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating profile: {str(e)}")
            return False, f"Error updating profile: {str(e)}"