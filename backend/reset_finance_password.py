import sys
from passlib.context import CryptContext
from app.db.session import SessionLocal
from app.db.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_password():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "finance").first()
        if not user:
            print("Creating finance user...")
            user = User(
                username="finance",
                email="finance@example.com",
                full_name="Finance Manager",
                role="MANAGER",
                department_id=8,
                is_active=True
            )
            db.add(user)
        
        # Set password to 'finance'
        user.hashed_password = pwd_context.hash("finance")
        db.commit()
        
        print(f"✅ User '{user.username}' password set to: finance")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role}")
        print(f"   Department ID: {user.department_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_password()
