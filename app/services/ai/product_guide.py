"""What this app can do, so the assistant can explain itself.

A user who cannot find a feature does not file a bug — they leave. The
assistant is the one place they will ask "how do I get my kundli?", and it
could not answer, because nothing ever told it the product exists.

Everything here is written in English on purpose, including the steps. The
model translates into whatever language the user wrote in far better than a
hand-kept table of ten translations would, and translations are the thing that
silently rot when a screen is renamed. One source, always current.

Costs and availability are **not** stored here. They live in platform settings
and an admin changes them, so they are read live and merged in at the moment
the question is asked. A guide that quotes a stale price is worse than none.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Feature:
    """One thing a user can do, and how they do it."""

    key: str
    name: str
    route: str
    #: One sentence: what the user gets out of it.
    does: str
    #: The actual click path. Short, imperative, in order.
    steps: tuple[str, ...]
    #: Settings attribute holding its price, when it has one.
    coins_field: str | None = None
    #: Settings attribute holding its on/off switch.
    enabled_field: str | None = None
    #: What the user must have ready before starting.
    needs: tuple[str, ...] = ()
    #: Facts that are not steps: how it bills, what limits apply, what goes
    #: wrong most often. This is what turns a list of clicks into something
    #: that can actually answer "why did it not work".
    notes: tuple[str, ...] = ()
    #: Words a question about this feature is likely to contain.
    aliases: tuple[str, ...] = field(default_factory=tuple)


FEATURES: tuple[Feature, ...] = (
    Feature(
        key="kundli",
        name="Kundli (birth chart)",
        route="/kundli",
        does="Your full Vedic birth chart: planets, houses, divisional charts, yogas, doshas, running Vimshottari dasha and remedies.",
        steps=(
            "Open Kundli from the menu, or go to /kundli.",
            "Enter date, exact time and place of birth. Pick the place from the suggestions so the coordinates and timezone are right.",
            "Press Generate. The chart and its reading appear together.",
            "Saved birth details are filled in automatically next time.",
        ),
        coins_field="kundli_coins",
        enabled_field="kundli_enabled",
        needs=("date of birth", "time of birth as exactly as you know it", "place of birth"),
        notes=(
            "Birth time matters most. A few minutes changes the ascendant and every house with it, so use the hospital record if you have one.",
            "Always pick the birth place from the suggestions — typing it freehand can leave the coordinates and timezone wrong, which shifts the whole chart.",
            "Calculated with Swiss Ephemeris and the Lahiri ayanamsa.",
        ),
        aliases=("kundli", "kundali", "kundly", "birth chart", "horoscope chart", "janam", "janma", "patrika", "jatak", "chart",
                 "কুন্ডলী", "কুণ্ডলী", "কোষ্ঠী", "জন্মছক", "ছক",
                 "कुंडली", "जन्मकुंडली", "जन्मपत्री"),
    ),
    Feature(
        key="kundli_matching",
        name="Kundli Matching",
        route="/kundli-matching",
        does="Ashtakoot 36-guna compatibility for two charts, with Nadi, Bhakoot and Manglik checked.",
        steps=(
            "Open Kundli Matching, or go to /kundli-matching.",
            "Fill in both people's birth date, time and place.",
            "Press Match to get the guna score and what each koot says.",
        ),
        coins_field="kundli_matching_coins",
        enabled_field="kundli_matching_enabled",
        needs=("both people's birth date, time and place",),
        notes=(
            "Both birth times need to be as exact as possible; the Moon moves fast and most of the 36 gunas depend on it.",
            "A low guna score is not a verdict on the marriage — Nadi, Bhakoot and Manglik are read together, and remedies exist.",
        ),
        aliases=("matching", "milan", "match", "compatibility", "guna", "gun", "ashtakoot", "marriage match", "kundli milan",
                 "কুন্ডলী মিলন", "মিলন", "গুণ মিলান", "বিবাহ মিলন",
                 "कुंडली मिलान", "गुण मिलान"),
    ),
    Feature(
        key="daily_horoscope",
        name="Daily Horoscope",
        route="/daily-horoscope",
        does="Today's reading for your moon sign, with the panchang, hora and Rahu Kaal.",
        steps=(
            "Open Daily Horoscope, or go to /daily-horoscope.",
            "Choose your rashi, or let it use your saved birth details.",
        ),
        coins_field="daily_horoscope_coins",
        enabled_field="daily_horoscope_enabled",
        notes=(
            "Based on your moon sign, not your sun sign, which is what Vedic astrology reads.",
        ),
        aliases=("daily", "horoscope", "today", "rashifal", "panchang", "aaj",
                 "রাশিফল", "পঞ্চাঙ", "আজকের", "দৈনিক",
                 "राशिफल", "पंचांग", "दैनिक"),
    ),
    Feature(
        key="dasha",
        name="Dasha Calculator",
        route="/dasha-calculator",
        does="Your Vimshottari mahadasha and antardasha periods with their dates.",
        steps=(
            "Open Dasha Calculator, or go to /dasha-calculator.",
            "Enter birth date, time and place.",
            "The running period is highlighted; the rest are listed with dates.",
        ),
        coins_field="dasha_calculator_coins",
        enabled_field="dasha_calculator_enabled",
        needs=("date, time and place of birth",),
        aliases=("dasha", "dasa", "mahadasha", "antardasha", "bhukti", "period", "timing",
                 "দশা", "মহাদশা", "অন্তর্দশা", "दशा", "महादशा"),
    ),
    Feature(
        key="rashi",
        name="Rashi Calculator",
        route="/rashi-calculator",
        does="Your moon sign and what it means, from your exact birth moment.",
        steps=("Open Rashi Calculator, or go to /rashi-calculator.", "Enter birth date, time and place."),
        coins_field="rashi_calculator_coins",
        enabled_field="rashi_calculator_enabled",
        aliases=("rashi", "rasi", "moon sign", "zodiac", "sign",
                 "রাশি", "চন্দ্র রাশি", "राशि"),
    ),
    Feature(
        key="nakshatra",
        name="Nakshatra Calculator",
        route="/nakshatra-calculator",
        does="Your birth star, its pada and lord, and the classical techniques that apply to it.",
        steps=("Open Nakshatra Calculator, or go to /nakshatra-calculator.", "Enter birth date, time and place."),
        coins_field="nakshatra_calculator_coins",
        enabled_field="nakshatra_calculator_enabled",
        aliases=("nakshatra", "nakshatram", "star", "birth star", "pada",
                 "নক্ষত্র", "জন্মনক্ষত্র", "नक्षत्र"),
    ),
    Feature(
        key="kp",
        name="KP Astrology",
        route="/kp-calculator",
        does="Krishnamurti Paddhati: sub-lords, cuspal positions and significators.",
        steps=("Open KP Astrology, or go to /kp-calculator.", "Enter birth date, time and place."),
        coins_field="kp_calculator_coins",
        enabled_field="kp_calculator_enabled",
        aliases=("kp", "krishnamurti", "sublord", "sub lord", "significator"),
    ),
    Feature(
        key="numerology",
        name="Numerology",
        route="/numerology",
        does="Mulank, bhagyank, Chaldean name number and mobile number analysis.",
        steps=(
            "Open Numerology, or go to /numerology.",
            "Enter your name and date of birth; add a mobile number to have that checked too.",
        ),
        coins_field="numerology_coins",
        enabled_field="numerology_enabled",
        notes=(
            "Spelling matters: use the name you actually go by day to day, since the letters are what the number is built from.",
        ),
        aliases=("numerology", "mulank", "bhagyank", "number", "name number", "mobile number", "chaldean", "ank",
                 "সংখ্যাতত্ত্ব", "মূলাঙ্ক", "ভাগ্যাঙ্ক", "নামের সংখ্যা",
                 "अंक शास्त्र", "मूलांक"),
    ),
    Feature(
        key="vastu",
        name="Vastu Compass",
        route="/vastu",
        does="A live compass that judges any direction in your home for 38 placements, with the 16 zones and 32 padas.",
        steps=(
            "Open Vastu, or go to /vastu.",
            "Pick what you are placing — kitchen, bed, entrance and so on.",
            "Point your phone, or drag the compass. The verdict updates as you turn.",
        ),
        coins_field="vastu_coins",
        enabled_field="vastu_enabled",
        notes=(
            "On a phone it can use the real compass; on a desktop you drag the dial instead.\n"
            "Phone compasses drift near metal and electronics — step away from them if the needle looks wrong.",
            "North on the dial is true north, and the reading is for the direction you are facing from the centre of the room.",
        ),
        aliases=("vastu", "vaastu", "direction", "disha", "compass", "kitchen", "entrance", "bedroom", "home",
                 "বাস্তু", "দিক", "কম্পাস", "রান্নাঘর", "প্রবেশদ্বার",
                 "वास्तु", "दिशा", "रसोई"),
    ),
    Feature(
        key="palm",
        name="Palm Reading",
        route="/palm-reading",
        does="Reads the lines and mounts of your palm from a live camera scan.",
        steps=(
            "Open Palm Reading, or go to /palm-reading.",
            "Allow the camera and hold your open palm steady in the frame.",
            "It captures by itself once your hand is aligned, then reads it.",
            "You can upload a photo instead if you prefer.",
        ),
        coins_field="palm_reading_coins",
        enabled_field="palm_reading_enabled",
        needs=("a camera, or a clear photo of your open palm in good light",),
        notes=(
            "If the scan keeps refusing, it is usually one of: the palm not flat to the camera, fingers closed, the hand too far away, glare from direct light, or a blurred frame.",
            "Even indirect daylight works best. Avoid flash and direct sun, which flatten the lines.",
            "A photo that fails the quality checks is not charged for.",
        ),
        aliases=("palm", "palmistry", "hast", "hastrekha", "hand", "rekha", "line",
                 "হস্তরেখা", "হাতের রেখা", "রেখা", "হস্তরেখা বিচার",
                 "हस्तरेखा", "हाथ की रेखा"),
    ),
    Feature(
        key="face",
        name="Face Reading",
        route="/face-reading",
        does="Samudrik face analysis from a live camera scan.",
        steps=(
            "Open Face Reading, or go to /face-reading.",
            "Allow the camera and keep your face inside the guide.",
            "It captures once you are aligned.",
        ),
        coins_field="face_reading_coins",
        enabled_field="face_reading_enabled",
        needs=("a camera, in even light",),
        notes=(
            "Keep your face straight to the camera in even light; strong side lighting and tilted heads are the usual causes of a failed scan.",
            "A scan that fails the quality checks is not charged for.",
        ),
        aliases=("face", "face reading", "samudrik", "physiognomy", "mukh",
                 "মুখমণ্ডল", "মুখ বিচার", "সামুদ্রিক", "चेहरा"),
    ),
    Feature(
        key="astrologers",
        name="Talk to an Astrologer",
        route="/astrologers",
        does="Live chat or call with a verified human astrologer, charged by the minute.",
        steps=(
            "Open Astrologers, or go to /astrologers.",
            "Green means online now. Open a profile to see their rate per minute.",
            "Press Chat or Call. Coins are deducted per minute while you talk, so keep enough in your wallet for the length you want.",
        ),
        needs=("enough coins for the minutes you plan to talk",),
        aliases=("astrologer", "talk", "consult", "chat", "call", "expert", "live",
                 "জ্যোতিষী", "কথা বল", "পরামর্শ", "জ্যোতিষীর সাথে",
                 "ज्योतिषी", "बात कर"),
    ),
    Feature(
        key="appointments",
        name="Appointments",
        route="/appointments",
        does="Book a time with an astrologer instead of waiting for them to be online.",
        steps=("Open Appointments, or go to /appointments.", "Pick an astrologer, then a free slot.", "Confirm to book."),
        aliases=("appointment", "booking", "book", "slot", "schedule",
                 "অ্যাপয়েন্টমেন্ট", "বুকিং", "সময় বুক", "अपॉइंटमेंट"),
    ),
    Feature(
        key="ai_astrologer",
        name="AI Astrologer (this assistant)",
        route="/ai-astrologer",
        does="Ask anything about your chart, your life or how this app works, in your own language, any time.",
        steps=(
            "Open AI Astrologer, or go to /ai-astrologer.",
            "Type your question in whatever language you are comfortable with — Bengali, Hindi, English, Tamil, romanised, anything.",
            "Save your birth details once and every reading uses them automatically.",
        ),
        notes=(
            "Free to use.",
            "It calculates your real chart with Swiss Ephemeris rather than guessing, and it will say so when it does not know something.",
            "It answers in whatever language you write in, and switches when you do.",
        ),
        aliases=("ai", "assistant", "chatbot", "bot", "you", "এআই", "সহায়ক", "चैटबॉट"),
    ),
    Feature(
        key="live_chat",
        name="Live Chat with an Astrologer",
        route="/astrologers",
        does="A private text conversation with a human astrologer, billed per minute.",
        steps=(
            "Open Astrologers and pick someone showing Online.",
            "Press Chat and choose how many minutes you want.",
            "Wait for them to accept, then talk.",
            "Press End when you are done; you are billed only for the minutes used.",
        ),
        notes=(
            "You need the full amount up front: rate per minute × the minutes you ask for. If you are short it tells you by how much.",
            "Session length has a minimum and a maximum set by the platform.",
            "An astrologer must be online and accepting chats; a green dot means online now.",
            "If they are already with someone else you will be told they are busy.",
        ),
        needs=("enough coins for rate × minutes requested",),
        aliases=("live chat", "chat with", "message astrologer", "text astrologer", "লাইভ চ্যাট", "চ্যাট করব"),
    ),
    Feature(
        key="call",
        name="Audio Call with an Astrologer",
        route="/astrologers",
        does="A voice call with a human astrologer, billed per minute.",
        steps=(
            "Open Astrologers and pick someone showing Online who offers calls.",
            "Press the call button and choose your minutes.",
            "Allow microphone access when your browser asks.",
            "Hang up when done; you are billed for the minutes used.",
        ),
        notes=(
            "Calls usually cost more per minute than chat.",
            "Same rule as chat: you need rate × minutes in your wallet before it starts.",
            "Not every astrologer offers calls — the profile says which modes they take.",
        ),
        needs=("a microphone", "enough coins for rate × minutes"),
        aliases=("call", "voice", "phone", "audio", "কল", "ফোন", "কল করব", "कॉल"),
    ),
    Feature(
        key="reviews",
        name="Ratings and Reviews",
        route="/astrologers",
        does="Rate an astrologer after a consultation and read what others said.",
        steps=(
            "After a chat or call ends you are asked to rate it.",
            "Ratings appear on the astrologer's profile.",
        ),
        notes=("You can only review an astrologer you have actually consulted.",),
        aliases=("review", "rating", "rate", "feedback", "star", "রিভিউ", "রেটিং", "समीक्षा"),
    ),
    Feature(
        key="security",
        name="Password and Security",
        route="/account/security",
        does="Change your password, or reset it if you have forgotten it.",
        steps=(
            "Open Security from your account, or go to /account/security.",
            "To change it, enter your current password and the new one.",
            "If you have forgotten it, sign out and use Forgot Password — a code is emailed to your registered address.",
        ),
        notes=(
            "The reset code is emailed to you. It is never shown on screen and nobody can read it out to you.",
            "The code expires, so use it soon after asking for it.",
        ),
        aliases=("password", "security", "forgot", "reset", "login problem", "cannot sign in",
                 "পাসওয়ার্ড", "নিরাপত্তা", "পাসওয়ার্ড ভুলে", "पासवर्ड", "सुरक्षा"),
    ),
    Feature(
        key="addresses",
        name="Addresses",
        route="/account/addresses",
        does="Save delivery addresses, used when something physical is sent to you.",
        steps=("Open Addresses from your account, or go to /account/addresses.", "Add or edit an address."),
        aliases=("address", "delivery", "shipping", "ঠিকানা", "পতা", "पता"),
    ),
    Feature(
        key="billing",
        name="How Coins and Billing Work",
        route="/account/wallet",
        does="Coins are the currency for everything paid in this app.",
        steps=(
            "Recharge at /account/wallet to add coins.",
            "Calculators and readings charge a fixed number of coins each.",
            "Live chat and calls charge per minute, taken as the session runs.",
        ),
        notes=(
            "A reading that fails its quality checks is not charged for.",
            "For live sessions you must hold rate × requested minutes before starting, and you are billed only for the minutes actually used.",
            "Your full history of charges and recharges is on the wallet page.",
        ),
        aliases=("billing", "how much", "charge", "deducted", "cut", "kata", "খরচ", "চার্জ", "কাটা", "बिलिंग", "कटा"),
    ),
    Feature(
        key="wallet",
        name="Wallet",
        route="/account/wallet",
        does="Your coin balance, recharges and full transaction history.",
        steps=(
            "Open Wallet from your account menu, or go to /account/wallet.",
            "Press Recharge and choose an amount.",
            "Coins appear as soon as the payment succeeds.",
        ),
        aliases=("wallet", "coin", "coins", "balance", "recharge", "money", "payment", "topup", "top up", "taka", "paisa",
                 "ওয়ালেট", "কয়েন", "ব্যালেন্স", "রিচার্জ", "টাকা",
                 "वॉलेट", "रिचार्ज", "कॉयन"),
    ),
    Feature(
        key="birth_details",
        name="Saved Birth Details",
        route="/account/birth-details",
        does="Save your birth date, time and place once so every feature fills itself in.",
        steps=(
            "Open Birth Details from your account, or go to /account/birth-details.",
            "Enter and save them once.",
        ),
        aliases=("birth details", "save birth", "profile", "my details", "birth profile",
                 "জন্ম তথ্য", "জন্মতারিখ সেভ", "প্রোফাইল", "जन्म विवरण"),
    ),
)

#: Looked up by key.
BY_KEY: dict[str, Feature] = {f.key: f for f in FEATURES}


def find(question: str) -> Feature | None:
    """The feature a question is about, if it is clearly about one.

    Longest alias first, so "kundli matching" is not answered with the kundli
    page. Matching is on the raw lowercased text rather than on tokens so that
    multi-word aliases work.
    """
    text = question.lower()
    best: tuple[int, Feature] | None = None
    for feature in FEATURES:
        for alias in feature.aliases:
            if alias in text and (best is None or len(alias) > best[0]):
                best = (len(alias), feature)
    return best[1] if best else None


def _price(settings_obj: Any, feature: Feature) -> int | None:
    if not feature.coins_field:
        return None
    return getattr(settings_obj, feature.coins_field, None)


def describe(
    feature: Feature,
    platform: Any = None,
    balance: int | None = None,
) -> dict[str, Any]:
    """The feature, priced and checked against this user's wallet.

    `balance` is None for a signed-out visitor, which is a different answer
    from a balance of zero: one needs to sign in, the other needs to recharge,
    and telling a visitor to top up an account they do not have is the kind of
    thing that makes an assistant feel broken.
    """
    out: dict[str, Any] = {
        "feature": feature.name,
        "where": feature.route,
        "what_it_does": feature.does,
        "steps": list(feature.steps),
    }
    if feature.needs:
        out["you_will_need"] = list(feature.needs)
    if feature.notes:
        out["good_to_know"] = list(feature.notes)

    cost = _price(platform, feature) if platform is not None else None
    if cost is not None:
        out["cost_coins"] = cost
        out["is_free"] = cost == 0

    if (
        platform is not None
        and feature.enabled_field
        and getattr(platform, feature.enabled_field, True) is False
    ):
        out["currently_unavailable"] = True

    if balance is None:
        out["wallet"] = "not signed in"
        if cost:
            out["note"] = "Sign in to see your balance. This feature costs coins."
    else:
        out["wallet_balance_coins"] = balance
        if cost:
            if balance >= cost:
                out["can_afford"] = True
            else:
                out["can_afford"] = False
                out["short_by_coins"] = cost - balance
                out["recharge_at"] = "/account/wallet"
    return out


def index(platform: Any = None) -> list[dict[str, Any]]:
    """Every feature in one line each, for "what can you do?".

    Deliberately terse: this goes into a model's context against a per-minute
    token budget, so it carries the name, the route and the price and nothing
    else.
    """
    rows = []
    for feature in FEATURES:
        row: dict[str, Any] = {"feature": feature.name, "where": feature.route}
        cost = _price(platform, feature) if platform is not None else None
        if cost is not None:
            row["cost_coins"] = cost
        rows.append(row)
    return rows
