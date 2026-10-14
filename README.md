# Astra Astrology — Backend

FastAPI backend for the Astra Astrology platform.

**Stack:** Python 3.12 · FastAPI · uv · MongoDB (Beanie ODM) · Cloudinary · Resend

> Current scope: project setup only. The one route is `/health`; feature routers
> get added under `app/api/v1/` as they are built.

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
├── schemas/common.py    # ApiResponse envelope, HealthStatus
├── services/
│   ├── email.py         # send_email() via Resend
│   ├── email_templates.py
│   └── storage.py       # Cloudinary upload / delete
└── api/
    ├── router.py        # mounts every v1 router
    └── v1/health.py     # GET /health, GET /ping
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

- Set `APP_ENV=production` in the Render environment (it currently reports
  `development`, which leaves `/docs` publicly open).
- Set `RESEND_API_KEY` when you start sending email — `/health` currently
  reports `resend: false`.
- Point Render's own **Health Check Path** at `/api/v1/health`.
- MongoDB Atlas → Network Access must allow Render's egress (`0.0.0.0/0` on the
  free tier, since Render doesn't give a static outbound IP there).

## Commands

```bash
uv run uvicorn app.main:app --reload       # dev server
uv run pytest -q                           # tests
uv run ruff check app --fix                # lint
uv run ruff format app                     # format
docker build -t astra-backend .            # container image
```
