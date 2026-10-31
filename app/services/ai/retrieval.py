"""Ranking passages, and deciding whether a question is ours to answer.

Everything here is a pure function over text. Nothing touches MongoDB, which is
what makes it testable: the ranking and the gate are the two places where this
assistant is right or wrong, and both can be exercised without a database.

Two jobs:

**Ranking.** `rank()` scores candidate passages with BM25. The thing it replaced
counted substrings, which was wrong three ways at once: `"ram"` scored a hit
inside `"program"`, a passage that merely repeated a word beat one that was
about it, and a long passage beat a short precise one for no reason but length.
BM25 fixes all three — term saturation stops repetition paying, and the length
divisor stops size paying.

**The gate.** `is_answerable()` decides whether a question is about this product
at all, before the model is ever called. A refusal taken here cannot be argued
with; a model asked to refuse politely can always be talked round.

The gate here is deliberately *not* the one a pure document assistant would use.
This assistant answers from two different places: computed tools (a kundli, a
dasha, a numerology number — exact, and never retrieved from any document) and
retrieved text. Gating on "is this question covered by the corpus" would refuse
"আমার দশা কী চলছে?" — a question the ephemeris answers perfectly and no
document contains. So the gate asks a narrower question: is this within the
subjects we practise? Anything inside is passed to the model, which still has
the tools and the retrieved passages to keep it honest.

It errs towards answering. A wrongly refused paying customer is a worse failure
than a slightly loose answer, so refusal needs the question to carry no trace of
our subjects at all.
"""

from __future__ import annotations

import math
import re
import unicodedata
from bisect import bisect_left
from collections import Counter, OrderedDict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Tokenising
# ---------------------------------------------------------------------------
#: Bengali, Devanagari and Latin letters plus digits. Split on everything else,
#: which keeps "D9" and "7th" whole while dropping punctuation.
#: Any Unicode letter or digit. It used to list Latin, Devanagari and
#: Bengali only, which meant a Tamil or Gujarati question tokenised to
#: nothing at all: it slipped past the gate as a "short message" by
#: accident, and retrieval had no terms to search with. Every script a user
#: might write in now produces words.
_WORD = re.compile(
    "[0-9A-Za-z"
    "\u00C0-\u024F"   # Latin with diacritics
    "\u0400-\u04FF"   # Cyrillic
    "\u0590-\u05FF"   # Hebrew
    "\u0600-\u06FF\u0750-\u077F"   # Arabic, Urdu
    "\u0900-\u0DFF"   # every Indic block: Devanagari, Bengali, Gurmukhi,
                       # Gujarati, Odia, Tamil, Telugu, Kannada, Malayalam,
                       # Sinhala — including their combining vowel marks,
                       # which `\\w` leaves out and which splitting on would
                       # tear আমার into আম
    "\u0E00-\u0E7F"   # Thai
    "\u1000-\u109F"   # Myanmar
    "\u3040-\u30FF"   # Japanese kana
    "\u4E00-\u9FFF"   # CJK
    "\uAC00-\uD7AF"   # Hangul
    "]+"
)

#: Devanagari or Bengali. Marks the words that compound without spaces, and
#: so need the containment test the Latin ones must not have.
_NATIVE_CHARS = re.compile(r"[\u0900-\u097F\u0980-\u09FF]")

#: Words that match nearly everything and so separate nothing. The romanised
#: Bengali and Hindi entries matter as much as the English ones: questions
#: arrive as "amar biye kobe hobe" and "mera career kaisa rahega", and without
#: these every passage written in the same register scores for "amar" and "mera"
#: rather than for the subject actually asked about.
STOPWORDS: frozenset[str] = frozenset(
    {
        # English
        "a", "an", "and", "any", "are", "as", "at", "be", "been", "but",
        "by", "can", "could", "did", "do", "does", "for", "from", "get", "give",
        "had", "has", "have", "he", "her", "him", "his", "how", "i", "if", "in",
        "into", "is", "it", "its", "just", "know", "me", "much", "must", "my",
        "need", "of", "on", "or", "our", "out", "please", "say", "she", "should",
        "so", "some", "tell", "than", "that", "the", "their", "them", "then",
        "there", "these", "they", "this", "to", "too", "us", "very", "want",
        "was", "we", "were", "what", "when", "where", "which", "while", "who",
        "whom", "why", "will", "with", "would", "you", "your",
        # Romanised Bengali / Hindi function words
        "aar", "ache", "achhe", "ami", "amar", "amader", "amake", "apni",
        "apnar", "ar", "aur", "bol", "bolo", "chai", "chahiye", "dao", "debo",
        "dibo", "ebong", "ei", "eita", "er", "eta", "eto", "hai", "hain",
        "hobe", "hoy", "hota", "hoti", "hona", "honi", "jodi", "jonno",
        "jonne", "ka", "kaise", "kaisa", "kar", "ke", "keno", "ki", "kina",
        "kintu", "ko", "kobe", "korbe", "korbo", "kore", "kori", "korte",
        "kothay", "koto", "kya", "lagbe", "mein", "mera", "meri", "moto",
        "na", "nahi", "niye", "oi", "ota", "par", "pabo", "rahega", "se",
        "ta", "tai", "tao", "tha", "thake", "uchit", "ye", "yeh",
        # Native-script function words
        "এই", "ও", "এবং", "কি", "কী", "কে", "কেন", "কোন", "আমি", "আমার",
        "আমাকে", "আপনি", "আপনার", "হবে", "হয়", "কিন্তু", "যদি", "না",
        "কখন", "কোথায়", "আছে", "করে", "জন্য", "থেকে", "দিয়ে", "নিয়ে",
        "है", "हैं", "और", "क्या", "कौन", "क्यों", "मेरा", "मेरी", "मुझे",
        "आप", "आपका", "होगा", "होगी", "नहीं", "अगर", "कब", "कहाँ", "से",
        "के", "को", "का", "की", "में", "पर", "यह", "वह",
    }
)


