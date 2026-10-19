"""Re-derives the face-reading bands from measurements that have actually been seen.

The thresholds start life as guesses — no source gives a measurement, so
"broad" has to mean *broader than most faces*, and that cannot be known until
faces have been measured. This recomputes every band as a percentile of real
readings, which is the only honest definition of the word.

    uv run python -m scripts.recalibrate_face_rules            # show the proposal
    uv run python -m scripts.recalibrate_face_rules --apply    # write it

Nothing is written without `--apply`, and a rule an astrologer has marked
`reviewed` is never touched: a human judgement outranks a percentile.

With few readings stored it falls back to the bundled reference samples, and
says so. Those are three faces — enough to stop every band being wrong, not
enough to be a distribution. The numbers improve as the product is used.
"""

import asyncio
import statistics
import sys

from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.models.face_reading import FaceReading, FaceRule

# Measured with this exact pipeline from MediaPipe's own sample portraits.
# Used only until real readings exist.
REFERENCE = [
    dict(wh_ratio=0.963, jaw_cheek=0.801, brow_cheek=0.731, forehead_h=0.201,
         eye_open=0.189, eye_size=0.1844, eye_gap=1.342, eye_tilt=0.0289, eye_asym=0.0671,
         brow_thick=0.155, brow_arch=0.195, brow_gap=0.861, brow_len=1.635,
         nose_w=0.319, nose_len=0.276, nostril=0.56, nose_dev=0.0221,
         lip_thick=0.302, mouth_w=0.5299, lip_corner=0.0886, lip_asym=0.1048,
         chin_h=0.218, cheek_full=0.917),
    dict(wh_ratio=1.245, jaw_cheek=0.818, brow_cheek=0.712, forehead_h=0.219,
         eye_open=0.263, eye_size=0.2106, eye_gap=1.154, eye_tilt=0.0889, eye_asym=0.0957,
         brow_thick=0.119, brow_arch=0.193, brow_gap=0.898, brow_len=1.436,
         nose_w=0.268, nose_len=0.313, nostril=0.56, nose_dev=0.0970,
         lip_thick=0.170, mouth_w=0.4109, lip_corner=0.0563, lip_asym=0.3345,
         chin_h=0.201, cheek_full=0.915),
    dict(wh_ratio=0.990, jaw_cheek=0.805, brow_cheek=0.722, forehead_h=0.199,
         eye_open=0.209, eye_size=0.1826, eye_gap=1.322, eye_tilt=0.0161, eye_asym=0.0821,
         brow_thick=0.160, brow_arch=0.188, brow_gap=0.882, brow_len=1.632,
         nose_w=0.302, nose_len=0.278, nostril=0.56, nose_dev=0.0092,
         lip_thick=0.312, mouth_w=0.5165, lip_corner=0.0884, lip_asym=0.0625,
         chin_h=0.215, cheek_full=0.905),
]

