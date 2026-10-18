"""Removes astrologer accounts completely.

An astrologer lives in three places, and leaving any one behind causes trouble
later:

* MongoDB — the profile and the user account;
* Firebase — the sign-in identity. Leave this and the same email can never be
  used again: creating the account would fail with "email already exists";
* Cloudinary — the profile photo and gallery images, which otherwise sit there
  costing storage with nothing pointing at them.

Related call sessions go too, since the person they refer to is gone.

    uv run python scripts/delete_astrologers.py --db astra_astrology
    uv run python scripts/delete_astrologers.py --db astra_astrology --apply

Without --apply it only reports. One email can be spared with --keep.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from pymongo import AsyncMongoClient  # noqa: E402


async def main(db_name: str, apply: bool, keep: list[str]) -> int:
    client = AsyncMongoClient(settings.MONGODB_URI)
    db = client[db_name]

    profiles = await db.astrologers.find({}).to_list(length=None)
    if not profiles:
        print(f"{db_name}: no astrologers. Nothing to do.")
        await client.close()
        return 0

    keep_lower = {e.lower() for e in keep}
    targets = []
    for profile in profiles:
        user = await db.users.find_one({"_id": profile["user_id"]})
        email = (user or {}).get("email", "")
        if email.lower() in keep_lower:
            print(f"  keeping  {profile['display_name']} <{email}>")
            continue
        targets.append((profile, user))

    images: list[str] = []
    for profile, _ in targets:
        if profile.get("profile_image_public_id"):
            images.append(profile["profile_image_public_id"])
        for item in profile.get("gallery") or []:
            if item.get("public_id"):
                images.append(item["public_id"])

    firebase_uids = [u["firebase_uid"] for _, u in targets if u and u.get("firebase_uid")]
    user_ids = [u["_id"] for _, u in targets if u]
    profile_ids = [p["_id"] for p, _ in targets]

    calls = await db.call_sessions.count_documents({"astrologer_id": {"$in": profile_ids}})

    print(f"\n{db_name} — would remove:")
    for profile, user in targets:
        print(f"  - {profile['display_name']:<26} {(user or {}).get('email', '(no account)')}")
    print(f"\n  mongo profiles : {len(profile_ids)}")
    print(f"  mongo accounts : {len(user_ids)}")
    print(f"  firebase users : {len(firebase_uids)}")
    print(f"  cloudinary imgs: {len(images)}")
    print(f"  call sessions  : {calls}")

    if not apply:
        print("\nDry run — pass --apply to delete.")
        await client.close()
        return 0

    # Firebase first: if it fails we still have the Mongo record to retry from.
    # The other way round would leave an identity nobody can find.
    from app.services import firebase

    firebase.init_firebase()
    removed_fb = 0
    if firebase.is_enabled():
        for uid in firebase_uids:
            try:
                await firebase.delete_user(uid)
                removed_fb += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  ! firebase {uid}: {exc}")
    else:
        print("  ! Firebase is not configured — identities will be left behind,")
        print("    and those emails cannot be reused until they are removed.")

    from app.services import storage

    storage.configure_cloudinary()
    removed_img = 0
    for public_id in images:
        try:
            if await storage.delete_file(public_id):
                removed_img += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  ! cloudinary {public_id}: {exc}")

    r_calls = await db.call_sessions.delete_many({"astrologer_id": {"$in": profile_ids}})
    r_prof = await db.astrologers.delete_many({"_id": {"$in": profile_ids}})
    r_user = await db.users.delete_many({"_id": {"$in": user_ids}})

    print("\nDone:")
    print(f"  firebase users deleted : {removed_fb}/{len(firebase_uids)}")
    print(f"  cloudinary images      : {removed_img}/{len(images)}")
    print(f"  call sessions          : {r_calls.deleted_count}")
    print(f"  astrologer profiles    : {r_prof.deleted_count}")
    print(f"  user accounts          : {r_user.deleted_count}")
    print("\nThose emails are now free to use again.")
    await client.close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=settings.MONGODB_DB_NAME, help="database name")
    parser.add_argument("--apply", action="store_true", help="actually delete")
    parser.add_argument("--keep", action="append", default=[], help="email to spare")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.db, args.apply, args.keep)))
