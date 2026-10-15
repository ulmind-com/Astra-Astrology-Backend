"""Create the first admin, so the admin panel has someone to sign in as.

    uv run python -m scripts.create_admin

Reads FIRST_ADMIN_* from .env and prompts for whatever is missing. Running it
again on an existing email promotes that account and resets its password.
"""

import asyncio
import getpass
import sys

from app.core.config import settings
from app.core.security import hash_password
from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.models.enums import AuthProvider, UserRole
from app.models.user import User
from app.services import firebase


async def main() -> int:
    name = settings.FIRST_ADMIN_NAME or input("Admin name: ").strip()
    email = (settings.FIRST_ADMIN_EMAIL or input("Admin email: ").strip()).lower()
    password = settings.FIRST_ADMIN_PASSWORD or getpass.getpass("Admin password: ")

    if not email or not password:
        print("An email and a password are both required.")
        return 1
    if len(password) < 6:
        print("The password must be at least 6 characters (Firebase's minimum).")
        return 1

    await connect_to_mongo()
    firebase.init_firebase()
    try:
        existing = await User.find_one(User.email == email)
        if existing is not None:
            existing.role = UserRole.SUPER_ADMIN
            existing.hashed_password = hash_password(password)
            existing.is_email_verified = True
            existing.add_provider(AuthProvider.PASSWORD)
            await existing.save()
            if firebase.is_enabled() and existing.firebase_uid:
                await firebase.update_user(existing.firebase_uid, password=password)
            print(f"Existing account {email} promoted to super admin, password reset.")
            return 0

        firebase_uid = None
        if firebase.is_enabled():
            twin = await firebase.get_user_by_email(email)
            if twin is not None:
                await firebase.update_user(twin.uid, password=password, email_verified=True)
                firebase_uid = twin.uid
            else:
                record = await firebase.create_user(
                    email=email, password=password, display_name=name, email_verified=True
                )
                firebase_uid = record.uid

        user = User(
            email=email,
            first_name=name.split()[0] if name else "Admin",
            last_name=" ".join(name.split()[1:]) or None if name else None,
            hashed_password=hash_password(password),
            firebase_uid=firebase_uid,
            auth_providers=[AuthProvider.PASSWORD],
            role=UserRole.SUPER_ADMIN,
            is_email_verified=True,
        )
        await user.insert()
        print(f"Super admin created: {email} (id {user.id})")
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
