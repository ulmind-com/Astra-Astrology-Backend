# Per-minute billing — Implementation Plan

What the client asked for, in one line: **a consultation costs coins per minute,
the coins leave the user's wallet as the minutes pass, the astrologer is paid
the rest in rupees, and the session stops itself when the coins run out.**

---

## 1. What already exists

Most of the dangerous machinery is built and tested, which is why this is
mostly wiring rather than invention.

| Already there | Why it matters here |
| --- | --- |
| `wallet.debit()` with `insufficient_balance` | the deduction itself |
| **Unique `idempotency_key` on every ledger row** | makes double-charging *impossible*, not merely unlikely |
| Heartbeats every 20–30s on both calls and chats | something that ticks while a session runs |
| The sweeper | closes sessions nobody closed |
| `started_at` on the server's clock | the only clock a client cannot wind back |
| `commission_percent` per astrologer | the per-astrologer override, already modelled |

---

## 2. Two numbers in the client's example contradict each other

> "5 ta coin e 1 min voice call" … and later … "10 ta coin mane dhor 100 taka"

Ten coins being ₹100 makes one coin ₹10. But the recharge example was ₹1 = 5
coins, which makes one coin ₹0.20 — fifty times apart. They are illustrations,
not a rate, so neither is taken as one.

**What this plan does instead:** a coin is worth exactly what people pay for it.
If ₹1 buys 5 coins, a coin is worth 20 paise. An 8-coin video minute is ₹1.60 of
the user's money; at 20% commission the astrologer earns ₹1.28.

That keeps one number — `coins_per_rupee` — as the only place the value of a
coin is set, and leaves **commission as the one margin lever**, which is what
the client asked for. If they want to pay out at a different rate than they
sell at, that is a second knob and a different conversation.

---

## 3. Rates: platform defaults, per-astrologer override

