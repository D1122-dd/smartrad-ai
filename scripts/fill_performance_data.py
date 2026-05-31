import os
import sys
import random
from datetime import datetime, timedelta

# Add parent directory to sys.path to import app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from app.database import db

def run():
    print("=== SmartRAD Performance Data Filler ===")
    user_input = input("Enter User Email or ID: ").strip()
    if not user_input:
        print("Invalid input.")
        return

    # Initialize DB
    try:
        db.initialize()
    except Exception as e:
        print(f"Could not connect to the database: {e}")
        return

    user_id = None
    with db.cursor() as cursor:
        if user_input.isdigit():
            cursor.execute("SELECT id FROM users WHERE id = %s", (int(user_input),))
        else:
            cursor.execute("SELECT id FROM users WHERE email = %s", (user_input,))
        
        row = cursor.fetchone()
        if row:
            user_id = row['id']
        else:
            print("User not found in database.")
            return

    print(f"Found User ID: {user_id}")

    flush = input("Do you want to flush (delete) old performance data for this user? (y/N): ").strip().lower()
    if flush == 'y':
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM history WHERE user_id = %s", (user_id,))
            db.commit()
            print("Old data flushed.")

    print("Generating 14 days of mock data...")
    now = datetime.now()
    
    rooms = [
        (1, 'X-Ray-1 - Room 1A'),
        (2, 'X-Ray-2 - Room 2B'),
        (3, 'X-Ray-3 - Room 1C'),
        (4, 'X-Ray-4 - Room 3D')
    ]
    exams = ['Chest', 'Spine', 'Pelvis', 'Hand', 'Knee', 'Shoulder', 'Abdomen']
    modalities = ['DX', 'CR']

    inserted_count = 0
    with db.cursor() as cursor:
        # Loop over last 14 days (0 to 14)
        for day_offset in range(14, -1, -1):
            date_base = now - timedelta(days=day_offset)
            
            # Generate 5-25 cases per day
            cases_today = random.randint(5, 25)
            for _ in range(cases_today):
                room_id, room_name = random.choice(rooms)
                exam_type = random.choice(exams)
                modality_type = random.choice(modalities)
                pred = random.randint(10, 25)
                actual = max(2, int(pred * random.uniform(0.5, 1.2)))
                is_urgent = 1 if random.random() < 0.2 else 0
                
                hour = random.randint(8, 17)
                minute = random.randint(0, 59)
                completed_at = date_base.replace(hour=hour, minute=minute, second=random.randint(0, 59))

                patient_id = random.randint(1000, 9999)
                patient_name = f"Patient {patient_id}"

                cursor.execute("""
                    INSERT INTO history 
                    (patient_id, patient_name, room_id, room_name, exam_type, modality_type, 
                     predicted_duration, actual_duration, is_urgent, user_id, completed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (patient_id, patient_name, room_id, room_name, exam_type, modality_type, 
                      pred, actual, is_urgent, user_id, completed_at))
                
                inserted_count += 1
        
        db.commit()
    
    print(f"Success! Inserted {inserted_count} mock cases for User ID {user_id}.")

if __name__ == '__main__':
    run()
