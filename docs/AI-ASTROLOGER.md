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