def normalise(text: str) -> str:
    """Fold to a single Unicode form and lowercase.

    Bengali conjuncts and nuqta forms have more than one valid encoding, so the
    same word typed on two keyboards can be two different strings. NFC folds
    them together before anything compares them.
    """
    return unicodedata.normalize("NFC", text).lower()


def tokenize(text: str, *, keep_stopwords: bool = False) -> list[str]:
    """Words worth matching on, normalised and lowercased."""
    words = _WORD.findall(normalise(text))
    if keep_stopwords:
        return words
    return [w for w in words if w not in STOPWORDS and len(w) > 1]



# ---------------------------------------------------------------------------
# Crossing the language gap
# ---------------------------------------------------------------------------
#: Native-script terms and the English they should also search for.
#:
#: This exists because of a measured fact about this deployment, not as a
#: nicety: the client's knowledge base is 1.2 million characters and contains
#: **no Bengali at all**, while the product answers in Bengali by default and
#: most questions arrive in it. A Bengali question tokenises to Bengali words,
#: matches nothing, and the assistant answers with no retrieved support
#: whatsoever — the grounding silently does nothing for the majority of users.
#:
#: Expanding the query is the cheap half of the fix. The thorough half is a
#: multilingual embedding, which needs an API key this deployment does not yet
#: have; until then this closes most of the gap for the vocabulary that matters.
TERM_EQUIVALENTS: dict[str, tuple[str, ...]] = {
    # --- Bengali ---
    "জ্যোতিষ": ("astrology", "jyotish"),
    "কুন্ডলী": ("kundli", "horoscope", "chart"),
    "কুণ্ডলী": ("kundli", "horoscope", "chart"),
    "কোষ্ঠী": ("kundli", "horoscope"),
    "রাশি": ("rashi", "sign", "zodiac"),
    "নক্ষত্র": ("nakshatra", "star"),
    "দশা": ("dasha", "period"),
    "মহাদশা": ("mahadasha", "dasha"),
    "অন্তর্দশা": ("antardasha", "bhukti"),
    "গ্রহ": ("planet", "graha"),
    "লগ্ন": ("lagna", "ascendant"),
    "ভাব": ("house", "bhava"),
    "যোগ": ("yoga",),
    "দোষ": ("dosha", "dosh"),
    "মাঙ্গলিক": ("manglik", "mangal"),
    "শনি": ("saturn", "shani"),
    "বৃহস্পতি": ("jupiter", "guru"),
    "মঙ্গল": ("mars", "mangal"),
    "শুক্র": ("venus", "shukra"),
    "বুধ": ("mercury", "budh"),
    "সূর্য": ("sun", "surya"),
    "চন্দ্র": ("moon", "chandra"),
    "রাহু": ("rahu",),
    "কেতু": ("ketu",),
    "গোচর": ("transit", "gochar"),
    "পঞ্চাং": ("panchang",),
    "তিথি": ("tithi",),
    "মুহূর্ত": ("muhurta", "muhurat"),
    "বাস্তু": ("vastu",),
    "দিক": ("direction", "disha"),
    "রত্ন": ("gemstone", "ratna", "stone"),
    "প্রতিকার": ("remedy", "remedies", "upay"),
    "মন্ত্র": ("mantra",),
    "পূজা": ("puja", "worship"),
    "হস্তরেখা": ("palmistry", "palm"),
    "রেখা": ("line", "rekha"),
    "সংখ্যাতত্ত্ব": ("numerology", "number"),
    "অঙ্ক": ("number", "mulank"),
    "মূলাঙ্ক": ("mulank", "number"),
    "ভাগ্যাঙ্ক": ("bhagyank", "destiny"),
    "বিবাহ": ("marriage", "vivah", "wedding"),
    "বিয়ে": ("marriage", "vivah", "wedding"),
    "মিলন": ("matching", "milan", "compatibility"),
    "গুণ": ("guna", "gun"),
    "চাকরি": ("job", "career", "employment"),
    "ব্যবসা": ("business", "trade"),
    "অর্থ": ("money", "wealth", "finance"),
    "টাকা": ("money", "wealth"),
    "সম্পত্তি": ("property", "land"),
    "স্বাস্থ্য": ("health",),
    "রোগ": ("disease", "illness", "health"),
    "সন্তান": ("child", "children", "progeny"),
    "শিক্ষা": ("education", "study"),
    "বিদেশ": ("foreign", "abroad"),
    "ভ্রমণ": ("travel", "journey"),
    "শত্রু": ("enemy", "enemies"),
    "প্রেম": ("love", "romance"),
    "ভবিষ্যৎ": ("future",),
    "ভাগ্য": ("fortune", "luck", "destiny"),
    "মোবাইল": ("mobile", "phone"),
    "নম্বর": ("number",),
    "নাম": ("name",),
    # --- Hindi ---
    "ज्योतिष": ("astrology", "jyotish"),
    "कुंडली": ("kundli", "horoscope", "chart"),
    "राशि": ("rashi", "sign", "zodiac"),
    "नक्षत्र": ("nakshatra", "star"),
    "दशा": ("dasha", "period"),
    "ग्रह": ("planet", "graha"),
    "लग्न": ("lagna", "ascendant"),
    "भाव": ("house", "bhava"),
    "योग": ("yoga",),
    "दोष": ("dosha", "dosh"),
    "मांगलिक": ("manglik", "mangal"),
    "शनि": ("saturn", "shani"),
    "गुरु": ("jupiter", "guru"),
    "मंगल": ("mars", "mangal"),
    "शुक्र": ("venus", "shukra"),
    "बुध": ("mercury", "budh"),
    "सूर्य": ("sun", "surya"),
    "चंद्र": ("moon", "chandra"),
    "राहु": ("rahu",),
    "केतु": ("ketu",),
    "गोचर": ("transit", "gochar"),
    "पंचांग": ("panchang",),
    "तिथि": ("tithi",),
    "मुहूर्त": ("muhurta", "muhurat"),
    "वास्तु": ("vastu",),
    "दिशा": ("direction", "disha"),
    "रत्न": ("gemstone", "ratna", "stone"),
    "उपाय": ("remedy", "remedies", "upay"),
    "मंत्र": ("mantra",),
    "पूजा": ("puja", "worship"),
    "हस्तरेखा": ("palmistry", "palm"),
    "अंक": ("number", "mulank"),
    "विवाह": ("marriage", "vivah", "wedding"),
    "शादी": ("marriage", "wedding"),
    "नौकरी": ("job", "career", "employment"),
    "व्यापार": ("business", "trade"),
    "धन": ("money", "wealth"),
    "पैसा": ("money", "wealth"),
    "संपत्ति": ("property", "land"),
    "स्वास्थ्य": ("health",),
    "रोग": ("disease", "illness", "health"),
    "संतान": ("child", "children", "progeny"),
    "शिक्षा": ("education", "study"),
    "विदेश": ("foreign", "abroad"),
    "यात्रा": ("travel", "journey"),
    "शत्रु": ("enemy", "enemies"),
    "प्रेम": ("love", "romance"),
    "भविष्य": ("future",),
    "भाग्य": ("fortune", "luck", "destiny"),
}


