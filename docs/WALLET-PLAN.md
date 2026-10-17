# Wallet & Recharge — Implementation Plan

> **Status: built and verified (17 Oct 2026).**
> Backend: 4 models, 13 endpoints, 21 tests. Frontend: `/account/wallet` on Web;
> `/wallets`, `/transactions`, `/payments` on Admin.
> Verified against the real Razorpay test gateway — a live order was created, a
> forged signature was refused, a correctly signed webhook credited the wallet,
> its retry was ignored, and an abandoned order was reconciled to *failed*.
> **Still to do before real money:** set `RAZORPAY_WEBHOOK_SECRET` in the
> Razorpay dashboard and deploy, then swap the test key for the live key.

The money layer. Everything later (chat billing, astrologer payouts, refunds)
sits on top of this, so it is built to be auditable from day one.

Payment provider: **Razorpay** (test keys already in `.env`).

---

## 1. Two rules that shape everything

**Rule 1 — the ledger is the truth, not a balance field.**
Every movement of money is an append-only row. The wallet's `balance_paise` is a
*cache* of the ledger, and a reconcile script can rebuild it at any time. Without
this, a single lost write silently corrupts someone's money with no way to prove
what happened.

**Rule 2 — the client never decides that money moved.**
The browser saying "payment successful" means nothing. A wallet is credited only
after the server verifies Razorpay's HMAC signature, and the credited amount is
read from **Razorpay's payload**, never from the request body.

---

## 2. Money representation

**Integer paise everywhere. No floats.** `₹100.00` is stored as `10000`.

Floating point cannot represent `0.1` exactly, so repeated per-minute deductions
drift and balances stop matching the ledger. Rupees appear only at the UI edge.

> ⚠️ **Existing conflict:** `RateCard` in `app/models/astrologer.py` stores
> `chat_per_minute: float` (e.g. `40.0`). When consultation billing is built,
> those become `*_paise: int`. Decide then whether to migrate the field or
> convert at the boundary — not a blocker for the wallet itself.

---

## 3. Data model

### `Wallet` — one per user

| Field | Type | Note |
| --- | --- | --- |
| `user_id` | PydanticObjectId | **unique index** |
| `balance_paise` | int | cached sum of the ledger, never negative |
| `currency` | str | `INR` |
| `is_frozen` | bool | admin can freeze on suspected fraud |
| `last_transaction_at` | datetime? | |

### `WalletTransaction` — append-only ledger

| Field | Type | Note |
| --- | --- | --- |
| `wallet_id`, `user_id` | ObjectId | indexed |
| `direction` | `credit` / `debit` | |
| `reason` | `recharge`, `consultation`, `refund`, `adjustment`, `bonus`, `payout`, `reversal` | |
| `amount_paise` | int | always positive; `direction` carries the sign |
| `balance_after_paise` | int | snapshot, so history reads without re-summing |
| `idempotency_key` | str | **unique index** — the guard against double credit |
| `ref` | object | `{razorpay_order_id, razorpay_payment_id, session_id}` |
| `note` | str? | shown to the user |
| `created_by` | ObjectId? | set for admin adjustments |

**Never updated, never deleted.** A mistake is corrected by a `reversal` row.

### `PaymentOrder` — one per recharge attempt

`user_id`, `razorpay_order_id` (**unique**), `amount_paise`, `receipt`,
`status` (`created` → `paid` / `failed` / `expired`), `razorpay_payment_id`,
`method`, `failure_reason`, `verified_via` (`callback` / `webhook`).

Keeps a record of attempts that never completed — needed when a user says
"money gone but no balance".

### `WebhookEvent` — replay guard

