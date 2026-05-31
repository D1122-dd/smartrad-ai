from app.database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_tables():
    db.initialize()
    try:
        with db.cursor() as cursor:
            for table in ['rooms', 'patients', 'history']:
                try:
                    cursor.execute(f"DESCRIBE {table}")
                    columns = cursor.fetchall()
                    logger.info(f"\nTable: {table}")
                    for col in columns:
                        logger.info(f"  Column: {col['Field']} | Type: {col['Type']}")
                except Exception as e:
                    logger.error(f"Error describing {table}: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    check_tables()
