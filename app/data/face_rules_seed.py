"""The starting rule set for face reading.

Two things are being asserted here, and they have very different standing.

**The meanings** are traditional associations — Samudrika Shastra and the wider
physiognomy tradition, as summarised in the client's own reference book and the
classical sources it draws on. They are written fresh: not one sentence is
copied, because the supplied book is a watermarked copy with no named publisher
(see RESOURCES-MASTER §9, §12.1).

**The thresholds are not traditional at all.** No source gives a measurement.
"Broad" in every text means *broad compared to other faces*, and each band is
set around values actually produced by this pipeline, using ratios normalised
against the person's own face so camera distance cancels out.

They were first written as guesses, and measuring three real faces showed about
half of those guesses put every real face at an extreme — every forehead read
"low", every nose "broad". The bands below are centred on measured values
instead. Three faces is a starting point, not a distribution: the right fix is
`scripts.recalibrate_face_rules`, which re-derives every band by percentile
once enough real readings have accumulated.

They are a calibration, and they are meant to be argued with — which is why
they live in the database. When the client's astrologer sends numbers, these
rows get edited and nothing is rebuilt.

Loaded by `scripts.seed_face_rules`. Re-running it leaves edited rows alone
unless `--force` is passed.
"""

# Every ratio is measured against the subject's own face, never in pixels.
#
#   face_w             cheekbone to cheekbone
#   face_h             hairline to chin
#   wh_ratio           face_w / face_h
#   jaw_cheek          jaw width / face_w
#   brow_cheek         forehead width / face_w
#   forehead_h         forehead height / face_h
#   eye_open           eye height / eye width
#   eye_size           eye width / face_w
#   eye_gap            inner-corner gap / eye width
#   eye_tilt           outer corner above (+) or below (−) inner, / eye width
#   eye_asym           |left − right| eye height, / mean
#   brow_thick         brow thickness / eye height
#   brow_arch          arch rise / brow length
#   brow_gap           gap between brows / eye width
#   brow_len           brow length / eye width
#   nose_w             nose width / face_w
#   nose_len           nose length / face_h
#   nostril            nostril width / nose width
#   bridge_w           bridge width / nose width
#   nose_dev           tip offset from the face midline / face_w
#   lip_thick          lip height / mouth width
#   mouth_w            mouth width / face_w
#   lip_corner         corner height vs lip centre, / mouth width
#   lip_asym           left/right lip height difference, / mean
#   chin_h             chin height / face_h
#   cheek_full         cheek width at mouth height / face_w

