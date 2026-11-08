# AI Astrologer — how it answers, and how it is kept honest

Read this before changing anything under `app/services/ai/`.

## The shape of it

The assistant answers from **two** places, and the difference matters:

| | Source | Trustworthy because |
| :--- | :--- | :--- |
| Computed | `calculate_kundli_tool`, `calculate_matchmaking_tool`, `calculate_numerology_tool`, `get_daily_horoscope_tool` | Swiss Ephemeris. Exact, and never retrieved from any document. |
| Retrieved | `search_vedic_rules_tool` → `knowledge_service.search_knowledge` | Passages from the client's own resources, cited back. |

This is why the gate is not the one a pure document assistant would use — see below.

## Retrieval (`knowledge_service.search_knowledge`)

Two steps. The database narrows the field with an index; BM25 decides the order.

1. **Candidates** come from the MongoDB `$text` index on `(title, content)`,
   capped at `_CANDIDATE_LIMIT`. If that yields almost nothing — the index
   stems for English and merely tokenises Bengali and Hindi — a bounded,
   word-anchored regex query runs as well.
2. **Ranking** is BM25 (`retrieval.rank`) over title and body, title weighted
   `TITLE_WEIGHT`.

### What this replaced, and why it was wrong

The previous search called `AIKnowledgeDoc.find(...).to_list()` — **the entire
collection, on every message** — and scored with `content.count(token)`. Four
separate defects:

- `count("ram")` scored a hit inside `"program"`. Substring, not word.
- No length normalisation, so size alone won. Measured on the real corpus, the
  same 106,678-character passage came back as the top hit for three unrelated
  questions; mean top-1 length was 77,170 against a corpus mean of 2,286.
- No term saturation, so repeating a word bought unbounded score.
- It got slower with every document seeded.

After: mean top-1 length 12,135, and ranking is ~1ms warm against ~45ms.

### Things that look like bugs and are not

- **`_idf` is floored at zero.** Textbook BM25 idf goes negative for a term in
  more than half the passages, which lets a common word *subtract* and push a
  real match below an unrelated one.
- **Matching is by prefix, not exact, for terms of `MIN_PREFIX` or more.**
  Bengali and Hindi inflect by suffix — চাকরি becomes চাকরির, দোষ becomes
  দোষের — so exact matching answers normal questions with nothing. A prefix is
  anchored at the start of a word; a substring is anchored nowhere, which is
  the `ram`/`program` bug. Short terms stay exact because a three-letter
  prefix matches far too much.
- **Tokenised passages are cached** (`_INDEX_CACHE`). Tokenising dominates the
  cost and passages do not change between questions. The key includes the text
  length so an edited passage cannot be served stale. Call
  `retrieval.clear_index_cache()` after reseeding.

## Crossing the language gap

**The client's knowledge base contains no Bengali at all** — 1.2 million
characters, zero Bengali codepoints — while the product answers in Bengali by
default and most questions arrive in it. Before `retrieval.expand`, every
Bengali question retrieved *nothing*, so grounding silently did nothing for the
majority of users. This was not a ranking problem and no amount of ranking
work would have found it.

`TERM_EQUIVALENTS` maps native-script vocabulary to the English the corpus
actually uses, and `expand()` adds those terms to both the `$text` query and
the BM25 scoring. Inflected forms resolve through the longest matching stem, so
দোষের finds দোষ.

This is the cheap half of the fix. The thorough half is a multilingual
embedding — see *Not done yet*.

## The gate (`retrieval.is_answerable`)

Checked **before the model is called at all**, in
`groq_service.generate_astrology_response`. A refusal taken here cannot be
argued with; a model merely instructed to refuse can always be talked round.

It is deliberately **not** a corpus-coverage gate. Gating on "is this question
covered by a document" would refuse *"আমার দশা কী চলছে?"* — which the ephemeris
answers perfectly and no document contains. So it asks a narrower question: is
this within the subjects we practise?

