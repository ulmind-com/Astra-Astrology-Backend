"""Rashi (Moon Sign) trait tables used for the narrative section of the calculator.

PROVENANCE - read this before treating anything here as client-approved.

Only part of each entry is traceable to a client-supplied document:

  FROM THE CLIENT  element, modality, polarity, body_parts, nature, lord, and the
                   physical-description portion of overview. These come from
                   Resource Documents/Rashi Rules/01.pdf, 12 Rashis and Their
                   Planetary Lords.pdf and Rashi Characteristics and Traits
                   Overview.pdf, whose combined rashi content is about 4,800 words.
                   The authoritative, fully cited copies of these now live in
                   app/services/astrology/client_rules.py, which is what the API
                   returns as `client_rules`.

  NOT FROM THE     strengths, cautions_and_pitfalls,
  CLIENT           beneficial_actions_and_remedies, career_fields, lucky_color,
                   lucky_numbers, lucky_gemstone, lucky_day, ruling_deity and
                   compatible_rashis. These were written from general Vedic
                   astrology knowledge to fill out the reading. They are not in any
                   client file and have not been reviewed or signed off by the
                   client. lucky_color in particular is NOT the client's rasi-colour
                   table - that table is in client_rules.COLOURS and is returned
                   under the `colour` classification group.

An earlier version of this docstring claimed the whole module was "derived from the
client's resource documents", which was not accurate and would mislead anyone
auditing the rules. Treat every field in the NOT FROM THE CLIENT list as editorial
content pending client review.
"""

from typing import Any

