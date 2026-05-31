"""
mock_ris/generate_order.py
--------------------------
Run this script manually (or on a timer) to simulate a new patient order
arriving from the RIS (Radiology Information System).

Usage:
    python mock_ris/generate_order.py
    python mock_ris/generate_order.py --urgent   # force urgent case
"""

import json
import os
import random
import argparse
from datetime import datetime

# ── Output folder (watcher watches this) ──────────────────────────────────────
INCOMING_DIR = os.path.join(os.path.dirname( __file__), 'incoming')
os.makedirs(INCOMING_DIR, exist_ok=True)

# ── Sample data pools (match model training values) ───────────────────────────
REGIONAL_NAMES = {
    'Arabic': {
        'first_names': [
            'Ahmed', 'Sara', 'Khalid', 'Fatima', 'Omar', 'Layla', 'Mohammed', 'Nora', 'Ali', 'Hana', 'Yusuf', 'Maha',
            'Tariq', 'Zainab', 'Hassan', 'Aisha', 'Ibrahim', 'Mariam', 'Faisal', 'Salma', 'Abdullah', 'Rania', 'Majed', 'Noor',
            'Saeed', 'Yasmin', 'Saleh', 'Huda', 'Adel', 'Reem', 'Sami', 'Amal', 'Karim', 'Farah', 'Nasser', 'Lina', 'Walid'
        ],
        'last_names': [
            'Al-Rashid', 'Hassan', 'Al-Ghamdi', 'Abdullah', 'Al-Zahrani', 'Ibrahim', 'Al-Otaibi', 'Saleh', 'Al-Qahtani', 'Mansour',
            'Al-Fassi', 'Mahmoud', 'Al-Dosari', 'Hussein', 'Al-Maliki', 'Ali', 'Al-Nasser', 'Suleiman', 'Al-Harbi', 'Yousef',
            'Al-Mutairi', 'Othman', 'Al-Shehri', 'Qasim', 'Al-Subaie', 'Taleb', 'Al-Jaber', 'Zidan', 'Al-Saeed', 'Fayed'
        ]
    },
    'Western': {
        'first_names': [
            'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth',
            'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen',
            'Christopher', 'Lisa', 'Daniel', 'Nancy', 'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra',
            'Donald', 'Ashley', 'Steven', 'Kimberly', 'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle'
        ],
        'last_names': [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
            'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
            'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
            'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores'
        ]
    },
    'Asian': {
        'first_names': [
            'Wei', 'Yan', 'Ming', 'Li', 'Hua', 'Mei', 'Jian', 'Xin', 'Ping', 'Lei',
            'Ravi', 'Priya', 'Amit', 'Neha', 'Rahul', 'Anjali', 'Vikram', 'Sneha', 'Sanjay', 'Pooja',
            'Kenji', 'Yuki', 'Hiroshi', 'Sakura', 'Takeshi', 'Akiko', 'Taro', 'Yumi', 'Satoshi', 'Naomi',
            'Ji-Hoon', 'Min-Ji', 'Seo-Joon', 'Ji-Woo', 'Do-Yoon', 'Seo-Yeon', 'Gun-Woo', 'Ha-Eun', 'Min-Jun', 'Ji-Min'
        ],
        'last_names': [
            'Wang', 'Li', 'Zhang', 'Liu', 'Chen', 'Yang', 'Huang', 'Zhao', 'Wu', 'Zhou',
            'Patel', 'Sharma', 'Singh', 'Kumar', 'Gupta', 'Desai', 'Shah', 'Mehta', 'Rao', 'Joshi',
            'Sato', 'Suzuki', 'Takahashi', 'Tanaka', 'Watanabe', 'Ito', 'Yamamoto', 'Nakamura', 'Kobayashi', 'Kato',
            'Kim', 'Lee', 'Park', 'Choi', 'Jung', 'Kang', 'Cho', 'Yoon', 'Jang', 'Lim'
        ]
    }
}

PHYSICIANS = ['Dr. Al-Mutairi', 'Dr. Al-Qahtani', 'Dr. Al-Subaie', 'Dr. Al-Dossari', 'Dr. Al-Shehri']

CLINICAL_HISTORIES = {
    'Chest':    ['Cough and fever', 'Shortness of breath', 'Chest pain', 'Pre-op clearance'],
    'Abdomen':  ['Abdominal pain', 'Suspected appendicitis', 'Bloating', 'Follow-up on cyst'],
    'Spine':    ['Chronic back pain', 'Recent fall', 'Numbness in limbs', 'Radiculopathy'],
    'Knee':     ['ACL tear suspicion', 'Swelling after sports', 'Osteoarthritis follow-up'],
    'Shoulder': ['Rotator cuff injury', 'Dislocation', 'Frozen shoulder'],
    'Hand':     ['Suspected fracture', 'Arthritis', 'Crush injury'],
    'Pelvis':   ['Hip pain', 'Fall in elderly', 'Trauma'],
}

