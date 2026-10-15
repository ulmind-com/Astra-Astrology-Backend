# Astra Astrology — Backend

FastAPI backend for the Astra Astrology platform.

**Stack:** Python 3.12 · FastAPI · uv · MongoDB (Beanie ODM) · Cloudinary · Resend

> Current scope: project setup + **user registration**. Everything else gets
> added under `app/api/v1/` as it is built.

---

## Quick start

```bash
uv sync --extra dev          # create .venv and install everything
```

`.env` already exists with a generated `SECRET_KEY` — fill in `MONGODB_URI`
(and Resend/Cloudinary when you need them), then:

```bash
uv run uvicorn app.main:app --reload
```

- API → http://localhost:8000
- Swagger → http://localhost:8000/docs
- ReDoc → http://localhost:8000/redoc
- Health → http://localhost:8000/api/v1/health

## Environment

| Variable | Where to get it |
| --- | --- |
| `MONGODB_URI` | MongoDB Atlas → Connect → Drivers (`mongodb+srv://...`) |
| `RESEND_API_KEY` | https://resend.com/api-keys |
| `RESEND_FROM_EMAIL` | An address on a domain verified in Resend |
| `CLOUDINARY_CLOUD_NAME` / `_API_KEY` / `_API_SECRET` | Cloudinary console → Dashboard |
| `JWT_SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `FIREBASE_CREDENTIALS_PATH` | Firebase console → Project settings → Service accounts → Generate new private key |
| `FIREBASE_CREDENTIALS_JSON` | The same JSON on one line, for hosts where you cannot upload a file (Render) |

Notes:

- URL-encode your Mongo password if it contains `@ : / ? # [ ] %`.
- `ALLOWED_ORIGINS` is a comma-separated list — add the deployed web and admin
  URLs before going live.
- Resend and Cloudinary are optional to boot: the app logs a warning and keeps
  running, and `/health` reports which ones are configured.

## Layout

```
app/
├── main.py              # app factory, lifespan, startup checks
├── core/
│   ├── config.py        # every env var, typed and validated
│   ├── middleware.py    # request id, access log, CORS
│   ├── exceptions.py    # AppError hierarchy + uniform JSON error handlers
│   └── logging.py       # loguru, with stdlib/uvicorn logs routed through it
├── db/mongodb.py        # connection lifecycle + Beanie init
├── models/
│   ├── base.py          # TimestampedDocument (created_at / updated_at)
│   └── __init__.py      # DOCUMENT_MODELS registry — add each new model here
├── core/
│   ├── security.py      # bcrypt hashing, JWT access/refresh tokens
│   └── crypto.py        # reversible encryption for the pending password
├── models/
│   ├── user.py          # the account
│   ├── otp.py           # OTPs (hashed, TTL'd, attempt-capped)
│   └── pending_registration.py
├── schemas/
│   ├── common.py        # ApiResponse envelope, HealthStatus
│   └── auth.py          # registration requests/responses
├── services/
│   ├── registration.py  # the Firebase <-> MongoDB sync, with rollback
│   ├── firebase.py      # Firebase Auth wrapper
│   ├── otp.py           # generate / send / verify
│   ├── email.py         # send_email() via Resend
│   ├── email_templates.py
│   └── storage.py       # Cloudinary upload / delete
└── api/
    ├── dependencies.py  # CurrentUser, client context
    ├── router.py        # mounts every v1 router
    └── v1/
        ├── health.py    # GET /health, GET /ping
        └── auth.py      # registration + /auth/me
```

## Response shape

Every endpoint returns the same envelope, so clients handle it in one place.

```jsonc
// success
{ "success": true, "message": "Service is healthy", "data": { } }

// error
{ "success": false, "message": "Resource not found.", "error_code": "not_found" }
```

Raise one of the `AppError` subclasses in `app/core/exceptions.py`
(`BadRequestError`, `UnauthorizedError`, `ForbiddenError`, `NotFoundError`,
`ConflictError`, `TooManyRequestsError`, `ServiceUnavailableError`) and the
handler turns it into that shape. Validation failures come back as a `422` with
a `details` array of `{ field, message, type }`.