RASHIS_DATA: list[dict[str, Any]] = [
    {
        "index": 0,
        "name_en": "Aries",
        "name_hi": "मेष",
        "name_bn": "মেষ",
        "symbol": "♈",
        "lord": "Mars",
        "element": "Fiery (অগ্নি)",
        "modality": "Movable / Cardinal (চর)",
        "polarity": "Masculine / Positive / Odd (পুরুষ / বিষম রাশি)",
        "body_parts": "Head, brain, forehead, skull, cranial vessels",
        "nature": "Dynamic, enterprising, valiant, energetic, impulsive, leadership-driven",
        "overview": (
            "Ruled by Mars, Aries represents the spark of life and initial impulse. "
            "Individuals with Moon in Aries are natural pioneers who thrive on action, challenges, "
            "and courageous initiatives. They possess a lean physique, prominent forehead, sharp gaze, "
            "and spontaneous enthusiasm."
        ),
        "strengths": [
            "Fearless leadership and pioneering initiative",
            "High stamina, quick problem solving, and determination",
            "Honest, direct, and straightforward communication",
            "Protective towards dependents and team members",
        ],
        "cautions_and_pitfalls": [
            "Hot temper, rash irritability, and speaking without forethought",
            "Impulsive financial gambles and leaping before looking",
            "Starting many ambitious projects but losing momentum halfway through",
            "Prone to headaches, migraines, fevers, and face/head injuries due to rush",
            "Inability to accept delays, advice, or subordination gracefully",
        ],
        "beneficial_actions_and_remedies": [
            "Daily morning meditation or slow breathwork (Pranayama) to cool Mars fire",
            "Recite Hanuman Chalisa or Kartikeya Stotra on Tuesdays for mental calm",
            "Channel intense energy into sports, martial arts, gym, or executive management",
            "Donate red lentils (masoor dal), copper vessels, or sweet jaggery on Tuesdays",
            "Practice pausing for 10 seconds before reacting in heated arguments",
        ],
        "career_fields": [
            "Defense, police, military & security",
            "Surgery, medicine & emergency services",
            "Entrepreneurship, venture capital & startup leadership",
            "Engineering, mechanics, real estate & construction",
            "Athletics, competitive sports & sports training",
        ],
        "lucky_color": "Crimson Red, Coral & Saffron",
        "lucky_numbers": [9, 1, 3],
        "lucky_gemstone": "Red Coral (Moonga)",
        "lucky_day": "Tuesday",
        "ruling_deity": "Lord Hanuman & Lord Kartikeya",
        "compatible_rashis": ["Leo", "Sagittarius", "Gemini", "Aquarius"],
    },
    {
        "index": 1,
        "name_en": "Taurus",
        "name_hi": "वृष",
        "name_bn": "বৃষ",
        "symbol": "♉",
        "lord": "Venus",
        "element": "Earthy (পৃথ্বী)",
        "modality": "Fixed / Static (স্থির)",
        "polarity": "Feminine / Negative / Even (স্ত্রী / সম রাশি)",
        "body_parts": "Face, neck, throat, vocal cords, thyroid, chin",
        "nature": "Stable, loyal, patient, luxury-loving, artistic, dependable, methodical",
        "overview": (
            "Ruled by Venus, Taurus embodies stability, endurance, and sensual beauty. "
            "Those with Moon in Taurus have a peaceful demeanor, attractive face, fine teeth, and "
            "an eye for aesthetics. They value financial security, domestic comfort, and lasting loyalty."
        ),
        "strengths": [
            "Rock-solid dependability, patience, and loyalty",
            "Superb financial planning and resource management",
            "Refined taste in fine arts, music, culinary delights, and luxury",
            "Calm resilience under pressure and steadfast endurance",
        ],
        "cautions_and_pitfalls": [
            "Extreme stubbornness and resistance to necessary modern changes",
            "Overindulgence in heavy food, sweets, and material luxuries",
            "Tendency towards sluggishness, procrastination, and physical lethargy",
            "Possessiveness and insecurity in emotional relationships",
            "Vulnerability to throat infections, vocal strain, and thyroid imbalances",
        ],
        "beneficial_actions_and_remedies": [
            "Embrace flexibility and practice letting go of rigid mental stances",
            "Worship Goddess Mahalakshmi on Fridays; offer white flowers and kheer",
            "Regular throat gargling and vocal care; spend time in lush gardens/nature",
            "Donate white garments, rice, dairy products, or silver items on Fridays",
            "Incorporate light cardio and outdoor walking into your daily routine",
        ],
        "career_fields": [
            "Banking, financial advisory, wealth management & accounting",
            "Fashion, jewelry, cosmetics, beauty & interior design",
            "Culinary arts, restaurant business, hospitality & luxury hotels",
            "Music, singing, fine arts & voice artistry",
            "Agriculture, horticulture & luxury real estate",
        ],
        "lucky_color": "White, Cream, Pearl & Rose Pink",
        "lucky_numbers": [6, 2, 8],
        "lucky_gemstone": "Diamond (Heera) or White Sapphire",
        "lucky_day": "Friday",
        "ruling_deity": "Goddess Lakshmi",
        "compatible_rashis": ["Virgo", "Capricorn", "Cancer", "Pisces"],
    },
    {
        "index": 2,
        "name_en": "Gemini",
        "name_hi": "मिथुन",
        "name_bn": "মিথুন",
        "symbol": "♊",
        "lord": "Mercury",
        "element": "Airy (বায়ু)",
        "modality": "Dual / Common (দ্বিস্বভাব)",
        "polarity": "Masculine / Positive / Odd (পুরুষ / বিষম রাশি)",
        "body_parts": "Shoulders, arms, hands, respiratory system, nervous system",
        "nature": "Intellectual, witty, communicative, curious, versatile, social",
        "overview": (
            "Ruled by Mercury, Gemini is the master of communication, intellect, and versatility. "
            "Moon in Gemini bestows a youthful appearance, curious eyes, eloquent speech, and "
            "an agile mind that absorbs knowledge like a sponge. They excel in networking, writing, "
            "and information exchange."
        ),
        "strengths": [
            "Brilliant conversationalist and sharp verbal acumen",
            "Quick mental adaptability and capacity to multitask",
            "Insatiable curiosity and fast learning curve",
            "Youthful zest, humor, and friendly interpersonal charm",
        ],
        "cautions_and_pitfalls": [
            "Restless mind leading to chronic anxiety and nervous exhaustion",
            "Indecision and scattering energy across too many half-done ideas",
            "Superficial interest without drilling down to mastery",
            "Tendency to gossip or change commitments abruptly",
            "Respiratory sensitivities, bronchial congestion, and sleep irregularity",
        ],
        "beneficial_actions_and_remedies": [
            "Practice single-tasking; complete one project before starting the next",
            "Chant Lord Ganesha Mantras (`Om Gan Ganapataye Namaha`) on Wednesdays",
            "Feed green grass or spinach to cows; donate books or stationery to students",
            "Daily breathwork (Anulom-Vilom Pranayama) to calm overstimulated nerves",
            "Maintain a written gratitude journal to anchor scattered thoughts",
        ],
        "career_fields": [
            "Journalism, media, content writing, publishing & broadcasting",
            "Software engineering, IT, telecommunications & data networks",
            "Marketing, public relations, sales & advertising",
            "Teaching, linguistics, translation & corporate training",
            "Trade, commerce, brokerage & diplomacy",
        ],
        "lucky_color": "Emerald Green, Light Yellow & Mint",
        "lucky_numbers": [5, 3, 7],
        "lucky_gemstone": "Emerald (Panna)",
        "lucky_day": "Wednesday",
        "ruling_deity": "Lord Ganesha & Lord Vishnu",
        "compatible_rashis": ["Libra", "Aquarius", "Aries", "Leo"],
    },
    {
        "index": 3,
        "name_en": "Cancer",
        "name_hi": "कर्क",
        "name_bn": "কর্কট",
        "symbol": "♋",
        "lord": "Moon",
        "element": "Watery (জল)",
        "modality": "Movable / Cardinal (চর)",
        "polarity": "Feminine / Negative / Even (স্ত্রী / সম রাশি)",
        "body_parts": "Chest, breasts, stomach, digestive tract, diaphragm",
        "nature": "Empathetic, intuitive, maternal, protective, emotional, nostalgic",
        "overview": (
            "As the natural domicile of the Moon, Cancer vibrates with deep emotion, intuition, "
            "and protective devotion. Those with Moon in Cancer are deeply caring, devoted to family, "
            "and sensitive to environmental energies. They have an expressive face, gentle eyes, and a "
            "magnetic warmth."
        ),
        "strengths": [
            "Unrivaled intuition, psychic sensitivity, and emotional depth",
            "Profound loyalty to family, home, and trusted loved ones",
            "Exceptional memory and nurturing, healing presence",
            "High emotional intelligence and creative imagination",
        ],
        "cautions_and_pitfalls": [
            "Fluctuating mood swings synchronized with waxing/waning moon cycles",
            "Clinging to past grievances, hurt feelings, and toxic attachments",
            "Emotional eating or digestive upset triggered by stress",
            "Defensive shell that shuts out well-meaning friends when hurt",
            "Over-sensitivity to minor criticisms or perceived rejection",
        ],
        "beneficial_actions_and_remedies": [
            "Take blessings from your mother or elder maternal figures regularly",
            "Offer raw milk and clean water (Jala Abhishekam) to Shiva Lingam on Mondays",
            "Drink water stored in clean silver cups or containers",
            "Donate white items (milk, rice, sugar, silver, white sweets) on Mondays",
            "Spend peaceful moments by water bodies (lakes, rivers, seas) to reset emotions",
        ],
        "career_fields": [
            "Medicine, nursing, pediatrics, psychology & counseling",
            "Hospitality, catering, culinary arts & dairy farming",
            "Real estate, home decor, architecture & interior design",
            "Education, childcare, social welfare & NGO leadership",
            "Marine industries, shipping, creative writing & poetry",
        ],
        "lucky_color": "Pearl White, Silver & Sea Green",
        "lucky_numbers": [2, 7, 9],
        "lucky_gemstone": "Natural Pearl (Moti) or Moonstone",
        "lucky_day": "Monday",
        "ruling_deity": "Lord Shiva & Goddess Parvati",
        "compatible_rashis": ["Scorpio", "Pisces", "Taurus", "Virgo"],
    },
    {
        "index": 4,
        "name_en": "Leo",
        "name_hi": "सिंह",
        "name_bn": "সিংহ",
        "symbol": "♌",
        "lord": "Sun",
        "element": "Fiery (অগ্নি)",
        "modality": "Fixed / Static (স্থির)",
        "polarity": "Masculine / Positive / Odd (পুরুষ / বিষম রাশি)",
        "body_parts": "Heart, upper back, spine, solar plexus, vitality",
        "nature": "Royal, charismatic, generous, noble, confident, authoritative",
        "overview": (
            "Ruled by the Sun, Leo represents royalty, nobility, and natural majesty. "
            "Moon in Leo individuals have a regal presence, broad chest, commanding voice, and "
            "a golden warmth that draws others in. They are born to lead, inspire, and create lasting "
            "impact with unshakeable dignity."
        ),
        "strengths": [
            "Natural charisma, leadership, and magnetic presence",
            "Magnanimous generosity and loyalty to followers",
            "High creative courage, self-confidence, and dignity",
            "Optimistic enthusiasm that elevates any group or team",
        ],
        "cautions_and_pitfalls": [
            "Inflated ego, false pride, and intolerance of criticism",
            "Commanding or authoritarian attitude that alienates peers",
            "Vulnerability to flattery from dishonest individuals",
            "Overworking heart/circulatory system; spine and postural strain",
            "Refusing to seek assistance when facing personal vulnerability",
        ],
        "beneficial_actions_and_remedies": [
            "Offer water (Surya Arghya) to the rising morning Sun with Gayatri Mantra",
            "Practice humble leadership and actively praise teammates' achievements",
            "Respect father, teachers, and authority figures with genuine reverence",
            "Donate wheat, copper, or jaggery to the needy on Sundays",
            "Maintain cardiovascular wellness with moderate aerobics and back stretches",
        ],
        "career_fields": [
            "Governance, politics, civil services & senior administrative roles",
            "Corporate executive leadership (CEO/Director) & management",
            "Theatre, cinema, performing arts, directing & entertainment",
            "Gold, jewelry, luxury branding & high-end real estate",
            "Event management, public leadership & motivational speaking",
        ],
        "lucky_color": "Gold, Saffron, Orange & Royal Crimson",
        "lucky_numbers": [1, 4, 9],
        "lucky_gemstone": "Ruby (Manikya)",
        "lucky_day": "Sunday",
        "ruling_deity": "Lord Surya (Sun God) & Lord Rama",
        "compatible_rashis": ["Aries", "Sagittarius", "Gemini", "Libra"],
    },
    {
        "index": 5,
        "name_en": "Virgo",
        "name_hi": "कन्या",
        "name_bn": "কন্যা",
        "symbol": "♍",
        "lord": "Mercury",
        "element": "Earthy (পৃথ্বী)",
        "modality": "Dual / Common (দ্বিস্বভাব)",
        "polarity": "Feminine / Negative / Even (স্ত্রী / সম রাশি)",
        "body_parts": "Abdomen, intestines, digestive system, spleen, nervous tract",
        "nature": "Analytical, meticulous, disciplined, intellectual, humble, service-minded",
        "overview": (
            "Ruled by Mercury, Virgo is the hallmark of perfection, analytical precision, and selfless "
            "service. Moon in Virgo individuals possess sharp observation skills, a modest demeanor, "
            "exceptional organizational ability, and an instinct for problem-solving and health."
        ),
        "strengths": [
            "Flawless eye for detail, proofreading, and quality control",
            "Practical analytical intelligence and systematic methods",
            "Devotion to duty, self-improvement, and health hygiene",
            "Compassionate dedication to healing and problem-solving",
        ],
        "cautions_and_pitfalls": [
            "Paralysis by analysis; finding fault in everything and everyone",
            "Chronic worry, overthinking, and health anxiety (hypochondria)",
            "Digestive distress, IBS, and food sensitivities driven by stress",
            "Difficulty enjoying leisure without guilt of unfinished chores",
            "Harsh self-criticism that erodes self-confidence",
        ],
        "beneficial_actions_and_remedies": [
            "Practice non-judgmental acceptance of human flaws (including your own)",
            "Chant Budh Mantra (`Om Budhaya Namaha`) or Vishnu Sahasranama on Wednesdays",
            "Feed birds, cows, or stray dogs; keep clean indoor green plants",
            "Maintain gut health with probiotics, light fibrous diet, and regular meals",
            "Engage in hands-on hobbies like gardening, sketching, or craftwork to relax mind",
        ],
        "career_fields": [
            "Data science, auditing, accounting, quality assurance & analysis",
            "Healthcare, nursing, pharmacy, nutrition & medical diagnostics",
            "Editing, research, libraries, archives & technical writing",
            "Software testing, debugging & systems engineering",
            "Environmental science, agriculture & administrative services",
        ],
        "lucky_color": "Light Green, Olive, Beige & Pearl Gray",
        "lucky_numbers": [5, 2, 7],
        "lucky_gemstone": "Emerald (Panna) or Peridot",
        "lucky_day": "Wednesday",
        "ruling_deity": "Lord Vishnu & Lord Ganesha",
        "compatible_rashis": ["Taurus", "Capricorn", "Cancer", "Scorpio"],
    },
    {
        "index": 6,
        "name_en": "Libra",
        "name_hi": "तुला",
        "name_bn": "তুলা",
        "symbol": "♎",
        "lord": "Venus",
        "element": "Airy (বায়ু)",
        "modality": "Movable / Cardinal (চর)",
        "polarity": "Masculine / Positive / Odd (পুরুষ / বিষম রাশি)",
        "body_parts": "Kidneys, lumbar region, lower back, skin, buttocks",
        "nature": "Diplomatic, harmonious, just, charming, artistic, socially graceful",
        "overview": (
            "Ruled by Venus, Libra is represented by the divine scales of balance, justice, and harmony. "
            "Moon in Libra bestows aesthetic grace, charming manners, pleasant speech, and a deep instinct "
            "for fairness. They thrive in partnerships, trade, and culturally enriching environments."
        ),
        "strengths": [
            "Superb mediation, diplomatic arbitration, and conflict resolution",
            "Aesthetic sophistication, artistic taste, and social charm",
            "Commitment to justice, fair play, and equality",
            "Ability to see multiple perspectives with neutral balance",
        ],
        "cautions_and_pitfalls": [
            "Chronic indecisiveness and agonizing over minor choices",
            "Over-compromising personal values to appease others or avoid conflict",
            "Dependence on external validation and relationship status",
            "Kidney strain, lower back stiffness, and dehydration vulnerabilities",
            "Extravagance in shopping for luxury items beyond budget",
        ],
        "beneficial_actions_and_remedies": [
            "Set clear personal boundaries and make timely, firm decisions",
            "Drink plenty of water to maintain kidney and urinary health",
            "Worship Goddess Mahalakshmi on Fridays; donate cosmetics, perfume, or sweets",
            "Practice core and lumbar strengthening exercises (like Bhujangasana)",
            "Surround yourself with balanced colors, pleasant fragrances, and calming music",
        ],
        "career_fields": [
            "Law, judiciary, human rights advocacy & diplomacy",
            "Public relations, negotiation, partnership brokering & arbitration",
            "Fashion design, architecture, photography, cosmetics & luxury trade",
            "Event curation, hospitality management & fine dining",
            "Consulting, marketing & social media management",
        ],
        "lucky_color": "Pastel Blue, White, Lavender & Pink",
        "lucky_numbers": [6, 9, 3],
        "lucky_gemstone": "Diamond (Heera), White Zircon or Opal",
        "lucky_day": "Friday",
        "ruling_deity": "Goddess Lakshmi & Goddess Saraswati",
        "compatible_rashis": ["Gemini", "Aquarius", "Leo", "Sagittarius"],
    },
    {
        "index": 7,
        "name_en": "Scorpio",
        "name_hi": "वृश्चिक",
        "name_bn": "বৃশ্চিক",
        "symbol": "♏",
        "lord": "Mars",
        "element": "Watery (জল)",
        "modality": "Fixed / Static (স্থির)",
        "polarity": "Feminine / Negative / Even (স্ত্রী / সম রাশি)",
        "body_parts": "Reproductive organs, pelvis, excretory system, bladder",
        "nature": "Intense, investigative, magnetic, secretive, loyal, transformative",
        "overview": (
            "Ruled by Mars and representing the deep mystical waters, Scorpio is the sign of profound "
            "regeneration and hidden power. Moon in Scorpio (debilitated in classical terms, yet deeply perceptive) "
            "bestows penetrating intuition, iron willpower, unwavering loyalty, and the ability to resurrect "
            "from life's greatest tribulations."
        ),
        "strengths": [
            "Unshakeable willpower, resilience, and transformative capacity",
            "Profound psychological penetration and lie-detection ability",
            "Fierce, lifelong loyalty to those who earn their trust",
            "Mastery over research, occult mysteries, and confidential matters",
        ],
        "cautions_and_pitfalls": [
            "Harboring deep resentment, jealousy, and revenge fantasies",
            "Extreme secrecy and paranoia pushing loving people away",
            "Emotional all-or-nothing extremes leading to self-sabotage",
            "Vulnerability to reproductive, urinary, or pelvic inflammation",
            "Difficulty forgiving past betrayals or emotional wounds",
        ],
        "beneficial_actions_and_remedies": [
            "Practice conscious forgiveness and release mental grudges daily",
            "Worship Lord Shiva (Maha Mrityunjaya Mantra) or Lord Hanuman on Tuesdays",
            "Donate blood voluntarily or donate red lentils/copper on Tuesdays",
            "Channel intensity into investigative work, occult research, or psychotherapy",
            "Maintain hygienic reproductive/pelvic health and practice grounding meditation",
        ],
        "career_fields": [
            "Investigation, forensics, criminology, intelligence & cybersecurity",
            "Surgery, pathology, oncology, pharmacology & occult healing",
            "Psychotherapy, psychiatry, hypnosis & transformational coaching",
            "Mining, petroleum, geology & marine engineering",
            "Auditing, tax investigation, corporate espionage & venture capital",
        ],
        "lucky_color": "Deep Maroon, Rust Red, Crimson & Black",
        "lucky_numbers": [9, 4, 8],
        "lucky_gemstone": "Red Coral (Moonga) or Carnelian",
        "lucky_day": "Tuesday",
        "ruling_deity": "Lord Shiva & Lord Kartikeya",
        "compatible_rashis": ["Cancer", "Pisces", "Virgo", "Capricorn"],
    },
    {
        "index": 8,
        "name_en": "Sagittarius",
        "name_hi": "धनु",
        "name_bn": "ধনু",
        "symbol": "♐",
        "lord": "Jupiter",
        "element": "Fiery (অগ্নি)",
        "modality": "Dual / Common (দ্বিস্বভাব)",
        "polarity": "Masculine / Positive / Odd (পুরুষ / বিষম রাশি)",
        "body_parts": "Hips, thighs, sciatic nerve, liver, arterial system",
        "nature": "Philosophical, optimistic, righteous, adventurous, truth-seeking, wise",
        "overview": (
            "Ruled by Jupiter, Sagittarius is the seeker of higher truth, divine wisdom, and distant horizons. "
            "Those with Moon in Sagittarius possess an athletic build, open forehead, joyful countenance, "
            "and an expansive philosophy. They inspire others with their optimism, faith, and ethical nobility."
        ),
        "strengths": [
            "Boundless optimism, spiritual faith, and philosophical outlook",
            "Love for knowledge, world cultures, higher education, and truth",
            "Honest, candid, and inspiring mentorship qualities",
            "Enthusiastic explorer of physical and intellectual realms",
        ],
        "cautions_and_pitfalls": [
            "Over-optimism leading to reckless financial bets or over-commitments",
            "Blunt, tactless speech that unintentionally hurts sensitive souls",
            "Restlessness and abandoning discipline for wanderlust",
            "Liver vulnerabilities, cholesterol issues, and sciatic/hip pain",
            "Preaching moral standards to others while ignoring personal routines",
        ],
        "beneficial_actions_and_remedies": [
            "Ground philosophical vision into disciplined daily responsibilities",
            "Honor and take blessings from teachers, professors, and spiritual Gurus",
            "Chant Guru Mantra (`Om Gram Greem Grom Sah Gurave Namaha`) on Thursdays",
            "Donate turmeric, yellow lentils (chana dal), or saffron on Thursdays",
            "Maintain liver wellness with clean hydration and regular outdoor hiking",
        ],
        "career_fields": [
            "Higher education, philosophy, university professorship & academia",
            "Law, international relations, judiciary & civil advocacy",
            "Publishing, spiritual leadership, coaching & public lecturing",
            "Tourism, aviation, international trade & exploration",
            "Judicial advisory, sports coaching & religious institutions",
        ],
        "lucky_color": "Golden Yellow, Saffron, Royal Blue & Purple",
        "lucky_numbers": [3, 7, 9],
        "lucky_gemstone": "Yellow Sapphire (Pukhraj) or Topaz",
        "lucky_day": "Thursday",
        "ruling_deity": "Lord Vishnu & Lord Brihaspati",
        "compatible_rashis": ["Aries", "Leo", "Libra", "Aquarius"],
    },
    {
        "index": 9,
        "name_en": "Capricorn",
        "name_hi": "मकर",
        "name_bn": "মকর",
        "symbol": "♑",
        "lord": "Saturn",
        "element": "Earthy (পৃথ্বী)",
        "modality": "Movable / Cardinal (চর)",
        "polarity": "Feminine / Negative / Even (স্ত্রী / সম রাশি)",
        "body_parts": "Knees, joints, bones, skeletal frame, skin, teeth",
        "nature": "Pragmatic, ambitious, disciplined, patient, persevering, authoritative",
        "overview": (
            "Ruled by Saturn, Capricorn represents the master climber who scales the steepest summits "
            "through sheer endurance, organization, and unyielding discipline. Moon in Capricorn individuals "
            "have a mature demeanor, sharp jawline, patient gaze, and an extraordinary capacity for long-term "
            "strategic achievement."
        ),
        "strengths": [
            "Matchless endurance, discipline, and strategic perseverance",
            "Mastery of corporate hierarchy, organizational systems, and governance",
            "Prudent financial acumen and high professional integrity",
            "Patient ability to turn delayed obstacles into stepping stones",
        ],
        "cautions_and_pitfalls": [
            "Tendency toward chronic pessimism, gloominess, and emotional coldness",
            "Workaholism leading to neglect of family life and simple joys",
            "Judging personal self-worth solely by worldly status and achievements",
            "Knee joint pain, arthritis, bone density reduction, and dry skin",
            "Difficulty trusting others with delegation due to perfectionist fear",
        ],
        "beneficial_actions_and_remedies": [
            "Intentionally cultivate warmth, gratitude, and spontaneous laughter",
            "Serve elderly people, disabled individuals, or daily wage laborers on Saturdays",
            "Light a mustard oil lamp under a Peepal tree on Saturday evenings",
            "Chant Shani Mantra (`Om Sham Shanaishcharaya Namaha`) for grace",
            "Nourish bones and joints with sesame oil massage and calcium-rich nutrition",
        ],
        "career_fields": [
            "Corporate governance, executive administration & project management",
            "Engineering, architecture, heavy industries & civil infrastructure",
            "Banking, insurance, real estate management & resource allocation",
            "Government services, policy planning & organizational consulting",
            "Mining, manufacturing, supply chain & legal compliance",
        ],
        "lucky_color": "Charcoal Grey, Navy Blue, Forest Green & Black",
        "lucky_numbers": [8, 4, 6],
        "lucky_gemstone": "Blue Sapphire (Neelam) or Amethyst",
        "lucky_day": "Saturday",
        "ruling_deity": "Lord Shiva & Lord Shani",
        "compatible_rashis": ["Taurus", "Virgo", "Scorpio", "Pisces"],
    },
    {
        "index": 10,
        "name_en": "Aquarius",
        "name_hi": "कुम्भ",
        "name_bn": "কুম্ভ",
        "symbol": "♒",
        "lord": "Saturn",
        "element": "Airy (বায়ু)",
        "modality": "Fixed / Static (স্থির)",
        "polarity": "Masculine / Positive / Odd (পুরুষ / বিষম রাশি)",
        "body_parts": "Ankles, shins, calves, circulatory system, nervous transmission",
        "nature": "Visionary, humanitarian, scientific, unconventional, intellectual, egalitarian",
        "overview": (
            "Ruled by Saturn, Aquarius is the cosmic water-bearer pouring forth streams of innovative "
            "wisdom and universal brotherhood. Moon in Aquarius individuals are futuristic thinkers, deeply "
            "devoted to social progress, scientific advancement, and philosophical inquiry with an independent spirit."
        ),
        "strengths": [
            "Visionary intellect capable of understanding futuristic concepts",
            "Deep humanitarian compassion and dedication to societal upliftment",
            "Unbiased, objective, and democratic interpersonal outlook",
            "Original thinker unaffected by herd mentality or dogmatic traditions",
        ],
        "cautions_and_pitfalls": [
            "Emotional aloofness and treating personal relationships like intellectual formulas",
            "Rebelliousness purely for the thrill of going against the grain",
            "Circulatory sluggishness, varicose veins, and ankle injuries",
            "Stubborn attachment to personal theories despite contrary evidence",
            "Feeling like an alienated outsider, leading to sudden self-isolation",
        ],
        "beneficial_actions_and_remedies": [
            "Balance intellectual detachment with heart-centered emotional presence",
            "Support humanitarian causes, orphanages, or environmental innovations",
            "Chant Hanuman Chalisa or Shani Gayatri Mantra on Saturdays",
            "Donate blue garments, iron tools, or black sesame seeds to the needy",
            "Practice regular ankle rotations and leg elevation for healthy blood circulation",
        ],
        "career_fields": [
            "Scientific research, aerospace, robotics & cutting-edge technology",
            "Astrology, astronomy, philosophy, sociology & occult metaphysics",
            "Humanitarian NGOs, social reform, environmental advocacy & philanthropy",
            "Software architecture, artificial intelligence, UI/UX & telecommunications",
            "Aviation, electronics, innovation lab direction & research",
        ],
        "lucky_color": "Electric Blue, Cyan, Purple & Midnight Navy",
        "lucky_numbers": [8, 7, 4],
        "lucky_gemstone": "Blue Sapphire (Neelam) or Hessonite (Gomed)",
        "lucky_day": "Saturday",
        "ruling_deity": "Lord Shiva & Lord Hanuman",
        "compatible_rashis": ["Gemini", "Libra", "Aries", "Sagittarius"],
    },
    {
        "index": 11,
        "name_en": "Pisces",
        "name_hi": "मीन",
        "name_bn": "মীন",
        "symbol": "♓",
        "lord": "Jupiter",
        "element": "Watery (জল)",
        "modality": "Dual / Common (দ্বিস্বভাব)",
        "polarity": "Feminine / Negative / Even (স্ত্রী / সম রাশি)",
        "body_parts": "Feet, toes, lymphatic system, pineal gland, psychic aura",
        "nature": "Compassionate, spiritual, intuitive, artistic, dreamy, gentle, empathetic",
        "overview": (
            "Ruled by Jupiter, Pisces is the concluding sign of the zodiac, symbolizing spiritual "
            "liberation (Moksha) and universal cosmic oneness. Moon in Pisces creates an oceanic empathy, "
            "luminous artistic imagination, dream telepathy, and an instinctual affinity for divine meditation."
        ),
        "strengths": [
            "Infinite empathy, compassionate healing, and unconditional love",
            "Profound psychic intuition, prophetic dreams, and spiritual vision",
            "Rich creative and artistic imagination in music, poetry, and arts",
            "Ego-free willingness to sacrifice for the well-being of others",
        ],
        "cautions_and_pitfalls": [
            "Escapism, daydreaming, and avoidance of worldly practical realities",
            "Weak personal boundaries leading to being exploited by manipulative people",
            "Prone to mood absorption from negative surroundings like a sponge",
            "Foot problems, bunions, lymphatic stagnation, and water retention",
            "Victim mentality or retreating into fantasy when confronted with conflict",
        ],
        "beneficial_actions_and_remedies": [
            "Establish firm, healthy energetic boundaries with discernment",
            "Feed fish in clean ponds/rivers with small flour balls on Thursdays",
            "Worship Lord Vishnu (`Om Namo Bhagavate Vasudevaya`) on Thursdays",
            "Donate yellow clothes, bananas, books, or honey to spiritual seekers",
            "Channel boundless imagination into tangible arts, music, writing, or meditation",
        ],
        "career_fields": [
            "Spiritual teaching, meditation instruction, yoga & psychic healing",
            "Music composition, poetry, cinematography, acting & fine arts",
            "Psychology, psychiatry, hospice care, rehabilitation & nursing",
            "Oceanography, marine conservation, naval navigation & water sciences",
            "Charitable foundations, ashram management & international welfare",
        ],
        "lucky_color": "Golden Yellow, Sea Green, Aquamarine & Lavender",
        "lucky_numbers": [3, 9, 7],
        "lucky_gemstone": "Yellow Sapphire (Pukhraj) or Natural Aquamarine",
        "lucky_day": "Thursday",
        "ruling_deity": "Lord Vishnu & Lord Dakshinamurthy",
        "compatible_rashis": ["Cancer", "Scorpio", "Taurus", "Capricorn"],
    },
]

