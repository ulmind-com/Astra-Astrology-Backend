"""Put a set of real questions through the live assistant and score what comes back.

"The AI is not answering properly" is not something that can be fixed by
guessing. This exists so the claim can be checked: run it, read the table, and
see which questions actually fail and why.

    uv run uvicorn app.main:app --port 8000      # in another terminal
    uv run python scripts/evaluate_ai.py
    uv run python scripts/evaluate_ai.py --gap 30 --out results.json

**Mind the gap.** The free Groq tier allows 8,000 tokens a minute, account
wide, and a reading costs two to three thousand. Asking faster than one
question every ~25 seconds exhausts the allowance and every later answer falls
back to canned text — which looks exactly like a broken assistant and is not
one. The first run of this harness used a 14-second gap and reported six
failures; all six were rate limits. The default here is deliberately slower
than feels necessary.

What each verdict means:

    ok          answered by the model, with tools where appropriate
    FALLBACK    the model could not be reached; local synthesis answered
    REFUSED     the gate judged the question off-subject
    ASKS-BIRTH  answered, but asked for birth details it should have had
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DEFAULT_URL = "http://localhost:8000/api/v1/ai-astrologer/chat"

#: A stand-in native, so questions that need a chart can get one.
BIRTH = {
    "name": "Test Native",
    "gender": "male",
    "day": 14,
    "month": 7,
    "year": 1995,
    "hour": 9,
    "minute": 25,
    "place": "Kolkata",
    "lat": 22.5726,
    "lon": 88.3639,
}

#: What people actually ask, across every discipline, language and register.
#: Add to this whenever a real question is reported as badly answered — a case
#: here is a regression that cannot quietly come back.
CASES: list[tuple[str, str]] = [
    ("chart", "আমার কুন্ডলীতে কোন রাজযোগ আছে?"),
    ("chart", "আমার লগ্ন কী এবং তার ফল কী?"),
    ("dasha", "আমার বর্তমান মহাদশা ও অন্তর্দশা কেমন?"),
    ("dasha", "শনির সাড়ে সাতি কি আমার চলছে?"),
    ("timing", "আজকের দিনটা আমার কেমন যাবে?"),
    ("timing", "বিয়ের শুভ দিন কবে?"),
    ("career", "আমার job কবে হবে?"),
    ("career", "আমি কি ব্যবসা করব নাকি চাকরি?"),
    ("marriage", "আমার বিয়ে কবে হবে?"),
    ("marriage", "আমার কি মাঙ্গলিক দোষ আছে?"),
    ("money", "আমার আর্থিক অবস্থা কেমন হবে?"),
    ("health", "আমার স্বাস্থ্য নিয়ে কিছু বলুন"),
    ("remedy", "আমার জন্য কোন রত্ন শুভ?"),
    ("remedy", "শনির প্রতিকার কী?"),
    ("numerology", "আমার মূলাঙ্ক কত এবং তার ফল?"),
    ("vastu", "রান্নাঘর কোন দিকে হওয়া উচিত?"),
    ("vastu", "মূল প্রবেশদ্বার কোন দিকে ভালো?"),
    ("palm", "হস্তরেখায় বিবাহ রেখা কী বলে?"),
    ("guide", "কুন্ডলী ফিচারটা কীভাবে ব্যবহার করব?"),
    ("guide", "ওয়ালেট রিচার্জ কীভাবে করব?"),
    ("hindi", "मेरी कुंडली में कौन से राजयोग हैं?"),
    ("hindi", "मेरी शादी कब होगी?"),
    ("english", "What is my current dasha and what does it mean?"),
    ("english", "Which gemstone should I wear and why?"),
    ("romanised", "amar biye kobe hobe bolun"),
    ("romanised", "mera career kaisa rahega"),
    ("followup", "আর কিছু বলুন"),
    ("greeting", "নমস্কার"),
]

#: Phrasings that mean "I need your birth details", in the three languages.
_ASKS_BIRTH = ("জন্মতারিখ", "জন্মসময়", "জন্মস্থান", "birth date", "birth time", "जन्म")

#: The refusal, which the gate returns verbatim.
_REFUSAL_MARK = "ক্ষমা করবেন"

#: "I am handling a lot of charts" — what a non-Bengali reader gets when the
#: model is unreachable. It carries no `tools_called` marker, so without this
#: the harness scored it as a success and hid real failures behind a polite
#: sentence. Matched on a distinctive fragment of each translation.
_BUSY_MARKS = (
    "handling a lot of charts",
    "बहुत सारी कुंडलियाँ",
    "நிறைய ஜாதகங்களை",
    "చాలా జాతకాలు",
    "ധാരാളം ജാതകങ്ങൾ",
    "ಹಲವು ಜಾತಕಗಳನ್ನು",
    "ઘણી કુંડળીઓ",
    "ਕਈ ਕੁੰਡਲੀਆਂ",
    "ଅନେକ କୁଣ୍ଡଳୀ",
    "بہت سی کنڈلیاں",
)


def ask(url: str, message: str, timeout: float) -> tuple[dict, float]:
    body = json.dumps(
        {"message": message, "preferred_language": "bn", "birth_details": BIRTH}
    ).encode()
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    started = time.time()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    return payload.get("data") or {}, time.time() - started


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument(
        "--gap",
        type=float,
        default=26.0,
        help="seconds between questions; below ~25 the free tier runs out",
    )
    parser.add_argument("--timeout", type=float, default=200.0)
    parser.add_argument("--out", default="", help="write the full replies to this file")
    args = parser.parse_args()

    rows: list[dict] = []
    for index, (category, question) in enumerate(CASES, start=1):
        try:
            data, seconds = ask(args.url, question, args.timeout)
        except (urllib.error.URLError, TimeoutError) as exc:
            rows.append({"category": category, "question": question, "error": str(exc)})
            print(f"{index:3}/{len(CASES)} {category:11} ERROR      {exc}")
            time.sleep(args.gap)
            continue

        reply = (data.get("reply") or "").strip()
        tools = data.get("tools_called") or []
        row = {
            "category": category,
            "question": question,
            "chars": len(reply),
            "seconds": round(seconds, 1),
            "tools": tools,
            "fallback": (
                "local_astrology_rules_engine" in tools
                or any(mark in reply for mark in _BUSY_MARKS)
            ),
            "refused": _REFUSAL_MARK in reply,
            # Explaining a screen is not asking for the data. A guide answer
            # naturally says "enter your date, time and place" because that is
            # step two of using the feature — flagging it as a failure made a
            # correct reply look broken.
            "asks_birth": (
                "app_guide_tool" not in tools
                and any(mark in reply for mark in _ASKS_BIRTH)
            ),
            "reply": reply,
        }
        rows.append(row)

        verdict = (
            "FALLBACK"
            if row["fallback"]
            else "REFUSED"
            if row["refused"]
            else "ASKS-BIRTH"
            if row["asks_birth"]
            else "ok"
        )
        print(
            f"{index:3}/{len(CASES)} {category:11} {verdict:10} "
            f"{row['chars']:5}c {row['seconds']:5.1f}s  {question[:40]}"
        )
        time.sleep(args.gap)

    answered = sum(
        1
        for r in rows
        if not r.get("error") and not r.get("fallback") and not r.get("refused")
    )
    print()
    print(f"answered by the model : {answered}/{len(CASES)}")
    print(f"fell back             : {sum(1 for r in rows if r.get('fallback'))}")
    print(f"refused               : {sum(1 for r in rows if r.get('refused'))}")
    print(f"asked for birth data  : {sum(1 for r in rows if r.get('asks_birth'))}")
    print(f"errors                : {sum(1 for r in rows if r.get('error'))}")

    if args.out:
        Path(args.out).write_text(
            json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"\nfull replies written to {args.out}")

    # A fallback is not a crash, so this does not fail the run. Read the table.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
