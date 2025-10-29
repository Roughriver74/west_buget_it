"""
Script to create default admin user
Run this after applying migrations: python create_admin.py

Environment variables (optional):
- ADMIN_USERNAME: Admin username (default: admin)
- ADMIN_PASSWORD: Admin password (default: admin)
- ADMIN_EMAIL: Admin email (default: admin@example.com)
- ADMIN_FULL_NAME: Admin full name (default: System Administrator)
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.db.models import User, UserRoleEnum
from app.utils.auth import get_password_hash


def create_admin_user():
    """Create default admin user if not exists"""
    db = SessionLocal()

    # Get admin credentials from environment variables
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_full_name = os.getenv("ADMIN_FULL_NAME", "System Administrator")

    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == admin_username).first()

        if existing_admin:
            print("✓ Admin user already exists!")
            print(f"Username: {existing_admin.username}")
            print(f"Email: {existing_admin.email}")
            return

        # Create admin user
        admin_user = User(
            username=admin_username,
            email=admin_email,
            full_name=admin_full_name,
            hashed_password=get_password_hash(admin_password),
            role=UserRoleEnum.ADMIN,
            is_active=True,
            is_verified=True,
            department_id=1,  # IT Department
            position="Administrator"
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✓ Admin user created successfully!")
        print(f"Username: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        if admin_password == "admin":
            print(f"Password: {admin_password}")
            print("\n⚠️  IMPORTANT: Using default password! Please change it after first login!")
        else:
            print(f"Password: (from ADMIN_PASSWORD env var)")

    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
