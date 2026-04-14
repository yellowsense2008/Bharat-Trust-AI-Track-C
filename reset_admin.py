"""
Reset or create admin user in the local SQLite database.
Usage: python reset_admin.py
"""
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import hash_password

ADMIN_EMAIL = "admin@bharattrust.ai"
ADMIN_PASSWORD = "Admin@1234"
ADMIN_NAME = "Admin"

Base.metadata.create_all(bind=engine)

db = SessionLocal()

admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()

if admin:
    admin.password_hash = hash_password(ADMIN_PASSWORD)
    print(f"Password reset for {ADMIN_EMAIL}")
else:
    admin = User(
        name=ADMIN_NAME,
        email=ADMIN_EMAIL,
        password_hash=hash_password(ADMIN_PASSWORD),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    print(f"Admin user created: {ADMIN_EMAIL}")

db.commit()
db.close()

print(f"Email:    {ADMIN_EMAIL}")
print(f"Password: {ADMIN_PASSWORD}")