The client asked for commission to work this way ("ekta particular astrologer
er jonno ও separate kore"), so rates work the same way. One mental model, not
two.

| Setting | Where | Example |
| --- | --- | --- |
| Default commission % | admin settings | 20% |
| Commission for *this* astrologer | astrologer's own page | 30% |
| Default coins/minute for chat, call, video | admin settings | 3 / 5 / 8 |
| Rates for *this* astrologer | astrologer's own page | video 12 |

Blank on an astrologer means "use the platform default", so onboarding a new
astrologer needs no pricing decisions at all.

> ⚠️ **`RateCard` is rupees today** (`chat_per_minute: float`). It becomes
> **integer coins per minute**. Converting at the coin rate instead would mean
> an admin changing `coins_per_rupee` silently re-priced every astrologer on the
> platform — the same trap the coin plan already avoided once.

---

## 4. Starting a session

```
User taps "Video call"
  → "How long do you want to talk?"  [5] minutes
  → server: rate 8 coins/min × 5 = 40 coins; wallet holds 100 → fine
  → ring
```

When it is not fine the refusal says the useful thing, not just "no":

> *Not enough coins for 5 minutes. You need 40 and have 25 — add 15 more, or
> talk for 3 minutes.*

The requested minutes are a **affordability check and a record**, not a hard
stop: a conversation that is going well should not be cut off at exactly five
minutes when the wallet can carry it. The wallet running out is what ends it.

**Frozen at the moment the session starts**, exactly as the coin rate is frozen
on a payment order:

- `coins_per_minute` — an admin re-pricing mid-call must not change this call
- `commission_percent` — likewise
- `coin_value_paise` — so a later change to `coins_per_rupee` cannot restate
  what an astrologer already earned

---

## 5. Charging as the minutes pass

**Each started minute is paid for before it is used.** Minute 1 is charged when
the astrologer answers; minute 2 at the 60-second mark, and so on. Charging
afterwards would mean handing over a minute that might turn out to be
unaffordable — a minute given away every time anyone runs out.

**What drives the clock:** the heartbeat that already runs. On each one the
server asks "which started minutes are not yet paid for?" and charges them. The
sweeper does the same before closing anything, so a dropped client cannot skip
a minute it used.

**Why it cannot double-charge:** the key is `session:{id}:minute:{n}`. Both
sides heartbeat, and the two can land in the same instant — but the unique index
means only one of them can ever insert minute 7.

Every charge writes two rows:

| Row | Where |
| --- | --- |
| user debit, `reason=consultation` | the existing wallet ledger |
| astrologer earning, in **paise** | a new earnings ledger |

Earnings go to a separate ledger rather than the astrologer's wallet, because an
astrologer withdraws money — they do not spend coins.

---

## 6. Running out, exactly as the client described

```
15 coins left, video is 10 coins/min
  → warn now: "about 1 minute left"
  → that minute still runs; 10 coins taken, 5 left
  → next minute: 5 < 10, cannot be paid for
  → the session ends itself, reason "ran out of coins"
```

For chat, ending also flips the Firestore conversation to `ended`, so the
browser physically cannot send another message — not a disabled button, a
refusal from the database.

The warning threshold is "fewer than two minutes affordable", computed on the
server and sent with the session so both sides agree on it.

---

## 7. Earnings

**For the astrologer** — `GET /astrologers/me/earnings`: today, this week, this
month, plus the recent entries. Shown as **rupees only**. The client was
explicit that astrologers should not be shown the commission being taken, so the
view shows what was credited and nothing about what was deducted.

**For the admin** — the same entries from the other side: gross, commission
kept, net paid out. The admin sees the whole picture; the astrologer sees
theirs.

---

## 8. What gets built

### Models
- `PlatformSettings` **+** `default_commission_percent`, `default_chat_coins_per_minute`, `default_call_coins_per_minute`, `default_video_coins_per_minute`
- `RateCard` → integer coins per minute; `None` means "use the default"
- `CallSession` / `ChatSession` **+** `coins_per_minute`, `commission_percent`, `coin_value_paise`, `requested_minutes`, `minutes_charged`, `coins_charged`, `earning_paise`
- **New** `EarningEntry` — astrologer, session, mode, coins, `earning_paise`, when

### Services
- **New** `billing.py` — `rate_for()`, `affordable_minutes()`, `charge_due()`, `end_if_broke()`
- `call.py` / `chat.py` — check the balance at start, charge on heartbeat, charge-and-close in the sweeper

### Endpoints
- `GET /astrologers/{id}/quote?mode=video` — rate, balance, minutes affordable, minimum
- `POST /calls`, `POST /chats` — take `requested_minutes`
- `GET /astrologers/me/earnings` — today / week / month
- `GET /admin/earnings` — the same, with commission shown
- `PATCH /admin/settings` — defaults

### Frontend
- Duration prompt before starting
- Live coin counter and the low-balance warning during a session
- "Out of coins" end screen with a recharge button
- Astrologer earnings page
- Admin: default rates and commission; per-astrologer rates in coins

---

## 9. Tests that must exist

| Test | Why |
| --- | --- |
| 5 minutes requested, enough coins → starts | the happy path |
| not enough → refused, and says how many more are needed | the client asked for this message |
| minute 1 charged on answer, minute 2 at 60s | pre-paid, not post-paid |
| two heartbeats at once → one charge | the race, against the real index |
| 15 coins, 10/min → one more minute, then auto-end | the client's own example |
| ending a chat for no coins closes it in Firestore | the browser cannot write after |
| rate changed mid-session → the frozen rate is used | §4 |
| commission: per-astrologer beats the default | the client asked for both |
| earnings add up to the coins charged, less commission | the invariant |
| `sum(ledger) == wallet balance` still holds | the old invariant, under the new load |

---

## 10. Order of work

1. Settings + rates in coins, with the per-astrologer override
2. `billing.py` and the session fields
3. Charging on heartbeat and in the sweeper, with auto-end
4. Earnings ledger and endpoints
5. Admin UI (defaults, per-astrologer rates, earnings)
6. User UI (duration prompt, live counter, warning, out-of-coins screen)
7. Astrologer earnings page
8. Full suite, then a browser run end to end
