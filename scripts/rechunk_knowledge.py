"""Re-splits over-sized AI knowledge passages into properly sized ones.

`_chunk_text` used to split only on blank lines. A PDF extracted as one
unbroken run of text has none, so whole documents were stored as a single
"chunk" — the live corpus held passages of up to 367,000 characters against a
requested 800. That one defect caused three separate problems:

  * a giant passage contains every common word, so it matched almost every
    question and crowded out the passage that was actually relevant;
  * the context handed to the model was useless, being either truncated or
    mostly irrelevant;
  * a single question pulled over a megabyte out of Atlas, which is why
    retrieval took seconds rather than milliseconds.

The chunker is fixed, but documents already stored were chunked by the old one.
This rewrites those, and only those.

    uv run python scripts/rechunk_knowledge.py            # dry run, writes nothing
    uv run python scripts/rechunk_knowledge.py --apply

Deliberately narrower than re-seeding. A reseed deletes the whole collection
and rebuilds it; this replaces one over-sized document at a time, leaving every
correctly sized passage untouched. Replacements are inserted *before* the
original is removed, so an interrupted run leaves duplicates — which retrieval
tolerates — rather than a hole.

`AICustomRule` lives in its own collection and is not touched either way.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.mongodb import connect_to_mongo  # noqa: E402
from app.models.ai_astrologer import AIKnowledgeDoc  # noqa: E402
from app.services.ai import retrieval  # noqa: E402
from app.services.ai.knowledge_service import _chunk_text  # noqa: E402

#: Anything larger than this was never split properly. Comfortably above the
#: target chunk size, so a passage that merely ran a little long is left alone.
OVERSIZE_LIMIT = 2_000

#: What the seeder asks for, and what the pieces are rebuilt to.
CHUNK_SIZE = 800
OVERLAP = 150


async def main(apply: bool) -> int:
    await connect_to_mongo()

    all_docs = await AIKnowledgeDoc.find_all().to_list()
    oversized = [d for d in all_docs if len(d.content) > OVERSIZE_LIMIT]

    if not oversized:
        print(f"{len(all_docs)} passages, none over {OVERSIZE_LIMIT:,} characters. Nothing to do.")
        return 0

    produced = sum(len(_chunk_text(d.content, CHUNK_SIZE, OVERLAP)) for d in oversized)
    held = sum(len(d.content) for d in oversized)
    print(f"passages in total     : {len(all_docs)}")
    print(f"over {OVERSIZE_LIMIT:,} characters : {len(oversized)}")
    print(f"characters they hold  : {held:,}")
    print(f"they would become     : {produced} passages")
    print(f"largest right now     : {max(len(d.content) for d in oversized):,} characters")

    if not apply:
        print("\nDry run. Nothing was written. Re-run with --apply to rewrite them.")
        return 0

    print()
    replaced = 0
    for doc in oversized:
        pieces = _chunk_text(doc.content, CHUNK_SIZE, OVERLAP)
        if not pieces:
            continue
        total = len(pieces)
        await AIKnowledgeDoc.insert_many(
            [
                AIKnowledgeDoc(
                    title=f"{doc.title} [{i + 1}/{total}]" if total > 1 else doc.title,
                    category=doc.category,
                    content=piece,
                    tags=doc.tags,
                    source_file=doc.source_file,
                    is_active=doc.is_active,
                )
                for i, piece in enumerate(pieces)
            ]
        )
        await doc.delete()
        replaced += 1
        print(f"  {replaced:>3}/{len(oversized)}  {doc.title[:44]:46} {len(doc.content):>9,} -> {total}")

    retrieval.clear_index_cache()

    after = await AIKnowledgeDoc.find_all().to_list()
    sizes = sorted((len(d.content) for d in after), reverse=True)
    print(f"\npassages now : {len(after)}")
    print(f"largest      : {sizes[0]:,}")
    print(f"median       : {sizes[len(sizes) // 2]:,}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write the changes")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.apply)))
