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

`SUBJECT_TERMS` covers the disciplines *and* the life matters people consult an
astrologer about, so *"When will I get a job?"* passes without naming a single
technical term.

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