Order: injection → pleasantry → subject term → corpus vocabulary → very short →
refuse. It errs towards answering, because wrongly refusing a paying customer
is worse than a slightly loose answer.

`SUBJECT_TERMS` covers the disciplines, the life matters people consult an
astrologer about, *and* timing and auspiciousness, so *"When will I get a job?"*
passes without naming a single technical term.

The timing group (`_TIMING`) was missing from the first version and the gate
refused *"আজকের দিনে কোন সময়ে শুভ কাজ শুরু করা উচিত?"* — which hour of today is
auspicious to begin something, one of the most ordinary questions an astrologer
is asked. Several of its words are generic on their own ("time", "day",
"work"); they are included anyway, because refusing a real question costs more
than letting a vague one reach a model that still has the tools and the
passages behind it. `tests/test_ai_retrieval.py` pins every question that was
wrongly refused.

The knowledge base's own vocabulary is passed in as `extra_vocabulary`
(`knowledge_service.corpus_vocabulary`), so seeding new material widens the
gate without anybody editing the lexicon.

### Matching is not exact, and must not be

`_subject_hits` runs three tests, because an exact lookup is wrong for the
languages this is asked in:

1. the word is in `SUBJECT_TERMS`;
2. `TERM_EQUIVALENTS` can translate it — that table is already a curated list
   of this product's vocabulary, so anything in it is on subject by definition;
3. **for Indic script only**, a subject word sitting anywhere inside a longer
   one.

Test 3 is the important one. Bengali and Hindi build compounds with no space:
মহাদশা is মহা + দশা, অন্তর্দশা is অন্তর + দশা, রাশিফল is রাশি + ফল,
কালসর্পদোষ is কালসর্প + দোষ. A lexicon holding দশা matched none of them, and
the gate refused *"আমার বর্তমান মহাদশা ও অন্তর্দশা কেমন?"* — about as central
a question as Vedic astrology has.

It is restricted to Indic script deliberately. English does not compound
without spaces, so containment there would accept "homework" for "work" and
"Monday" for "day", and off-topic questions would start getting through.

### Why there is a sweep instead of a list of fixes

Two rounds of false refusals reached the user before
`SHOULD_ANSWER` / `SHOULD_REFUSE` existed in `tests/test_ai_retrieval.py`.
Adding vocabulary as each one was reported was never going to converge — the
first round was the missing muhurta words, the second was the compound-word
defect above, and the sweep then found six more in one pass, plus a question
the gate should have refused and did not ("Recommend a good movie" matched
"good", which is now out of the lexicon).

**Add to the sweep, not to the lexicon.** If a real question is refused, put it
in `SHOULD_ANSWER` first and then make it pass; the sweep runs both directions,
so widening the gate cannot quietly open it to everything.

## Grounding

`citations` reflects what was actually consulted — tool results and matched
admin rules. **It is empty when nothing was consulted, and that is correct.**

This previously attached a citation to *"বৃহৎ পরাশর হোরাশাস্ত্র ও ফলদীপিকা"*
whenever no tool had run and no rule had matched — which is precisely when the
answer rested on no source at all. An empty list is the truthful answer to
"what was this based on", and it can be shown to the client without anybody
having to defend a reference that was never read.

## Chunking

`_chunk_text` used to split on blank lines only. A PDF extracted as one
unbroken run has none, so whole documents were stored as single passages — the
live corpus held one of **367,703 characters** against a requested 800. That
one defect made those passages match nearly every question, made the context
sent to the model useless, and meant a single query pulled over a megabyte out
of Atlas (measured: 3.2s for one lookup).

Now over-long blocks are split at sentence boundaries — including the Bengali
and Hindi danda `।`, without which native-script text had no split points at
all — and mid-sentence only when one sentence exceeds the limit, cutting at the
last space so no word is left in neither piece.

**Documents seeded before this fix are still over-sized.** Run:

```
uv run python scripts/rechunk_knowledge.py          # dry run
uv run python scripts/rechunk_knowledge.py --apply
```

It replaces one over-sized passage at a time rather than dropping the
collection, and inserts replacements before removing the original.

## Tests

`tests/test_ai_retrieval.py` — 72 tests, no MongoDB and no Groq required.
Ranking and the gate are where this is right or wrong, so both are testable on
every commit. Several tests are named for the specific defect they pin down.

The chat-level tests monkeypatch `httpx.AsyncClient.post` to raise, proving the
refusal happens *before* any network call rather than after one.

## Rendering the reply

The model is asked for structured readings and answers in Markdown — headed
sections, bold terms, tables of planet against effect. The chat printed that as
plain text, so a reading arrived as a wall of `##`, `**` and pipe characters.

`src/components/ai/ai-markdown.tsx` in the web app renders it, with two choices
that are about the chat bubble rather than about Markdown:

- **Tables scroll sideways in their own box.** A reading's table is often five
  or six columns of Bengali, far wider than a phone. Verified at 375px: a
  789px-wide table scrolls inside a 276px wrapper and the page itself still has
  no horizontal scroll.
- **Headings render at close to body size.** In a chat bubble these are section
  labels, not page headings.

Only the astrologer's side is rendered as Markdown. What the user typed is
shown verbatim — nobody asking about their "7*7 numerology" wants half their
question turned into italics.

Raw HTML is not enabled, and should stay that way: the text comes from a
language model and nothing it writes should become markup.

## Giving the model something worth interpreting

An interpreter is only as accurate as the chart it is handed. Four things were
wrong with what the tools passed, all found by reading real replies rather than
by reading code:

- **Numbers instead of names.** `d1_asc_sign` is an int 1-12 and every planet
  carried a `sign_num`, so a reading opened with "জন্ম লগ্ন: 11". `_sign_name`
  and `_planet_name` now resolve both through `RASHI_TRANSLATIONS` and
  `PLANET_NAMES_LOCALIZED`, in the language being answered in.
- **English names in Bengali prose** — "Jupiter", "Capricorn". Now
  "বৃহস্পতি (Jupiter)": the reading reads naturally and the English stays
  available to anyone checking the figures.
- **No dasha dates.** `CurrentDashaInfo` has `start_date` and `end_date` and the
  summary did not pass them, so a model asked "when will I get a job?" held no
  dates and invented some — it announced a Venus sub-period running in 2024
  when the chart said 2026-2028. The real dates are now sent.
- **Date-less periods are deliberately not sent.** `dashas_grid` carries the
  coming mahadasha lords but leaves their dates empty. Passing those would
  invite exactly the invention above, so they are left out and the prompt tells
  the model to say a fuller dasha chart is needed rather than guess.

## One round of tools was not enough

The model got one chance to call tools. The results were then sent back
*without* the tool definitions, and Groq reads a request carrying no tools as
`tool_choice: none` — so the moment the model wanted a second tool it answered

```
"Tool choice is none, but model called a tool"
```

with a 400, and the code quietly served `_local_astrological_fallback` instead.

This hit exactly the questions that need two tools. *"আজকের দিনটা আমার কেমন
যাবে?"* needs the birth chart **and** today's sky, so it could never be
answered properly — and the failure was invisible, because the fallback is
plausible-looking text. Two different questions returning a byte-identical
reply is what gave it away.

Tool calling is now a loop (`MAX_TOOL_ROUNDS`), carrying the tools every round.

## Fitting inside the free tier

The product must run on Groq's free tier. Every model available on this key —
`openai/gpt-oss-120b`, `gpt-oss-20b`, `qwen/qwen3.8-27b` — carries the same
**8,000 tokens per minute**, so there is no model to switch to. The budget is
fixed and the work had to fit inside it.

What made it fit, largest effect first:

**The chart is computed before the model is called.** When birth details are
known, the kundli is not a question — it is arithmetic. It is run up front and
placed in the system context, so the common question costs **one** API call
instead of three. Every tool round re-sends the system prompt, the tool
definitions *and* the whole conversation, so a round costs about 1,500 tokens;
the chart block costs about 550. It pays for itself immediately.

**Everything re-sent per round was cut.** Tool schemas 3,491 → 2,511
characters; system prompt 4,257 → 2,069. Per-round overhead fell from ~2,273
tokens to ~1,526.

**The chart summary lost its largest field.** `dignities` restated in prose
what `planets` already carries — sign, house, retrogradation. Summary 2,641 →
1,661 characters.

**History is bounded.** The endpoint sends the last 8 messages; readings are
long, so each is now truncated to `MAX_HISTORY_CHARS` and only
`MAX_HISTORY_MESSAGES` are replayed. Quoting several full readings back costs
thousands of tokens that the current question needs.

**Replies are capped** at `MAX_REPLY_TOKENS` (900, was 2,048). Output is
charged against the same budget, and a longer answer is unreadable on a phone.

**Short rate limits are waited out** rather than falling back. Groq states the
delay; `_post_groq` honours it up to `MAX_RATE_LIMIT_WAIT`.

Measured after: **three questions inside one minute, all answered from the
model, no fallback**, in five API calls total. One 429 occurred and the retry
absorbed it.

If a future change adds tokens per round, this is the budget it is spending.

## Errors must be logged

Every Groq failure used to be swallowed by `except Exception` straight into the
fallback. That is how a 400 on every two-tool question survived unnoticed: the
chat looked alive while no reading was being generated. Failures are now logged
with the response body, which is how both the 400 and the 429 above were found.

## Any language the user writes in

The product answers in whatever language the question arrives in, the way a
general assistant does. Three things make that work.

**The tokenizer reads every script.** It listed Latin, Devanagari and Bengali
only, so a Tamil or Gujarati question produced *no words at all* — it slipped
past the gate as a "short message" by accident, and retrieval had nothing to
search with. `_WORD` now covers the Indic blocks, Arabic, Cyrillic, Hebrew,
Thai, CJK and the rest. Note the ranges are explicit rather than `\w`: Python's
`\w` excludes combining vowel marks, and splitting on those tears আমার into আম.

**`detect_language` picks the language by script.** Coarse and deliberate — it
needs no model, no network and no training data, and it is right about the only
thing that matters here: whether we hold any vocabulary for this language.
Latin script is reported as `en`, since it cannot separate English from Spanish
from romanised Bengali and does not need to.

**The gate refuses only languages it can read.** `JUDGEABLE` is `{bn, hi, en}`
— the languages `SUBJECT_TERMS` covers. A question in Tamil, Telugu, Gujarati,
Punjabi, Malayalam, Odia or Urdu returns `unjudged_language` and is answered,
because refusing someone on the grounds that we cannot read them is the worst
possible reason to refuse. A small Latin-script vocabulary (`_LATIN_OTHER`)
covers Spanish, Portuguese, French, German and Indonesian so those are
recognised rather than waved through.

The reply language is the model's job, not a detector's: it is told to mirror
the user's language *and script*, including romanised Hinglish. The language is
**named** in the instruction ("write in Tamil (தமிழ்)") rather than described,
because "the user's language" sometimes had it answer in the language of the
chart data instead.

### Chart data must be in the reader's language too

A Tamil reply came back with Bengali words in it. The cause was not the prompt:
`current_dasha` sent `verdict_bn` and `guidance_bn` regardless of language, and
the model reasonably read that as the house style. `_narrative` now picks the
English, Bengali or Hindi variant to match, and the same applies to the
dignity's `avastha`. The prompt's Bengali sign-name list is scoped to Bengali
replies for the same reason.

### Tone

The prompt asks for an astrologer on WhatsApp, not a report generator: answer
sized to the question, short paragraphs, no headings for a small question,
greetings answered with a greeting rather than a reading. It is still required
to name the planet, house or dasha behind each claim — that is what separates a
reading from a horoscope column.