#: The equivalence keys, sorted, so an inflected word can find its stem by
#: binary search instead of by scanning the whole table.
_EQUIV_KEYS = sorted(TERM_EQUIVALENTS)


def _equivalents(term: str) -> tuple[str, ...]:
    """English for a native term, matching inflected forms too.

    Bengali and Hindi add their case endings to the back of the word, so a
    question says দোষের where the table holds দোষ. An exact lookup misses every
    such form — and those forms are the normal way people write. The longest
    key that the term begins with is used, so দোষের finds দোষ while মাঙ্গলিক
    is not mistaken for it.
    """
    exact = TERM_EQUIVALENTS.get(term)
    if exact is not None:
        return exact
    if len(term) < 4:
        return ()
    i = bisect_left(_EQUIV_KEYS, term)
    # The candidate stems sit immediately before the term in sort order.
    for key in reversed(_EQUIV_KEYS[max(0, i - 8) : i]):
        if len(key) >= 3 and term.startswith(key):
            return TERM_EQUIVALENTS[key]
    return ()


def expand(terms: list[str]) -> list[str]:
    """Add the English a native-script term should also search for.

    Order is kept and duplicates dropped, so the question's own words still come
    first and an expansion never displaces them.
    """
    out: list[str] = []
    seen: set[str] = set()
    for term in terms:
        for candidate in (term, *_equivalents(term)):
            if candidate not in seen:
                seen.add(candidate)
                out.append(candidate)
    return out


# ---------------------------------------------------------------------------
# BM25
# ---------------------------------------------------------------------------
#: Term-frequency saturation. Standard; above it, repeating a word stops paying.
K1 = 1.5
#: Length normalisation. 0 ignores length, 1 divides by it fully.
B = 0.75
#: A hit in the title is worth this many hits in the body. The titles here are
#: rule names ("Manglik Dosha", "মাঙ্গলিক দোষ"), so a question naming one is
#: almost always asking for that rule rather than mentioning it in passing.
TITLE_WEIGHT = 3.0


@dataclass
class Scored:
    """One candidate and what it scored."""

    doc: Any
    score: float
    matched: list[str] = field(default_factory=list)


#: Below this length a query term must match a document word exactly. Above it,
#: a document word that *begins* with the term counts too.
#:
#: Bengali and Hindi inflect by suffix — চাকরি becomes চাকরির, দোষ becomes দোষের
#: — so an exact-match-only index answers "চাকরির কথা" with nothing at all. A
#: prefix is the right amount of looseness here: it catches the inflections
#: without the substring bug that let "ram" score inside "program", because a
#: prefix is anchored at the start of a word and a substring is anchored nowhere.
#:
#: Short terms are held to exact matching because a three-letter prefix matches
#: far too much ("sun" would take "sunday", "ket" would take every "ketu" and
#: "ketaki" alike).
MIN_PREFIX = 4


