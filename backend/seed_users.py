import sys
import os

# Add the project root to the python path so imports work when running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.models import User
from backend.core.password import hash_password

DEMO_USERS = [
    {
        "username": "victim1",
        "password_plain": "demo-victim-001",
        "role": "VICTIM",
        "case_id_ref": "AAROH-001"
    },
    {
        "username": "counsellor1",
        "password_plain": "demo-counsellor-001",
        "role": "COUNSELLOR"
    },
    {
        "username": "district_pune",
        "password_plain": "demo-district-001",
        "role": "DISTRICT_OFFICIAL",
        "district": "Pune"
    },
    {
        "username": "state_maharashtra",
        "password_plain": "demo-state-001",
        "role": "STATE_OFFICIAL",
        "state": "Maharashtra"
    },
    {
        "username": "national1",
        "password_plain": "demo-national-001",
        "role": "NATIONAL_OFFICIAL"
    },
    {
        "username": "admin1",
        "password_plain": "demo-admin-001",
        "role": "ADMIN"
    }
]

def seed_users():
    db = SessionLocal()
    try:
        print("Starting user seeding...")
        for user_data in DEMO_USERS:
            # Check if user exists
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            if existing:
                print(f"User {user_data['username']} already exists. Skipping.")
                continue

            # Ensure case_id_ref uniqueness (if any)
            if "case_id_ref" in user_data:
                existing_ref = db.query(User).filter(User.case_id_ref == user_data["case_id_ref"]).first()
                if existing_ref:
                    print(f"Case ID ref {user_data['case_id_ref']} already used. Skipping.")
                    continue

            new_user = User(
                username=user_data["username"],
                password_hash=hash_password(user_data["password_plain"]),
                role=user_data["role"],
                district=user_data.get("district"),
                state=user_data.get("state"),
                case_id_ref=user_data.get("case_id_ref")
            )
            db.add(new_user)
            print(f"Created user: {user_data['username']}")
        
        db.commit()
        print("User seeding completed.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
