# Remaining Risks & Operational Caveats

**Implementation ID:** IMPL-20261124-001  
**Audit Reference:** AUD-20261124-001  

---

## 1. Residual Risk Matrix

| Risk ID | Category | Severity | Description | Trigger Condition | Operational Mitigation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RISK-01** | Dependency Security | HIGH | Next.js 16.4.3 security advisory | Public internet exposure of SSR endpoints | Execute `next upgrade --agent=security` once user specifies worktree preference. |
| **RISK-02** | Test Fixture Mocking | MEDIUM | 343 tests skipped in offline pytest runs | Offline CI pipeline execution | Expand mock cassette fixtures for Razorpay webhook HMAC signatures in upcoming sprint. |
| **RISK-03** | Third-Party Webhook Delivery | MEDIUM | Razorpay webhook secret missing in dev | UPI payment callbacks when browser redirect is lost | Ensure `RAZORPAY_WEBHOOK_SECRET` is strictly set in production staging environment. |

---

## 2. External Dependencies & Blocked Tasks
- **AUD-004 (Next.js Security Upgrade):** Currently awaiting explicit user direction on worktree isolation (`next upgrade --agent=security`) per Phase 11 Scope and Safety Approval Gates.