#: A passage's words, sorted, with running totals of how often each occurs.
#:
#: Sorting is what makes the prefix lookup cheap. Every word beginning with a
#: given prefix sits in one contiguous run of a sorted list, so two binary
#: searches find the run and the running totals give its size without walking
#: it. Scanning each passage's whole vocabulary for every query term instead
#: measured about ten times slower on the real corpus, which is the difference
#: between a chat that answers and one that is noticeably waiting.
_Index = tuple[list[str], list[int]]


def _build_index(tokens: list[str]) -> _Index:
    counts = Counter(tokens)
    words = sorted(counts)
    running = [0]
    for word in words:
        running.append(running[-1] + counts[word])
    return words, running


def _tf(index: _Index, term: str) -> int:
    """How often `term` occurs in a passage, counting inflected forms."""
    words, running = index
    if len(term) < MIN_PREFIX:
        i = bisect_left(words, term)
        if i < len(words) and words[i] == term:
            return running[i + 1] - running[i]
        return 0
    lo = bisect_left(words, term)
    # "\uffff" sorts above every character that can appear in a word, so this
    # lands just past the last word carrying the prefix.
    hi = bisect_left(words, term + "\uffff")
    return running[hi] - running[lo]


def _idf(n_docs: int, n_containing: int) -> float:
    """Inverse document frequency, floored at zero.

    The classic BM25 idf goes negative for a term in more than half the
    documents, which would let a common word *subtract* from a passage's score
    and push a good match below a bad one. Floored instead: a common word is
    worth nothing, never less than nothing.
    """
    value = math.log(1.0 + (n_docs - n_containing + 0.5) / (n_containing + 0.5))
    return max(0.0, value)


#: Tokenised passages, keyed by whatever identity the caller gives them.
#:
#: Tokenising dominates the cost of ranking — it is a regex over the full text
#: of every candidate — and passages do not change between questions. Caching
#: the tokens took ranking of the real corpus from roughly 370ms to 30ms, which
#: is the whole difference now that the lookup itself is a binary search.
#:
#: Bounded and FIFO: a knowledge base is allowed to grow without this growing
#: with it. The key includes the text length so an edited passage cannot be
#: served from a stale entry.
_INDEX_CACHE: OrderedDict[tuple[Any, int], _Index] = OrderedDict()
_INDEX_CACHE_MAX = 8192


def _cached_index(key: Any, text: str) -> _Index:
    if key is None:
        return _build_index(tokenize(text))
    cache_key = (key, len(text))
    hit = _INDEX_CACHE.get(cache_key)
    if hit is not None:
        return hit
    built = _build_index(tokenize(text))
    _INDEX_CACHE[cache_key] = built
    while len(_INDEX_CACHE) > _INDEX_CACHE_MAX:
        _INDEX_CACHE.popitem(last=False)
    return built


def clear_index_cache() -> None:
    """Forget every tokenised passage. Called after the corpus is reseeded."""
    _INDEX_CACHE.clear()


