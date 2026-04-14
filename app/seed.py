"""
Seed script - creates default admin and test user if they don't exist.
Run once after deploy: python3 -m app.seed
"""
import os
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def seed():
    db = SessionLocal()
    try:
        # Create admin if not exists
        admin = db.query(User).filter(User.email == "admin@grievance.com").first()
        if not admin:
            admin = User(
                name="Admin",
                email="admin@grievance.com",
                hashed_password=get_password_hash("admin@123"),
                role="admin",
                is_active=True
            )
            db.add(admin)
            print("✅ Admin created: admin@grievance.com / admin@123")
        else:
            print("ℹ️  Admin already exists")

        # Create test citizen if not exists
        citizen = db.query(User).filter(User.email == "citizen@grievance.com").first()
        if not citizen:
            citizen = User(
                name="Test Citizen",
                email="citizen@grievance.com",
                hashed_password=get_password_hash("citizen@123"),
                role="citizen",
                is_active=True
            )
            db.add(citizen)
            print("✅ Citizen created: citizen@grievance.com / citizen@123")
        else:
            print("ℹ️  Citizen already exists")

        db.commit()
        print("✅ Seed complete")
    except Exception as e:
        print(f"❌ Seed failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
