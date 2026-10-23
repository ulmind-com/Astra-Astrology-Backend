"""Palm rules, taken directly from the client's own palmistry documents.

PROVENANCE
----------
Every rule below cites the file it came from under `Resource Documents/Plam Reading/`:
  [FT]  Fingers in general and Thumb (1).docx   - finger & thumb proportions, spread, lean, flanges
  [JF]  Jupiter finger.docx                     - index finger, leadership, ethics, authority
  [HL]  Heart line.docx                         - termination zones, curvature, emotional depth
  [EL]  Earth line.docx                         - life line reach, vitality, roots, expansion
  [NP]  Nature through palm.docx                - composite temperament, hand types, intellect
  [ML]  Mercury line.docx                       - pinky finger, commerce, eloquence, nervous system
  [HP]  Health palmistry.docx                   - health indicators, skin vitality, constitution
  [RS]  Palmistry_Notes_Astro_Rahul_Sharma.docx - Vedic study guide, Mounts, major/secondary lines
"""

from __future__ import annotations

from typing import Any

from app.models.palm_reading import PalmFeature, Requirement

GEOMETRY = [Requirement.GEOMETRY.value]
HEART = [Requirement.GEOMETRY.value, Requirement.HEART_LINE.value]
HEAD = [Requirement.GEOMETRY.value, Requirement.HEAD_LINE.value]
LIFE = [Requirement.GEOMETRY.value, Requirement.LIFE_LINE.value]
FATE = [Requirement.GEOMETRY.value, Requirement.FATE_LINE.value]
HEART_HEAD = [Requirement.GEOMETRY.value, Requirement.HEART_LINE.value, Requirement.HEAD_LINE.value]

