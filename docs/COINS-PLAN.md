# Coins — Implementation Plan

The client's requirement: a user recharges in rupees, but the wallet holds
**coins**. An admin sets how many coins a rupee buys. ₹100 at 10 coins/₹ gives
1000 coins, added to whatever the wallet already held.

---

## 1. The decision everything else follows from

**The wallet stores coins, not rupees.**

The tempting shortcut is to keep storing rupees and multiply by the rate when
showing the balance. That is wrong, and badly so: the moment an admin changed
the rate from 10 to 5, every existing balance on the platform would *halve on
screen overnight*. Coins people already bought must keep the value they were
bought at.

So the ledger moves to coins, and rupees survive only where money actually
changed hands — on the recharge row and the payment order.

| Thing | Unit |
| --- | --- |
| `Wallet.balance_coins` | coins |
| `WalletTransaction.amount_coins` / `balance_after_coins` | coins |
| `WalletTransaction.amount_paise` (recharge rows only) | paise — what was actually paid |
| `PaymentOrder.amount_paise` | paise — what Razorpay charged |
| Consultation pricing (later) | coins |

---

## 2. Three bugs this design exists to prevent

### 2.1 The rate changing mid-payment

```
10:00:00  User opens checkout. Rate is 10. Screen says "₹100 → 1000 coins".
10:00:20  Admin changes the rate to 5.
10:00:40  The payment captures.
```

Crediting at the *current* rate gives 500 coins for a purchase the user made
expecting 1000. That is a bait-and-switch, and it is the kind of thing a user
screenshots.

**So the rate is frozen when the order is created.** `PaymentOrder` stores
`coins_per_rupee` and the exact `coins` quoted, and the credit uses those —
never a fresh lookup. A reconcile days later still honours the original quote.

### 2.2 A refund recomputing instead of reversing

```
Monday   ₹100 recharged at rate 10  → 1000 coins
Tuesday  Admin changes the rate to 5
Wednesday  The ₹100 payment is refunded
```

Recomputing at today's rate takes back 500 coins and leaves the user 500 coins
they no longer paid for. **A refund reverses the exact coins that recharge
created**, found through the original ledger row's payment id.

### 2.3 Fractional coins

`coins = rupees × rate` must never produce 995.5. Two rules make it exact:

- `coins_per_rupee` is an **integer ≥ 1**
- a recharge is a **whole number of rupees** (`amount_paise % 100 == 0`)

Then `coins = (amount_paise // 100) × coins_per_rupee` is always a clean
integer — no rounding, no drift, nothing to reconcile later. It also matches
the client's own words: *1 takay N ta coin*.

---

## 3. Where the rate lives

Not an environment variable — the client has to change it from the panel, so it
is a document.

### `PlatformSettings` — a singleton

| Field | Note |
| --- | --- |
| `key` | always `"platform"`, uniquely indexed, so a second row is impossible |
| `coins_per_rupee` | int ≥ 1, default **1** |
| `updated_by` | the admin who last changed it |

### `CoinRateChange` — the audit trail

`from_rate`, `to_rate`, `changed_by`, `created_at`. A setting that decides how
much money people get must be answerable for later.

---

## 4. What changes

### Models

| Model | Change |
| --- | --- |
| `Wallet` | `balance_paise` → `balance_coins` |
| `WalletTransaction` | `amount_paise` → `amount_coins`, `balance_after_paise` → `balance_after_coins`; **adds** `amount_paise` and `coins_per_rupee`, both nullable and set only on recharge rows |
| `PaymentOrder` | **adds** `coins_per_rupee` and `coins`, frozen at creation |
| `PlatformSettings` | new |
| `CoinRateChange` | new |

### Services

- `settings.py` — read and update the rate, write the audit row
- `wallet.py` — `credit()` / `debit()` take `amount_coins`
- `payments.py` — `create_order` quotes coins and freezes the rate;
  `_credit_for_payment` credits the quoted coins; the refund path reverses the
  original recharge's coins

### Endpoints

| New | Does |
| --- | --- |
| `GET /admin/settings` | current rate |
| `PATCH /admin/settings` | change it, audited |
| `GET /admin/settings/coin-rate-history` | who changed what, when |

Changed: every wallet response now speaks coins. `/wallet/recharge/options`
also returns `coins_per_rupee` and each pack's coin value, so the Web app can
show "₹100 → 1000 coins" without doing the arithmetic itself.

**Removed:** `balance_rupees`. Once the rate can change there is no single
rupee value for a coin balance, and showing one would be a lie.

### Frontend

- **Web** `/account/wallet` — balance in coins, each pack labelled with the
  coins it buys, history in coins with the rupees shown on recharge rows
- **Admin** `/settings` — set coins per rupee, with a worked example and the
  change history
- **Admin** wallets / transactions — coins, and the adjust dialog in coins

### Migration

`scripts/migrate_wallet_to_coins.py` — converts existing wallets and ledger
rows at a rate given on the command line, defaulting to 1 so nobody's balance
changes value unless asked. Production currently holds **0 wallets**, so this
is really insurance for the demo data and for anything created before deploy.

---

## 5. Tests to add

| Test | Why |
| --- | --- |
| rate 10, ₹100 → 1000 coins | the client's example, exactly |
| 100 existing + 1000 new = 1100 | the client's second example |
| rate changed after the order → the **quoted** coins are credited | §2.1 |
| refund after a rate change takes back the **original** coins | §2.2 |
| a non-whole-rupee amount is rejected | §2.3 |
| `coins_per_rupee` of 0 or a fraction is rejected | §2.3 |
| rate change is recorded with the admin who made it | audit |
| a non-admin cannot change the rate | authorisation |
| `sum(ledger coins) == wallet.balance_coins` | the invariant, in the new unit |

---

## 6. Build order

1. This plan
2. `PlatformSettings` + `CoinRateChange` models, settings service
3. Wallet model and service → coins
4. Payments → quote, freeze, credit, refund reversal
5. Schemas and endpoints, including admin settings
6. Migration script
7. Tests
8. Web wallet page
9. Admin settings page + wallet pages
10. Full suite, then browser verification against the real gateway