def rank(
    query: str,
    docs: Sequence[Any],
    *,
    top_k: int = 5,
    get_title=lambda d: getattr(d, "title", "") or "",
    get_content=lambda d: getattr(d, "content", "") or "",
    get_key=lambda d: getattr(d, "id", None),
) -> list[Scored]:
    """Rank `docs` against `query` with BM25 over title and body.

    The statistics come from the candidates passed in, not from the whole
    collection. That makes this a re-ranker: whatever narrowed the field is
    trusted to have found the plausible passages, and this decides their order.
    """
    terms = expand(tokenize(query))
    if not terms or not docs:
        return []

    wanted = set(terms)
    body_counts: list[_Index] = []
    title_counts: list[_Index] = []
    body_lengths: list[int] = []
    title_lengths: list[int] = []
    for d in docs:
        key = get_key(d)
        body = _cached_index(key, get_content(d))
        title = _cached_index(("t", key) if key is not None else None, get_title(d))
        body_counts.append(body)
        title_counts.append(title)
        body_lengths.append(body[1][-1])
        title_lengths.append(title[1][-1])

    n = len(docs)
    avg_body = sum(body_lengths) / n or 1.0
    avg_title = sum(title_lengths) / n or 1.0

    containing_body = Counter()
    containing_title = Counter()
    for counts in body_counts:
        for t in wanted:
            if _tf(counts, t):
                containing_body[t] += 1
    for counts in title_counts:
        for t in wanted:
            if _tf(counts, t):
                containing_title[t] += 1

    results: list[Scored] = []
    for i, d in enumerate(docs):
        body_tf = body_counts[i]
        title_tf = title_counts[i]
        body_len = body_lengths[i] or 1
        title_len = title_lengths[i] or 1

        score = 0.0
        matched: list[str] = []
        for term in wanted:
            tf_b = _tf(body_tf, term)
            if tf_b:
                idf = _idf(n, containing_body[term])
                score += idf * (tf_b * (K1 + 1)) / (
                    tf_b + K1 * (1 - B + B * body_len / avg_body)
                )
            tf_t = _tf(title_tf, term)
            if tf_t:
                idf = _idf(n, containing_title[term])
                score += TITLE_WEIGHT * idf * (tf_t * (K1 + 1)) / (
                    tf_t + K1 * (1 - B + B * title_len / avg_title)
                )
            if tf_b or tf_t:
                matched.append(term)

        if score > 0:
            results.append(Scored(doc=d, score=score, matched=sorted(matched)))

    results.sort(key=lambda s: s.score, reverse=True)
    return results[:top_k]


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------
#: The subjects this product practises, in the three languages it is asked in,
#: plus the romanised spellings people actually type. One of these appearing is
#: what makes a question ours.
#:
#: Split by discipline only for reading; the gate treats them as one set.
_DISCIPLINES = {
    # Astrology proper
    "astrology", "astrologer", "horoscope", "kundli", "kundali", "janam",
    "jyotish", "jyotisha", "rashi", "rasi", "zodiac", "lagna", "ascendant",
    "nakshatra", "nakshatras", "dasha", "dasa", "mahadasha", "antardasha",
    "bhukti", "transit", "gochar", "graha", "grah", "planet", "planetary",
    "house", "bhava", "yoga", "yogas", "dosha", "dosh", "manglik", "mangal",
    "kaalsarp", "kalsarp", "sadesati", "shani", "saturn", "guru", "jupiter",
    "mars", "venus", "shukra", "budh", "mercury", "surya", "sun", "chandra",
    "moon", "rahu", "ketu", "retrograde", "combust", "aspect", "drishti",
    "navamsa", "d9", "d10", "varga", "divisional", "panchang", "panchanga",
    "tithi", "muhurat", "muhurta", "hora", "ayanamsa", "sidereal",
    "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
    "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    "mesh", "brish", "mithun", "kark", "singha", "kanya", "tula", "brischik",
    "dhanu", "makar", "kumbha", "meen",
    # Matchmaking
    "matchmaking", "kundlimilan", "milan", "guna", "gun", "ashtakoot",
    "compatibility", "nadi", "bhakoot", "marriage", "biye", "bibaho", "shaadi",
    "vivah", "spouse", "partner", "husband", "wife",
    # Numerology
    "numerology", "mulank", "bhagyank", "chaldean", "lifepath", "destiny",
    "namenumber", "numeroscope", "sankhya",
    # Vastu
    "vastu", "vaastu", "direction", "disha", "brahmasthan", "pada", "zone",
    "entrance", "northeast", "southwest", "ishan", "agni", "nairitya",
    # Palm / face
    "palm", "palmistry", "hast", "hastrekha", "rekha", "mount", "lifeline",
    "heartline", "headline", "face", "physiognomy", "samudrik", "forehead",
    # Remedies
    "remedy", "remedies", "upay", "upaay", "gemstone", "ratna", "stone",
    "mantra", "puja", "pooja", "donation", "daan", "fasting", "vrat",
    "rudraksha", "yantra",
    # Romanised multi-word terms arrive as separate tokens.
    "sade", "saadhe", "sati", "dhaiya",
    # Native script
    "জন্মছক", "ছক", "প্রবেশদ্বার", "দ্বার", "মুখমণ্ডল", "মুখ", "রুদ্রাক্ষ",
    "জন্মপত্রিকা", "পত্রিকা", "গ্রহণ", "অমাবস্যা", "পূর্ণিমা", "একাদশী",
    "জন্मকুণ্ডলী", "জাতক", "জাতিকা", "ঠিকুজি",
    "जन्मकुंडली", "प्रवेशद्वार", "रुद्राक्ष", "मुखमंडल", "जन्मपत्री",
    "জ্যোতিষ", "কুন্ডলী", "কুণ্ডলী", "রাশি", "নক্ষত্র", "দশা", "গ্রহ",
    "লগ্ন", "যোগ", "দোষ", "মাঙ্গলিক", "শনি", "বৃহস্পতি", "মঙ্গল", "শুক্র",
    "বুধ", "সূর্য", "চন্দ্র", "রাহু", "কেতু", "ভাব", "গোচর", "পঞ্চাং",
    "তিথি", "মুহূর্ত", "বাস্তু", "দিক", "সংখ্যাতত্ত্ব", "অঙ্ক", "রত্ন",
    "প্রতিকার", "মন্ত্র", "পূজা", "হস্তরেখা", "রেখা", "বিবাহ", "বিয়ে",
    "কোষ্ঠী", "ফলাফল", "ভাগ্য", "গুণ", "মিলন",
    "ज्योतिष", "कुंडली", "राशि", "नक्षत्र", "दशा", "ग्रह", "लग्न", "योग",
    "दोष", "मांगलिक", "शनि", "गुरु", "मंगल", "शुक्र", "बुध", "सूर्य",
    "चंद्र", "राहु", "केतु", "भाव", "गोचर", "पंचांग", "तिथि", "मुहूर्त",
    "वास्तु", "दिशा", "अंक", "रत्न", "उपाय", "मंत्र", "पूजा", "हस्तरेखा",
    "विवाह", "शादी", "भाग्य", "गुण",
}