### When the model is unreachable

`_local_astrological_fallback` writes Bengali, which is right for a Bengali
reader and unreadable for everyone else. For any other language it now returns
a short note in that language saying the astrologer is busy and to ask again.
Translating the whole local synthesis is the better fix and a larger one.

## The assistant is also the product's guide

A user who cannot find a feature does not file a bug — they leave. The
assistant is the one place they will ask "how do I get my kundli?", and until
`product_guide.py` existed it could not answer, because nothing told it the
product exists.

`app_guide_tool` answers "how do I use X", "where is X", "what does X cost",
"what can you do", and anything about coins or recharging. It returns the
feature's steps, its **live** price and this user's **live** wallet balance in
one call — one call on purpose, because every extra tool round costs ~1,500
tokens against the free tier's 8,000 a minute.

### What the catalogue covers

All 22 user-facing things, checked against the API routers and the web routes
rather than remembered: every calculator, the live chat and call flows,
appointments, reviews, the wallet, saved birth details, password and security,
addresses, the assistant itself, and a "how billing works" entry for the
questions that are about money rather than a page.
`test_every_user_facing_route_is_covered` fails if a route has no feature
explaining it, so a new screen cannot ship without the assistant learning about
it.

### `notes` is what makes it a guide rather than a menu

Steps tell a user where to click. `notes` answers "why did it not work", and
the facts in it come from the code: the palm scan's failure modes are its
actual quality gates, the live-session rule ("you need rate × requested
minutes up front, and are billed for the minutes used") is what
`billing.check_can_start` enforces, and the warning to pick a birth place from
the suggestions is the bug that shifts a whole chart.

Verified live: *"amar palm scan bar bar fail hochhe keno?"* comes back with the
real causes — palm not flat, fingers bent, glare, too far, blurred.

### What is and is not stored in the catalogue

Steps and routes are in `FEATURES`. Prices and on/off switches are **not**:
they live in platform settings where an admin changes them, and are merged in
when the question is asked. A guide that quotes a stale price is worse than no
guide.

The steps are written in English only. The model translates into the user's
language better than ten hand-kept translations would, and translations are
what silently rot when a screen is renamed.

### Signed out is not the same as broke

`describe()` takes `balance=None` for a visitor and a number for a signed-in
user, and they get different answers: one is asked to sign in, the other is
told how many coins short they are and pointed at `/account/wallet`. Telling a
visitor to top up an account they do not have is the kind of thing that makes
an assistant feel broken.

### The gate had never heard of the product

Adding the guide was pointless until the gate would let the questions through.
"How do I use the kundli feature?" squeaked past on the word *kundli*, but
*"I want to know how I can add more coins to my account balance"* was refused
as off-topic — no astrology term, no life topic. The most reasonable question a
user can ask was the one question the assistant would not take. `_APP_TERMS`
fixes it.

Note what is deliberately **absent** from that list: "how", "where", "work",
"use", "free". They are question words that appear in everything, and with
"how" in the list the gate accepted *"Explain how a car engine works in
detail"*. The noun carries the subject, so the noun is what is matched. The
native-script question words are kept, because an off-topic question in Bengali
or Hindi is rare enough that the trade runs the other way.

### Aliases must cover the scripts people type in

`find()` matched romanised and English aliases only at first, so *"আমার
কুন্ডলী কীভাবে বানাবো"* found nothing — most of the audience missed. Every
feature now carries Bengali and Hindi aliases, and the longest alias wins so
"kundli matching" is not answered with the kundli page.

## Streaming

`POST /ai-astrologer/chat/stream` returns server-sent events:
`status` while a tool runs, `delta` for each piece of the answer, `done` with
the citations and follow-ups. The web page consumes it in `lib/ai-stream.ts`.

The tool rounds stream too. Groq sends tool calls as deltas like anything
else, so there is no need for an unstreamed call followed by a streamed one —
that would cost a whole extra round against the token budget. Tool-call
arguments arrive in fragments keyed by `index` and must be concatenated before
they can be parsed; `_merge_tool_call_deltas` does that.

### `reasoning_effort` — the bug that made streaming produce nothing

gpt-oss reasons before it answers, and that reasoning is charged against the
same `max_tokens` as the reply. At the default effort it reasoned 2,232
characters on a simple question and **never reached the answer**: a stream of
855 chunks containing no content at all. At `"low"` the same question reasoned
118 characters and went straight to calling the tool it needed.

It is sent only to gpt-oss, which is the only model here that accepts it.

### The tag shield

`[FOLLOW_UP: …]` and `[REMEMBER: …]` arrive at the end of a reply like any
other tokens, so a naive stream shows the reader the machinery — and
`[REMEMBER:` is a note the assistant writes to itself *about them*.
`memory.TagShield` withholds text after an unclosed `[` until the bracket
closes, drops it if it was a tag, and releases it if it was ordinary prose
("[see note]"). Text with no bracket is never delayed.

### Rate-limit retries must be capped by attempts, not only by time

The streaming path cannot reuse `_post_groq`, which buffers, so the wait is
done inline. The first version capped only total time — and because
`x-ratelimit-reset-tokens` reports a sub-second refill during sustained use,
it spun **55 times in one request**, sending the reader a status line each
time. `MIN_RATE_LIMIT_WAIT` and `MAX_RATE_LIMIT_RETRIES` bound it now.

## Memory between visits

An astrologer who forgets you the moment you leave is a search box.
`AIUserMemory` holds a handful of short facts per user, replayed into the
system context as `[WHAT YOU REMEMBER ABOUT THIS USER]` with a note of how long
ago they last spoke.

**The facts are written by the model, for free.** Asking a second model to
summarise each conversation would double the cost of every message. Instead
the model emits `[REMEMBER: …]` inline in the reply it was already producing,
exactly as it already emits `[FOLLOW_UP: …]`.

Bounded hard, because this rides along on every request: `MAX_FACTS`,
`MAX_FACT_CHARS`, `MAX_CONTEXT_CHARS`, and a TTL, enforced on write and on
read. Secrets — passwords, OTPs, card and ID numbers — are refused outright;
astrology invites intimate disclosure and a memory file is the wrong place for
any of it. `DELETE /ai-astrologer/memory` erases everything, because people are
entitled to ask and an assistant that cannot forget is one they stop telling
things to.

## Voice

`POST /ai-astrologer/transcribe` takes an audio clip and returns the words,
via Whisper on the **same Groq key**, metered in audio-seconds (7,200 an hour)
rather than against the 8,000 tokens a minute the readings compete for. Voice
therefore costs nothing that the chat needs.

Typing Bengali or Hindi on a phone keyboard is the barrier for a great many of
the people this is for, and for older users it is often the whole barrier. The
button is held rather than toggled so it cannot be left recording, and the
transcript lands **in the input box rather than being sent**, so a mis-heard
word can be corrected before it is answered.

No language is passed to Whisper: it detects better than our guess, and a user
whose app is set to Bengali may well speak Hindi.

## Handing over to a human

`find_astrologer_tool` returns who is online now, their speciality and their
rate. The prompt is explicit that it comes *after* the assistant's own answer,
once, never as a lead and never twice in a conversation. Presence is re-judged
against the clock inside the service, so an astrologer whose panel closed
without a clean disconnect is not offered.

## Routing: deciding what a question needs before calling the model

The complaint that "the AI is not answering properly" was measured rather than
guessed at. Twenty-eight realistic questions were put through the live service
(`scripts/`-style harness, kept out of the repo) and **every one of the six
failures was a rate limit**, not a mistake in the reasoning. The readings
themselves were fine; the budget ran out and users got canned fallback text.

The cause was fixed overhead. Measured on the live service:

| question | input tokens, before |
| :--- | ---: |
| "নমস্কার" | 2,342 |
| "how do I use the kundli feature?" | 2,351 |
| "আমার রাশি কী?" | 2,984 |

Saying *hello* cost 2,342 tokens, because every tool schema and the whole
system prompt went with it. At that rate three or four questions exhaust the
minute.

`services/ai/router.py` now decides, locally and with no model call:

- **which tools to offer.** Small talk gets none. A product question gets the
  guide and not the ephemeris. A reading gets the chart and the rule search,
  plus whichever specialist the wording calls for.
- **whether to compute the chart.** It costs ~550 tokens in the system context
  and is pure waste on "how do I recharge my wallet", which was being sent the
  native's full planetary positions.
- **which system prompt.** A question needing no tools needs none of the rules
  about tools either; `CONVERSATIONAL_PROMPT` is a fraction of the size.

| question | before | after |
| :--- | ---: | ---: |
| "নমস্কার" | 2,342 | 239 (−89%) |
| "আর কিছু বলুন" | 2,342 | 241 (−89%) |
| "how do I use the kundli feature?" | 2,351 | 1,369 (−41%) |
| "আমার রাশি কী?" | 2,984 | 2,173 (−27%) |

The router's bias is deliberate and is what its tests pin down: offering a tool
that goes unused costs only its schema, while failing to offer one the question
needed costs the answer. So anything uncertain gets the full set.

### Two limits, not one — and only one of them is a pause

This is the finding that explains "the AI stopped working".

Groq's free tier meters **tokens per minute** (8,000) *and* **tokens per day**
(200,000, per model). Only the first was being handled. A per-minute limit is a
pause: wait a few seconds and it refills. A per-day limit is not — once it is
spent it is gone until tomorrow, and waiting achieves nothing.

So after roughly seventy readings the day's budget for one model was gone and
**every user got canned fallback text for the rest of the day**, whatever they
asked. Diagnosed from the error body, which says so plainly:

```
tokens per day (TPD): Limit 200000, Used 199168, Requested 2160
```

Each model has its own daily bucket. `MODEL_CHAIN` steps over a spent model to
the next, so the assistant keeps answering. Verified live with the primary
model genuinely exhausted: it switched to `gpt-oss-20b` and gave real readings
rather than falling back.

Three models is three times the free daily capacity, at no cost.


### The streaming path needs the same treatment

`stream_astrology_response` builds its own request rather than going through
`_post_groq`, so the daily-limit handling had to be repeated there. Without it
the **website** — which streams — kept falling back for the rest of the day
while the non-streaming endpoint had already moved to another model. Two code
paths, one rule; forgetting the second is how a fix looks applied and is not.

### Do not offer a tool whose answer is already in the context

The chart is precomputed into the system context *and* `calculate_kundli_tool`
was still being offered, so the model fetched what it had just been given. That
cost a whole extra round, and a round re-sends the prompt, the schemas and the
conversation: roughly 2,600 tokens became roughly 6,000. Against a daily
allowance that is the difference between about seventy-five readings a day and
about thirty-three.

### What the free tier actually supports

Roughly **two to three readings a minute**, per account, and that limit is
account-wide rather than per user. A single person chatting at a human pace
fits comfortably. Several at once will not, and no amount of trimming changes
that — it is the shape of the tier.

## Not done yet

- **Embeddings.** Dense retrieval with reciprocal-rank fusion would fix
  cross-language retrieval properly rather than by vocabulary table. Needs a
  Gemini key (`GEMINI_API_KEY`); this deployment has only `GROQ_API_KEY`, and
  Groq serves no embedding model. `retrieval.rank` is written so a dense score
  can be fused in without restructuring.
- **An evaluation set.** There is no gold set of questions with known-good
  answers, so retrieval quality is argued from examples rather than measured.
  Until one exists, "accurate" is a judgement, not a number.
- **Streaming.** Neither the API nor the web page streams; the whole answer
  lands at once after several seconds.