## Adding a model

```python
# app/models/horoscope.py
from app.models.base import TimestampedDocument

class Horoscope(TimestampedDocument):
    sign: str
    body: str

    class Settings(TimestampedDocument.Settings):
        name = "horoscopes"
```

Then add it to `DOCUMENT_MODELS` in `app/models/__init__.py`; Beanie registers
it and creates its indexes on the next startup.

## Registration

Two ways in. **Both create the account in Firebase Auth *and* MongoDB**, and the
account exists in both or in neither — see "Staying in sync" below.

### Manual — email + password, verified by OTP

```
POST /api/v1/auth/register/email
     { email, password, first_name, middle_name?, last_name? }
  -> checks the email in MongoDB *and* Firebase
  -> 409 if it is already registered
  -> otherwise parks the details and emails a 6-digit code

POST /api/v1/auth/register/email/verify
     { email, code }
  -> 201, creates the account in Firebase + MongoDB, returns user + tokens,
     and sends the welcome email

POST /api/v1/auth/register/email/resend   { email }
GET  /api/v1/auth/email/available?email=  -> { available, exists_in }
```

Nothing is written to either store until the code is verified: the half-finished
sign-up lives in `pending_registrations`, which has a TTL. There are **no
password strength rules** — the user picks whatever they want (only the 72-byte
bcrypt ceiling is enforced).

### Google

```
POST /api/v1/auth/google   { id_token }
```

The client signs in with Google through the Firebase SDK and posts the resulting
ID token. The backend verifies it, then:

- **account exists** → signs in (`is_new_user: false`)
- **account is new** → registers, pulling the name and photo straight from
  Google, and sends the welcome email (`is_new_user: true`)
- **email matches an account registered with a password** → links the Google
  identity to it rather than creating a second account

The display name is split across `first_name` / `middle_name` / `last_name`
("Ravi Shankar Sharma" → Ravi / Shankar / Sharma).

### Staying in sync

The rule the registration service is built around: **an account exists in both
stores or in neither.**

- Firebase is written first, MongoDB second. If the MongoDB insert fails, the
  Firebase user that was just created is **deleted again**.
- If Firebase is unreachable, sign-up is refused up front rather than creating a
  MongoDB user with no twin (`FIREBASE_REQUIRED=true`). Set it to `false` only
  for local work without Firebase credentials.
- An email found **in Firebase but not MongoDB** is a sign-up that died halfway.
  It is not treated as taken: once the OTP proves the person owns the email,
  that Firebase user is adopted instead of refusing them forever.
- The password is encrypted (not hashed) while a sign-up waits on its OTP,
  because Firebase needs it in plaintext at creation time. The record is
  short-lived, TTL'd, and deleted the moment it is used. MongoDB stores only a
  bcrypt hash.

Syncing happens **at creation only** — later profile edits are not mirrored.

### Collections

| Collection | Holds |
| --- | --- |
| `users` | the account; unique index on `email` and on `firebase_uid` |
| `otp_codes` | OTPs, stored as an HMAC, TTL'd, attempt-capped |
| `pending_registrations` | sign-ups awaiting their OTP, TTL'd |

## Uptime monitoring (keep the Render instance awake)

Deployed at `https://astra-astrology-backend.onrender.com`. Render's free tier
spins an instance down after ~15 minutes of inactivity, so UptimeRobot and
cron-job.org ping it to keep it warm.

Point monitors at either endpoint — both accept **GET and HEAD**:

| Endpoint | Touches the DB | Use for |
| --- | --- | --- |
| `/api/v1/ping` | no | keep-alive (cheapest, answers in ~2 ms) |
| `/api/v1/health` | yes (bounded) | keep-alive + a real status readout |

Suggested settings:

- **UptimeRobot** — HTTP(s) monitor, interval **5 minutes**. It sends `HEAD` by
  default, which these routes support.
- **cron-job.org** — every **5 minutes**, request timeout **30s**. The generous
  timeout covers a cold start, which can take 30–60s if the instance did manage
  to sleep.

Why the monitors stay green:

- `GET` *and* `HEAD` are both registered. FastAPI's router does not add `HEAD`
  automatically, and a `HEAD` request against a GET-only route returns `405` —
  that was the original source of UptimeRobot errors.
- Both endpoints always answer `200`. A database problem shows up as
  `data.status == "degraded"` in the body rather than an HTTP error.
- A failed database connection at startup is **not** fatal: the app boots,
  serves `/health` as degraded, and finishes its setup on the next successful
  ping. Previously an unreachable Atlas would crash startup and Render would
  serve `502`.
- The database ping is capped by `HEALTH_DB_TIMEOUT_SECONDS` (default 3s), so
  health never hangs.
- Both send `Cache-Control: no-store`, so a CDN can't serve a cached `200`
  while the instance sleeps behind it.

If you *do* want alerting on a real outage, add a second UptimeRobot **keyword**
monitor on `/api/v1/health` that expects `"status":"ok"`.

### Render settings worth checking

- Point Render's own **Health Check Path** at `/api/v1/health`.
- MongoDB Atlas → Network Access must allow Render's egress (`0.0.0.0/0` on the
  free tier, since Render doesn't give a static outbound IP there).

## Deploying to production

> ⚠️ **Set every variable below in one go.** The app *refuses to start* when
> `APP_ENV=production` and any of them is unsafe, so a half-finished environment
> means a failed deploy rather than a broken-but-running service. That is
> deliberate: the alternative is leaking OTPs or signing tokens with a guessable
> key.

| Variable | Production value |
| --- | --- |
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `OTP_DEV_MODE` | **`false`** — `true` would return sign-up codes in API responses |
| `SECRET_KEY` | a fresh `secrets.token_urlsafe(48)` |
| `JWT_SECRET_KEY` | a different fresh `secrets.token_urlsafe(48)`, at least 32 chars |
| `FIREBASE_REQUIRED` | `true` |
| `FIREBASE_PROJECT_ID` | your Firebase project id |
| `FIREBASE_CREDENTIALS_JSON` | the whole service-account JSON **on one line** |
| `FIREBASE_CREDENTIALS_PATH` | leave unset — Render has no file to point at |
| `ALLOWED_ORIGINS` | your real web + admin URLs, not `*` |

Everything else (`MONGODB_URI`, `RESEND_*`, `CLOUDINARY_*`) carries over.

Startup refuses to continue on any of these, and logs each one as
`CONFIG: ...` before exiting:

- `OTP_DEV_MODE` is on
- `SECRET_KEY` or `JWT_SECRET_KEY` left at the default, or a JWT key under 32 chars
- `FIREBASE_REQUIRED` is on with no credentials (nobody could register)
- `RESEND_API_KEY` missing (sign-up codes could not be delivered)

`DEBUG=true` and `ALLOWED_ORIGINS=*` only warn.

To produce the one-line Firebase JSON:

```bash
python3 -c "import json,pathlib; print(json.dumps(json.loads(pathlib.Path('secrets/firebase.json').read_text()),separators=(',',':')))"
```

In production `/docs`, `/redoc` and `/openapi.json` all return 404.

### Firebase console setup

- **Authentication → Sign-in method**: enable **Email/Password** and **Google**.
- **Project settings → Service accounts → Generate new private key** gives the
  JSON above. It is a secret; `secrets/` and `*firebase-adminsdk*.json` are
  gitignored.
- The **client** config (apiKey, authDomain, …) under *Project settings →
  General → Your apps* is a different thing: it is public, and the web and
  mobile apps need it to do the Google sign-in that produces the `id_token`.

### A note on password length

Firebase Auth enforces a **6-character minimum** on passwords. There are no
strength rules beyond that — no uppercase, digit or symbol requirements — but
the floor cannot be turned off while Firebase owns email/password sign-in, so
the API rejects anything shorter *before* sending an OTP rather than failing
after the user has already typed the code in.

## Commands

```bash
uv run uvicorn app.main:app --reload       # dev server
MONGODB_URI=... uv run pytest -q           # tests (need a reachable MongoDB)
uv run ruff check app --fix                # lint
uv run ruff format app                     # format
docker build -t astra-backend .            # container image
```