#: Timing and auspiciousness — the muhurta vocabulary.
#:
#: Missing from the first version of this lexicon, which refused
#: "আজকের দিনে কোন সময়ে শুভ কাজ শুরু করা উচিত?" — asking which hour of today
#: is auspicious to begin something, one of the most ordinary questions an
#: astrologer is asked. Several of these words are generic on their own
#: ("time", "day", "work"); they are here anyway, because the cost of refusing
#: a real question is higher than the cost of letting a vague one reach a model
#: that still has the tools and the passages behind it.
_TIMING = {
    "auspicious", "inauspicious", "favourable", "favorable", "unfavourable",
    "shubh", "shubha", "ashubh", "time", "timing", "today", "tomorrow",
    "day", "date", "hour", "moment", "period", "season", "start", "begin",
    "work", "success", "successful", "progress", "colour", "color", "lucky",
    "suitable", "best",
    # Romanised — how people actually type on a phone keyboard.
    "aaj", "aj", "ajke", "ajker", "din", "raat", "rat", "subah", "sokal",
    "shaam", "sondha", "samay", "somoy", "waqt", "kal", "parso", "hafta",
    "saptah", "mahina", "mash", "saal", "bachar", "bochor", "varsh",
    "shubho", "bhalo", "kharap", "accha", "bura",
    "muhurat", "muhurta", "kaj", "kaam", "shuru", "safal", "safalta",
    "unnati", "rang", "rong",
    "শুভ", "অশুভ", "শুভাশুভ", "সময়", "দিন", "তারিখ", "ক্ষণ", "বেলা",
    "আজ", "আজকে", "আজকের", "কাল", "আগামী", "কাজ", "শুরু", "সফল",
    "সাফল্য", "উন্নতি", "রং", "রঙ", "ভালো", "খারাপ", "উপযুক্ত", "অনুকূল",
    "शुभ", "अशुभ", "समय", "दिन", "तारीख", "क्षण", "आज", "कल", "काम",
    "शुरू", "सफल", "सफलता", "उन्नति", "रंग", "अच्छा", "बुरा", "अनुकूल",
}

#: The things people consult an astrologer *about*. A question naming one of
#: these is ours even when it names no technical term: "আমার চাকরি কবে হবে"
#: is a career reading, not an off-topic question.
_LIFE_TOPICS = {
    "career", "job", "chakri", "chakuri", "business", "byabsa", "vyapar",
    "profession", "promotion", "salary", "money", "wealth", "finance",
    "financial", "income", "debt", "loan", "rin", "poisa", "taka", "dhan",
    "paisa", "property", "land", "house", "home", "bari", "flat",
    "health", "illness", "disease", "rog", "asustho", "surgery", "operation",
    "child", "children", "santan", "baccha", "pregnancy", "conceive",
    "education", "study", "exam", "porasona", "padhai", "result", "admission",
    "foreign", "abroad", "bidesh", "videsh", "visa", "travel", "journey",
    "litigation", "court", "case", "mamla", "enemy", "shatru", "dushman",
    "love", "prem", "pyar", "relationship", "divorce", "separation",
    "future", "bhabishyat", "bhavishya", "luck", "fate", "life",
    "চাকরি", "ব্যবসা", "অর্থ", "টাকা", "সম্পত্তি", "স্বাস্থ্য", "রোগ",
    "সন্তান", "শিক্ষা", "পড়াশোনা", "পরীক্ষা", "বিদেশ", "ভ্রমণ", "মামলা",
    "শত্রু", "প্রেম", "ভালোবাসা", "বিচ্ছেদ", "ভবিষ্যৎ", "ভাগ্য", "জীবন",
    "উন্নতি", "চাকরী", "পদোন্নতি", "ঋণ",
    "नौकरी", "व्यापार", "धन", "पैसा", "संपत्ति", "स्वास्थ्य", "रोग",
    "संतान", "शिक्षा", "पढ़ाई", "परीक्षा", "विदेश", "यात्रा", "मुकदमा",
    "शत्रु", "प्रेम", "तलाक", "भविष्य", "भाग्य", "जीवन", "उन्नति",
}

# ---------------------------------------------------------------------------
# Which language is this, and can we judge it?
# ---------------------------------------------------------------------------
#: Script ranges, in the order they are tested. A message is attributed to
#: whichever script most of its letters belong to.
_SCRIPTS: tuple[tuple[str, tuple[tuple[int, int], ...]], ...] = (
    ("bn", ((0x0980, 0x09FF),)),
    ("hi", ((0x0900, 0x097F),)),        # Devanagari: Hindi, Marathi, Nepali
    ("pa", ((0x0A00, 0x0A7F),)),
    ("gu", ((0x0A80, 0x0AFF),)),
    ("or", ((0x0B00, 0x0B7F),)),
    ("ta", ((0x0B80, 0x0BFF),)),
    ("te", ((0x0C00, 0x0C7F),)),
    ("kn", ((0x0C80, 0x0CFF),)),
    ("ml", ((0x0D00, 0x0D7F),)),
    ("si", ((0x0D80, 0x0DFF),)),
    ("ur", ((0x0600, 0x06FF), (0x0750, 0x077F))),
    ("he", ((0x0590, 0x05FF),)),
    ("ru", ((0x0400, 0x04FF),)),
    ("th", ((0x0E00, 0x0E7F),)),
    ("my", ((0x1000, 0x109F),)),
    ("ja", ((0x3040, 0x30FF),)),
    ("zh", ((0x4E00, 0x9FFF),)),
    ("ko", ((0xAC00, 0xD7AF),)),
)

#: The languages SUBJECT_TERMS actually covers. A question in anything else
#: cannot be judged off-subject here, because we hold none of its vocabulary.
JUDGEABLE = frozenset({"bn", "hi", "en"})