# Which end of the range each option sits at. "high" means the option applies
# above the upper cut; "low" below the lower cut.
SIDE = {
    ("face_shape", "round"): ("wh_ratio", "high"),
    ("face_shape", "square"): ("wh_ratio", "high"),
    ("face_shape", "long"): ("wh_ratio", "low"),
    ("face_shape", "heart"): ("brow_cheek", "high"),
    ("face_shape", "diamond"): ("brow_cheek", "low"),
    ("face_shape", "triangular"): ("jaw_cheek", "high"),
    ("forehead", "high"): ("forehead_h", "high"),
    ("forehead", "low"): ("forehead_h", "low"),
    ("forehead", "wide"): ("brow_cheek", "high"),
    ("forehead", "narrow"): ("brow_cheek", "low"),
    ("forehead", "broad_high"): ("forehead_h", "high"),
    ("eyebrows", "thick"): ("brow_thick", "high"),
    ("eyebrows", "thin"): ("brow_thick", "low"),
    ("eyebrows", "arched"): ("brow_arch", "high"),
    ("eyebrows", "straight"): ("brow_arch", "low"),
    ("eyebrows", "joined"): ("brow_gap", "low"),
    ("eyebrows", "long"): ("brow_len", "high"),
    ("eyebrows", "short"): ("brow_len", "low"),
    ("eyes", "large"): ("eye_open", "high"),
    ("eyes", "narrow"): ("eye_open", "low"),
    ("eyes", "close_set"): ("eye_gap", "low"),
    ("eyes", "wide_set"): ("eye_gap", "high"),
    ("eyes", "upturned"): ("eye_tilt", "high"),
    ("eyes", "downturned"): ("eye_tilt", "low"),
    ("eyes", "uneven"): ("eye_asym", "high"),
    ("nose", "broad"): ("nose_w", "high"),
    ("nose", "narrow"): ("nose_w", "low"),
    ("nose", "long"): ("nose_len", "high"),
    ("nose", "short"): ("nose_len", "low"),
    ("nose", "long_straight"): ("nose_len", "high"),
    ("nose", "large_nostrils"): ("nostril", "high"),
    ("nose", "small_nostrils"): ("nostril", "low"),
    ("nose", "deviated"): ("nose_dev", "high"),
    ("lips", "full"): ("lip_thick", "high"),
    ("lips", "thin"): ("lip_thick", "low"),
    ("lips", "upturned"): ("lip_corner", "high"),
    ("lips", "downturned"): ("lip_corner", "low"),
    ("lips", "uneven"): ("lip_asym", "high"),
    ("chin", "square"): ("jaw_cheek", "high"),
    ("chin", "pointed"): ("jaw_cheek", "low"),
    ("chin", "round"): ("chin_h", "high"),
    ("chin", "receding"): ("chin_h", "low"),
    ("cheeks", "full"): ("cheek_full", "high"),
    ("cheeks", "hollow"): ("cheek_full", "low"),
}

# A third of faces at each end, a third in the middle reading "balanced".
LOW_PCT, HIGH_PCT = 0.33, 0.67


def cut(values: list[float], fraction: float) -> float:
    """The value below which `fraction` of the sample falls."""
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 4)
    index = fraction * (len(ordered) - 1)
    low, high = int(index), min(int(index) + 1, len(ordered) - 1)
    value = ordered[low] + (ordered[high] - ordered[low]) * (index - low)
    return round(value, 4)


async def main() -> None:
    apply = "--apply" in sys.argv
    await connect_to_mongo()

    readings = await FaceReading.find_all().to_list()
    samples = [r.measurements for r in readings if r.measurements]
    source = f"{len(samples)} stored readings"
    if len(samples) < 30:
        samples = samples + REFERENCE
        source = (
            f"{len(readings)} stored readings + {len(REFERENCE)} reference faces "
            "— too few to be a distribution yet"
        )

    by_metric: dict[str, list[float]] = {}
    for sample in samples:
        for metric, value in sample.items():
            by_metric.setdefault(metric, []).append(float(value))

    print(f"Calibrating from {source}\n")

    rules = await FaceRule.find_all().to_list()
    changes, skipped = 0, 0

    for rule in rules:
        key = (rule.feature, rule.option)
        if key not in SIDE or rule.is_default:
            continue
        if rule.reviewed:
            skipped += 1
            continue

        metric, side = SIDE[key]
        values = by_metric.get(metric)
        if not values:
            continue

        bound = cut(values, HIGH_PCT if side == "high" else LOW_PCT)
        before = next(
            (c for c in rule.conditions if c.metric == metric), None
        )
        was = f"min={before.min} max={before.max}" if before else "—"

        for condition in rule.conditions:
            if condition.metric != metric:
                continue
            if side == "high":
                condition.min, condition.max = bound, None
            else:
                condition.min, condition.max = None, bound

        now = "min=" + str(bound) if side == "high" else "max=" + str(bound)
        if was != now:
            print(f"  {rule.feature:<11} {rule.option:<15} {metric:<12} {was}  ->  {now}")
            changes += 1
        if apply:
            await rule.save()

    print(f"\n{changes} band(s) {'updated' if apply else 'would change'};"
          f" {skipped} left alone (reviewed by an astrologer)")
    if not apply:
        print("Nothing was written. Re-run with --apply to keep these.")

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
