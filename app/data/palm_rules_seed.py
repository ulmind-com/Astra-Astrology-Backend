"""Palm rules, taken from the client's own palmistry documents.

PROVENANCE
----------
Every rule below cites the file it came from, under
`Resource Documents/Plam Reading/`:

  [FT]  Fingers in general and Thumb (1).docx   - finger and thumb proportions
  [JF]  Jupiter finger.docx                     - the index finger in detail
  [HL]  Heart line.docx                         - where the heart line terminates
  [EL]  Earth line.docx                         - the life line's reach
  [NP]  Nature through palm.docx                - composite temperament rules
  [ML]  Mercury line.docx, Health palmistry.docx

The client's documents use an elemental naming for the creases - Earth for the
life line, Water for the heart, Air for the head, Fire for the fate - and that
naming is carried into the labels so an astrologer checking the output against
the source sees the same words.

WORDING
-------
Meanings are written here in our own words from the rules those documents state.
The client's palmistry folder contains material carrying other people's branding
(see open question 13 in RESOURCES-MASTER.md), and the standing decision on this
project is to take the rule and never the wording.

WHAT IS DELIBERATELY ABSENT
---------------------------
A large part of the client's palm corpus - all of `Loops.docx` and much of
`Nature through palm.docx` - depends on fingerprint patterns, skin texture and
mount height. None of those can be read from a photograph of a whole hand. Rather
than approximate them, those rules are carried with a `requires` that can never be
satisfied from a photo, so the system lists them as not assessable and says why.
That is what `Requirement` and `UNAVAILABLE_REASONS` in the model are for.
"""

from __future__ import annotations

from typing import Any

from app.models.palm_reading import PalmFeature, Requirement

GEOMETRY = [Requirement.GEOMETRY.value]