def detect_language(text: str) -> str:
    """Which language this message is written in, by script.

    Script is a coarse signal and a deliberate one: it needs no model, no
    network and no training data, and it is right about exactly the thing that
    matters here — whether we hold any vocabulary for this language.

    Latin script is reported as "en". It cannot distinguish English from
    Spanish or from romanised Bengali, and it does not need to: the model is
    told to answer in whatever language the user wrote, and the gate treats
    Latin as judgeable because its English lexicon applies.
    """
    counts: dict[str, int] = {}
    latin = 0
    for char in text:
        code = ord(char)
        if not char.isalpha():
            continue
        if code < 0x0250:
            latin += 1
            continue
        for name, ranges in _SCRIPTS:
            if any(lo <= code <= hi for lo, hi in ranges):
                counts[name] = counts.get(name, 0) + 1
                break
    if not counts:
        return "en"
    best, best_count = max(counts.items(), key=lambda kv: kv[1])
    # A few stray native characters in an otherwise Latin message (a name, a
    # quoted term) should not change the language of the whole message.
    return best if best_count >= latin else "en"


#: Astrology vocabulary in the Latin-script languages people are most likely to
#: write in besides English. Small on purpose: enough that a real question is
#: recognised, not an attempt at a dictionary.
_LATIN_OTHER = {
    # Spanish / Portuguese
    "astrologia", "astrología", "horoscopo", "horóscopo", "horoscópo",
    "signo", "carta", "astral", "natal", "luna", "lua", "planeta",
    "casamento", "matrimonio", "matrimônio", "boda", "trabajo", "trabalho",
    "empleo", "emprego", "dinero", "dinheiro", "salud", "saúde", "amor",
    "suerte", "sorte", "futuro", "destino", "piedra", "pedra",
    # French
    "astrologie", "horoscope", "thème", "theme", "lune", "planète", "planete",
    "mariage", "travail", "emploi", "argent", "santé", "sante", "amour",
    "chance", "avenir", "destin", "pierre",
    # German
    "horoskop", "sternzeichen", "geburtshoroskop", "mond",
    "planet", "hochzeit", "heirat", "arbeit", "beruf", "geld", "gesundheit",
    "liebe", "glück", "gluck", "zukunft", "schicksal", "stein",
    # Indonesian / Malay
    "astrologi", "zodiak", "bulan", "pernikahan",
    "jodoh", "pekerjaan", "kerja", "uang", "kesehatan", "cinta",
    "keberuntungan", "masa", "depan", "nasib", "batu",
}

#: Everything the gate accepts, as one set.
SUBJECT_TERMS: frozenset[str] = frozenset(
    _DISCIPLINES | _LIFE_TOPICS | _TIMING | _LATIN_OTHER
)

#: Attempts to reset the assistant's instructions rather than ask it something.
#: These are refused outright: there is no legitimate question that needs them,
#: so there is no cost to refusing, and letting one through costs the persona
#: and every rule attached to it.
_INJECTION = re.compile(
    r"(ignore\s+(all\s+|any\s+|the\s+)?(previous|prior|above|earlier)\s+"
    r"(instruction|instructions|prompt|prompts|rule|rules|message|messages)"
    r"|disregard\s+(all\s+|any\s+|the\s+)?(previous|prior|above)"
    r"|forget\s+(everything|all\s+(previous|prior)|your\s+instructions)"
    r"|you\s+are\s+now\s+(a|an)\s"
    r"|act\s+as\s+(if\s+you\s+are\s+)?(a|an)?\s*(dan|developer\s+mode|jailbreak)"
    r"|pretend\s+(to\s+be|you\s+are)"
    r"|(reveal|show|print|repeat|output)\s+(me\s+)?(your\s+)?"
    r"(system\s+prompt|initial\s+prompt|instructions)"
    r"|<\s*/?\s*(system|assistant)\s*>"
    r")",
    re.IGNORECASE,
)


def looks_like_injection(question: str) -> bool:
    """Whether this is an attempt to rewrite the assistant rather than ask it."""
    return bool(_INJECTION.search(question))



#: Subject words written in an Indic script, long enough to be distinctive.
#:
#: Used for the containment test below. Latin terms are deliberately excluded:
#: English does not compound without spaces, so containment there would accept
#: "homework" for "work" and "Monday" for "day", and off-topic questions would
#: start getting through.
_NATIVE_SUBJECTS = tuple(
    sorted(
        (t for t in SUBJECT_TERMS if len(t) >= 3 and _NATIVE_CHARS.search(t)),
        key=len,
        reverse=True,
    )
)


def _subject_hits(terms: list[str]) -> set[str]:
    """Which of these words are about our subjects.

    Three tests, because an exact lookup is not enough for the languages this
    is asked in.

    Bengali and Hindi build compounds with no space: মহাদশা is মহা + দশা,
    অন্তর্দশা is অন্তর + দশা, রাশিফল is রাশি + ফল. A lexicon holding দশা does
    not match any of them, and the gate refused "আমার বর্তমান মহাদশা ও
    অন্তর্দশা কেমন?" — about as central a question as Vedic astrology has.
    Adding each compound by hand is endless; containment catches the whole
    family at once.

    The equivalence table counts as well. It is already a curated list of this
    product's vocabulary, so anything it can translate is by definition
    something we talk about.
    """
    found: set[str] = set()
    for term in terms:
        if term in SUBJECT_TERMS:
            found.add(term)
            continue
        # Anything the translation table recognises is on subject by definition.
        if _equivalents(term):
            found.add(term)
            continue
        # Indic compounds: a subject word sitting anywhere inside a longer one.
        if _NATIVE_CHARS.search(term):
            for subject in _NATIVE_SUBJECTS:
                if subject in term:
                    found.add(term)
                    break
    return found