`event_id` (**unique**, Razorpay's `x-razorpay-event-id`), `event`, `payload`,
`processed_at`, `result`.

---

## 4. Recharge flow

```
1. User picks ₹500
2. POST /wallet/recharge/order  { amount_paise: 50000 }
   → server validates min/max, creates a Razorpay Order,
     saves PaymentOrder(status=created)
   → returns { razorpay_order_id, amount_paise, key_id }

3. Frontend opens Razorpay Checkout with that order

4. User pays. Razorpay confirms through TWO independent paths:

   (a) browser callback → POST /wallet/recharge/verify
       { order_id, payment_id, signature }
       server checks HMAC_SHA256("order_id|payment_id", key_secret)

   (b) webhook → POST /webhooks/razorpay
       server checks HMAC_SHA256(raw_body, webhook_secret)

5. Whichever arrives first credits the wallet.
   The second one finds the idempotency key taken and does nothing.
```

Both paths exist on purpose: the callback is fast but the user may close the
browser; the webhook always arrives but can be delayed. **Neither alone is
enough.**

### Crediting, atomically

```
1. insert WalletTransaction with idempotency_key = razorpay_payment_id
   → DuplicateKeyError means it is already credited: stop, return success
2. $inc the wallet balance, read the new value back
3. write balance_after_paise onto the row
4. mark PaymentOrder paid
```

Step 1 first, because the unique index is what makes a double credit
*impossible* rather than merely unlikely. Atlas is a replica set, so steps 1–4
run inside a MongoDB transaction; if transactions are unavailable the ordering
above still prevents the dangerous failure (double credit) and leaves only a
repairable one (ledger row without balance snapshot).

---

## 5. Endpoints

### User (`/api/v1/wallet`)

| Method | Path | Does |
| --- | --- | --- |
| GET | `/wallet` | balance + last 5 transactions |
| GET | `/wallet/transactions` | paginated history, filter by reason |
| GET | `/wallet/recharge/packs` | preset amounts (₹100 / 500 / 1000 / 2000 / 5000) |
| POST | `/wallet/recharge/order` | creates a Razorpay order |
| POST | `/wallet/recharge/verify` | verifies the browser callback |

### Webhook (no auth — signature is the auth)

| POST | `/api/v1/webhooks/razorpay` | `payment.captured`, `payment.failed`, `refund.processed` |

### Admin (`/api/v1/admin`)

| GET | `/admin/wallets` | balances, search by user |
| GET | `/admin/transactions` | all movements, filters |
| GET | `/admin/payments` | orders incl. failed/abandoned, for reconciliation |
| POST | `/admin/wallets/{user_id}/adjust` | manual credit/debit with a mandatory reason, recorded with `created_by` |
| POST | `/admin/wallets/{user_id}/freeze` | freeze / unfreeze |

---

## 6. Security checklist

- **Raw body for the webhook.** Signature is computed over bytes — read
  `await request.body()` before any JSON parsing, or re-serialisation breaks it.
- `hmac.compare_digest` for every comparison — never `==`.
- **Replay guard:** `WebhookEvent.event_id` unique. Razorpay retries, and a
  retry must not be processed twice.
- **Amount comes from Razorpay**, never from the client. The verify endpoint
  reads the amount off the fetched payment, not off the request.
- **Server-side min/max** (₹10 – ₹50,000 per recharge, configurable).
- Order creation is **rate limited** per user.
- A frozen wallet rejects both credit and debit.
- Key secret and webhook secret are never logged, never returned. Only
  `key_id` goes to the browser — it is public by design.

---

## 7. Config to add

```env
RAZORPAY_KEY_ID=rzp_test_xxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxx
RAZORPAY_WEBHOOK_SECRET=xxxxxxxx        # set in the Razorpay dashboard
WALLET_CURRENCY=INR
WALLET_MIN_RECHARGE_PAISE=1000          # ₹10
WALLET_MAX_RECHARGE_PAISE=5000000       # ₹50,000
```

`_check_config()` in `app/main.py` gains: in production, refuse to start when the
keys are missing, **or when a `rzp_test_` key is used**.

> ⚠️ **The current `.env` will not load.** It has `API key=` and `Secret=` —
> `API key` contains a space, which is not a valid environment variable name.
> These must be renamed to `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`, and the
> webhook secret added.

---

## 8. Frontend

### Web — `/account/wallet`

- Balance card
- Recharge packs + custom amount
- Razorpay Checkout (`checkout.js`, opened with the order from our API)
- Transaction history: date, reason, amount, running balance, infinite scroll
- Honest states: `pending` while the webhook is still in flight, and a clear
  failure screen that tells the user money is not lost

### Admin

- `/wallets` — balances, search
- `/transactions` — every movement, filters, CSV export
- `/payments` — reconciliation view: created vs paid vs failed
- Manual adjust dialog with a required reason

---

## 9. Tests

| Test | Why |
| --- | --- |
| min / max amount rejected | server-side validation |
| valid signature credits once | the happy path |
| **invalid signature credits nothing** | the attack |
| same payment id twice → one credit | idempotency |
| callback and webhook both arrive → one credit | the real-world race |
| webhook replay (same event id) → no-op | Razorpay retries |
| `sum(ledger) == wallet.balance_paise` | the invariant |
| frozen wallet rejects movement | admin control |
| admin adjustment records `created_by` | audit |
| failed payment leaves balance untouched | |

---

## 10. Build order

1. Config + `razorpay` dependency, `.env` fix
2. Models + indexes
3. Wallet service: `credit()`, `debit()`, `get_or_create()`, idempotency
4. Recharge: order → verify → credit
5. Webhook endpoint + replay guard
6. Admin endpoints
7. Tests
8. Web wallet page
9. Admin wallet pages

## 11. Deliberately not in this feature

Astrologer payouts · consultation debit (arrives with chat) · GST invoices ·
coupons and cashback · auto-recharge · subscriptions.

The ledger's `reason` enum already has room for each, so none of them require a
schema change later.
