#!/usr/bin/env python3
"""
Reset Admin Password Script

Usage:
    cd backend
    source venv/bin/activate
    python scripts/reset_admin_password.py

This script will:
- Create an admin user if none exists
- Reset the admin password if the user exists
- Generate a secure random password
"""

import secrets
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User
from app.utils.auth import hash_password


def reset_admin_password():
    """Create or reset the admin user password."""
    # Generate a new secure password
    new_password = secrets.token_urlsafe(16)

    db = SessionLocal()
    try:
        # Check if any users exist
        user_count = db.query(User).count()

        if user_count == 0:
            # Create admin user
            admin = User(
                username="admin",
                password_hash=hash_password(new_password),
                is_active=True,
            )
            db.add(admin)
            db.commit()

            print("Admin user created successfully!")
            print("")
            print(f"Username: admin")
            print(f"Password: {new_password}")
            print("")
            print("Please save this password securely and change it after login.")
        else:
            # Reset existing admin
            admin = db.query(User).filter(User.username == "admin").first()
            if admin:
                admin.password_hash = hash_password(new_password)
                db.commit()
                print("Admin password reset successfully!")
                print("")
                print(f"Username: admin")
                print(f"New Password: {new_password}")
                print("")
                print("Please save this password securely and change it after login.")
            else:
                print("Admin user not found but other users exist.")
                print("Please check your database.")
    finally:
        db.close()


if __name__ == "__main__":
    reset_admin_password()