EXAM_BODY_MAP = {
    'Chest':    'Thorax',
    'Abdomen':  'Abdomen',
    'Spine':    'Spine',
    'Knee':     'Lower_Limb',
    'Shoulder': 'Upper_Limb',
    'Hand':     'Upper_Limb',
    'Pelvis':   'Lower_Limb',
}

MODALITY_WEIGHTS = {'DX': 0.75, 'CR': 0.25}   # mirrors dataset
AGE_GROUPS       = ['Child', 'Adult', 'Elderly']
AGE_WEIGHTS      = [0.12, 0.73, 0.15]

def generate_hl7(order):
    """Simulate a raw HL7 ORM^O01 message string."""
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    msh = f"MSH|^~\\&|RIS-SIM|HOSPITAL-X|DYYMA-AI|XRAY-DEPT|{now}||ORM^O01|{order['accession_number']}|P|2.3|||"
    pid = f"PID|1||{order['mrn']}||{order['patient_name']}||19850101|M|||123 Main St^^Riyadh^KSA|||||||"
    orc = f"ORC|NW|{order['order_id']}|||||1^once||{now}|{order['physician']}||||||"
    obr = f"OBR|1|{order['order_id']}||{order['exam_type']}^X-Ray|||{now}|||||||{order['history']}||||||||||P|"
    return f"{msh}\n{pid}\n{orc}\n{obr}"

def generate_order(force_urgent=False, count=1, user_id=None):
    generated_files = []
    for i in range(count):
        exam_type = random.choice(list(EXAM_BODY_MAP.keys()))
        modality  = random.choices(
            list(MODALITY_WEIGHTS.keys()),
            weights=list(MODALITY_WEIGHTS.values())
        )[0]
        
        # ── URGENCY BIAS LOGIC ────────────────────────────────────────────────
        if force_urgent:
            is_urgent = 1
        elif count > 1:
            is_urgent = 1 if (i + 1) % 3 == 0 else 0
        else:
            is_urgent = random.choices([0, 1], weights=[0.82, 0.18])[0]
        
        mrn = f"MRN-{random.randint(100000, 999999)}"
        acc = f"ACC-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
        physician = random.choice(PHYSICIANS)
        history = random.choice(CLINICAL_HISTORIES.get(exam_type, ['No history provided']))
        
        region = random.choice(list(REGIONAL_NAMES.keys()))
        first_name = random.choice(REGIONAL_NAMES[region]['first_names'])
        last_name = random.choice(REGIONAL_NAMES[region]['last_names'])

        order = {
            'order_id':         f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i}-{random.randint(100,999)}",
            'user_id':          user_id,
            'mrn':              mrn,
            'accession_number': acc,
            'patient_name':     f"{first_name} {last_name}",
            'patient_age_group': random.choices(AGE_GROUPS, weights=AGE_WEIGHTS)[0],
            'exam_type':        exam_type,
            'body_part':        EXAM_BODY_MAP[exam_type],
            'modality_type':    modality,
            'is_urgent':        is_urgent,
            'urgency_score':    random.randint(7, 10) if is_urgent else random.randint(1, 6),
            'physician':        physician,
            'history':          history,
            'request_time':     datetime.now().isoformat(),
            'source':           'Mock-RIS-HL7',
        }
        
        order['hl7_raw'] = generate_hl7(order)

        filename = f"{order['order_id']}.json"
        filepath = os.path.join(INCOMING_DIR, filename)

        with open(filepath, 'w') as f:
            json.dump(order, f, indent=2)

        print(f"\n[RIS] ⚡ NEW ORDER RECEIVED ({i+1}/{count})")
        print(f"      ───────────────────────────")
        print(f"      Accession : {order['accession_number']}")
        print(f"      Patient   : {order['patient_name']} ({order['mrn']})")
        print(f"      Exam      : {order['exam_type']} ({order['modality_type']})")
        print(f"      Physician : {order['physician']}")
        print(f"      Urgent    : {'YES 🔴' if is_urgent else 'No'}")
        print(f"      ───────────────────────────\n")
        generated_files.append(filepath)
    
    return generated_files[-1] if count == 1 else generated_files


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--urgent', action='store_true', help='Force urgent case')
    parser.add_argument('--count', type=int, default=1, help='Number of cases to generate')
    args = parser.parse_args()
    generate_order(force_urgent=args.urgent, count=args.count)
