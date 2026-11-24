# Diagnostic & Test Execution Log

**Audit ID:** AUD-20261124-001  
**Generated At:** 2026-11-24T11:30:00+05:30  
**Target Project:** Astra Astrology Full-Stack Platform  

---

## 1. Automated Diagnostic Command Log

| Command Executed | Environment | Exit Code | Status | Duration | Summary / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `npx tsc --noEmit` (Admin) | Node 20.x / Darwin (macOS) | 0 | PASSED | 1.2s | Clean compilation; 0 TypeScript errors |
| `npx tsc --noEmit` (Web) | Node 20.x / Darwin (macOS) | 0 | PASSED | 1.9s | Clean compilation; 0 TypeScript errors |
| `npx tsc --noEmit` (App) | React Native 0.88 / Expo SDK 58 | 0 | PASSED | 3.1s | Clean compilation; 0 TypeScript errors |
| `npm run build` (Admin) | Next.js 16.4.3 / Turbopack | 0 | PASSED | 4.8s | 46/46 static pages generated successfully |
| `npm run build` (Web) | Next.js 16.4.3 / Turbopack | 0 | PASSED | 5.2s | 54/54 static pages generated successfully |
| `pytest tests/` (Backend) | Python 3.12.14 / venv | 0 | PASSED | 41.8s | 794 passed, 343 skipped (live payment gateway / cloud mocks) |

---

## 2. Detailed Breakdown of Test Suites

### Backend Unit & Integration Tests (FastAPI / Beanie / Pytest)
- **Total Test Cases Discovered:** 1,137
- **Passed Test Cases:** 794
- **Skipped Test Cases:** 343 (Intentionally bypassed for offline safety: live Razorpay charge executions, live Agora token exchange, live Firebase cloud messaging)
- **Failed Test Cases:** 0
- **Execution Time:** 41.81 seconds

### Frontend & Mobile Static Analysis
- **Astra-Astrology-Admin:** Full type check passed (0 errors across 46 routes).
- **Astra-Astrology-Web:** Full type check passed (0 errors across 54 routes).
- **Astra-Astrology-App:** Full React Native / Expo type check passed (0 errors across 101 screens and components).

---

## 3. Skipped or Blocked Tests Rationale

1. **Live Payment Webhook Tests (`test_billing.py` & `test_wallet.py`):**
   - Certain tests require an active `RAZORPAY_KEY_SECRET` and live webhook callback triggers. In strict read-only audit mode, live financial transactions are prohibited to prevent accidental billing charges.
2. **Agora & ZegoCloud Live Media Room Negotiation:**
   - Media server tests requiring live UDP socket allocation and external RTC media negotiation were bypassed, with token generation logic validated in unit test suites.
