import sys
import os
import logging

# Dynamically add the parent directory (code/) to the python path so it runs from anywhere
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_schema():
    db.initialize()
    try:
        with db.cursor() as cursor:
            # 1. Add user_id to patients
            try:
                cursor.execute("ALTER TABLE patients ADD COLUMN user_id INT(11) DEFAULT NULL")
                logger.info("Added user_id to patients")
            except Exception as e:
                logger.warning(f"patients update: {e}")

            # 2. Add user_id to rooms
            try:
                cursor.execute("ALTER TABLE rooms ADD COLUMN user_id INT(11) DEFAULT NULL")
                logger.info("Added user_id to rooms")
            except Exception as e:
                logger.warning(f"rooms update: {e}")

            # 3. Add user_id to history
            try:
                cursor.execute("ALTER TABLE history ADD COLUMN user_id INT(11) DEFAULT NULL")
                logger.info("Added user_id to history")
            except Exception as e:
                logger.warning(f"history update: {e}")

            # 4. Associate existing data with the first user (if any)
            cursor.execute("SELECT id FROM users LIMIT 1")
            user = cursor.fetchone()
            if user:
                uid = user['id']
                cursor.execute("UPDATE patients SET user_id = %s WHERE user_id IS NULL", (uid,))
                cursor.execute("UPDATE rooms SET user_id = %s WHERE user_id IS NULL", (uid,))
                cursor.execute("UPDATE history SET user_id = %s WHERE user_id IS NULL", (uid,))
                logger.info(f"Associated existing data with user {uid}")

            db.commit()
            logger.info("Schema update completed successfully")
    except Exception as e:
        logger.error(f"Schema update failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_schema()