@dataclass
class Verdict:
    """Why a question was let through, or was not."""

    answerable: bool
    reason: str
    subjects: list[str] = field(default_factory=list)


#: A question with no subject term and fewer than this many real words is
#: treated as conversational rather than off-topic, so greetings and
#: "thank you" are not met with a refusal notice.
_SHORT_QUESTION = 3

#: Longest a message can be and still count as a greeting or a "go on".
#: Beyond this it is a question in its own right and is judged as one.
_PLEASANTRY_MAX_TERMS = 3

#: Openers and continuations that should not be refused.
_PLEASANTRIES = {
    "hi", "hello", "hey", "namaskar", "namaste", "nomoskar", "pranam",
    "salam", "assalamualaikum", "thanks", "thank", "dhanyabad", "dhonnobad",
    "ok", "okay", "accha", "thik", "bye", "goodbye",
    # Asking the reading to continue.
    "more", "details", "detail", "explain", "continue", "elaborate",
    "বলুন", "বল", "আরও", "আরো", "বিস্তারিত", "বুঝিয়ে", "বিশদ",
    "बताइए", "बताओ", "और", "विस्तार", "समझाइए",
    "নমস্কার", "প্রণাম", "ধন্যবাদ", "হ্যালো", "আচ্ছা", "ঠিক",
    "नमस्कार", "नमस्ते", "प्रणाम", "धन्यवाद", "हैलो", "अच्छा",
}


def is_answerable(question: str, *, extra_vocabulary: Iterable[str] = ()) -> Verdict:
    """Whether this question is within the subjects we practise.

    Deliberately generous. A question is refused only when it carries no trace
    of astrology, none of the life matters people consult an astrologer about,
    and no word the knowledge base itself uses. Anything else is passed to the
    model, which still has the tools and the retrieved passages behind it.

    `extra_vocabulary` lets the caller widen the subject list with the words of
    the corpus actually loaded, so seeding new material widens the gate without
    anybody editing this file.
    """
    if not question or not question.strip():
        return Verdict(False, "empty")

    if looks_like_injection(question):
        return Verdict(False, "injection")

    terms = tokenize(question)

    # Greetings and "go on" — but only when the message is actually short.
    # "explain" and "detail" mean continue a reading when they are the whole
    # message; in "Explain how a car engine works in detail" they are not what
    # the question is about, and without the length bound that sentence got in.
    words = set(tokenize(question, keep_stopwords=True))
    if words & _PLEASANTRIES and len(terms) <= _PLEASANTRY_MAX_TERMS:
        return Verdict(True, "pleasantry")
    hits = sorted(_subject_hits(terms))
    if hits:
        return Verdict(True, "subject", hits)

    extra = {normalise(w) for w in extra_vocabulary}
    if extra:
        corpus_hits = sorted(set(terms) & extra)
        if corpus_hits:
            return Verdict(True, "corpus", corpus_hits)

    # Nothing recognised. A very short question is more likely conversational
    # than off-topic, so it is let through rather than refused.
    if len(terms) < _SHORT_QUESTION:
        return Verdict(True, "short")

    # Written in a language we hold no vocabulary for, so there is nothing to
    # judge it against. Refusing here would mean refusing every Tamil, Telugu,
    # Gujarati, Punjabi, Malayalam, Odia and Urdu speaker on the grounds that
    # we cannot read them, which is the worst possible reason. The model still
    # has the tools and the passages behind it, and it answers in whatever
    # language it was asked in.
    language = detect_language(question)
    if language not in JUDGEABLE:
        return Verdict(True, "unjudged_language", [language])

    return Verdict(False, "off_topic")


#: What to say when a question is not ours, in the reader's language.
REFUSALS = {
    "bn": (
        "ক্ষমা করবেন, আমি কেবল জ্যোতিষ, কুন্ডলী, রাশি, নক্ষত্র, সংখ্যাতত্ত্ব, "
        "বাস্তু, হস্তরেখা ও মুখমণ্ডল বিচার সংক্রান্ত প্রশ্নের উত্তর দিতে পারি। "
        "আপনার জীবন, ভাগ্য বা কুন্ডলী সম্পর্কে কিছু জিজ্ঞাসা করুন, আমি সাহায্য করব।"
    ),
    "hi": (
        "क्षमा करें, मैं केवल ज्योतिष, कुंडली, राशि, नक्षत्र, अंक शास्त्र, "
        "वास्तु, हस्तरेखा और मुख विश्लेषण से जुड़े प्रश्नों का उत्तर दे सकता हूँ। "
        "कृपया अपने जीवन, भाग्य या कुंडली के बारे में पूछें।"
    ),
    "en": (
        "I can only help with astrology, kundli, rashi, nakshatra, numerology, "
        "vastu, palmistry and face reading. Please ask me about your chart, "
        "your life or your fortune and I will gladly help."
    ),
}


def refusal_text(language: str) -> str:
    """The refusal, in the reader's language where we have it written.

    Only reached for bn, hi and en in practice: a question in any other
    language is never refused for being off-subject, because `is_answerable`
    cannot judge a language it holds no vocabulary for.
    """
    return REFUSALS.get(language, REFUSALS["en"])