NAKSHATRAS_DATA: list[dict[str, Any]] = [
    {"index": 0, "name": "Ashwini", "lord": "Ketu", "rashi_index": 0},
    {"index": 1, "name": "Bharani", "lord": "Venus", "rashi_index": 0},
    {"index": 2, "name": "Krittika", "lord": "Sun", "rashi_index": 0},
    {"index": 3, "name": "Rohini", "lord": "Moon", "rashi_index": 1},
    {"index": 4, "name": "Mrigashira", "lord": "Mars", "rashi_index": 1},
    {"index": 5, "name": "Ardra", "lord": "Rahu", "rashi_index": 2},
    {"index": 6, "name": "Punarvasu", "lord": "Jupiter", "rashi_index": 2},
    {"index": 7, "name": "Pushya", "lord": "Saturn", "rashi_index": 3},
    {"index": 8, "name": "Ashlesha", "lord": "Mercury", "rashi_index": 3},
    {"index": 9, "name": "Magha", "lord": "Ketu", "rashi_index": 4},
    {"index": 10, "name": "Purva Phalguni", "lord": "Venus", "rashi_index": 4},
    {"index": 11, "name": "Uttara Phalguni", "lord": "Sun", "rashi_index": 4},
    {"index": 12, "name": "Hasta", "lord": "Moon", "rashi_index": 5},
    {"index": 13, "name": "Chitra", "lord": "Mars", "rashi_index": 5},
    {"index": 14, "name": "Swati", "lord": "Rahu", "rashi_index": 6},
    {"index": 15, "name": "Vishakha", "lord": "Jupiter", "rashi_index": 6},
    {"index": 16, "name": "Anuradha", "lord": "Saturn", "rashi_index": 7},
    {"index": 17, "name": "Jyeshtha", "lord": "Mercury", "rashi_index": 7},
    {"index": 18, "name": "Mula", "lord": "Ketu", "rashi_index": 8},
    {"index": 19, "name": "Purva Ashadha", "lord": "Venus", "rashi_index": 8},
    {"index": 20, "name": "Uttara Ashadha", "lord": "Sun", "rashi_index": 8},
    {"index": 21, "name": "Shravana", "lord": "Moon", "rashi_index": 9},
    {"index": 22, "name": "Dhanishta", "lord": "Mars", "rashi_index": 9},
    {"index": 23, "name": "Shatabhisha", "lord": "Rahu", "rashi_index": 10},
    {"index": 24, "name": "Purva Bhadrapada", "lord": "Jupiter", "rashi_index": 10},
    {"index": 25, "name": "Uttara Bhadrapada", "lord": "Saturn", "rashi_index": 11},
    {"index": 26, "name": "Revati", "lord": "Mercury", "rashi_index": 11},
]

# Vimshottari dasha years for proportional KP Sub-Lord division
DASHA_LORDS_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}
TOTAL_DASHA_YEARS = 120


def calculate_kp_sub_lord(nakshatra_lord: str, offset_in_nakshatra_deg: float) -> str:
    """Calculates the KP Sub-Lord for any given offset within a Nakshatra (0 to 13.3333°).
    In KP Astrology, each 13°20' nakshatra is subdivided into 9 sub-divisions
    in the proportional order of Vimshottari dasha years starting from the nakshatra lord.
    """
    nak_span_deg = 360.0 / 27.0  # 13.33333333°
    start_idx = DASHA_LORDS_ORDER.index(nakshatra_lord)

    accumulated = 0.0
    for i in range(9):
        current_lord = DASHA_LORDS_ORDER[(start_idx + i) % 9]
        sub_span = (DASHA_YEARS[current_lord] / TOTAL_DASHA_YEARS) * nak_span_deg
        if accumulated <= offset_in_nakshatra_deg <= accumulated + sub_span:
            return current_lord
        accumulated += sub_span

    return nakshatra_lord
