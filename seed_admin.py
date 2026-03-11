  
from database import SessionLocal
from models import User, UserRole
from auth import hash_password

db = SessionLocal()

# Check if admin already exists
existing = db.query(User).filter(User.email == "admin@vixon.co.ke").first()
if existing:
    print("Admin already exists!")
else:
    admin = User(
        full_name="Vixon Admin",
        email="admin@vixon.co.ke",
        hashed_password=hash_password("Kimj.jackson1"),
        role=UserRole.super_admin,
        is_active=True
    )
    db.add(admin)
    db.commit()
    print("Super admin created: admin@vixon.co.ke / Kimj.jackson1")

db.close()