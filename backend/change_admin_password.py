#!/usr/bin/env python3
"""
Change admin user password

Usage:
    python change_admin_password.py <new_password>
    or
    NEW_ADMIN_PASSWORD=<password> python change_admin_password.py
"""
import os
import sys
from getpass import getpass

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.db.models import User
from app.core.security import get_password_hash


def change_admin_password(new_password=None):
    """Change admin password"""
    db = SessionLocal()

    try:
        # Find admin user
        admin = db.query(User).filter(User.username == "admin").first()

        if not admin:
            print("❌ Admin user not found!")
            print("Available users:")
            users = db.query(User).all()
            for user in users:
                print(f"  - {user.username} ({user.email})")
            return False

        print(f"✅ Found admin user: {admin.username} ({admin.email})")
        print()

        # Get new password from argument, env var, or prompt
        if new_password is None:
            new_password = os.environ.get('NEW_ADMIN_PASSWORD')

        if new_password is None:
            # Interactive mode
            while True:
                new_password = getpass("Enter new password (min 8 characters): ")

                if len(new_password) < 8:
                    print("❌ Password must be at least 8 characters long!")
                    continue

                confirm_password = getpass("Confirm new password: ")

                if new_password != confirm_password:
                    print("❌ Passwords do not match!")
                    continue

                break

        # Validate password
        if len(new_password) < 8:
            print("❌ Password must be at least 8 characters long!")
            return False

        # Update password
        admin.hashed_password = get_password_hash(new_password)
        db.commit()

        print()
        print("✅ Password updated successfully!")
        print(f"Username: {admin.username}")
        print(f"Email: {admin.email}")
        print()
        print("⚠️  IMPORTANT: Save the new password securely!")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Change Admin Password")
    print("=" * 50)
    print()

    # Get password from command line argument if provided
    password = sys.argv[1] if len(sys.argv) > 1 else None

    success = change_admin_password(password)

    sys.exit(0 if success else 1)
