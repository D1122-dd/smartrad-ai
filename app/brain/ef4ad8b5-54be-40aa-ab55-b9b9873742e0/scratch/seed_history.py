import random
import datetime
from app.database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample Data
FIRST_NAMES = ['Ahmed', 'Sara', 'Khalid', 'Fatima', 'Omar', 'Layla', 'Mohammed', 'Nora', 'Ali', 'Hana']
LAST_NAMES = ['Al-Rashid', 'Hassan', 'Al-Ghamdi', 'Abdullah', 'Al-Zahrani', 'Ibrahim', 'Al-Otaibi', 'Saleh']
EXAMS = [
    ('Chest', 'DX', 'Thorax'),
    ('Abdomen', 'DX', 'Abdomen'),
    ('Spine', 'CR', 'Spine'),
    ('Knee', 'DX', 'Lower_Limb'),
    ('Shoulder', 'CR', 'Upper_Limb')
]
ROOMS = [
    (1, 'Room 1A'),
    (2, 'Room 1B'),
    (3, 'Room 2A'),
    (4, 'Room 2B')
]

def seed_history(count=20):
    try:
        with db.cursor() as cursor:
            logger.info(f"Seeding {count} history records...")
            
            accurate_count = 0
            for i in range(count):
                name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                exam, modality, body = random.choice(EXAMS)
                room_id, room_name = random.choice(ROOMS)
                
                # To keep accuracy > 85%, make ~90% of records accurate (error <= 3)
                is_accurate = random.random() < 0.9
                predicted = random.randint(10, 25)
                
                if is_accurate:
                    actual = predicted + random.randint(-3, 3)
                    accurate_count += 1
                else:
                    actual = predicted + random.randint(4, 8) * random.choice([-1, 1])
                
                actual = max(5, actual) # Ensure at least 5 mins
                is_urgent = 1 if random.random() < 0.2 else 0
                
                # Random completion time within the last 7 days
                days_ago = random.randint(0, 7)
                hours_ago = random.randint(0, 23)
                completed_at = datetime.datetime.now() - datetime.timedelta(days=days_ago, hours=hours_ago)
                
                cursor.execute("""
                    INSERT INTO history 
                    (patient_id, patient_name, room_id, room_name, exam_type, modality_type, 
                     predicted_duration, actual_duration, is_urgent, completed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    random.randint(1000, 9999), # Dummy patient ID
                    name, room_id, room_name, exam, modality,
                    predicted, actual, is_urgent, completed_at
                ))
            
            db.commit()
            final_accuracy = (accurate_count / count) * 100
            logger.info(f"Successfully seeded {count} records. Seeded Accuracy: {final_accuracy}%")
            
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        db.rollback()

if __name__ == "__main__":
    seed_history(20)
