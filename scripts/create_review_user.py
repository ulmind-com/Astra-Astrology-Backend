"""Create or update a dedicated Google Play Review Test Account.

Usage:
    .venv/bin/python -m scripts.create_review_user
"""

import asyncio
from datetime import date, datetime, timezone
import sys

from app.core.config import settings
from app.core.security import hash_password
from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.models.enums import AccountStatus, AuthProvider, Gender, MaritalStatus, UserRole
from app.models.profile import BirthDetails, CurrentLocation
from app.models.user import User
from app.models.wallet import Wallet
from app.services import firebase

TEST_EMAIL = "google.review@divinlink.com"
TEST_PASSWORD = "DivinLink@Review2026"
TEST_NAME = "Google Review Tester"
WALLET_COINS = 100000  # 100,000 coins for testing consultations


async def main() -> int:
    print(f"Creating / Updating review user: {TEST_EMAIL}...")
    await connect_to_mongo()
    firebase.init_firebase()

    try:
        # 1. Firebase Mirroring
        firebase_uid = None
        if firebase.is_enabled():
            twin = await firebase.get_user_by_email(TEST_EMAIL)
            if twin is not None:
                await firebase.update_user(
                    twin.uid, password=TEST_PASSWORD, email_verified=True, display_name=TEST_NAME
                )
                firebase_uid = twin.uid
                print(f"Firebase user updated: {twin.uid}")
            else:
                record = await firebase.create_user(
                    email=TEST_EMAIL,
                    password=TEST_PASSWORD,
                    display_name=TEST_NAME,
                    email_verified=True,
                )
                firebase_uid = record.uid
                print(f"Firebase user created: {record.uid}")

        # 2. Birth Details so tester has full astrology access immediately
        birth = BirthDetails(
            date_of_birth=date(1995, 5, 15),
            time_of_birth="10:30",
            is_time_known=True,
            place="New Delhi, Delhi, India",
            city="New Delhi",
            state="Delhi",
            country="India",
            latitude=28.6139,
            longitude=77.2090,
            timezone="Asia/Kolkata",
            timezone_offset=5.5,
        )

        current_location = CurrentLocation(
            city="New Delhi",
            state="Delhi",
            country="India",
            latitude=28.6139,
            longitude=77.2090,
        )

        user = await User.find_one(User.email == TEST_EMAIL)
        if user is None:
            user = User(
                email=TEST_EMAIL,
                first_name="Google",
                last_name="Tester",
                hashed_password=hash_password(TEST_PASSWORD),
                firebase_uid=firebase_uid,
                auth_providers=[AuthProvider.PASSWORD],
                role=UserRole.USER,
                status=AccountStatus.ACTIVE,
                is_email_verified=True,
                phone="+919876543210",
                is_phone_verified=True,
                gender=Gender.MALE,
                marital_status=MaritalStatus.SINGLE,
                language="en",
                birth=birth,
                current_location=current_location,
            )
            await user.insert()
            print(f"User created in MongoDB: {user.id}")
        else:
            user.hashed_password = hash_password(TEST_PASSWORD)
            user.first_name = "Google"
            user.last_name = "Tester"
            user.role = UserRole.USER
            user.status = AccountStatus.ACTIVE
            user.is_email_verified = True
            user.phone = "+919876543210"
            user.is_phone_verified = True
            user.birth = birth
            user.current_location = current_location
            if firebase_uid:
                user.firebase_uid = firebase_uid
            user.add_provider(AuthProvider.PASSWORD)
            await user.save()
            print(f"User updated in MongoDB: {user.id}")

        # 3. Create or Update Wallet with 100,000 Coins
        wallet = await Wallet.find_one(Wallet.user_id == user.id)
        if wallet is None:
            wallet = Wallet(
                user_id=user.id,
                balance_coins=WALLET_COINS,
                is_frozen=False,
                last_transaction_at=datetime.now(timezone.utc),
            )
            await wallet.insert()
            print(f"Wallet created with {WALLET_COINS} coins for user {user.id}")
        else:
            wallet.balance_coins = max(wallet.balance_coins, WALLET_COINS)
            wallet.is_frozen = False
            await wallet.save()
            print(f"Wallet updated: now has {wallet.balance_coins} coins")

        print("\nSUCCESS! Google Play Review credentials ready:")
        print(f"Email: {TEST_EMAIL}")
        print(f"Password: {TEST_PASSWORD}")
        print(f"Balance Coins: {wallet.balance_coins}")
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
