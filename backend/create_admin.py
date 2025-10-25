"""
Script to create default admin user
Run this after applying migrations: python create_admin.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.db.models import User, UserRoleEnum
from app.utils.auth import get_password_hash


def create_admin_user():
    """Create default admin user if not exists"""
    db = SessionLocal()

    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()

        if existing_admin:
            print("Admin user already exists!")
            print(f"Username: {existing_admin.username}")
            print(f"Email: {existing_admin.email}")
            return

        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            full_name="System Administrator",
            hashed_password=get_password_hash("admin123"),  # Change this password after first login!
            role=UserRoleEnum.ADMIN,
            is_active=True,
            is_verified=True,
            department="IT",
            position="Administrator"
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✓ Admin user created successfully!")
        print(f"Username: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print(f"Password: admin123")
        print("\nIMPORTANT: Please change the password after first login!")

    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