PALM_RULES_SEED: list[dict[str, Any]] = [
    # ======================================================================
    # Hand type - the client's central classification [FT], [NP]
    # ======================================================================
    {
        "feature": PalmFeature.HAND_TYPE.value, "option": "earth", "label": "Earth hand",
        "conditions": [{"metric": "hand_type", "equals": "Earth"}], "requires": GEOMETRY,
        "area": "Temperament", "source": "Fingers in general and Thumb; Nature through palm",
        "priority": 10,
        "meaning": (
            "A square palm with shorter fingers. The client's material reads this hand as "
            "practical and grounded: sociable, assertive, confident, hard working and honest, "
            "with a stubborn streak and a liking for what can be touched and tested. Such hands "
            "are described as holding a certain rigidity, slow to act on impulse."
        ),
    },
    {
        "feature": PalmFeature.HAND_TYPE.value, "option": "air", "label": "Air hand",
        "conditions": [{"metric": "hand_type", "equals": "Air"}], "requires": GEOMETRY,
        "area": "Temperament", "source": "Nature through palm", "priority": 10,
        "meaning": (
            "A square palm with longer fingers. Read as the thinking hand: quick with language, "
            "diplomatic, drawn to reasoning and to explaining. The client's notes link this hand "
            "to language skill and to an ascetic turn of mind when the fingers are knotty."
        ),
    },
    {
        "feature": PalmFeature.HAND_TYPE.value, "option": "fire", "label": "Fire hand",
        "conditions": [{"metric": "hand_type", "equals": "Fire"}], "requires": GEOMETRY,
        "area": "Temperament", "source": "Nature through palm", "priority": 10,
        "meaning": (
            "A longer palm with shorter fingers. The client's notes tie this hand to restlessness "
            "and drive: ambition, a strong thumb, decisiveness, and a tendency to act before "
            "deliberating. Energy arrives in bursts rather than evenly."
        ),
    },
    {
        "feature": PalmFeature.HAND_TYPE.value, "option": "water", "label": "Water hand",
        "conditions": [{"metric": "hand_type", "equals": "Water"}], "requires": GEOMETRY,
        "area": "Temperament", "source": "Nature through palm", "priority": 10,
        "meaning": (
            "A longer palm with longer fingers. Read as the feeling hand: intuitive, receptive "
            "and diplomatic, attentive to what is unsaid. The client's notes associate it with "
            "caring work and with a susceptibility to taking on other people's moods."
        ),
    },

    # ======================================================================
    # Fingers [FT]
    # ======================================================================
    {
        "feature": PalmFeature.FINGERS.value, "option": "long_fingers", "label": "Long fingers",
        "conditions": [{"metric": "finger_palm_ratio", "min": 1.0}], "requires": GEOMETRY,
        "area": "Thinking", "source": "Fingers in general and Thumb", "priority": 5,
        "meaning": (
            "Long fingers are read as investigative. Such a person does not take information at "
            "first hand, preferring to check it, and so responds more slowly - the client's note "
            "is that they arrive late almost everywhere."
        ),
    },
    {
        "feature": PalmFeature.FINGERS.value, "option": "short_fingers", "label": "Short fingers",
        "conditions": [{"metric": "finger_palm_ratio", "max": 0.90}], "requires": GEOMETRY,
        "area": "Thinking", "source": "Fingers in general and Thumb", "priority": 5,
        "meaning": (
            "Short fingers are read as taking information at first hand and acting on it. Quick "
            "to respond and typically first to arrive, with less patience for checking detail."
        ),
    },
    {
        "feature": PalmFeature.FINGERS.value, "option": "balanced_fingers",
        "label": "Balanced finger length", "requires": GEOMETRY, "is_default": True,
        "area": "Thinking", "source": "Fingers in general and Thumb",
        "meaning": (
            "Finger length sits between the long and short cases, which the client's material "
            "reads as a balance between checking a thing and acting on it."
        ),
    },
    {
        "feature": PalmFeature.FINGERS.value, "option": "spread_fingers", "label": "Spread fingers",
        "conditions": [{"metric": "finger_spread", "min": 11.0}], "requires": GEOMETRY,
        "area": "Disposition", "source": "Fingers in general and Thumb", "priority": 6,
        "meaning": (
            "Fingers held well apart are read as boldness - the client's phrasing is that such a "
            "person is afraid of nothing, open and unguarded in dealings with others."
        ),
    },
    {
        "feature": PalmFeature.FINGERS.value, "option": "closed_fingers",
        "label": "Fingers held close", "conditions": [{"metric": "finger_spread", "max": 5.0}],
        "requires": GEOMETRY, "area": "Disposition",
        "source": "Fingers in general and Thumb", "priority": 6,
        "meaning": (
            "Fingers held close together are read as caution and inhibition - sankoch - a habit "
            "of holding back rather than committing."
        ),
    },
    {
        "feature": PalmFeature.FINGERS.value, "option": "lean_to_thumb",
        "label": "Fingers leaning towards the thumb",
        "conditions": [{"metric": "finger_lean_to_thumb", "min": 0.12}], "requires": GEOMETRY,
        "area": "Relationships", "source": "Fingers in general and Thumb", "priority": 7,
        "meaning": (
            "Fingers inclining towards the thumb are read as a leaning on others - for a life "
            "role, for a career, for needs generally. The client's note describes such people as "
            "carers and partners of prominent people."
        ),
    },
    {
        "feature": PalmFeature.FINGERS.value, "option": "lean_from_thumb",
        "label": "Fingers leaning away from the thumb",
        "conditions": [{"metric": "finger_lean_to_thumb", "max": -0.12}], "requires": GEOMETRY,
        "area": "Relationships", "source": "Fingers in general and Thumb", "priority": 7,
        "meaning": (
            "Fingers inclining away from the thumb are read as withdrawal - a pulling back from "
            "the demands of the world rather than a leaning into them."
        ),
    },
    {
        "feature": PalmFeature.FINGERS.value, "option": "thick_fingers", "label": "Thick fingers",
        "conditions": [{"metric": "finger_thickness", "min": 0.30}], "requires": GEOMETRY,
        "area": "Work", "source": "Fingers in general and Thumb", "priority": 4,
        "meaning": (
            "Thicker fingers are read as the field-work hand: tangible, earthy, drawn to what can "
            "be handled rather than to what is held in the head."
        ),
    },
    {
        "feature": PalmFeature.FINGERS.value, "option": "thin_fingers", "label": "Slender fingers",
        "conditions": [{"metric": "finger_thickness", "max": 0.22}], "requires": GEOMETRY,
        "area": "Work", "source": "Fingers in general and Thumb", "priority": 4,
        "meaning": (
            "Slender fingers are read as the office hand: connected to the internal world, "
            "philosophical, more at ease with ideas than with materials."
        ),
    },

    # ======================================================================
    # Thumb [FT]
    # ======================================================================
    {
        "feature": PalmFeature.THUMB.value, "option": "long_thumb", "label": "Long thumb",
        "conditions": [{"metric": "thumb_length_ratio", "min": 1.15}], "requires": GEOMETRY,
        "area": "Will", "source": "Fingers in general and Thumb", "priority": 8,
        "meaning": (
            "The client's material treats the thumb as the launching pad - will power, logic and "
            "motivation together. A long thumb is the leader's thumb: without fear, and inclined "
            "to find its own way out of a difficulty rather than wait for one."
        ),
    },
    {
        "feature": PalmFeature.THUMB.value, "option": "medium_thumb", "label": "Medium thumb",
        "conditions": [{"metric": "thumb_length_ratio", "min": 1.0, "max": 1.15}],
        "requires": GEOMETRY, "area": "Will",
        "source": "Fingers in general and Thumb", "priority": 7,
        "meaning": (
            "A thumb of middling length is read as the executive's thumb: able to carry a thing "
            "through without needing to originate it."
        ),
    },
    {
        "feature": PalmFeature.THUMB.value, "option": "small_thumb", "label": "Short thumb",
        "conditions": [{"metric": "thumb_length_ratio", "max": 1.0}], "requires": GEOMETRY,
        "area": "Will", "source": "Fingers in general and Thumb", "priority": 8,
        "meaning": (
            "A short thumb is read as the follower's thumb. The client's note is specific: such a "
            "person begins with great energy but struggles once competition arrives, and finds "
            "security in following someone else - which can put the wrong path in front of them."
        ),
    },
    {
        "feature": PalmFeature.THUMB.value, "option": "will_over_logic",
        "label": "Upper thumb flange dominant",
        "conditions": [{"metric": "thumb_flange_ratio", "min": 1.25}], "requires": GEOMETRY,
        "area": "Will", "source": "Fingers in general and Thumb", "priority": 5,
        "meaning": (
            "The client reads the upper flange as will and the lower as reasoning. A dominant "
            "upper flange puts resolve ahead of deliberation: decisions are made and then "
            "justified rather than the other way round."
        ),
    },
    {
        "feature": PalmFeature.THUMB.value, "option": "logic_over_will",
        "label": "Lower thumb flange dominant",
        "conditions": [{"metric": "thumb_flange_ratio", "max": 0.95}], "requires": GEOMETRY,
        "area": "Will", "source": "Fingers in general and Thumb", "priority": 5,
        "meaning": (
            "A dominant lower flange puts reasoning ahead of resolve. The client's caution is "
            "that too much of it confuses rather than clarifies - so many reasons are produced "
            "that no conclusion is reached."
        ),
    },
    {
        "feature": PalmFeature.THUMB.value, "option": "wide_thumb_gap",
        "label": "Wide opening between thumb and index",
        "conditions": [{"metric": "thumb_index_angle", "min": 48.0}], "requires": GEOMETRY,
        "area": "Disposition", "source": "Fingers in general and Thumb", "priority": 6,
        "meaning": (
            "A wide gap between thumb and index is read as outspoken and generous, with a "
            "carelessness that comes along with the openness."
        ),
    },
    {
        "feature": PalmFeature.THUMB.value, "option": "narrow_thumb_gap",
        "label": "Narrow opening between thumb and index",
        "conditions": [{"metric": "thumb_index_angle", "max": 30.0}], "requires": GEOMETRY,
        "area": "Disposition", "source": "Fingers in general and Thumb", "priority": 6,
        "meaning": (
            "A narrow gap is read as speaking less and giving less away - careful rather than "
            "careless, and harder to read from the outside."
        ),
    },

    # ======================================================================
    # Jupiter finger [JF]
    # ======================================================================
    {
        "feature": PalmFeature.JUPITER_FINGER.value, "option": "long_jupiter",
        "label": "Long Jupiter finger",
        "conditions": [{"metric": "index_ring_ratio", "min": 1.0}], "requires": GEOMETRY,
        "area": "Authority", "source": "Jupiter finger", "priority": 8,
        "meaning": (
            "An index finger longer than the ring finger is read as working hard towards one's "
            "own objectives without compromising on values or standards. Such a person knows how "
            "to exercise personal authority and takes calculated rather than reckless risks."
        ),
    },
    {
        "feature": PalmFeature.JUPITER_FINGER.value, "option": "short_jupiter",
        "label": "Short Jupiter finger",
        "conditions": [{"metric": "index_ring_ratio", "max": 0.96}], "requires": GEOMETRY,
        "area": "Authority", "source": "Jupiter finger", "priority": 8,
        "meaning": (
            "An index finger shorter than the ring finger means the Sun finger leads. The "
            "client's reading is of a higher appetite for risk and more competitiveness, with "
            "self-esteem more readily compromised in pursuit of a target."
        ),
    },
    {
        "feature": PalmFeature.JUPITER_FINGER.value, "option": "balanced_jupiter",
        "label": "Balanced Jupiter finger",
        "conditions": [{"metric": "index_ring_ratio", "min": 0.96, "max": 1.0}],
        "requires": GEOMETRY, "area": "Authority", "source": "Jupiter finger", "priority": 7,
        "meaning": (
            "An index finger matching the ring finger is read as a balanced personality: "
            "accommodating, aware of one's own feelings and other people's, neither dominating "
            "nor self-effacing."
        ),
    },
    {
        "feature": PalmFeature.JUPITER_FINGER.value, "option": "jupiter_bends_thumb",
        "label": "Jupiter finger leaning towards the thumb",
        "conditions": [{"metric": "jupiter_bend", "min": 12.0}], "requires": GEOMETRY,
        "area": "Authority", "source": "Jupiter finger", "priority": 6,
        "meaning": (
            "An index finger inclining towards the thumb is read as a built-in desire to lead, "
            "with real confidence in one's own authority. The client's caution attached to it is "
            "a tendency to overreach, and a need to watch the social responsibility that comes "
            "with the authority."
        ),
    },

    # ======================================================================
    # Phalanges [JF], [FT]
    # ======================================================================
    {
        "feature": PalmFeature.PHALANGES.value, "option": "first_dominant",
        "label": "Top phalanges dominant",
        "conditions": [{"metric": "index_phalange_first", "min": 0.33}], "requires": GEOMETRY,
        "area": "Orientation", "source": "Fingers in general and Thumb; Jupiter finger",
        "priority": 5,
        "meaning": (
            "The client's material assigns the top phalange to the spiritual and philosophical: "
            "intellect, inherited disposition, life philosophy and ideas. A dominant top "
            "phalange puts those concerns ahead of the practical."
        ),
    },
    {
        "feature": PalmFeature.PHALANGES.value, "option": "second_dominant",
        "label": "Middle phalanges dominant",
        "conditions": [{"metric": "index_phalange_second", "min": 0.36}], "requires": GEOMETRY,
        "area": "Orientation", "source": "Fingers in general and Thumb; Jupiter finger",
        "priority": 5,
        "meaning": (
            "The middle phalange is assigned to processing and execution - administering, "
            "organising, turning an idea into a sequence of steps. Dominant here, that is where "
            "the person's strength lies."
        ),
    },
    {
        "feature": PalmFeature.PHALANGES.value, "option": "third_dominant",
        "label": "Base phalanges dominant",
        "conditions": [{"metric": "index_phalange_third", "min": 0.42}], "requires": GEOMETRY,
        "area": "Orientation", "source": "Fingers in general and Thumb; Jupiter finger",
        "priority": 5,
        "meaning": (
            "The base phalange is assigned to the physical and material: food, comfort, "
            "possessions, what can be held. A thick, dominant base phalange is read as those "
            "appetites leading."
        ),
    },

    # ======================================================================
    # Heart line - the client's termination rules [HL]
    # ======================================================================
    {
        "feature": PalmFeature.HEART_LINE.value, "option": "ends_top_jupiter",
        "label": "Caring heart line",
        "conditions": [{"metric": "heart_line.termination_zone", "contains": "upper Jupiter"}],
        "requires": [Requirement.GEOMETRY.value, Requirement.HEART_LINE.value],
        "area": "Relationships", "source": "Heart line", "priority": 10,
        "meaning": (
            "A heart line running to the top of the Jupiter mount is the caring line. The "
            "client's reading is unconditional care, family first, no expectation in return and "
            "no complaint when it is not returned - with a difficulty in saying no, which can "
            "become dependence where the rest of the hand supports it."
        ),
    },
    {
        "feature": PalmFeature.HEART_LINE.value, "option": "ends_lower_jupiter",
        "label": "Idealistic heart line",
        "conditions": [{"metric": "heart_line.termination_zone", "contains": "lower Jupiter"}],
        "requires": [Requirement.GEOMETRY.value, Requirement.HEART_LINE.value],
        "area": "Relationships", "source": "Heart line", "priority": 10,
        "meaning": (
            "A heart line ending on the lower Jupiter mount is the idealistic line: needs love "
            "and gives it, and will say so when it is not returned. Expressive, persuasive, "
            "willing to admit a mistake, and drawn to art and craft."
        ),
    },
    {
        "feature": PalmFeature.HEART_LINE.value, "option": "ends_below_saturn",
        "label": "Independent heart line",
        "conditions": [{"metric": "heart_line.termination_zone", "contains": "Saturn"}],
        "requires": [Requirement.GEOMETRY.value, Requirement.HEART_LINE.value],
        "area": "Relationships", "source": "Heart line", "priority": 10,
        "meaning": (
            "A straight heart line stopping below the Saturn finger is the hermit or independent "
            "line. Not expressive in love and not hesitant either; dislikes working under anyone "
            "or to another's design, thinks deeply and independently, and is content alone."
        ),
    },
    {
        "feature": PalmFeature.HEART_LINE.value, "option": "heart_high", "label": "High heart line",
        "conditions": [{"metric": "heart_height", "max": 0.26}],
        "requires": [Requirement.GEOMETRY.value, Requirement.HEART_LINE.value],
        "area": "Emotion", "source": "Heart line", "priority": 6,
        "meaning": (
            "A heart line set close to the fingers is read as feeling overpowering reasoning: "
            "the emotional response arrives first and the argument for it afterwards."
        ),
    },
    {
        "feature": PalmFeature.HEART_LINE.value, "option": "heart_low", "label": "Low heart line",
        "conditions": [{"metric": "heart_height", "min": 0.36}],
        "requires": [Requirement.GEOMETRY.value, Requirement.HEART_LINE.value],
        "area": "Emotion", "source": "Heart line", "priority": 6,
        "meaning": (
            "A low-set heart line reaches down into the reasoning zone, which the client reads as "
            "reason dominating emotion. Set very low it is read as coolness - detached, and "
            "weighing a matter before feeling it."
        ),
    },

    # ======================================================================
    # Relationship between heart and head lines [HL]
    # ======================================================================
    {
        "feature": PalmFeature.LINE_RELATIONSHIP.value, "option": "narrow_gap",
        "label": "Narrow gap between heart and head lines",
        "conditions": [{"metric": "heart_head_gap", "max": 0.10}],
        "requires": [Requirement.GEOMETRY.value, Requirement.HEART_LINE.value,
                     Requirement.HEAD_LINE.value],
        "area": "Disposition", "source": "Heart line", "priority": 8,
        "meaning": (
            "A small gap between the water and air lines is read as a narrower outlook: less "
            "open, slower to share what is known, and more careful with what is given away."
        ),
    },
    {
        "feature": PalmFeature.LINE_RELATIONSHIP.value, "option": "wide_gap",
        "label": "Wide gap between heart and head lines",
        "conditions": [{"metric": "heart_head_gap", "min": 0.18}],
        "requires": [Requirement.GEOMETRY.value, Requirement.HEART_LINE.value,
                     Requirement.HEAD_LINE.value],
        "area": "Disposition", "source": "Heart line", "priority": 8,
        "meaning": (
            "A wide gap is read as openness and generosity - willing to share what is known and "
            "to help without being asked. The client's notes also tie a clear gap here to "
            "independence of thought."
        ),
    },

    {
        "feature": PalmFeature.LINE_RELATIONSHIP.value, "option": "balanced_gap",
        "label": "Balanced gap between heart and head lines",
        "requires": [Requirement.GEOMETRY.value, Requirement.HEART_LINE.value,
                     Requirement.HEAD_LINE.value],
        "is_default": True, "area": "Disposition", "source": "Heart line",
        "meaning": (
            "The spacing between the water and air lines sits between the narrow and wide "
            "cases, which the client's material reads as feeling and reasoning holding each "
            "other in balance rather than one running ahead of the other."
        ),
    },

    # ======================================================================
    # Life line - the client's reach cases [EL]
    # ======================================================================
    {
        "feature": PalmFeature.LIFE_LINE.value, "option": "life_narrow",
        "label": "Close-set life line",
        "conditions": [{"metric": "life_reach", "max": 0.26}],
        "requires": [Requirement.GEOMETRY.value, Requirement.LIFE_LINE.value],
        "area": "Vitality", "source": "Earth line", "priority": 8,
        "meaning": (
            "A life line hugging the thumb without reaching across the palm is the client's "
            "first case. It is read as a life kept within a known compass - and, in their "
            "phrasing, as timidity and restraint rather than as any shortness of life."
        ),
    },
    {
        "feature": PalmFeature.LIFE_LINE.value, "option": "life_wide",
        "label": "Wide-sweeping life line",
        "conditions": [{"metric": "life_reach", "min": 0.40}],
        "requires": [Requirement.GEOMETRY.value, Requirement.LIFE_LINE.value],
        "area": "Vitality", "source": "Earth line", "priority": 8,
        "meaning": (
            "A life line sweeping well across the palm is read as expansion - travel to larger "
            "places and a life lived beyond where it began. The further the arc reaches, the "
            "further the client's material takes that expansion."
        ),
    },
    {
        "feature": PalmFeature.LIFE_LINE.value, "option": "life_clear",
        "label": "Deep, clear life line",
        "conditions": [{"metric": "life_line.contrast", "min": 4.0}],
        "requires": [Requirement.GEOMETRY.value, Requirement.LIFE_LINE.value],
        "area": "Vitality", "source": "Earth line", "priority": 6,
        "meaning": (
            "The earth line is the line of roots - family, place and tradition. Deep and clearly "
            "carved, the client reads it as good nourishment and vitality, a settled sense of "
            "place and steady internal stability."
        ),
    },
    {
        "feature": PalmFeature.LIFE_LINE.value, "option": "life_faint",
        "label": "Faint life line",
        "conditions": [{"metric": "life_line.contrast", "max": 2.4}],
        "requires": [Requirement.GEOMETRY.value, Requirement.LIFE_LINE.value],
        "area": "Vitality", "source": "Earth line", "priority": 6,
        "meaning": (
            "A faint or feeble earth line is read not as poor health but as a looser grip - "
            "irregular routine, uncertain energy, and a weaker sense of permanence. The client is "
            "explicit that it is fragility rather than illness."
        ),
    },

    # ======================================================================
    # Fate line [EL], [NP]
    # ======================================================================
    {
        "feature": PalmFeature.FATE_LINE.value, "option": "fate_strong",
        "label": "Clear fate line",
        "conditions": [{"metric": "fate_line.contrast", "min": 3.5}],
        "requires": [Requirement.GEOMETRY.value, Requirement.FATE_LINE.value],
        "area": "Work", "source": "Earth line; Nature through palm", "priority": 7,
        "meaning": (
            "A clearly marked fire line is read as a defined direction in work - a thread running "
            "through the working life rather than a series of unconnected turns."
        ),
    },
    {
        "feature": PalmFeature.FATE_LINE.value, "option": "fate_absent",
        "label": "No clear fate line", "requires": [Requirement.GEOMETRY.value],
        "conditions": [{"metric": "fate_line.found", "equals": "False"}],
        "area": "Work", "source": "Earth line", "priority": 7,
        "meaning": (
            "No distinct fire line was traced. This is common and is not read as a bad sign: the "
            "client's material associates its absence with a working life shaped by the person's "
            "own choices rather than by a single fixed track."
        ),
    },
]


def rule_count_by_feature() -> dict[str, int]:
    counts: dict[str, int] = {}
    for rule in PALM_RULES_SEED:
        counts[rule["feature"]] = counts.get(rule["feature"], 0) + 1
    return counts