RULES: list[dict] = [
    # ======================================================== FACE SHAPE
    {
        "feature": "face_shape", "option": "round", "label": "Round face",
        "priority": 20, "area": "temperament",
        "conditions": [{"metric": "wh_ratio", "min": 1.08}, {"metric": "jaw_cheek", "min": 0.80}],
        "meaning": (
            "A face as wide as it is long, with a soft jaw and little angle "
            "anywhere, is read as the mark of an approachable nature. The "
            "tradition associates it with warmth, sociability and an easy "
            "first impression — people tend to find you unguarded and talk to "
            "you readily. The same softness is said to show in how you handle "
            "conflict: you would rather smooth a disagreement than win it. "
            "Where it is thought to cost you is in holding a hard line; "
            "saying no, and meaning it the second time, is the discipline "
            "this face is told to practise."
        ),
    },
    {
        "feature": "face_shape", "option": "square", "label": "Square face",
        "priority": 25, "area": "temperament",
        "conditions": [{"metric": "wh_ratio", "min": 1.05}, {"metric": "jaw_cheek", "min": 0.86}],
        "meaning": (
            "A strong jaw carried at nearly the width of the cheekbones is one "
            "of the oldest marks of endurance in the tradition. It is read as "
            "determination that does not depend on mood: you finish things, "
            "and you are the one others rely on when a task turns dull. "
            "Authority tends to find you rather than the other way round. The "
            "caution attached to it is rigidity — a face read this way is said "
            "to hold a position long after the ground beneath it has shifted, "
            "and is advised to revisit decisions it has already made."
        ),
    },
    {
        "feature": "face_shape", "option": "long", "label": "Long face",
        "priority": 20, "area": "temperament",
        "conditions": [{"metric": "wh_ratio", "max": 0.92}],
        "meaning": (
            "A face noticeably longer than it is wide is associated with a "
            "considered, interior temperament. The reading is of someone who "
            "thinks before speaking and is comfortable alone — drawn to study, "
            "planning and work that rewards patience rather than quick "
            "reaction. Such a face is said to age well in reputation, being "
            "trusted more the longer people know it. Its difficulty is "
            "carrying worry privately: the tradition advises saying things out "
            "loud earlier than feels natural, since nothing here shows on the "
            "surface until it is already heavy."
        ),
    },
    {
        "feature": "face_shape", "option": "heart", "label": "Heart-shaped face",
        "priority": 30, "area": "temperament",
        "conditions": [{"metric": "brow_cheek", "min": 0.74}, {"metric": "jaw_cheek", "max": 0.77}],
        "meaning": (
            "A broad upper face tapering to a fine chin is read as imagination "
            "sitting above a light practical anchor. The association is with "
            "expressiveness, quick sympathy and an eye for what others miss — "
            "faces read this way are placed in creative and persuasive work "
            "rather than administrative. Affection comes easily and is given "
            "early. The warning in the tradition concerns stamina rather than "
            "ability: enthusiasm arrives fast and can leave the same way, so "
            "the counsel is to commit to fewer things and see them through."
        ),
    },
    {
        "feature": "face_shape", "option": "diamond", "label": "Diamond face",
        "priority": 30, "area": "temperament",
        "conditions": [{"metric": "brow_cheek", "max": 0.7}, {"metric": "jaw_cheek", "max": 0.78}],
        "meaning": (
            "Cheekbones that are the widest part of the face, with both brow "
            "and jaw narrower, are read as a self-directed nature. The "
            "tradition gives this face precision and a certain unwillingness "
            "to be managed: you would rather do a thing properly alone than "
            "quickly with others. It is associated with detailed, demanding "
            "work and with standards applied first to oneself. The caution is "
            "that the same exactness is turned outward without meaning to, and "
            "can be felt by others as coldness it was never intended as."
        ),
    },
    {
        "feature": "face_shape", "option": "triangular", "label": "Triangular face",
        "priority": 28, "area": "temperament",
        "conditions": [{"metric": "jaw_cheek", "min": 0.88}, {"metric": "brow_cheek", "max": 0.7}],
        "meaning": (
            "A jaw broader than the upper face reverses the usual proportion, "
            "and the tradition reads it as practical force. The association is "
            "with physical competence, persistence and a preference for doing "
            "over discussing — such a face is placed in work with visible "
            "results. Loyalty is strong and slow to give. What it is advised "
            "to watch is the pace at which it decides: once this face commits "
            "it rarely reconsiders, so the counsel is to spend longer at the "
            "beginning than at the end."
        ),
    },
    {
        "feature": "face_shape", "option": "oval", "label": "Oval face", "is_default": True,
        "priority": 0, "area": "temperament",
        "conditions": [],
        "meaning": (
            "Balanced proportions, with the face longer than it is wide and no "
            "single region dominating, are treated in the tradition as the "
            "settled form — the one other shapes are described against. It is "
            "read as adaptability: comfortable in different rooms, able to "
            "take a position without needing to hold it forever. Such a face "
            "is associated with diplomacy and with being underestimated early "
            "and reassessed later. Its own difficulty is diffuseness — being "
            "reasonable about everything can postpone choosing anything, and "
            "the tradition asks it to commit sooner."
        ),
    },

    # ========================================================== FOREHEAD
    {
        "feature": "forehead", "option": "broad_high", "label": "Broad and high forehead",
        "priority": 30, "area": "intellect",
        "conditions": [{"metric": "forehead_h", "min": 0.180}, {"metric": "brow_cheek", "min": 0.725}],
        "meaning": (
            "Height and width together make the forehead the most prominent "
            "region of the face, and the tradition treats it as the seat of "
            "reasoning. Read together they suggest a wide span of interest "
            "held with real capacity — the kind of mind that takes in a whole "
            "problem before working on any part of it. Teaching, planning and "
            "advisory work are the classical placements. The caution is "
            "staying at the level of ideas: this forehead is said to think a "
            "matter through so thoroughly that it never quite begins it."
        ),
    },
    {
        "feature": "forehead", "option": "high", "label": "High forehead",
        "priority": 20, "area": "intellect",
        "conditions": [{"metric": "forehead_h", "min": 0.180}],
        "meaning": (
            "A tall forehead is associated with reflection and with learning "
            "that continues past the age most people stop. The reading is of "
            "someone who wants to understand the reason behind an instruction "
            "before following it, and who is uneasy with being told rather "
            "than shown. Independent and analytical work suits it. What the "
            "tradition asks of this forehead is patience with people who reach "
            "conclusions differently — quickly, or by feel — since dismissing "
            "them is the habit it falls into most easily."
        ),
    },
    {
        "feature": "forehead", "option": "low", "label": "Low forehead",
        "priority": 20, "area": "intellect",
        "conditions": [{"metric": "forehead_h", "max": 0.145}],
        "meaning": (
            "A short forehead is read not as less capacity but as a different "
            "route to it: conclusions arrive quickly and by instinct rather "
            "than by working through steps. The association is with "
            "decisiveness and with being effective under pressure, where "
            "waiting costs more than being slightly wrong. Practical, "
            "immediate work suits it. The tradition's caution is proportionate "
            "— speed that serves you in a crisis is the same speed that "
            "commits you to things on an ordinary afternoon."
        ),
    },
    {
        "feature": "forehead", "option": "wide", "label": "Wide forehead",
        "priority": 15, "area": "intellect",
        "conditions": [{"metric": "brow_cheek", "min": 0.735}],
        "meaning": (
            "Width across the brow is read as range rather than depth — an "
            "interest in many things at once and an ease in moving between "
            "them. Such a face is associated with conversation, with "
            "connecting people and ideas that had not met, and with work that "
            "would bore someone narrower. The difficulty is finishing: breadth "
            "offers a new direction exactly when the current one becomes "
            "tedious, and the tradition advises choosing the tedious part on "
            "purpose."
        ),
    },
    {
        "feature": "forehead", "option": "narrow", "label": "Narrow forehead",
        "priority": 15, "area": "intellect",
        "conditions": [{"metric": "brow_cheek", "max": 0.675}],
        "meaning": (
            "A narrow brow concentrates rather than spreads. It is read as "
            "focus — the ability to stay with one matter until it yields, and "
            "a corresponding impatience with distraction. Specialist work, "
            "craft and anything requiring sustained attention are the "
            "classical placements, and the tradition expects such a face to go "
            "deeper into one subject than most go into any. Its cost is "
            "perspective: absorbed in the detail, it can miss that the "
            "surrounding situation has changed."
        ),
    },
    {
        "feature": "forehead", "option": "balanced", "label": "Even forehead", "is_default": True,
        "priority": 0, "area": "intellect",
        "conditions": [],
        "meaning": (
            "A forehead in proportion with the rest of the face is read as "
            "thought and action kept in balance — neither deliberating past "
            "the moment for acting nor moving before the matter is understood. "
            "The tradition treats this as the practical ideal rather than a "
            "remarkable sign, associating it with steady judgement and with "
            "being trusted to decide on others' behalf. It asks only that the "
            "balance be used: an evenness that never commits to a view is "
            "indistinguishable from having none."
        ),
    },

    # ========================================================== FOREHEAD LINES (কপালের রেখা / ভাঁজ)
    {
        "feature": "forehead_lines", "option": "smooth", "label": "Smooth & Uncreased Forehead (মসৃণ ও রেখাহীন কপাল)",
        "priority": 10, "area": "intellect", "is_default": True,
        "conditions": [{"metric": "forehead_lines", "max": 0.5}],
        "meaning": (
            "কপালে কোনো দৃশ্যমান ভাঁজ বা রেখা না থাকা মুক্তচিন্তা, তরুণসুলভ প্রাণশক্তি এবং প্রত্যক্ষ পদক্ষেপের নির্দেশক। "
            "আপনি জটিল তাত্ত্বিক আলোচনায় সময় ব্যয় না করে বাস্তবিক পদক্ষেপ নিতে ভালোবাসেন। খোলামনের দৃষ্টিভঙ্গি আপনাকে প্রতিকূলতায় দ্রুত মানিয়ে নিতে সাহায্য করে।"
        ),
    },
    {
        "feature": "forehead_lines", "option": "single_line", "label": "Single Prominent Line - Sun (একরেখা কপাল - সূর্য রেখা)",
        "priority": 20, "area": "ambition",
        "conditions": [{"metric": "forehead_lines", "min": 0.5, "max": 1.5}],
        "meaning": (
            "কপালে একটি সুস্পষ্ট রেখা (সূর্য রেখা) প্রবল ইচ্ছাশক্তি এবং গভীর আত্মবিশ্বাসের পরিচায়ক। "
            "সমুদ্র শাস্ত্র অনুযায়ী আপনি যেকোনো একটি নির্দিষ্ট লক্ষ্য স্থির করে একাগ্রচিত্তে তা অর্জন করতে সক্ষম। সমাজে স্বকীয় বৈশিষ্ট্য ও দৃঢ় নেতৃত্বের গুণে পরিচিতি লাভ করেন।"
        ),
    },
    {
        "feature": "forehead_lines", "option": "two_lines", "label": "Two Balanced Lines - Jupiter & Mars (দ্বিরেখা কপাল - বৃহস্পতি ও মঙ্গল)",
        "priority": 25, "area": "intellect",
        "conditions": [{"metric": "forehead_lines", "min": 1.5, "max": 2.5}],
        "meaning": (
            "কপালে দুটি সুস্পষ্ট সমান্তরাল রেখা প্রজ্ঞা (বৃহস্পতি) এবং কর্মশক্তি (মঙ্গল)-র সুসমন্বিত ভারসাম্যের লক্ষণ। "
            "আপনি যেকোনো সিদ্ধান্ত নেওয়ার আগে ভালোমন্দ বিচার করেন এবং নির্ভুলভাবে পরিকল্পনা বাস্তবায়ন করেন। পারিবারিক ও সামাজিক ক্ষেত্রে সুপরামর্শদাতা হিসেবে সম্মান লাভ করেন।"
        ),
    },
    {
        "feature": "forehead_lines", "option": "three_lines", "label": "Three Royal Lines - Trishula Yoga (ত্রিরেখা কপাল - রাজযোগ লক্ষণ)",
        "priority": 30, "area": "wealth",
        "conditions": [{"metric": "forehead_lines", "min": 2.5, "max": 3.5}],
        "meaning": (
            "সমুদ্র শাস্ত্রে কপালে তিনটি অটুট সমান্তরাল রেখা থাকা পরম সৌভাগ্য ও রাজযোগের প্রতীক (শনি, বৃহস্পতি ও মঙ্গল রেখা)। "
            "এই লক্ষণ দীর্ঘায়ু, অগাধ জ্ঞান, সামাজিক প্রতিপত্তি এবং অর্থভাগ্যের দ্বার উন্মোচন করে। জীবনে বাধা এলেও আপনি দৃঢ়তার সাথে জয়ী হয়ে প্রতিষ্ঠিত হন।"
        ),
    },
    {
        "feature": "forehead_lines", "option": "multi_lines", "label": "Multiple Planetary Lines (বহুরেখা কপাল - বহুদর্শী প্রজ্ঞা)",
        "priority": 25, "area": "intellect",
        "conditions": [{"metric": "forehead_lines", "min": 3.5}],
        "meaning": (
            "কপালে চার বা ততোধিক গ্রহীয় রেখা থাকা বহুদর্শী অভিজ্ঞতা, দূরদৃষ্টি এবং দার্শনিক চিন্তাশীলতার পরিচায়ক। "
            "আপনি জীবনের বাহ্যিক বিষয়ের চেয়ে অন্তর্নিহিত সত্য অন্বেষণে বেশি আগ্রহী। বহুমুখী প্রতিভার অধিকারী হয়ে বিভিন্ন ক্ষেত্রে পথপ্রদর্শকের ভূমিকা পালন করতে পারেন।"
        ),
    },

    # ========================================================== EYEBROWS
    {
        "feature": "eyebrows", "option": "thick", "label": "Thick eyebrows",
        "priority": 20, "area": "drive",
        "conditions": [{"metric": "brow_thick", "min": 0.155}],
        "meaning": (
            "Heavy brows are read as vitality that is visible before you speak. "
            "The tradition associates them with physical confidence, a strong "
            "will and opinions arrived at early and held firmly. People tend to "
            "assume such a face is in charge, which becomes true by repetition. "
            "The caution is force applied where persuasion would have done: "
            "this brow is said to win arguments it would have been better to "
            "lose, and is advised to let smaller points go."
        ),
    },
    {
        "feature": "eyebrows", "option": "thin", "label": "Thin eyebrows",
        "priority": 20, "area": "drive",
        "conditions": [{"metric": "brow_thick", "max": 0.125}],
        "meaning": (
            "Fine brows are associated with sensitivity of perception — "
            "noticing mood, tone and the thing not said. The reading is of "
            "someone who reads a room accurately and adjusts, which makes them "
            "easy company and effective where tact matters more than force. "
            "The difficulty is that the same receptiveness takes on others\' "
            "moods as if they were its own, and the tradition advises "
            "deliberate distance from people who are consistently heavy going."
        ),
    },
    {
        "feature": "eyebrows", "option": "arched", "label": "Arched eyebrows",
        "priority": 25, "area": "expression",
        "conditions": [{"metric": "brow_arch", "min": 0.49}],
        "meaning": (
            "A pronounced arch is read as expressiveness — a face that shows "
            "interest and doubt before its owner decides to show them. The "
            "association is with curiosity, a feel for drama and ease in front "
            "of people; such faces are placed in performance, teaching and "
            "selling. The tradition's caution concerns reaction: an arch "
            "responds faster than judgement does, and what it reveals cannot "
            "be taken back."
        ),
    },
    {
        "feature": "eyebrows", "option": "straight", "label": "Straight eyebrows",
        "priority": 25, "area": "expression",
        "conditions": [{"metric": "brow_arch", "max": 0.28}],
        "meaning": (
            "Brows with little curve are read as a direct, unornamented "
            "manner. The tradition associates them with logic, plain speech "
            "and a dislike of theatre — you say what you mean and expect the "
            "same, which makes you restful to deal with and occasionally "
            "blunt. Technical and analytical work suits this brow. Its cost is "
            "warmth that does not reach the surface: the feeling is present "
            "but unshown, and the counsel is to say it rather than assume it "
            "is obvious."
        ),
    },
    {
        "feature": "eyebrows", "option": "joined", "label": "Close-set eyebrows",
        "priority": 30, "area": "drive",
        "conditions": [{"metric": "brow_gap", "max": 0.95}],
        "meaning": (
            "Brows set close together, with little space above the nose, are "
            "read as concentration — attention that settles on one thing and "
            "stays. The tradition gives this brow intensity and a long memory, "
            "for obligations and for slights alike. It is associated with "
            "persistence that outlasts opposition. What it is advised to watch "
            "is the gap between taking something seriously and taking it "
            "personally, which this face crosses without noticing."
        ),
    },
    {
        "feature": "eyebrows", "option": "long", "label": "Long eyebrows",
        "priority": 15, "area": "relationships",
        "conditions": [{"metric": "brow_len", "min": 1.56}],
        "meaning": (
            "Brows extending well past the eye are traditionally a friendly "
            "sign, associated with wide and lasting connection. The reading is "
            "of someone who keeps relationships in repair over years, is asked "
            "for help often, and benefits later from people they were kind to "
            "early. The caution is dilution: a circle this wide is expensive "
            "to maintain, and the tradition advises keeping the few that "
            "matter rather than all of them equally."
        ),
    },
    {
        "feature": "eyebrows", "option": "short", "label": "Short eyebrows",
        "priority": 15, "area": "relationships",
        "conditions": [{"metric": "brow_len", "max": 1.48}],
        "meaning": (
            "Brows stopping short of the eye\'s end are read as "
            "self-sufficiency. The association is with independence, a small "
            "and closely held circle, and a preference for getting on with "
            "things rather than organising others to help. Such a face is "
            "trusted with what it is given. The tradition\'s advice is "
            "specific: ask earlier than feels comfortable, because this face "
            "is inclined to carry alone what it need not."
        ),
    },
    {
        "feature": "eyebrows", "option": "balanced", "label": "Even eyebrows", "is_default": True,
        "priority": 0, "area": "drive",
        "conditions": [],
        "meaning": (
            "Brows in proportion to the eyes, neither heavy nor sparse and "
            "gently curved, are read as a temperament that neither forces nor "
            "withdraws. The tradition treats this as steadiness: able to "
            "assert when it matters, content not to when it does not. It is "
            "associated with being easy to work alongside over long periods. "
            "Its only noted risk is being overlooked in rooms where louder "
            "faces are competing."
        ),
    },

    # ============================================================== EYES
    {
        "feature": "eyes", "option": "large", "label": "Large, open eyes",
        "priority": 20, "area": "temperament",
        "conditions": [{"metric": "eye_open", "min": 0.25}, {"metric": "eye_size", "min": 0.19}],
        "meaning": (
            "Wide, open eyes are read throughout the tradition as openness of "
            "nature — feeling that reaches the surface and is not hidden well. "
            "The association is with warmth, expressiveness and being trusted "
            "quickly, because what you think is visible before you say it. "
            "Such faces are placed where people must be put at ease. The "
            "caution is exposure: openness invites those who will use it, and "
            "the counsel is to be slower with new people than instinct wants."
        ),
    },
    {
        "feature": "eyes", "option": "narrow", "label": "Narrow eyes",
        "priority": 20, "area": "temperament",
        "conditions": [{"metric": "eye_open", "max": 0.19}],
        "meaning": (
            "Narrow eyes are read as discernment — a gaze that assesses before "
            "it accepts. The tradition associates them with concentration, "
            "composure under pressure and a reluctance to show a hand early, "
            "which is an advantage in negotiation and in any work where "
            "judgement matters more than reaction. The cost is being read as "
            "distant before you have decided anything, and the advice is to "
            "say warmth aloud, since this face does not display it."
        ),
    },
    {
        "feature": "eyes", "option": "close_set", "label": "Close-set eyes",
        "priority": 25, "area": "intellect",
        "conditions": [{"metric": "eye_gap", "max": 1.18}],
        "meaning": (
            "Eyes set near together are associated with focus and precision — "
            "attention that narrows onto a single matter and holds it. The "
            "reading is of someone who notices detail others step past and who "
            "is uncomfortable leaving a thing half-understood. Specialist work "
            "rewards this. The tradition\'s caution is proportion: absorbed "
            "closely, this face can treat a small problem with the seriousness "
            "a large one deserved."
        ),
    },
    {
        "feature": "eyes", "option": "wide_set", "label": "Wide-set eyes",
        "priority": 25, "area": "intellect",
        "conditions": [{"metric": "eye_gap", "min": 1.35}],
        "meaning": (
            "Eyes set well apart are read as breadth of view — taking in the "
            "whole situation rather than its parts, and being slow to panic "
            "because the panic-worthy detail is seen in context. The "
            "association is with tolerance, perspective and an unhurried "
            "manner. What it is advised to guard is follow-through on detail: "
            "seeing the shape of a thing is not the same as having done it, "
            "and this face sometimes mistakes one for the other."
        ),
    },
    {
        "feature": "eyes", "option": "upturned", "label": "Upturned eyes",
        "priority": 15, "area": "temperament",
        "conditions": [{"metric": "eye_tilt", "min": 0.075}],
        "meaning": (
            "Outer corners carried above the inner are read as optimism "
            "visible at rest — a face that looks receptive before it has "
            "decided to be. The tradition associates this with ambition held "
            "lightly, with recovering quickly from setbacks and with drawing "
            "opportunity through manner rather than effort. The caution is "
            "that a face which always looks willing is asked for more than it "
            "intended to give."
        ),
    },
    {
        "feature": "eyes", "option": "downturned", "label": "Downturned eyes",
        "priority": 15, "area": "temperament",
        "conditions": [{"metric": "eye_tilt", "max": 0.005}],
        "meaning": (
            "Outer corners resting below the inner give a gaze the tradition "
            "reads as gentle and considering. The association is with empathy, "
            "with being told things people do not tell others, and with "
            "judging situations more accurately than cheerful faces do. Its "
            "difficulty is appearing troubled when nothing is wrong, so that "
            "others approach carefully — and the counsel is simply to be aware "
            "the face is saying something the mind is not."
        ),
    },
    {
        "feature": "eyes", "option": "uneven", "label": "Eyes of different sizes",
        "priority": 28, "area": "temperament",
        "conditions": [{"metric": "eye_asym", "min": 0.13}],
        "meaning": (
            "A visible difference between the two eyes is treated in the "
            "tradition as a sign of two natures held in one person — a public "
            "manner and a private one that do not always agree. The reading is "
            "of adaptability and of seeing both sides genuinely, which makes "
            "such a face a good mediator. What it is asked to watch is "
            "deciding: holding both views indefinitely is comfortable, and "
            "postpones the moment of choosing."
        ),
    },
    {
        "feature": "eyes", "option": "balanced", "label": "Even eyes", "is_default": True,
        "priority": 0, "area": "temperament",
        "conditions": [],
        "meaning": (
            "Eyes in proportion to the face, evenly set and evenly open, are "
            "read as emotional steadiness — feeling that is neither hidden nor "
            "worn openly. The tradition associates this with reliability and "
            "with being believed, since nothing about the gaze works against "
            "what is said. It is the arrangement other eye signs are measured "
            "against, and carries no particular warning beyond being "
            "unremarkable at first meeting."
        ),
    },

    # ============================================================== NOSE
    {
        "feature": "nose", "option": "long_straight", "label": "Long, straight nose",
        "priority": 30, "area": "wealth",
        "conditions": [{"metric": "nose_len", "min": 0.31}, {"metric": "nose_dev", "max": 0.03}],
        "meaning": (
            "The nose is the tradition\'s wealth sign, and a long straight one "
            "is its most favourable form. It is read as money handled with "
            "method rather than luck: earning steadily, spending deliberately "
            "and building over years instead of chasing a sudden gain. The "
            "association is with discipline, long-range planning and being "
            "trusted with other people\'s resources. The caution is rigidity "
            "about money — a plan that survives every circumstance was not a "
            "plan but a habit."
        ),
    },
    {
        "feature": "nose", "option": "long", "label": "Long nose",
        "priority": 18, "area": "wealth",
        "conditions": [{"metric": "nose_len", "min": 0.31}],
        "meaning": (
            "Length in the nose is read as patience with money and with work. "
            "The association is with slow accumulation, a long view and a "
            "distaste for shortcuts; such a face is expected to do better at "
            "forty than at twenty-five and to mind that less than most. "
            "Professional and advisory work suits it. Its difficulty is "
            "acting late: an opportunity examined thoroughly enough is "
            "sometimes an opportunity that has gone."
        ),
    },
    {
        "feature": "nose", "option": "short", "label": "Short nose",
        "priority": 18, "area": "wealth",
        "conditions": [{"metric": "nose_len", "max": 0.27}],
        "meaning": (
            "A short nose is associated with immediacy rather than "
            "accumulation — money that comes from quick movement, present "
            "opportunity and the willingness to begin before the picture is "
            "complete. The tradition places such faces in trade and in work "
            "paid by result. Flexibility is the strength. The caution is the "
            "obvious one: income that arrives easily leaves the same way, and "
            "the counsel is to put a fixed share aside before it is spent."
        ),
    },
    {
        "feature": "nose", "option": "broad", "label": "Broad nose",
        "priority": 20, "area": "wealth",
        "conditions": [{"metric": "nose_w", "min": 0.32}],
        "meaning": (
            "Width in the nose is read as generosity and reach. The "
            "association is with earning through people — partnership, trade, "
            "anything where goodwill returns later as opportunity — and with "
            "an open hand that the tradition counts as a cause of wealth "
            "rather than a drain on it. Leadership of teams suits this face. "
            "The caution is lending on sympathy rather than judgement, which "
            "this nose is said to do repeatedly with the same people."
        ),
    },
    {
        "feature": "nose", "option": "narrow", "label": "Narrow nose",
        "priority": 20, "area": "wealth",
        "conditions": [{"metric": "nose_w", "max": 0.27}],
        "meaning": (
            "A narrow nose is read as care with resources — precise about what "
            "is spent and on what, and uncomfortable with waste in any form. "
            "The association is with refinement, quality over quantity, and "
            "work requiring exactness. Little is lost through carelessness. "
            "What the tradition warns of is holding too tightly: an "
            "opportunity that required spending was still an opportunity, and "
            "this face declines some it should have taken."
        ),
    },
    {
        "feature": "nose", "option": "large_nostrils", "label": "Open nostrils",
        "priority": 15, "area": "wealth",
        "conditions": [{"metric": "nostril", "min": 0.875}],
        "meaning": (
            "Visibly open nostrils are read as money that moves freely — "
            "earned readily and spent readily, with comfort in both "
            "directions. The association is with enjoyment of what is earned, "
            "a confident manner about money and a reluctance to let caution "
            "become the point of living. The tradition's counsel is "
            "structural rather than moral: set aside a share automatically, "
            "because deciding to save is not a decision this face makes in "
            "the moment."
        ),
    },
    {
        "feature": "nose", "option": "small_nostrils", "label": "Tight nostrils",
        "priority": 15, "area": "wealth",
        "conditions": [{"metric": "nostril", "max": 0.862}],
        "meaning": (
            "Narrow nostrils are read as retention — money that is kept once "
            "it arrives. The association is with prudence, planning for "
            "difficulty before it comes, and reaching security earlier than "
            "peers. Such a face rarely faces a crisis unprepared. The warning "
            "attached is pleasure deferred so long it is forgotten about: the "
            "tradition specifically advises spending some of it, deliberately, "
            "while it can still be enjoyed."
        ),
    },
    {
        "feature": "nose", "option": "deviated", "label": "Uneven nose line",
        "priority": 26, "area": "wealth",
        "conditions": [{"metric": "nose_dev", "min": 0.085}],
        "meaning": (
            "A nose whose line departs from the face\'s midline is read as "
            "fortune that arrives irregularly rather than steadily. The "
            "tradition does not treat this as misfortune but as rhythm: good "
            "periods and thin ones alternating, with the person often better "
            "at the thin ones than steadier faces are. Resourcefulness is the "
            "associated strength. The counsel is to budget against the "
            "average rather than the good months."
        ),
    },
    {
        "feature": "nose", "option": "balanced", "label": "Even nose", "is_default": True,
        "priority": 0, "area": "wealth",
        "conditions": [],
        "meaning": (
            "A nose proportionate to the face in both width and length is read "
            "as a balanced relationship with money — neither anxious nor "
            "careless, able to spend and to keep. The tradition treats this as "
            "the stable form against which the others are described, "
            "associating it with steady means arrived at without drama. It "
            "carries no specific warning, which in this tradition is itself "
            "the point."
        ),
    },

    # ============================================================== LIPS
    {
        "feature": "lips", "option": "full", "label": "Full lips",
        "priority": 20, "area": "relationships",
        "conditions": [{"metric": "lip_thick", "min": 0.31}],
        "meaning": (
            "Full lips are read as warmth that is given rather than withheld. "
            "The association is with generosity in affection, ease in speaking "
            "to strangers and a nature that enjoys company and food and "
            "comfort without apology. Such faces are placed where persuasion "
            "and hospitality matter. The caution concerns saying yes: this "
            "mouth agrees in the moment and discovers the cost afterwards, and "
            "is advised to leave a pause before answering."
        ),
    },
    {
        "feature": "lips", "option": "thin", "label": "Thin lips",
        "priority": 20, "area": "relationships",
        "conditions": [{"metric": "lip_thick", "max": 0.21}],
        "meaning": (
            "Thin lips are read as economy of speech — saying what is needed "
            "and stopping. The tradition associates them with discretion, "
            "self-control and keeping confidences, which makes such a face "
            "trusted with what others cannot hold. Precision in work follows "
            "the same pattern. The cost is affection assumed rather than "
            "expressed: those close by are left to infer it, and the counsel "
            "is to state it plainly rather than rely on being understood."
        ),
    },
    {
        "feature": "lips", "option": "upturned", "label": "Upturned mouth",
        "priority": 22, "area": "relationships",
        "conditions": [{"metric": "lip_corner", "min": 0.095}],
        "meaning": (
            "Corners that rest above the centre of the mouth give a face that "
            "appears willing before it speaks. The tradition reads this as "
            "optimism and as good fortune through manner — people approach "
            "such a face first, and opportunity follows from being approached. "
            "Resilience after setbacks is part of the same sign. The caution "
            "is being thought untroubled when you are not, so that help is "
            "never offered because it never looked needed."
        ),
    },
    {
        "feature": "lips", "option": "downturned", "label": "Downturned mouth",
        "priority": 22, "area": "relationships",
        "conditions": [{"metric": "lip_corner", "max": 0.045}],
        "meaning": (
            "Corners resting below the mouth\'s centre are read as "
            "seriousness rather than unhappiness — a face that does not "
            "perform a mood it is not in. The association is with sincerity, "
            "with being believed when pleased because the pleasure is real, "
            "and with judging situations soberly. Its difficulty is first "
            "impressions: strangers read discouragement where there is only "
            "composure, and the counsel is to greet people more warmly than "
            "feels necessary."
        ),
    },
    {
        "feature": "lips", "option": "uneven", "label": "Uneven lips",
        "priority": 26, "area": "expression",
        "conditions": [{"metric": "lip_asym", "min": 0.3}],
        "meaning": (
            "A mouth that sits differently on each side is read as wit and "
            "independence of mind — the face of someone who finds the angle "
            "others miss and says it. The tradition associates it with humour, "
            "with persuasion that works by surprise rather than pressure, and "
            "with resisting being told what to think. The caution is timing: "
            "the remark that is funny among friends is costly in front of "
            "people who do not know you."
        ),
    },
    {
        "feature": "lips", "option": "balanced", "label": "Even lips", "is_default": True,
        "priority": 0, "area": "relationships",
        "conditions": [],
        "meaning": (
            "Lips in proportion to the face, evenly set and level, are read as "
            "measured speech and steady affection — neither effusive nor "
            "withholding. The tradition associates this with being easy to be "
            "close to over long periods, and with saying difficult things "
            "without damage. It is the settled form, and carries no warning "
            "beyond being less immediately striking than the others."
        ),
    },

    # ======================================================== CHIN & JAW
    {
        "feature": "chin", "option": "square", "label": "Square jaw",
        "priority": 25, "area": "resolve",
        "conditions": [{"metric": "jaw_cheek", "min": 0.835}],
        "meaning": (
            "A broad, defined jaw is the tradition's clearest mark of "
            "resolve. It is read as the capacity to hold a position under "
            "pressure and to finish what was begun after the interest has "
            "gone. Such a face is given responsibility early and keeps it. "
            "The associated difficulty is yielding: this jaw treats changing "
            "its mind as losing, and the counsel is to separate the two "
            "deliberately, since the strength is wasted defending positions "
            "that no longer matter."
        ),
    },
    {
        "feature": "chin", "option": "pointed", "label": "Pointed chin",
        "priority": 25, "area": "resolve",
        "conditions": [{"metric": "jaw_cheek", "max": 0.812}],
        "meaning": (
            "A fine, tapering chin is read as refinement rather than force — "
            "achieving by precision, charm and timing what a heavier jaw "
            "achieves by pressure. The association is with artistic and "
            "intellectual work, quick perception and an unwillingness to win "
            "crudely. The tradition's caution concerns endurance: this chin "
            "is said to withdraw from a long contest it could have won, and "
            "is advised to stay in them longer."
        ),
    },
    {
        "feature": "chin", "option": "round", "label": "Rounded chin",
        "priority": 15, "area": "resolve",
        "conditions": [{"metric": "chin_h", "min": 0.222}],
        "meaning": (
            "A full, rounded chin is read as good nature with staying power "
            "underneath — accommodating by preference but not weak, and "
            "capable of settling in when something matters. The association is "
            "with family loyalty, hospitality and being the person a group "
            "organises itself around. Its difficulty is saying no early: this "
            "chin agrees first and resents later, and the tradition advises "
            "refusing at the outset rather than withdrawing afterwards."
        ),
    },
    {
        "feature": "chin", "option": "receding", "label": "Receding chin",
        "priority": 20, "area": "resolve",
        "conditions": [{"metric": "chin_h", "max": 0.188}],
        "meaning": (
            "A chin that sits back from the face\'s line is read as a nature "
            "that prefers accommodation to confrontation. The tradition gives "
            "it sensitivity, adaptability and skill at working around "
            "obstacles rather than through them — useful where force would "
            "only harden a situation. What it is advised to practise is the "
            "direct statement: this face is heard less than it should be, not "
            "for lack of a view but for not pressing it."
        ),
    },
    {
        "feature": "chin", "option": "balanced", "label": "Even chin", "is_default": True,
        "priority": 0, "area": "resolve",
        "conditions": [],
        "meaning": (
            "A chin in proportion to the face is read as resolve held in "
            "reserve — able to insist when it matters without needing to "
            "insist generally. The tradition associates this with "
            "even-handedness and with being trusted to arbitrate, since "
            "neither stubbornness nor retreat is the first instinct. It is the "
            "settled form and carries no specific warning."
        ),
    },

    # ============================================================ CHEEKS
    {
        "feature": "cheeks", "option": "high", "label": "High cheekbones",
        "priority": 25, "area": "standing",
        "conditions": [
            {"metric": "cheek_full", "min": 0.9, "max": 0.925},
            {"metric": "wh_ratio", "max": 0.80},
        ],
        "meaning": (
            "Cheekbones set high and clearly defined are read as standing — "
            "the quality of being noticed and taken seriously before anything "
            "is said. The tradition associates them with ambition, with "
            "authority that does not need to be claimed, and with reaching "
            "positions of visible responsibility. The caution concerns "
            "distance: a face carried this way is approached less often than "
            "it realises, and is advised to invite people closer on purpose."
        ),
    },
    {
        "feature": "cheeks", "option": "full", "label": "Full cheeks",
        "priority": 20, "area": "standing",
        "conditions": [{"metric": "cheek_full", "min": 0.932}],
        "meaning": (
            "Full cheeks are read as vitality and welcome. The tradition "
            "associates them with physical robustness, good relations across "
            "age and station, and the sort of presence that makes a room "
            "easier rather than more formal. Support tends to be available "
            "when needed, having been earned without effort. The caution is "
            "comfort: this face is said to settle into an agreeable situation "
            "and stay past the point where it should have moved."
        ),
    },
    {
        "feature": "cheeks", "option": "hollow", "label": "Lean cheeks",
        "priority": 20, "area": "standing",
        "conditions": [{"metric": "cheek_full", "max": 0.918}],
        "meaning": (
            "Lean cheeks are read as intensity and self-containment — energy "
            "directed inward at a purpose rather than outward at company. The "
            "association is with discipline, with work pursued past the point "
            "others stop, and with indifference to approval that makes such a "
            "face effective and occasionally isolated. The tradition's "
            "counsel is maintenance: this face neglects rest and company while "
            "something is unfinished, and pays for it later."
        ),
    },
    {
        "feature": "cheeks", "option": "balanced", "label": "Even cheeks", "is_default": True,
        "priority": 0, "area": "standing",
        "conditions": [],
        "meaning": (
            "Cheeks in proportion to the rest of the face are read as "
            "standing that rests on substance rather than impression — neither "
            "commanding a room nor disappearing in it. The tradition "
            "associates this with being judged on what you do, and with "
            "reputation that accumulates quietly and holds. It is the settled "
            "form, and carries no particular warning."
        ),
    },
]
