"""Publishes `firestore/firestore.rules` to the live project.

The rules are the only thing guarding chat and the live mirror, so they are
kept in the repository and pushed from here rather than pasted into a console
— a rule that exists only in someone's browser history is a rule nobody can
review.

    uv run python -m scripts.publish_firestore_rules          # publish
    uv run python -m scripts.publish_firestore_rules --check  # show what is live

Uses the same service-account credentials as the rest of the backend.
"""

import sys
from pathlib import Path

RULES_FILE = Path(__file__).resolve().parent.parent / "firestore" / "firestore.rules"
SCOPE = "https://www.googleapis.com/auth/cloud-platform"


def _session_and_project():
    import google.auth.transport.requests as tr
    from google.oauth2 import service_account

    from app.core.config import settings
    from app.services import firebase

    firebase.init_firebase()
    if not firebase.is_enabled():
        raise SystemExit("Firebase is not configured — set FIREBASE_CREDENTIALS_*.")

    if settings.FIREBASE_CREDENTIALS_JSON:
        import json

        info = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
        creds = service_account.Credentials.from_service_account_info(info, scopes=[SCOPE])
    else:
        creds = service_account.Credentials.from_service_account_file(
            settings.FIREBASE_CREDENTIALS_PATH, scopes=[SCOPE]
        )

    session = tr.AuthorizedSession(creds)
    return session, firebase.get_app().project_id


def live_rules() -> str:
    """The source of whatever ruleset the project is actually serving."""
    session, project = _session_and_project()
    base = f"https://firebaserules.googleapis.com/v1/projects/{project}"

    release = session.get(f"{base}/releases/cloud.firestore")
    release.raise_for_status()
    ruleset_name = release.json()["rulesetName"]

    ruleset = session.get(f"https://firebaserules.googleapis.com/v1/{ruleset_name}")
    ruleset.raise_for_status()
    files = ruleset.json()["source"]["files"]
    return "\n".join(f["content"] for f in files)


def publish() -> None:
    session, project = _session_and_project()
    base = f"https://firebaserules.googleapis.com/v1/projects/{project}"
    source = RULES_FILE.read_text()

    created = session.post(
        f"{base}/rulesets",
        json={"source": {"files": [{"name": "firestore.rules", "content": source}]}},
    )
    if not created.ok:
        raise SystemExit(f"Firebase rejected the rules:\n{created.text}")
    ruleset_name = created.json()["name"]

    # The release name in the body is the bare resource path, not the URL.
    release_name = f"projects/{project}/releases/cloud.firestore"
    released = session.patch(
        f"{base}/releases/cloud.firestore",
        json={"release": {"name": release_name, "rulesetName": ruleset_name}},
    )
    if not released.ok:
        raise SystemExit(f"Could not release the rules:\n{released.text}")

    print(f"Published {RULES_FILE.name} to {project} as {ruleset_name.rsplit('/', 1)[-1]}.")


if __name__ == "__main__":
    if "--check" in sys.argv:
        print(live_rules())
    else:
        publish()