PALM_RULES_SEED: list[dict[str, Any]] = [
    # ======================================================================
    # 1. Hand type - Elemental constitution [FT], [NP], [RS]
    # ======================================================================
    {
        "feature": PalmFeature.HAND_TYPE.value, "option": "earth", "label": "Earth Hand (Practical & Grounded)",
        "conditions": [{"metric": "hand_type", "equals": "Earth"}], "requires": GEOMETRY,
        "area": "Temperament", "source": "Fingers in general and Thumb; Nature through palm",
        "priority": 10,
        "meaning": (
            "A square palm with shorter fingers. The client's material reads this hand as practical, "
            "reliable, and grounded: sociable, assertive, honest, with a strong work ethic and an affinity "
            "for what can be tested and built in the physical world. Moves methodically and resists impulsive trends."
        ),
    },
    {
        "feature": PalmFeature.HAND_TYPE.value, "option": "air", "label": "Air Hand (Intellectual & Communicative)",
        "conditions": [{"metric": "hand_type", "equals": "Air"}], "requires": GEOMETRY,
        "area": "Temperament", "source": "Nature through palm; Palmistry Notes Astro Rahul Sharma",
        "priority": 10,
        "meaning": (
            "A square palm with longer fingers. Read as the thinking hand: swift with concepts and language, "
            "analytical, diplomatic, and drawn to reasoning, research, and explaining. Possesses natural curiosity "
            "and thrives in stimulating intellectual environments."
        ),
    },
    {
        "feature": PalmFeature.HAND_TYPE.value, "option": "fire", "label": "Fire Hand (Dynamic & Passionate)",
        "conditions": [{"metric": "hand_type", "equals": "Fire"}], "requires": GEOMETRY,
        "area": "Temperament", "source": "Nature through palm; Palmistry Notes Astro Rahul Sharma",
        "priority": 10,
        "meaning": (
            "An elongated palm with shorter fingers. The client's notes link this hand to charisma, restlessness, "
            "and drive: natural ambition, strong willpower, decisive instincts, and quick action. Energy arrives "
            "in intense creative bursts that motivate others."
        ),
    },
    {
        "feature": PalmFeature.HAND_TYPE.value, "option": "water", "label": "Water Hand (Intuitive & Receptive)",
        "conditions": [{"metric": "hand_type", "equals": "Water"}], "requires": GEOMETRY,
        "area": "Temperament", "source": "Nature through palm; Palmistry Notes Astro Rahul Sharma",
        "priority": 10,
        "meaning": (
            "An elongated palm with long, slender fingers. Read as the intuitive hand: receptive, emotionally "
            "sensitive, diplomatic, and perceptive to subtleties that go unsaid. Gifted in creative, healing, "
            "counseling, and artistic vocations."
        ),
    },

    # ======================================================================
    # 2. Palm Shape - Foundation & Proportions [FT], [RS]
    # ======================================================================
    {
        "feature": PalmFeature.PALM_SHAPE.value, "option": "square_palm",
        "label": "Square Palm Foundation",
        "conditions": [{"metric": "is_square_palm", "min": 0.5}], "requires": GEOMETRY,
        "area": "Disposition", "source": "Fingers in general and Thumb", "priority": 6,
        "meaning": (
            "The palm width is nearly equal to its length, establishing a square foundation. Palmistry notes read "
            "this as strong domestic stability, practical common sense, perseverance, and a preference for order."
        ),
    },
    {
        "feature": PalmFeature.PALM_SHAPE.value, "option": "elongated_palm",
        "label": "Elongated Palm Foundation",
        "conditions": [{"metric": "is_square_palm", "max": 0.5}], "requires": GEOMETRY,
        "area": "Disposition", "source": "Fingers in general and Thumb", "priority": 6,
        "meaning": (
            "The palm is visibly longer than wide. This elongated framework signifies rich imagination, philosophical "
            "sensitivity, high emotional resonance, and an instinctive approach to solving problems."
        ),
    },
    {
        "feature": PalmFeature.PALM_SHAPE.value, "option": "balanced_palm",
        "label": "Harmonious Palm Proportion", "requires": GEOMETRY, "is_default": True,
        "area": "Disposition", "source": "Fingers in general and Thumb",
        "meaning": (
            "Palm proportions sit in harmonious equilibrium between square and rectangular dimensions, uniting practical "
            "industry with intuitive adaptability."
        ),
    },

    # ======================================================================
    # 3. Finger Length - Mental Processing Pace [FT]
    # ======================================================================
    {
        "feature": PalmFeature.FINGER_LENGTH.value, "option": "long_fingers",
        "label": "Long Fingers (Investigative & Thorough)",
        "conditions": [{"metric": "finger_palm_ratio", "min": 0.98}], "requires": GEOMETRY,
        "area": "Thinking", "source": "Fingers in general and Thumb", "priority": 7,
        "meaning": (
            "Fingers exceeding palm proportions denote an investigative, analytical turn of mind. The client's notes "
            "state such a person examines information thoroughly before accepting it, values precision, and avoids hasty conclusions."
        ),
    },
    {
        "feature": PalmFeature.FINGER_LENGTH.value, "option": "short_fingers",
        "label": "Short Fingers (Quick & Decisive)",
        "conditions": [{"metric": "finger_palm_ratio", "max": 0.90}], "requires": GEOMETRY,
        "area": "Thinking", "source": "Fingers in general and Thumb", "priority": 7,
        "meaning": (
            "Fingers shorter than palm proportions signify rapid mental processing and executive action. Quick to grasp the "
            "big picture, prompt to act, and prefers practical momentum over protracted deliberations."
        ),
    },
    {
        "feature": PalmFeature.FINGER_LENGTH.value, "option": "balanced_finger_length",
        "label": "Balanced Finger Proportion", "requires": GEOMETRY, "is_default": True,
        "area": "Thinking", "source": "Fingers in general and Thumb",
        "meaning": (
            "Finger length sits in balanced proportion with palm length, representing an ideal blend of thoughtful analysis "
            "and timely executive execution."
        ),
    },

    # ======================================================================
    # 4. Finger Dynamics - Temperament & Stance [FT]
    # ======================================================================
    {
        "feature": PalmFeature.FINGER_DYNAMICS.value, "option": "spread_fingers",
        "label": "Spread Fingers (Bold & Uninhibited)",
        "conditions": [{"metric": "finger_spread", "min": 14.0}], "requires": GEOMETRY,
        "area": "Disposition", "source": "Fingers in general and Thumb", "priority": 8,
        "meaning": (
            "Fingers naturally held well apart denote independence, bold candor, and openness. The client's notes observe "
            "that such individuals are afraid of nothing, speak their truth freely, and approach life without artificial defenses."
        ),
    },
    {
        "feature": PalmFeature.FINGER_DYNAMICS.value, "option": "closed_fingers",
        "label": "Held Close (Cautious & Discerning)",
        "conditions": [{"metric": "finger_spread", "max": 7.0}], "requires": GEOMETRY,
        "area": "Disposition", "source": "Fingers in general and Thumb", "priority": 8,
        "meaning": (
            "Fingers held close together reflect prudence, modesty, and emotional reserve (sankoch). The native guards their "
            "inner feelings carefully, exercises natural thrift, and deliberates before committing."
        ),
    },
    {
        "feature": PalmFeature.FINGER_DYNAMICS.value, "option": "lean_to_thumb",
        "label": "Fingers Leaning Towards Thumb (Collaborative)",
        "conditions": [{"metric": "finger_lean_to_thumb", "min": 0.08}], "requires": GEOMETRY,
        "area": "Relationships", "source": "Fingers in general and Thumb", "priority": 6,
        "meaning": (
            "Fingers inclining towards the thumb indicate devotion to family, cooperative loyalty, and a collaborative mindset. "
            "The client's notes link this to supportive partners, counselors, and those who thrive in strong alliances."
        ),
    },
    {
        "feature": PalmFeature.FINGER_DYNAMICS.value, "option": "lean_from_thumb",
        "label": "Fingers Leaning Away (Independent & Autonomous)",
        "conditions": [{"metric": "finger_lean_to_thumb", "max": -0.08}], "requires": GEOMETRY,
        "area": "Relationships", "source": "Fingers in general and Thumb", "priority": 6,
        "meaning": (
            "Fingers leaning towards the outer palm signify self-reliance, individuality, and a reflective detachment from "
            "societal pressures. They find contentment in their own space and self-guided pursuits."
        ),
    },
    {
        "feature": PalmFeature.FINGER_DYNAMICS.value, "option": "thick_fingers",
        "label": "Substantial Fingers (Field-Work & Execution)",
        "conditions": [{"metric": "finger_thickness", "min": 0.28}], "requires": GEOMETRY,
        "area": "Work", "source": "Fingers in general and Thumb", "priority": 5,
        "meaning": (
            "Sturdy, well-built fingers denote an earthy, practical disposition suited for tangible accomplishment, real-world "
            "construction, commerce, and managing physical resources."
        ),
    },
    {
        "feature": PalmFeature.FINGER_DYNAMICS.value, "option": "slender_fingers",
        "label": "Slender Fingers (Intellectual & Refined)",
        "conditions": [{"metric": "finger_thickness", "max": 0.22}], "requires": GEOMETRY,
        "area": "Work", "source": "Fingers in general and Thumb", "priority": 5,
        "meaning": (
            "Slender, graceful fingers signify affinity for conceptual, aesthetic, or advisory work. Deeply intuitive and "
            "more energized by ideas, strategy, and aesthetics than by raw physical labor."
        ),
    },
    {
        "feature": PalmFeature.FINGER_DYNAMICS.value, "option": "balanced_dynamics",
        "label": "Harmonious Finger Dynamics", "requires": GEOMETRY, "is_default": True,
        "area": "Disposition", "source": "Fingers in general and Thumb",
        "meaning": (
            "Finger posture is well-balanced, exhibiting healthy social warmth, moderate caution, and versatile communication."
        ),
    },

    # ======================================================================
    # 5. Thumb - Willpower, Logic & Direction [FT]
    # ======================================================================
    {
        "feature": PalmFeature.THUMB.value, "option": "long_thumb",
        "label": "Prominent Thumb (Leader's Will)",
        "conditions": [{"metric": "thumb_length_ratio", "min": 1.12}], "requires": GEOMETRY,
        "area": "Will", "source": "Fingers in general and Thumb", "priority": 9,
        "meaning": (
            "The client's notes treat the thumb as the primary engine of destiny. A long thumb is the leader's thumb: "
            "fearless, commanding, highly self-motivated, and capable of carving a path through any obstacle."
        ),
    },
    {
        "feature": PalmFeature.THUMB.value, "option": "short_thumb",
        "label": "Compact Thumb (Adaptive & Cooperative)",
        "conditions": [{"metric": "thumb_length_ratio", "max": 0.98}], "requires": GEOMETRY,
        "area": "Will", "source": "Fingers in general and Thumb", "priority": 9,
        "meaning": (
            "A shorter thumb denotes an adaptable, cooperative disposition that works well within established systems, "
            "valuing teamwork, empathy, and harmony over solitary confrontation."
        ),
    },
    {
        "feature": PalmFeature.THUMB.value, "option": "will_over_logic",
        "label": "Upper Flange Dominant (Decisive Resolve)",
        "conditions": [{"metric": "thumb_flange_ratio", "min": 1.20}], "requires": GEOMETRY,
        "area": "Will", "source": "Fingers in general and Thumb", "priority": 7,
        "meaning": (
            "Upper flange represents will and lower flange represents logic. A dominant upper flange gives resolute determination: "
            "instinctive conviction acts promptly, turning vision into concrete action without getting paralyzed by overthinking."
        ),
    },
    {
        "feature": PalmFeature.THUMB.value, "option": "logic_over_will",
        "label": "Lower Flange Dominant (Analytical Reason)",
        "conditions": [{"metric": "thumb_flange_ratio", "max": 0.95}], "requires": GEOMETRY,
        "area": "Will", "source": "Fingers in general and Thumb", "priority": 7,
        "meaning": (
            "A dominant lower flange puts analytical scrutiny ahead of hasty impulse. The native carefully assesses causes, "
            "weighs contingencies, and seeks solid rationale before committing energy."
        ),
    },
    {
        "feature": PalmFeature.THUMB.value, "option": "wide_thumb_gap",
        "label": "Wide Opening Angle (Generous & Outspoken)",
        "conditions": [{"metric": "thumb_index_angle", "min": 45.0}], "requires": GEOMETRY,
        "area": "Disposition", "source": "Fingers in general and Thumb", "priority": 6,
        "meaning": (
            "A wide opening between thumb and index finger reflects generosity of spirit, philanthropic inclinations, and "
            "candid, outspoken sincerity."
        ),
    },
    {
        "feature": PalmFeature.THUMB.value, "option": "narrow_thumb_gap",
        "label": "Narrow Opening Angle (Discreet & Prudent)",
        "conditions": [{"metric": "thumb_index_angle", "max": 32.0}], "requires": GEOMETRY,
        "area": "Disposition", "source": "Fingers in general and Thumb", "priority": 6,
        "meaning": (
            "A narrower opening angle reflects self-containment, confidentiality, careful resource management, and emotional discretion."
        ),
    },
    {
        "feature": PalmFeature.THUMB.value, "option": "medium_thumb",
        "label": "Balanced Executive Thumb", "requires": GEOMETRY, "is_default": True,
        "area": "Will", "source": "Fingers in general and Thumb",
        "meaning": (
            "Thumb length and flanges sit in harmonious balance, providing reliable executive capability, steady willpower, "
            "and sound practical judgment."
        ),
    },

    # ======================================================================
    # 6. Jupiter Finger - Authority, Ethics & Ambition [JF]
    # ======================================================================
    {
        "feature": PalmFeature.JUPITER_FINGER.value, "option": "long_jupiter",
        "label": "Long Jupiter Finger (Command & High Ethics)",
        "conditions": [{"metric": "index_ring_ratio", "min": 1.0}], "requires": GEOMETRY,
        "area": "Authority", "source": "Jupiter finger", "priority": 9,
        "meaning": (
            "Index finger exceeding the ring finger signifies natural authority, dignified self-respect, and strict adherence "
            "to ethical principles. Exercises leadership without compromising personal values."
        ),
    },
    {
        "feature": PalmFeature.JUPITER_FINGER.value, "option": "short_jupiter",
        "label": "Sun Finger Dominant (Charismatic Risk-Taker)",
        "conditions": [{"metric": "index_ring_ratio", "max": 0.96}], "requires": GEOMETRY,
        "area": "Authority", "source": "Jupiter finger", "priority": 9,
        "meaning": (
            "Ring finger longer than the index finger shows high commercial drive, charisma, competitive spirit, and an appetite "
            "for creative and financial risks. Thrives in high-stakes ventures."
        ),
    },
    {
        "feature": PalmFeature.JUPITER_FINGER.value, "option": "jupiter_bends_thumb",
        "label": "Jupiter Leaning to Thumb (Pioneering Drive)",
        "conditions": [{"metric": "jupiter_bend", "min": 10.0}], "requires": GEOMETRY,
        "area": "Authority", "source": "Jupiter finger", "priority": 7,
        "meaning": (
            "An index finger inclining towards the thumb indicates an innate urge to lead, initiate, and take direct control "
            "over one's destiny. Naturally commands respect and inspires followers."
        ),
    },
    {
        "feature": PalmFeature.JUPITER_FINGER.value, "option": "balanced_jupiter",
        "label": "Harmonious Jupiter Finger (Diplomatic Authority)", "requires": GEOMETRY,
        "is_default": True, "area": "Authority", "source": "Jupiter finger",
        "meaning": (
            "The index and ring fingers match evenly, reflecting a balanced personality: empathetic, accommodating, exercising "
            "quiet authority without arrogance, and earning broad social goodwill."
        ),
    },

    # ======================================================================
    # 7. Mercury Finger - Eloquence & Commerce [ML], [RS]
    # ======================================================================
    {
        "feature": PalmFeature.MERCURY_FINGER.value, "option": "long_mercury",
        "label": "Prominent Mercury Finger (Business Acumen & Eloquence)",
        "conditions": [{"metric": "mercury_reach_ratio", "min": 0.86}], "requires": GEOMETRY,
        "area": "Work", "source": "Mercury line; Palmistry Notes Astro Rahul Sharma", "priority": 8,
        "meaning": (
            "A well-extended pinky finger reaching past the top joint of the ring finger signifies sharp commercial intelligence, "
            "eloquent communication, quick wit, and persuasive capability in business and negotiation."
        ),
    },
    {
        "feature": PalmFeature.MERCURY_FINGER.value, "option": "expressive_mercury",
        "label": "Direct Mercury Finger (Sincere & Heartfelt)",
        "conditions": [{"metric": "mercury_reach_ratio", "max": 0.80}], "requires": GEOMETRY,
        "area": "Work", "source": "Mercury line", "priority": 8,
        "meaning": (
            "A shorter Mercury finger signifies emotional sincerity, straightforward honesty in communication, and a distaste "
            "for complicated corporate politics. Communicates from the heart."
        ),
    },
    {
        "feature": PalmFeature.MERCURY_FINGER.value, "option": "balanced_mercury",
        "label": "Balanced Mercury Proportion", "requires": GEOMETRY, "is_default": True,
        "area": "Work", "source": "Mercury line",
        "meaning": (
            "The Mercury finger sits in harmonious balance, supporting clear interpersonal communication and practical business discernment."
        ),
    },

    # ======================================================================
    # 8. Phalanges - Three Spheres of Energy [FT], [JF]
    # ======================================================================
    {
        "feature": PalmFeature.PHALANGES.value, "option": "first_dominant",
        "label": "Top Phalange Dominant (Spiritual & Idealistic)",
        "conditions": [{"metric": "index_phalange_first", "min": 0.34}], "requires": GEOMETRY,
        "area": "Orientation", "source": "Fingers in general and Thumb; Jupiter finger", "priority": 6,
        "meaning": (
            "The top fingertip phalange leads, signifying that philosophical ideas, intellectual curiosity, ethics, and "
            "higher principles guide life choices over purely commercial motives."
        ),
    },
    {
        "feature": PalmFeature.PHALANGES.value, "option": "second_dominant",
        "label": "Middle Phalange Dominant (Organization & Execution)",
        "conditions": [{"metric": "index_phalange_second", "min": 0.35}], "requires": GEOMETRY,
        "area": "Orientation", "source": "Fingers in general and Thumb; Jupiter finger", "priority": 6,
        "meaning": (
            "The middle phalange leads, conferring gifts for structured planning, tactical execution, administration, and "
            "turning conceptual ideas into organized, repeatable reality."
        ),
    },
    {
        "feature": PalmFeature.PHALANGES.value, "option": "third_dominant",
        "label": "Base Phalange Dominant (Material Grounding & Stability)",
        "conditions": [{"metric": "index_phalange_third", "min": 0.40}], "requires": GEOMETRY,
        "area": "Orientation", "source": "Fingers in general and Thumb; Jupiter finger", "priority": 6,
        "meaning": (
            "The base phalange leads, grounding energy in material security, tangible possessions, physical comfort, and "
            "practical achievements that produce lasting real-world security."
        ),
    },
    {
        "feature": PalmFeature.PHALANGES.value, "option": "balanced_phalanges",
        "label": "Harmonious Phalangeal Balance", "requires": GEOMETRY, "is_default": True,
        "area": "Orientation", "source": "Fingers in general and Thumb",
        "meaning": (
            "Phalanges exhibit proportional balance, effortlessly uniting conceptual vision, organized planning, and concrete delivery."
        ),
    },

    # ======================================================================
    # 9. Heart Line (Water Line) - Emotional Realm [HL], [RS]
    # ======================================================================
    {
        "feature": PalmFeature.HEART_LINE.value, "option": "ends_top_jupiter",
        "label": "Caring Water Line (Devoted & Family-First)",
        "conditions": [{"metric": "heart_line.termination_zone", "contains": "upper Jupiter"}],
        "requires": HEART, "area": "Relationships", "source": "Heart line", "priority": 10,
        "meaning": (
            "The Water Line sweeps high onto the Jupiter mount. The client's notes celebrate this as the Caring Line: "
            "unconditional affection, putting family and loved ones first, immense empathy, and an inability to see someone suffer, "
            "with a slight vulnerability of finding it difficult to say no."
        ),
    },
    {
        "feature": PalmFeature.HEART_LINE.value, "option": "ends_lower_jupiter",
        "label": "Idealistic Water Line (Romantic & Expressive)",
        "conditions": [{"metric": "heart_line.termination_zone", "contains": "lower Jupiter"}],
        "requires": HEART, "area": "Relationships", "source": "Heart line", "priority": 10,
        "meaning": (
            "Terminating on the lower Jupiter mount, this is the Idealistic Line: warmly romantic, verbally expressive, "
            "appreciates beauty and arts, gives wholehearted love, and values open communication and mutual devotion."
        ),
    },
    {
        "feature": PalmFeature.HEART_LINE.value, "option": "ends_between_jupiter_saturn",
        "label": "Harmonious Water Line (Balanced & Enduring)",
        "conditions": [{"metric": "heart_line.curvature", "min": 0.04}],
        "requires": HEART, "area": "Relationships", "source": "Heart line", "priority": 9,
        "meaning": (
            "Curving gracefully between the Jupiter and Saturn mounts, this marks emotional maturity: warm and loving yet "
            "sensible, possessing healthy relationship boundaries, and capable of enduring partnership."
        ),
    },
    {
        "feature": PalmFeature.HEART_LINE.value, "option": "ends_below_saturn",
        "label": "Hermit Water Line (Independent & Analytical)",
        "conditions": [{"metric": "heart_line.termination_zone", "contains": "Saturn"}],
        "requires": HEART, "area": "Relationships", "source": "Heart line", "priority": 10,
        "meaning": (
            "A straight Water Line ending beneath Saturn is classical palmistry's Independent Hermit Line: emotionally self-contained, "
            "dislikes dependency, highly objective in relationships, and content in their own sovereign space."
        ),
    },
    {
        "feature": PalmFeature.HEART_LINE.value, "option": "heart_deep_clear",
        "label": "Deep & Resilient Water Line",
        "conditions": [{"metric": "heart_line.contrast", "min": 3.0}],
        "requires": HEART, "area": "Relationships", "source": "Heart line", "priority": 7,
        "meaning": (
            "Clearly and deeply traced, this Water Line denotes steadfast emotional resilience, enduring loyalty, and an unshakeable "
            "inner calm during personal challenges."
        ),
    },
    {
        "feature": PalmFeature.HEART_LINE.value, "option": "heart_faint_delicate",
        "label": "Sensitive & Receptive Water Line",
        "conditions": [{"metric": "heart_line.contrast", "max": 1.8}],
        "requires": HEART, "area": "Relationships", "source": "Heart line", "priority": 7,
        "meaning": (
            "A delicate Water Line denotes high sensitivity, refined empathy, and impressionability. The native easily feels the moods "
            "of those around them and thrives in peaceful, supportive environments."
        ),
    },
    {
        "feature": PalmFeature.HEART_LINE.value, "option": "heart_balanced_line",
        "label": "Balanced Water Line", "requires": HEART, "is_default": True,
        "area": "Relationships", "source": "Heart line",
        "meaning": (
            "The Water Line follows a smooth, healthy trajectory across the upper palm, reflecting balanced empathy, emotional "
            "intelligence, and positive interpersonal connection."
        ),
    },

    # ======================================================================
    # 10. Head Line (Air Line) - Mind, Intellect & Strategy [NP], [HL], [RS]
    # ======================================================================
    {
        "feature": PalmFeature.HEAD_LINE.value, "option": "head_straight_practical",
        "label": "Linear Air Line (Sharp Logic & Practical Acumen)",
        "conditions": [{"metric": "head_slope", "max": 0.04}],
        "requires": HEAD, "area": "Thinking", "source": "Palmistry Notes Astro Rahul Sharma; Nature through palm",
        "priority": 10,
        "meaning": (
            "A direct, horizontal Air Line extending across the palm signifies sharp analytical reasoning, scientific clarity, "
            "commercial discernment, and realistic problem-solving. Prefers factual accuracy over wishful thinking."
        ),
    },
    {
        "feature": PalmFeature.HEAD_LINE.value, "option": "head_sloping_creative",
        "label": "Sloping Air Line (Creative Imagination & Intuition)",
        "conditions": [{"metric": "head_slope", "min": 0.08}],
        "requires": HEAD, "area": "Thinking", "source": "Palmistry Notes Astro Rahul Sharma; Nature through palm",
        "priority": 10,
        "meaning": (
            "An Air Line curving gently down towards the Moon mount signifies expansive imagination, intuitive perception, "
            "literary or artistic aptitude, and a visionary approach to life's possibilities."
        ),
    },
    {
        "feature": PalmFeature.HEAD_LINE.value, "option": "head_independent_origin",
        "label": "Independent Air Line (Bold Thinker & Pioneer)",
        "conditions": [{"metric": "head_life_gap", "min": 0.06}],
        "requires": HEAD, "area": "Thinking", "source": "Earth line; Nature through palm",
        "priority": 9,
        "meaning": (
            "A clear gap between the start of the Air Line and Earth Line signifies early intellectual independence. The native "
            "thinks outside conventional limits, is bold, self-directed, and unafraid to challenge orthodoxy."
        ),
    },
    {
        "feature": PalmFeature.HEAD_LINE.value, "option": "head_joined_origin",
        "label": "Joined Air Line (Thoughtful & Respectful of Roots)",
        "conditions": [{"metric": "head_life_gap", "max": 0.03}],
        "requires": HEAD, "area": "Thinking", "source": "Earth line; Palmistry Notes Astro Rahul Sharma",
        "priority": 9,
        "meaning": (
            "The Air Line commences joined with the Earth Line, reflecting prudence, deep respect for family traditions, "
            "thoughtful deliberation before acting, and strong conscientious loyalty."
        ),
    },
    {
        "feature": PalmFeature.HEAD_LINE.value, "option": "head_long_thorough",
        "label": "Expansive Air Line (Deep Concentration & Mastery)",
        "conditions": [{"metric": "head_line.length", "min": 0.45}],
        "requires": HEAD, "area": "Thinking", "source": "Palmistry Notes Astro Rahul Sharma",
        "priority": 8,
        "meaning": (
            "A long, continuous Air Line spanning much of the hand denotes sustained mental concentration, exceptional memory, "
            "intellectual stamina, and a capacity to master intricate, multi-layered subjects."
        ),
    },
    {
        "feature": PalmFeature.HEAD_LINE.value, "option": "head_balanced_line",
        "label": "Harmonious Air Line", "requires": HEAD, "is_default": True,
        "area": "Thinking", "source": "Palmistry Notes Astro Rahul Sharma",
        "meaning": (
            "The Air Line displays healthy clarity and balance across the mid-palm, uniting logical precision with flexible, "
            "adaptable problem-solving capability."
        ),
    },

    # ======================================================================
    # 11. Life Line (Earth Line) - Vitality, Roots & Expansion [EL], [RS]
    # ======================================================================
    {
        "feature": PalmFeature.LIFE_LINE.value, "option": "life_wide",
        "label": "Expansive Earth Line (Travel & Distant Growth)",
        "conditions": [{"metric": "life_reach", "min": 0.40}],
        "requires": LIFE, "area": "Vitality", "source": "Earth line", "priority": 10,
        "meaning": (
            "An Earth Line sweeping in a wide, magnificent arc across the palm. The client's material reads this as expansion: "
            "travel to distant lands, living beyond one's birthplace, thriving in large spaces, and an appetite for adventure."
        ),
    },
    {
        "feature": PalmFeature.LIFE_LINE.value, "option": "life_narrow",
        "label": "Close-Set Earth Line (Home-Loving & Energy-Conserving)",
        "conditions": [{"metric": "life_reach", "max": 0.28}],
        "requires": LIFE, "area": "Vitality", "source": "Earth line", "priority": 10,
        "meaning": (
            "An Earth Line curving close to the thumb base signifies domestic attachment, respect for familiar surroundings, and "
            "a quiet, energy-conserving lifestyle. The client explicitly notes this reflects caution rather than brevity of life."
        ),
    },
    {
        "feature": PalmFeature.LIFE_LINE.value, "option": "life_clear",
        "label": "Deep & Well-Carved Earth Line (Robust Vitality)",
        "conditions": [{"metric": "life_line.contrast", "min": 3.2}],
        "requires": LIFE, "area": "Vitality", "source": "Earth line", "priority": 8,
        "meaning": (
            "The Earth Line is the line of roots, family, and vitality. Deep and clearly defined, the client's notes link it to "
            "sound digestion, abundant physical stamina, settled peace of mind, and an ability to thrive anywhere."
        ),
    },
    {
        "feature": PalmFeature.LIFE_LINE.value, "option": "life_faint",
        "label": "Delicate Earth Line (Sensitive Constitution)",
        "conditions": [{"metric": "life_line.contrast", "max": 2.2}],
        "requires": LIFE, "area": "Vitality", "source": "Earth line", "priority": 8,
        "meaning": (
            "A delicate Earth Line signifies sensitive nervous energy rather than poor health. Thrives best when honoring a regular "
            "sleep schedule, nourishing diet, and serene surroundings that preserve inner calm."
        ),
    },
    {
        "feature": PalmFeature.LIFE_LINE.value, "option": "life_long_reach",
        "label": "Long-Rooted Earth Line (Enduring Stamina)",
        "conditions": [{"metric": "life_descent", "min": 0.78}],
        "requires": LIFE, "area": "Vitality", "source": "Earth line", "priority": 7,
        "meaning": (
            "The Earth Line sweeps cleanly into the base of the palm towards the wrist bracelets, signifying long-term vitality, "
            "a deep connection to ancestral roots, and steady lifetime resilience."
        ),
    },
    {
        "feature": PalmFeature.LIFE_LINE.value, "option": "life_balanced_line",
        "label": "Harmonious Earth Line", "requires": LIFE, "is_default": True,
        "area": "Vitality", "source": "Earth line",
        "meaning": (
            "A well-proportioned Earth Line providing steady physical stamina, rooted domestic security, and dependable recuperative power."
        ),
    },

    # ======================================================================
    # 12. Fate Line (Fire Line) - Career, Purpose & Vocation [EL], [NP], [ML]
    # ======================================================================
    {
        "feature": PalmFeature.FATE_LINE.value, "option": "fate_from_moon",
        "label": "Fire Line from Moon Mount (Public Support & Creativity)",
        "conditions": [{"metric": "fate_origin", "equals": "moon"}],
        "requires": FATE, "area": "Work", "source": "Mercury line; Nature through palm", "priority": 10,
        "meaning": (
            "The Fire Line originates from the lower lunar mount, indicating that professional growth and fortune are bolstered by "
            "public rapport, clients, networking, partnerships, travel, or creative fields."
        ),
    },
    {
        "feature": PalmFeature.FATE_LINE.value, "option": "fate_strong",
        "label": "Defined Fire Line (Clear Vocational Trajectory)",
        "conditions": [{"metric": "fate_line.contrast", "min": 2.8}],
        "requires": FATE, "area": "Work", "source": "Earth line; Nature through palm", "priority": 9,
        "meaning": (
            "A strongly etched Fire Line marks a continuous thread of purpose running through the working life, conferring focus, "
            "professional recognition, and purposeful career advancement."
        ),
    },
    {
        "feature": PalmFeature.FATE_LINE.value, "option": "fate_moderate",
        "label": "Emerging Fire Line (Adaptive Professional Progress)",
        "conditions": [{"metric": "fate_line.contrast", "min": 1.4}],
        "requires": FATE, "area": "Work", "source": "Earth line", "priority": 7,
        "meaning": (
            "A discernible Fire Line showing steady vocational responsibility, where career success develops naturally through "
            "perseverance and self-directed ambition."
        ),
    },
    {
        "feature": PalmFeature.FATE_LINE.value, "option": "fate_absent",
        "label": "Free-Spirited Destiny (Self-Made Path)",
        "conditions": [{"metric": "fate_line.found", "equals": "False"}],
        "requires": GEOMETRY, "area": "Work", "source": "Earth line", "priority": 8,
        "meaning": (
            "No single rigid Fire Line was traced. In classical palmistry this is a liberating sign: the native is not bound to a "
            "single corporate track, shaping their own destiny through adaptable skills and self-created opportunities."
        ),
    },
    {
        "feature": PalmFeature.FATE_LINE.value, "option": "fate_balanced_line",
        "label": "Balanced Fire Line", "requires": FATE, "is_default": True,
        "area": "Work", "source": "Earth line",
        "meaning": (
            "A balanced Fire Line providing flexibility and career stability, enabling the native to navigate changes with confidence."
        ),
    },

    # ======================================================================
    # 13. Line Relationships - Mind-Heart Equilibrium [HL]
    # ======================================================================
    {
        "feature": PalmFeature.LINE_RELATIONSHIP.value, "option": "wide_gap",
        "label": "Expansive Spacing (Broad-Minded & Generous)",
        "conditions": [{"metric": "heart_head_gap", "min": 0.15}],
        "requires": HEART_HEAD, "area": "Disposition", "source": "Heart line", "priority": 9,
        "meaning": (
            "A wide expanse between the Water and Air lines reflects an open-minded, generous spirit, willing to share knowledge "
            "and resources freely, with real independence of thought."
        ),
    },
    {
        "feature": PalmFeature.LINE_RELATIONSHIP.value, "option": "narrow_gap",
        "label": "Close Spacing (Cautious & Laser-Focused)",
        "conditions": [{"metric": "heart_head_gap", "max": 0.09}],
        "requires": HEART_HEAD, "area": "Disposition", "source": "Heart line", "priority": 9,
        "meaning": (
            "A compact interval between Water and Air lines indicates intense focus, prudent discretion, and a careful habit of "
            "guarding what is known and given away."
        ),
    },
    {
        "feature": PalmFeature.LINE_RELATIONSHIP.value, "option": "heart_high",
        "label": "High Water Line (Emotion Leading Reason)",
        "conditions": [{"metric": "heart_height", "max": 0.25}],
        "requires": HEART, "area": "Disposition", "source": "Heart line", "priority": 7,
        "meaning": (
            "The Water Line runs close beneath the finger mounts, meaning emotional impressions and spontaneous heart responses "
            "arrive first, with intellectual arguments following."
        ),
    },
    {
        "feature": PalmFeature.LINE_RELATIONSHIP.value, "option": "heart_low",
        "label": "Low Water Line (Reason Tempering Emotion)",
        "conditions": [{"metric": "heart_height", "min": 0.35}],
        "requires": HEART, "area": "Disposition", "source": "Heart line", "priority": 7,
        "meaning": (
            "The Water Line reaches down into the reasoning zone of the hand. Reasoning tempers feeling, resulting in composed, "
            "cool deliberation before expressing emotion."
        ),
    },
    {
        "feature": PalmFeature.LINE_RELATIONSHIP.value, "option": "balanced_gap",
        "label": "Balanced Mind-Heart Equilibrium", "requires": HEART_HEAD, "is_default": True,
        "area": "Disposition", "source": "Heart line",
        "meaning": (
            "Water and Air lines maintain ideal proportional spacing, enabling emotional empathy and logical intellect to support "
            "each other in harmonious balance."
        ),
    },

    # ======================================================================
    # 14. Career & Financial Synthesis [RS], [ML], [JF]
    # ======================================================================
    {
        "feature": PalmFeature.CAREER_FORECAST.value, "option": "career_executive",
        "label": "Executive & Strategic Leadership",
        "conditions": [{"metric": "index_ring_ratio", "min": 0.98}, {"metric": "thumb_length_ratio", "min": 1.05}],
        "requires": GEOMETRY, "area": "Work", "source": "Palmistry Notes Astro Rahul Sharma; Jupiter finger", "priority": 10,
        "meaning": (
            "Combination of high Jupiter finger authority and strong thumb determination indicates substantial executive capability. "
            "Suited for leadership, corporate management, entrepreneurship, governance, and high-responsibility leadership."
        ),
    },
    {
        "feature": PalmFeature.CAREER_FORECAST.value, "option": "career_commerce_media",
        "label": "Commerce, Media & Communication Mastery",
        "conditions": [{"metric": "mercury_reach_ratio", "min": 0.85}],
        "requires": GEOMETRY, "area": "Work", "source": "Mercury line; Palmistry Notes Astro Rahul Sharma", "priority": 8,
        "meaning": (
            "Prominent Mercury proportion points towards exceptional success in trade, business negotiations, sales, media, "
            "journalism, digital commerce, law, and advisory professions requiring persuasive presentation."
        ),
    },
    {
        "feature": PalmFeature.CAREER_FORECAST.value, "option": "career_practical_industry",
        "label": "Grounded Industry & Technical Excellence",
        "conditions": [{"metric": "is_square_palm", "min": 0.5}],
        "requires": GEOMETRY, "area": "Work", "source": "Nature through palm", "priority": 6,
        "meaning": (
            "A grounded palm foundation flourishes in engineering, real estate, finance, technology infrastructure, operations, "
            "and building solid, tangible enterprises with compounding long-term value."
        ),
    },
    {
        "feature": PalmFeature.CAREER_FORECAST.value, "option": "career_creative_innovator",
        "label": "Creative Vision & Independent Enterprise",
        "conditions": [{"metric": "is_square_palm", "max": 0.5}],
        "requires": GEOMETRY, "area": "Work", "source": "Nature through palm", "priority": 6,
        "meaning": (
            "An intuitive palm framework excels in creative design, branding, psychology, holistic counseling, independent "
            "consulting, and ventures requiring out-of-the-box conceptual innovation."
        ),
    },
    {
        "feature": PalmFeature.CAREER_FORECAST.value, "option": "career_balanced_path",
        "label": "Versatile Vocational Achievement", "requires": GEOMETRY, "is_default": True,
        "area": "Work", "source": "Palmistry Notes Astro Rahul Sharma",
        "meaning": (
            "Balanced hand geometry indicates versatile career adaptability, with financial momentum accelerating as self-directed "
            "initiatives are established."
        ),
    },

    # ======================================================================
    # 15. Love & Marriage Synthesis [HL], [FT], [RS]
    # ======================================================================
    {
        "feature": PalmFeature.RELATIONSHIP_FORECAST.value, "option": "love_deep_devotion",
        "label": "Devoted & Family-Centric Harmony",
        "conditions": [{"metric": "heart_line.termination_zone", "contains": "Jupiter"}],
        "requires": HEART, "area": "Relationships", "source": "Heart line; Palmistry Notes Astro Rahul Sharma", "priority": 9,
        "meaning": (
            "Water Line termination under Jupiter indicates an affectionate, deeply devoted partner who places domestic loyalty "
            "and family values at the center of their emotional world. Creates an enduring, supportive home."
        ),
    },
    {
        "feature": PalmFeature.RELATIONSHIP_FORECAST.value, "option": "love_independent_respect",
        "label": "Dignified Sovereignty & Mutual Respect",
        "conditions": [{"metric": "heart_line.termination_zone", "contains": "Saturn"}],
        "requires": HEART, "area": "Relationships", "source": "Heart line", "priority": 9,
        "meaning": (
            "Water Line ending under Saturn denotes a relationship built on quiet loyalty, shared principles, and mutual respect "
            "for personal autonomy. Thrives with a partner who values self-sufficiency and mature companionship."
        ),
    },
    {
        "feature": PalmFeature.RELATIONSHIP_FORECAST.value, "option": "love_harmonious_growth",
        "label": "Harmonious Partnership & Companionship", "requires": GEOMETRY, "is_default": True,
        "area": "Relationships", "source": "Heart line; Fingers in general and Thumb",
        "meaning": (
            "Balanced relationship indicators signify emotional reliability, warm companionship, and mutual dedication to "
            "building a harmonious and prosperous shared future."
        ),
    },

    # ======================================================================
    # 16. Vitality & Wellness Synthesis [EL], [HP], [RS]
    # ======================================================================
    {
        "feature": PalmFeature.HEALTH_FORECAST.value, "option": "vitality_robust",
        "label": "Robust Constitution & High Stamina",
        "conditions": [{"metric": "life_reach", "min": 0.35}],
        "requires": LIFE, "area": "Vitality", "source": "Earth line; Health palmistry", "priority": 9,
        "meaning": (
            "A well-extended Earth Line combined with grounded palm geometry reflects sound vitality, natural physical endurance, "
            "resilient digestion, and steady energy throughout demanding life phases."
        ),
    },
    {
        "feature": PalmFeature.HEALTH_FORECAST.value, "option": "vitality_sensitive_rhythm",
        "label": "Rhythmic Wellness & Nervous Restoration",
        "conditions": [{"metric": "life_reach", "max": 0.30}],
        "requires": LIFE, "area": "Vitality", "source": "Earth line; Health palmistry", "priority": 9,
        "meaning": (
            "A delicate Earth Line indicates a receptive nervous system that flourishes best through regular daily routines, "
            "mindful stress management, nourishing whole foods, and grounding outdoor activities."
        ),
    },
    {
        "feature": PalmFeature.HEALTH_FORECAST.value, "option": "vitality_balanced_lifestyle",
        "label": "Steady Vitality & Balanced Lifestyle", "requires": GEOMETRY, "is_default": True,
        "area": "Vitality", "source": "Earth line; Palmistry Notes Astro Rahul Sharma",
        "meaning": (
            "Balanced vitality indicators support consistent physical well-being, healthy recuperation, and a long-term foundation "
            "of active energy."
        ),
    },
]


def rule_count_by_feature() -> dict[str, int]:
    counts: dict[str, int] = {}
    for rule in PALM_RULES_SEED:
        counts[rule["feature"]] = counts.get(rule["feature"], 0) + 1
    return counts
