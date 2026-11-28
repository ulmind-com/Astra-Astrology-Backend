# Implementation-Ready Production Remediation Plan

**Audit ID:** AUD-20261124-001  
**Generated At:** 2026-11-24T11:30:00+05:30  
**Target Project:** Astra Astrology Full-Stack Platform  
**Overall Status:** `AUDIT_COMPLETE_WITH_HIGH_OR_MEDIUM_FINDINGS`  

---

## Phase 1: High-Priority P1 Security & Database Hardening

### Task 1.1: [AUD-001] Add MongoDB Indexes to Astrologer Beanie Document
- **Affected Files:** `Astra-Astrology-Backend/app/models/astrologer.py:130-220`
- **Root Cause:** Astrologer model lacks `class Settings` specifying indexes on `user_id`, `slug`, and `is_active`.
- **Remediation Steps:**
  1. Add an inner `class Settings:` block to `Astrologer` in `app/models/astrologer.py`:
     ```python
     class Settings:
         name = "astrologers"
         indexes = [
             [("user_id", pymongo.ASCENDING)],
             [("slug", pymongo.ASCENDING)],
             [("is_active", pymongo.ASCENDING), ("availability.is_online", pymongo.ASCENDING)],
             [("rating.average", pymongo.DESCENDING)],
         ]
     ```
  2. Verify index creation during MongoDB Beanie initialization.
- **Acceptance Criteria:** Lookups by `user_id` and `slug` utilize indexes; `explain()` shows IXSCAN instead of COLLSCAN.
- **Required Tests:** Run `pytest tests/test_astrologer_directory.py`.

### Task 1.2: [AUD-002] Implement Rate Limiting on Authentication & Public Endpoints
- **Affected Files:** `Astra-Astrology-Backend/app/api/v1/auth.py:30-180`, `Astra-Astrology-Backend/app/main.py:40-60`
- **Root Cause:** Missing rate limiting middleware allows unbounded brute-force attempts on login and OTP endpoints.
- **Remediation Steps:**
  1. Configure `slowapi.Limiter` with client IP key in `app/core/limiter.py`.
  2. Apply `@limiter.limit("5/minute")` to `login_access_token`, `register`, and `request_otp` in `app/api/v1/auth.py`.
  3. Register `RateLimitExceeded` exception handler returning HTTP 429 in `main.py`.
- **Acceptance Criteria:** Exceeding 5 requests/minute from a single IP triggers HTTP 429 with `Retry-After` header.
- **Required Tests:** Author `tests/test_auth_rate_limiting.py` verifying HTTP 429 response on rapid consecutive requests.

### Task 1.3: [AUD-003] Enforce Safe Production Defaults in Configuration
- **Affected Files:** `Astra-Astrology-Backend/app/core/config.py:22-35`, `Astra-Astrology-Backend/app/main.py:60-100`
- **Root Cause:** `DEBUG = True` and `ALLOWED_ORIGINS = ["*"]` defaults risk information disclosure if environment variables are missing in production.
- **Remediation Steps:**
  1. In `app/core/config.py`, add a model validator asserting that if `APP_ENV == "production"`, `DEBUG` must be `False` and `ALLOWED_ORIGINS` cannot contain `"*"`.
  2. Ensure `main.py` startup checks halt boot if production configuration invariants are violated.
- **Acceptance Criteria:** Backend refuses to boot in production if `DEBUG=True` or `ALLOWED_ORIGINS=["*"]`.
- **Required Tests:** Run `pytest tests/test_app_endpoints.py`.

### Task 1.4: [AUD-004] Upgrade Next.js Security Dependencies Across Admin & Web
- **Affected Files:** `Astra-Astrology-Admin/package.json:23`, `Astra-Astrology-Web/package.json:35`
- **Root Cause:** Next.js 16.4.3 contains a known security vulnerability reported by npm advisory.
- **Remediation Steps:**
  1. Execute `next upgrade --agent=security` in `Astra-Astrology-Admin/`.
  2. Execute `next upgrade --agent=security` in `Astra-Astrology-Web/`.
  3. Re-run `npm run build` to verify clean build without security fatal warnings.
- **Acceptance Criteria:** Production builds complete without `SecurityFatalError` notifications.
- **Required Tests:** Run `npm run build` in both Admin and Web directories.

---

## Phase 2: Medium-Priority P2 Testing & Privacy Hardening

### Task 2.1: [AUD-006] Implement Deterministic Offline Gateway Mock Fixtures
- **Affected Files:** `Astra-Astrology-Backend/tests/conftest.py`, `Astra-Astrology-Backend/tests/test_billing.py`
- **Root Cause:** 343 tests are skipped when live gateway credentials are absent.
- **Remediation Steps:**
  1. Add standard mock fixtures in `tests/conftest.py` for Razorpay webhook verification (`rzp_test` HMAC signature generation) and Agora RTC token generators.
  2. Update skipped tests in `test_billing.py` and `test_wallet.py` to utilize mock fixtures when live credentials are not set.
- **Acceptance Criteria:** Pytest offline run passes $> 1,000$ tests with $< 50$ skipped.
- **Required Tests:** Run `pytest tests/test_billing.py tests/test_wallet.py`.

### Task 2.2: [AUD-007] Enforce Client-Side Screen Capture Protection in Mobile Calls
- **Affected Files:** `Astra-Astrology-App/src/app/call/[id].tsx`, `Astra-Astrology-App/src/app/chat/[id].tsx`
- **Root Cause:** `expo-screen-capture` is installed but not attached to confidential consultation room lifecycle.
- **Remediation Steps:**
  1. In `call/[id].tsx` and `chat/[id].tsx`, import `* as ScreenCapture from 'expo-screen-capture'`.
  2. In `useEffect`:
     ```typescript
     ScreenCapture.preventScreenCaptureAsync();
     return () => {
       ScreenCapture.allowScreenCaptureAsync();
     };
     ```
- **Acceptance Criteria:** Mobile OS blocks screen recording and screenshots inside active call and chat screens.
- **Required Tests:** Mobile simulator validation.

---

## Phase 3: Low-Priority P3 Architecture & Data Retention Clean-up

### Task 3.1: [AUD-005] Configure Turbopack Root for Monorepo Lockfile Resolution
- **Affected Files:** `Astra-Astrology-Admin/next.config.ts`, `Astra-Astrology-Web/next.config.ts`
- **Root Cause:** Turbopack emits lockfile path warning when sub-projects reside in monorepo directories.
- **Remediation Steps:**
  1. Add `turbopack: { root: ".." }` in `next.config.ts` for both Admin and Web.
- **Acceptance Criteria:** `npm run build` executes without emitting lockfile path warnings.

### Task 3.2: [AUD-008] Add MongoDB TTL Index for Transitory AI Memory Context
- **Affected Files:** `Astra-Astrology-Backend/app/models/ai_astrologer.py:40-90`
- **Root Cause:** AI conversational vectors and transitory memory records persist indefinitely without automated TTL.
- **Remediation Steps:**
  1. In `AiAstrologerMemory.Settings.indexes`, add `IndexModel([("updated_at", pymongo.ASCENDING)], expireAfterSeconds=7776000)` (90-day retention).
- **Acceptance Criteria:** MongoDB automatically purges memory documents exceeding 90 days of inactivity.
- **Required Tests:** Run `pytest tests/test_ai_memory_purge.py`.
