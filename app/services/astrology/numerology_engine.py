"""Vedic, Chaldean, Name, and Mobile Numerology Engine.

Strictly derived from Client Resource Documents:
- NEW NUMRO.docx (Mulank 20-field master profiles, Bhagyank, Year forecast)
- vedic numero.docx (3x3 Lo Shu Grid, Planes, Raj Yogas, Digit Repetitions, Missing Number remedies, Numerology Dasha /45 formula, 18 Oct Friendship Table)
- name sound.docx (Chaldean values 1-8, 26 letter profiles & directions)
- Name Numerology/01.pdf (193 pp Master Encyclopedia of 1-100 Compound Name Numbers, Syllable phonetics, 4-tier harmony)
- mobile number (1).docx & Mobile Number Numerology/01.pdf, 02.pdf, 03.pdf (King number table, 60%/40% pair dominance, 3x3 Sepharial mobile grid, 16 L-shapes, compound preferences, avoid list, remedial injections)
"""

import math
import re
from datetime import date, datetime, timedelta
from typing import Any

from app.schemas.numerology import (
    BhagyankProfile,
    DigitRepetitionItem,
    LetterSoundProfile,
    LoShuGridCell,
    LoShuPlane,
    MissingNumberRemedy,
    MobileAnalysisResponse,
    MobileConjunctionPair,
    MobileLShape,
    MulankProfile,
    NameAnalysisResponse,
    NumerologyCalculateResponse,
    NumerologyDashaPeriod,
    RajYogaItem,
)

# ---------------------------------------------------------------------------
# Chaldean Alphabet Mapping (1-8; 9 is sacred & unassigned to single letters)
# ---------------------------------------------------------------------------
CHALDEAN_MAP: dict[str, int] = {
    "A": 1, "I": 1, "J": 1, "Q": 1, "Y": 1,
    "B": 2, "K": 2, "R": 2,
    "C": 3, "G": 3, "L": 3, "S": 3,
    "D": 4, "M": 4, "T": 4,
    "E": 5, "H": 5, "N": 5, "X": 5,
    "U": 6, "V": 6, "W": 6,
    "O": 7, "Z": 7,
    "F": 8, "P": 8,
}

# ---------------------------------------------------------------------------
# 18 Oct Authoritative Friendship Table (§3.5 in RESOURCES-MASTER.md)
# ---------------------------------------------------------------------------
# Score meanings: "friend" -> Favorable, "neutral" -> Neutral, "enemy" -> Unfavorable
FRIENDSHIP_TABLE: dict[int, dict[str, list[int]]] = {
    1: {"friends": [1, 2, 3, 5, 9], "neutrals": [4, 6, 7], "enemies": [8]},
    2: {"friends": [1, 3, 5], "neutrals": [2, 6, 7], "enemies": [4, 8, 9]},
    3: {"friends": [1, 2, 3, 5, 7], "neutrals": [4, 8, 9], "enemies": [6]},
    4: {"friends": [1, 6, 7], "neutrals": [3, 5], "enemies": [2, 4, 8, 9]},
    5: {"friends": [1, 2, 3, 5, 6], "neutrals": [4, 7, 8, 9], "enemies": []},  # Mercury has no enemies
    6: {"friends": [4, 5, 6, 7], "neutrals": [1, 2, 8, 9], "enemies": [3]},
    7: {"friends": [1, 4, 5, 6], "neutrals": [2, 3, 7, 8, 9], "enemies": []},
    8: {"friends": [3, 5, 6], "neutrals": [7, 9], "enemies": [1, 2, 4, 8]},
    9: {"friends": [1, 3, 5], "neutrals": [6, 7, 8, 9], "enemies": [2, 4]},  # 9 -> 5 is friend, but 9 -> 4/2 enemy
}

# ---------------------------------------------------------------------------
# 26 Letters Sound Profiles from `name sound.docx`
# ---------------------------------------------------------------------------
LETTER_PROFILES: dict[str, dict[str, str]] = {
    "A": {"element": "Air/Fire", "vibration": "Initiator, courageous, independent leader.", "health": "Headaches, eye strain, high blood pressure.", "direction": "East"},
    "B": {"element": "Water", "vibration": "Cooperative, sensitive, peaceful mediator.", "health": "Digestive weakness, emotional mood swings.", "direction": "North-West"},
    "C": {"element": "Fire", "vibration": "Creative, expressive, enthusiastic communicator.", "health": "Throat issues, nervous exhaustion.", "direction": "North-East"},
    "D": {"element": "Earth", "vibration": "Practical, systematic, steadfast worker.", "health": "Bone density, rheumatism, joint stiffness.", "direction": "South-West"},
    "E": {"element": "Mercury/Air", "vibration": "Versatile, dynamic, freedom lover, quick learner.", "health": "Respiratory, nervous system agitation.", "direction": "North"},
    "F": {"element": "Venus/Earth", "vibration": "Nurturing, responsible, family and community pillar.", "health": "Heart, chest congestion, circulation.", "direction": "South-East"},
    "G": {"element": "Ether/Fire", "vibration": "Intellectual, mystical, introspective seeker.", "health": "Melancholy, insomnia, mental fatigue.", "direction": "North-East"},
    "H": {"element": "Earth", "vibration": "Material ambition, self-reliant, executive power.", "health": "Stomach acidity, stress-related ulcers.", "direction": "South"},
    "I": {"element": "Fire", "vibration": "Compassionate, idealistic, artistic inspiration.", "health": "Sensory overload, blood circulation.", "direction": "East"},
    "J": {"element": "Fire/Air", "vibration": "Self-motivated, ingenious pioneer, ambitious.", "health": "Spinal tension, dental sensitivity.", "direction": "East"},
    "K": {"element": "Water/Air", "vibration": "Intuitive, energetic, nervous drive, charismatic.", "health": "Nervous anxiety, glandular imbalance.", "direction": "North-West"},
    "L": {"element": "Air", "vibration": "Diplomatic, intellectual, charitable, eloquent.", "health": "Kidney balance, throat fatigue.", "direction": "North-East"},
    "M": {"element": "Earth", "vibration": "Domestic stability, hard-working, disciplined.", "health": "Digestive sluggishness, lower back pain.", "direction": "South-West"},
    "N": {"element": "Air", "vibration": "Sensory versatility, communicative, curious.", "health": "Nervous twitching, insomnia, lung sensitivity.", "direction": "North"},
    "O": {"element": "Water/Ether", "vibration": "Dutiful, moral conviction, protective, warm.", "health": "Heart palpitations, emotional stress.", "direction": "West"},
    "P": {"element": "Earth/Fire", "vibration": "Philosophical, secluded intellect, keen authority.", "health": "Headaches, skin dryness.", "direction": "South"},
    "Q": {"element": "Water/Air", "vibration": "Original thinker, mysterious attractor of wealth.", "health": "Fluctuating vitality, lymphatic sensitivity.", "direction": "North"},
    "R": {"element": "Fire", "vibration": "Tireless worker, passionate, humanitarian drive.", "health": "Ulcers, anger-induced blood pressure.", "direction": "South"},
    "S": {"element": "Fire/Air", "vibration": "Magnetic, ambitious, emotional intensity, leadership.", "health": "Nervous tension, spinal strain.", "direction": "East"},
    "T": {"element": "Air/Water", "vibration": "Peaceful advisor, sensitive, spiritual inclination.", "health": "Thyroid, emotional stress, fluid retention.", "direction": "West"},
    "U": {"element": "Water", "vibration": "Generous, dramatic, lucky in partnerships.", "health": "Liver sluggishness, throat irritation.", "direction": "South-East"},
    "V": {"element": "Earth/Air", "vibration": "Visionary builder, determined, unwavering fortitude.", "health": "Circulation, muscle cramps.", "direction": "South-East"},
    "W": {"element": "Air", "vibration": "Multi-talented, expressive adventurer, resilient.", "health": "Respiratory fatigue, nervous restlessness.", "direction": "North-West"},
    "X": {"element": "Mercury/Air", "vibration": "High sensory perception, magnetic, fast-paced.", "health": "Sexual vitality fluctuations, back stiffness.", "direction": "West"},
    "Y": {"element": "Water/Fire", "vibration": "Independent, dignified seeker, loves solitude.", "health": "Mental exhaustion, arthritis.", "direction": "West"},
    "Z": {"element": "Ether/Air", "vibration": "Hopeful, resilient, diplomatic achiever.", "health": "Glandular vitality, nervous tension.", "direction": "West"},
}

# ---------------------------------------------------------------------------
# 1-100 Compound Name Numbers Catalog from `Name Numerology/01.pdf`
# ---------------------------------------------------------------------------
COMPOUND_NAMES: dict[int, dict[str, Any]] = {
    10: {"name": "The Wheel of Fortune (Sun)", "quality": "Favorable", "meaning": "Symbolizes honor, faith, self-confidence, and creative solar force. Rises to distinction."},
    11: {"name": "Hidden Peril / Clashing Wills", "quality": "Mixed", "meaning": "Double Sun vibration. High spiritual intuition, but vulnerable to deception and hidden adversaries."},
    12: {"name": "The Sacrifice / Anxious Intellect", "quality": "Unfavorable", "meaning": "Sacrifices made for ungrateful others. Deep mind but frequent anxieties and self-doubt."},
    13: {"name": "The Transformation / Master Builder", "quality": "Mixed", "meaning": "Sudden upheaval followed by rebirth. Practical, hardworking, but requires disciplined focus."},
    14: {"name": "The Magnetic Movement", "quality": "Favorable", "meaning": "Movement, commerce, travel, and financial gains through risk. Must guard against rash speculation."},
    15: {"name": "The Magician (Venus)", "quality": "Favorable", "meaning": "Charismatic magnetism, literary eloquence, love of luxuries, and substantial financial blessings."},
    16: {"name": "The Shattered Citadel / Tower", "quality": "Unfavorable", "meaning": "Vulnerable to unexpected falls from position, accidents, and broken plans. Requires caution."},
    17: {"name": "The Star of the Magi", "quality": "Favorable", "meaning": "Immortalized name, peace, spiritual rise, and steadfast victory over worldly obstacles."},
    18: {"name": "Spiritual Conflict / Bitter Deceit", "quality": "Unfavorable", "meaning": "Family disputes, broken friendships, treacherous associates, and internal unrest."},
    19: {"name": "The Prince of Heaven (Morning Sun)", "quality": "Extremely Favorable", "meaning": "Continuous expansion, honor, regal prestige, triumphant victory over adversity."},
    20: {"name": "The Awakening / Kettle Drums", "quality": "Mixed", "meaning": "Calls to higher purpose. Great plans delayed; requires steadfast spiritual faith to manifest."},
    21: {"name": "The Crown of the Magi", "quality": "Extremely Favorable", "meaning": "Final advancement, universal acclaim, and victorious emergence from prolonged struggles."},
    22: {"name": "The Master Architect", "quality": "Mixed", "meaning": "Colossal vision; if misdirected leads to delusion, but if disciplined creates lasting institutions."},
    23: {"name": "The Royal Star of the Lion", "quality": "Extremely Favorable", "meaning": "Universal success, divine protection, royal patronage, and high fortune in public life."},
    24: {"name": "The Love & Wealth Matrix", "quality": "Favorable", "meaning": "Assistance from influential people of high status, harmonious domestic life, and steady wealth."},
    25: {"name": "Wisdom Through Experience", "quality": "Favorable", "meaning": "Spiritual strength gained through early trials, success in travel, philosophy, and occult science."},
    26: {"name": "Partnership Reversal", "quality": "Unfavorable", "meaning": "Deceit from associates, litigation risks, financial losses in joint ventures; caution required."},
    27: {"name": "The Sceptre of Command", "quality": "Favorable", "meaning": "Courage, executive command, victory in literature and state affairs, independent authority."},
    28: {"name": "The Fall from Grace", "quality": "Extremely Unfavorable", "meaning": "Early brilliance followed by severe downfall, legal pitfalls, broken trust. Ruled by Moon & Saturn."},
    29: {"name": "Uncertainty & Deception", "quality": "Unfavorable", "meaning": "Emotional vulnerabilities, betrayal by partners, acute domestic heartache."},
    30: {"name": "The Solitary Thinker", "quality": "Favorable", "meaning": "Intellectual supremacy, philosophical detachment, indifference to petty material gains."},
    31: {"name": "The Practical Master", "quality": "Favorable", "meaning": "Sharp professional acumen, technical expertise, wise counsel, though prone to emotional solitude."},
    32: {"name": "The Magnetic Word", "quality": "Favorable", "meaning": "Commercial popularity, persuasive salesmanship, international links, rapid wealth accumulation."},
    33: {"name": "The Master Teacher (Avatar)", "quality": "Extremely Favorable", "meaning": "Universal compassion, creative genius, spiritual healing, and prosperity through service."},
    34: {"name": "Scientific Intelligence", "quality": "Favorable", "meaning": "Sharp mind, inventive genius, material rewards gained through technical discipline."},
    35: {"name": "Commercial Speculation", "quality": "Mixed", "meaning": "Rapid financial fluctuations; requires strict adherence to ethical investments."},
    36: {"name": "The Self-Made Authority", "quality": "Favorable", "meaning": "Tireless endeavor leading to high societal respect, strict adherence to personal principles."},
    37: {"name": "The Sceptre of Royalty", "quality": "Extremely Favorable", "meaning": "High charismatic leadership, prosperous partnerships, magnetic public adoration."},
    38: {"name": "The Peaceful Negotiator", "quality": "Favorable", "meaning": "Mediator in property and high-stakes affairs, peaceful resolution, steady land wealth."},
    39: {"name": "The Dual Visionary", "quality": "Mixed", "meaning": "Show-off tendencies, dramatic highs and sudden lows; requires grounded authenticity."},
    40: {"name": "The Philosophical Hermit", "quality": "Mixed", "meaning": "Deep solitary intellect, financial delays, spiritual maturity over worldly luxury."},
    41: {"name": "Dynamic Leadership", "quality": "Favorable", "meaning": "High energy, executive authority, successful enterprise, respected public figure."},
    42: {"name": "Matrimonial Bliss", "quality": "Favorable", "meaning": "Loving marriage, domestic elegance, abundant comfort, and thriving artistic taste."},
    43: {"name": "The Strategic Mind", "quality": "Mixed", "meaning": "Clever, equal friends and foes; requires ethical integrity to sustain conquests."},
    44: {"name": "The Heavy Labor", "quality": "Unfavorable", "meaning": "Relentless struggle, chronic delays, severe bodily fatigue, and heavy burdens."},
    45: {"name": "The Restless Traveler", "quality": "Mixed", "meaning": "Impulsive changes, judicial entanglements; requires grounding stability."},
    46: {"name": "The Crown of Authority", "quality": "Extremely Favorable", "meaning": "Commanding leadership, immense personal integrity, respected professor/statesman."},
    47: {"name": "The Honest Luminary", "quality": "Favorable", "meaning": "High integrity, brilliant mind, balanced Rahu-Ketu synthesis, respected advisor."},
    48: {"name": "Physical Affliction Risk", "quality": "Unfavorable", "meaning": "Blood disorders, marital coldness, deficiency of bedroom comfort, chronic fatigue."},
    49: {"name": "The Daring Defender", "quality": "Mixed", "meaning": "Uniform/military success, high-risk undertakings, bold courage."},
    50: {"name": "The Mercury Gateway", "quality": "Favorable", "meaning": "Agile communication, commercial balance, intellectual versatility, rapid money flow."},
    51: {"name": "The Solar Honor", "quality": "Favorable", "meaning": "Elevates father and family prestige, swift financial gains with moderate physical toil."},
    52: {"name": "The Healer's Grace (Shaffa)", "quality": "Favorable", "meaning": "Healing hands, occult intuition, medical success, overseas achievements."},
    53: {"name": "Success in Exile", "quality": "Mixed", "meaning": "Progress achieved far away from birthplace, strict upbringing, tight cash flow."},
    54: {"name": "The Restrictive Path", "quality": "Unfavorable", "meaning": "Legal hindrances, medical expenses, feelings of being hemmed in by fate."},
    55: {"name": "Universal Energy (Prana)", "quality": "Extremely Favorable", "meaning": "Supreme occult mastery, cosmic effulgence, scientific breakthroughs, warrior victory."},
    56: {"name": "Commercial Integrity", "quality": "Favorable", "meaning": "Prosperous business acumen, ethical commerce, respected communal elder."},
    57: {"name": "The Master Orator", "quality": "Extremely Favorable", "meaning": "Supreme eloquence, author, philosopher, vital vibration for astrologers and public guides."},
    58: {"name": "Financial Calculation", "quality": "Mixed", "meaning": "Deals in massive figures, but payments get locked; calculated intellect."},
    59: {"name": "The Sharp Analyst", "quality": "Mixed", "meaning": "Scientific brilliance, but sharp tongue alienates close family members."},
    60: {"name": "The Artistic Treasury", "quality": "Favorable", "meaning": "Luxurious comfort, harmonious partnerships, creative refinement, social joy."},
    61: {"name": "Spouse Health Sensitivity", "quality": "Unfavorable", "meaning": "Domestic stress, confined income while holding name, marital friction."},
    62: {"name": "The Educational Hurdle", "quality": "Unfavorable", "meaning": "Interrupted studies, domestic tension with in-laws, emotional distraction."},
    63: {"name": "The Rigid Academic", "quality": "Mixed", "meaning": "High moral codes, profound wisdom, but struggles with public presentation."},
    64: {"name": "The Victorious Strategist", "quality": "Favorable", "meaning": "Sharp acumen, triumphs over competitors, establishes formidable enterprise."},
    65: {"name": "The Reticent Merchant", "quality": "Favorable", "meaning": "Prosperous merchant, charitable, but hesitates to collect owed debts."},
    66: {"name": "The Cosmic Love", "quality": "Favorable", "meaning": "Supreme occult benevolence, higher wisdom, artistic triumph, magnetic warmth."},
    67: {"name": "The Romantic Chord", "quality": "Mixed", "meaning": "Artistic musical flair, romantic affairs, but marital volatility."},
    68: {"name": "Ophthalmic Sensitivity", "quality": "Unfavorable", "meaning": "Eye strain, physical organ sensitivity, stubborn disputes."},
    69: {"name": "The Creative Coordinator", "quality": "Favorable", "meaning": "Event management, strategic design, seamless coordination with opposite gender."},
    70: {"name": "The Solitary Mystic", "quality": "Favorable", "meaning": "Inner awakening, spiritual peace, detachment from shallow commercial pursuits."},
    71: {"name": "The Corporate Sovereign", "quality": "Favorable", "meaning": "MNC/Govt success, continuous cash flow, work-from-home comfort, prominent circle."},
    72: {"name": "The Rheumatic Warning", "quality": "Unfavorable", "meaning": "Joint and knee sensitivity (Vaat dosha), career fluctuations, emotional strain."},
    73: {"name": "Divine Wisdom (Ketu + Jupiter)", "quality": "Extremely Favorable", "meaning": "Saintly authority, pure-hearted conduct, blessed by teachers, divine insight."},
    74: {"name": "The Technical Luminary", "quality": "Favorable", "meaning": "Engineering excellence, unwavering integrity, steadfast adherence to truth."},
    75: {"name": "The Enlightened Counselor", "quality": "Extremely Favorable", "meaning": "Master teacher, supreme communication, public advisor, blessed consultancy."},
    76: {"name": "The Artistic Heartbreak", "quality": "Mixed", "meaning": "Refined music lover, but sensitive to emotional disappointments in love."},
    77: {"name": "The Mystic Intuitive", "quality": "Favorable", "meaning": "Deep intuition, social goodwill, psychological and spiritual insight."},
    78: {"name": "The Master Healer", "quality": "Extremely Favorable", "meaning": "Reiki and meditation master, solves crises through personal psychic willpower."},
    79: {"name": "Success Through Independence", "quality": "Favorable", "meaning": "Triumphs after separating from paternal shadow, self-made prominence."},
    80: {"name": "The Saturnian Sovereign", "quality": "Mixed", "meaning": "Heavy administrative burdens, unyielding discipline, slow and massive ascent."},
    81: {"name": "Father-Son Friction", "quality": "Unfavorable", "meaning": "Government regulatory scrutiny, frequent vocational changes, paternal clashes."},
    82: {"name": "The Resilient Endurer", "quality": "Mixed", "meaning": "Iron willpower, high wealth, but carries heavy trauma and accident alerts."},
    83: {"name": "The Real Estate Titan", "quality": "Favorable", "meaning": "Command over land and properties, counselor in territorial settlements."},
    84: {"name": "Blood Disorder Alert", "quality": "Unfavorable", "meaning": "Severe physiological sensitivity, lack of sensual peace, incurable fatigue."},
    85: {"name": "The Macro Financier", "quality": "Mixed", "meaning": "Controls vast fiscal sums, but payments experience protracted lockups."},
    86: {"name": "The Single-Minded Judge", "quality": "Mixed", "meaning": "Rigid sense of justice, eye sensitivity, uncompromising discipline."},
    87: {"name": "The Altruistic Sage", "quality": "Favorable", "meaning": "Pure selflessness, psychic healing, respected advisor across communities."},
    88: {"name": "The Saturnian Crucible", "quality": "Unfavorable", "meaning": "Prolonged trials, severe obstacles, relentless delays; requires immense fortitude."},
    89: {"name": "The Fiery Reformer", "quality": "Mixed", "meaning": "Combative debates, rigid principles, prone to late-life muscular strain."},
    90: {"name": "The Humanitarian Commander", "quality": "Favorable", "meaning": "Command over large groups, philanthropic projects, victorious leadership."},
    91: {"name": "Mars and Sun (Fiery Drive)", "quality": "Extremely Favorable", "meaning": "Fierce executive drive, administrative triumph, supreme willpower and command."},
    92: {"name": "Emotional Vulnerability", "quality": "Unfavorable", "meaning": "Ego friction in relationships, financial volatility, domestic sensitivity."},
    93: {"name": "The Grand Orator", "quality": "Favorable", "meaning": "Dramatically persuasive, influential in academia, bold theatrical presence."},
    94: {"name": "The Daring Vanguard", "quality": "Mixed", "meaning": "Unconventional occupations, fearless risk-taking, uniform/security roles."},
    95: {"name": "The Sharp Scientist", "quality": "Mixed", "meaning": "Commercial and technical intellect, but critical speech alienates allies."},
    96: {"name": "The Diplomatic Director", "quality": "Favorable", "meaning": "Strategic management, cross-gender collaboration, creative enterprises."},
    97: {"name": "The Independent Pioneer", "quality": "Favorable", "meaning": "Flourishes away from birthplace, self-made authority, spiritual clarity."},
    98: {"name": "The Relentless Debater", "quality": "Mixed", "meaning": "Unyielding arguments, principle-driven, prone to chronic health complaints."},
    99: {"name": "The Fiery Sovereign", "quality": "Mixed", "meaning": "Colossal energy, quick temper, debt and blood alerts; requires calm channel."},
    100: {"name": "Sun & The Infinite Void", "quality": "Extremely Favorable", "meaning": "Pure solar radiance, divine armor against enemies, cosmic fortune if righteous."},
}

# ---------------------------------------------------------------------------
# Mulank (1-9) Master 20-Field Profiles from `new-numro.txt`
# ---------------------------------------------------------------------------
MULANK_MASTER: dict[int, dict[str, Any]] = {
    1: {
        "planet": "Sun (সূর্য)",
        "planet_hi": "सूर्य",
        "deity": "Lord Surya (সূর্য দেব)",
        "metal": "Gold, Copper (স্বর্ণ, তামা)",
        "colors": ["Brown", "Yellow", "Red", "Golden"],
        "unlucky_colors": ["Black (কালো)"],
        "direction": "East (পূর্ব)",
        "lucky_numbers": [1, 2, 3, 4, 5, 7, 9],
        "unlucky_numbers": [6, 8],
        "beej_mantra": "ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः",
        "jap_count": 6000,
        "gemstone": "Ruby (চুনি / মানিক্য)",
        "lucky_days": ["Sunday", "Thursday", "Monday"],
        "lucky_months": ["January", "March", "May", "July", "October"],
        "grains_daan": "গম, গুড়, তামা, লাল বস্ত্র, লাল ফুল ও রক্তচন্দন",
        "health_traits": "রক্তচাপ, হৃদরোগ, চক্ষু পীড়া, পিত্ত বিকার এবং শিরঃপীড়ায় সতর্কতা প্রয়োজন।",
        "profession": "প্রশাসনিক সেবা (IAS/IPS), সরকার, ম্যানেজমেন্ট, প্রযুক্তি, রাজনীতি ও শীর্ষ নেতৃত্ব।",
    },
    2: {
        "planet": "Moon (চন্দ্র)",
        "planet_hi": "चंद्रमा",
        "deity": "Lord Shiva (ভগবান শিব)",
        "metal": "Silver, White Bronze (রূপা, শ্বেত কাঁসা)",
        "colors": ["White", "Cream", "Light Green"],
        "unlucky_colors": ["Dark Red", "Black"],
        "direction": "North-West (বায়ু কোণ / উত্তর-পশ্চিম)",
        "lucky_numbers": [1, 3, 5],
        "unlucky_numbers": [4, 8, 9],
        "beej_mantra": "ॐ श्रां श्रीं श्रौं सः चंद्रमसे नमः",
        "jap_count": 11000,
        "gemstone": "Pearl (মুক্তা) বা Moonstone",
        "lucky_days": ["Monday", "Friday", "Sunday"],
        "lucky_months": ["February", "April", "June", "November"],
        "grains_daan": "চাল, দুধ, দই, চিনি, শ্বেত বস্ত্র, কর্পূর ও রূপা",
        "health_traits": "মানসিক অস্থিরতা, বিষণ্নতা, পেটের সমস্যা, রক্তচাপ ও জলবাহিত রোগে সতর্কতা।",
        "profession": "মনোবিজ্ঞান, সঙ্গীত, শিল্প, দুগ্ধ ও পানীয় বাণিজ্য, নার্সিং, মানবসম্পদ ও পরামর্শদান।",
    },
    3: {
        "planet": "Jupiter (বৃহস্পতি / গুরু)",
        "planet_hi": "बृहस्पति",
        "deity": "Lord Vishnu / Brihaspati (ভগবান বিষ্ণু / গুরু)",
        "metal": "Gold, Brass (স্বর্ণ, পিতল)",
        "colors": ["Yellow", "Golden", "Amber", "Pink"],
        "unlucky_colors": ["Dark Blue", "Black"],
        "direction": "North-East (ঈশান কোণ / উত্তর-পূর্ব)",
        "lucky_numbers": [1, 2, 3, 5, 7],
        "unlucky_numbers": [6],
        "beej_mantra": "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",
        "jap_count": 19000,
        "gemstone": "Yellow Sapphire (পোখরাজ) বা Citrine",
        "lucky_days": ["Thursday", "Tuesday", "Sunday"],
        "lucky_months": ["March", "June", "September", "December"],
        "grains_daan": "ছোলা ডাল, হলুদ বস্ত্র, হলুদ ফুল, হলুদ, কাঁচা সোনা ও ধর্মীয় গ্রন্থ",
        "health_traits": "লিভার, বহুমূত্র (ডায়াবেটিস), স্থূলতা, কোলেস্টেরল ও রক্ত সঞ্চালনে সতর্কতা।",
        "profession": "আইন, বিচারক, অধ্যাপনা, জ্যোতিষ, ধর্মীয় সংগঠন, ব্যাংকিং, ফিনান্স ও উচ্চপদস্থ উপদেষ্টা।",
    },
    4: {
        "planet": "Rahu (রাহু)",
        "planet_hi": "राहु",
        "deity": "Lord Bhairav / Goddess Saraswati (কালভৈরব / মা সরস্বতী)",
        "metal": "Alloy, Lead (মিশ্র ধাতু, সিসা)",
        "colors": ["Electric Blue", "Grey", "Khaki"],
        "unlucky_colors": ["Black", "Red"],
        "direction": "South-West (নৈঋত কোণ / দক্ষিণ-পশ্চিম)",
        "lucky_numbers": [1, 6, 7],
        "unlucky_numbers": [2, 4, 8, 9],
        "beej_mantra": "ॐ भ्रां भ्रीं भ्रौं सः राहवे नमः",
        "jap_count": 18000,
        "gemstone": "Hessonite Garnet (গোমেদ)",
        "lucky_days": ["Saturday", "Sunday", "Wednesday"],
        "lucky_months": ["April", "August", "October"],
        "grains_daan": "উড়দ ডাল, কালো তিল, কম্বল, লোহার পাত্র ও নীলাভ বস্ত্র",
        "health_traits": "হঠাৎ আঘাত, স্নায়বিক দৌর্বল্য, অনিদ্রা, মাথা ঘোরা ও অজ্ঞাত রোগ।",
        "profession": "আইটি, সফটওয়্যার, গবেষণা, মহাকাশ বিজ্ঞান, শেয়ার বাজার, গোয়েন্দা সংস্থা ও ইলেকট্রনিক্স।",
    },
    5: {
        "planet": "Mercury (বুধ)",
        "planet_hi": "बुध",
        "deity": "Lord Ganesha / Vishnu (ভগবান গণেশ / নারায়ণ)",
        "metal": "Bronze, Bell Metal (কাঁসা, ব্রোঞ্জ)",
        "colors": ["Green", "Emerald", "Turquoise"],
        "unlucky_colors": ["Dark Red"],
        "direction": "North (উত্তর)",
        "lucky_numbers": [1, 2, 3, 5, 6],
        "unlucky_numbers": [],  # Mercury has no direct enemy
        "beej_mantra": "ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः",
        "jap_count": 9000,
        "gemstone": "Emerald (পান্না) বা Peridot",
        "lucky_days": ["Wednesday", "Friday", "Thursday"],
        "lucky_months": ["May", "June", "September"],
        "grains_daan": "মুগ ডাল, সবুজ বস্ত্র, ঘাস, ব্রোঞ্জের পাত্র ও সবুজ ফল",
        "health_traits": "স্নায়বিক চাপ, ত্বকের সমস্যা, তোতলামি, এলার্জি ও শ্বাসযন্ত্রীয় সংবেদনশীলতা।",
        "profession": "ব্যবসা, সাংবাদিকতা, জনসংযোগ, সিএ, ব্যাংকিং, ডেটা এনালিটিক্স ও আন্তর্জাতিক বাণিজ্য।",
    },
    6: {
        "planet": "Venus (শুক্র)",
        "planet_hi": "शुक्र",
        "deity": "Goddess Mahalakshmi (মা মহালক্ষ্মী)",
        "metal": "Silver, Platinum, White Gold (রূপা, প্লাটিনাম)",
        "colors": ["White", "Silver", "Pink", "Light Blue"],
        "unlucky_colors": ["Yellow", "Orange"],
        "direction": "South-East (অগ্নি কোণ / দক্ষিণ-পূর্ব)",
        "lucky_numbers": [4, 5, 6, 7],
        "unlucky_numbers": [3],
        "beej_mantra": "ॐ द्रां द्रीं द्रौं सः शुक्राय नमः",
        "jap_count": 16000,
        "gemstone": "Diamond (হীরা) বা White Zircon / Opal",
        "lucky_days": ["Friday", "Wednesday", "Saturday"],
        "lucky_months": ["May", "June", "October", "December"],
        "grains_daan": "চাল, সুজি, খাঁটি ঘি, সাদা চন্দন, সুগন্ধি আতর ও শ্বেত বস্ত্র",
        "health_traits": "ডায়াবেটিস, প্রজনন গ্রন্থি, কিডনি, মূত্রাশয় ও গলগণ্ডের সমস্যায় সতর্কতা।",
        "profession": "মিডিয়া, ফ্যাশন, সিনেমা, হোটেল, বিলাসবহুল দ্রব্য, প্রসাধন ও শিল্পকলা।",
    },
    7: {
        "planet": "Ketu (কেতু)",
        "planet_hi": "केतु",
        "deity": "Lord Ganesha / Matsya Avatar (ভগবান গণেশ / মৎস্য অবতার)",
        "metal": "Iron, Mixed Metal (লোহা, পঞ্চধাতু)",
        "colors": ["Light Yellow", "White", "Grey", "Smoky"],
        "unlucky_colors": ["Dark Red"],
        "direction": "North-East (ঈশান / কেন্দ্র)",
        "lucky_numbers": [1, 4, 5, 6],
        "unlucky_numbers": [],
        "beej_mantra": "ॐ स्रां स्रीं स्रौं सः केतवे नमः",
        "jap_count": 17000,
        "gemstone": "Cat's Eye (বৈদূর্যমণি / লহসুনিয়া)",
        "lucky_days": ["Sunday", "Tuesday", "Thursday"],
        "lucky_months": ["July", "August", "November"],
        "grains_daan": "সাত রকমের শস্য (সপ্তধান্য), কালো-সাদা কম্বল ও তিল",
        "health_traits": "জয়েন্ট পেইন, চর্মরোগ, পেটের কৃমি, প্রস্রাবের জটিলতা ও মানসিক একাকীত্ব।",
        "profession": "আধ্যাত্মিক সাধনা, হিলিং, গবেষণা, জ্যোতিষ, দর্শন, অনুবাদ ও সমাজ সংস্কার।",
    },
    8: {
        "planet": "Saturn (শনি)",
        "planet_hi": "शनि",
        "deity": "Lord Hanuman / Shani Dev (হনুমান জি / শনি দেব)",
        "metal": "Iron, Steel (লোহা, ইস্পাত)",
        "colors": ["Dark Blue", "Black", "Dark Brown"],
        "unlucky_colors": ["Red", "Bright Yellow"],
        "direction": "West (পশ্চিম)",
        "lucky_numbers": [3, 5, 6],
        "unlucky_numbers": [1, 2, 4, 8],
        "beej_mantra": "ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः",
        "jap_count": 23000,
        "gemstone": "Blue Sapphire (নীলা) বা Amethyst",
        "lucky_days": ["Saturday", "Wednesday", "Friday"],
        "lucky_months": ["January", "April", "August", "September"],
        "grains_daan": "কালো তিল, সরিষার তেল, লোহা, কালো জুতো, চামড়ার সামগ্রী ও কালো অড়হর",
        "health_traits": "বাত, গেঁটে বাত, দাঁতের রোগ, পক্ষাঘাত ও দীর্ঘস্থায়ী ক্রনিক ব্যাধি।",
        "profession": "খনন, ভারী শিল্প, রিয়েল এস্টেট, আইন, তেল ও পেট্রোলিয়াম, কৃষি ও সিভিল কনস্ট্রাকশন।",
    },
    9: {
        "planet": "Mars (মঙ্গল)",
        "planet_hi": "मंगल",
        "deity": "Lord Hanuman / Kartikeya (হনুমান জি / কার্তিকেয়)",
        "metal": "Copper, Red Gold (তামা, পঞ্চধাতু)",
        "colors": ["Red", "Crimson", "Scarlet", "Orange"],
        "unlucky_colors": ["Green", "Black"],
        "direction": "South (দক্ষিণ)",
        "lucky_numbers": [1, 3, 5],
        "unlucky_numbers": [2, 4],
        "beej_mantra": "ॐ क्रां क्रीं क्रौं सः भौमाय नमः",
        "jap_count": 10000,
        "gemstone": "Red Coral (রক্ত প্রবাল)",
        "lucky_days": ["Tuesday", "Thursday", "Sunday"],
        "lucky_months": ["March", "June", "September", "November"],
        "grains_daan": "মসুর ডাল, গুড়, তামা, লাল মিষ্টি ও সিঁদুর",
        "health_traits": "উচ্চ রক্তচাপ, ফোড়া, অস্ত্রোপচার, রক্ত সংক্রান্ত ব্যাধি ও পোড়া আঘাত।",
        "profession": "সেনাবাহিনী, পুলিশ, শল্যচিকিৎসক (সার্জন), ক্রীড়াবিদ, অগ্নিনির্বাপক ও প্রকৌশলী।",
    },
}

# ---------------------------------------------------------------------------
# Bhagyank (1-9) Master Profiles
# ---------------------------------------------------------------------------
BHAGYANK_MASTER: dict[int, dict[str, Any]] = {
    1: {
        "planet": "Sun (সূর্য)",
        "summary": "জীবনের মূল লক্ষ্য নেতৃত্ব প্রদান ও স্বয়ংসম্পূর্ণ হওয়া। অধীনস্থ না থেকে অগ্রণী ভূমিকা পালন করাই আপনার ভবিতব্য।",
        "strengths": ["দৃঢ় ইচ্ছাশক্তি", "অটল আত্মমর্যাদা", "দূরদর্শিতা", "মৌলিক উদ্ভাবন"],
        "karmic_lessons": "অন্যের মতামতের প্রতি শ্রদ্ধা রাখা ও অহংকার নিয়ন্ত্রণ করা শিখতে হবে।",
    },
    2: {
        "planet": "Moon (চন্দ্র)",
        "summary": "জীবনের লক্ষ্য শান্তি, সৌহার্দ্য ও আধ্যাত্মিক সমন্বয় স্থাপন করা। কূটনৈতিক দক্ষতায় বিশ্বকে একসূত্রে বাঁধা।",
        "strengths": ["উচ্চ অনুভূতিশীলতা", "সহমর্মিতা", "কূটনৈতিক পারদর্শিতা", "সহযোগিতামূলক মনোভাব"],
        "karmic_lessons": "অতি-সংবেদনশীলতা পরিহার করে আত্মবিশ্বাসকে বাস্তবমুখী করা প্রয়োজন।",
    },
    3: {
        "planet": "Jupiter (বৃহস্পতি)",
        "summary": "জ্ঞান বিতরণ, শিক্ষকতা ও সমাজকে আলোকবর্তিকা প্রদান। আধ্যাত্মিক ও মানসিক সমৃদ্ধি বিস্তার।",
        "strengths": ["প্রচণ্ড আশাবাদ", "বক্তৃতা ও বাচনভঙ্গি", "দার্শনিক প্রজ্ঞা", "সৃজনশীল প্রকাশ"],
        "karmic_lessons": "লক্ষ্যে স্থির থাকা এবং বহুমুখী উৎসাহের মাঝে শক্তি অপচয় না করা।",
    },
    4: {
        "planet": "Rahu (রাহু)",
        "summary": "নতুন কাঠামো নির্মাণ, প্রচলিত বাঁধন ভেঙে প্রযুক্তিমুখী রূপান্তর এবং শৃঙ্খলাবদ্ধ শ্রম।",
        "strengths": ["বাস্তববাদী দৃষ্টিভঙ্গি", "নির্ভরযোগ্যতা", "কঠোর পরিশ্রম", "অপ্রচলিত সমাধান উদ্ভাবন"],
        "karmic_lessons": "অনমনীয় মনোভাব ত্যাগ করে পরিবর্তনের সাথে খাপ খাওয়ানো শেখা।",
    },
    5: {
        "planet": "Mercury (বুধ)",
        "summary": "অভিজ্ঞতার বিস্তার, দ্রুত যোগাযোগ, ব্যবসা বাণিজ্য ও বিশ্বজনীন অভিযোজন ক্ষমতা।",
        "strengths": ["চটপটে বুদ্ধি", "বহুমুখী প্রতিভা", "অনুকূল বাচনশক্তি", "ঝুঁকি গ্রহণের সাহস"],
        "karmic_lessons": "চঞ্চলতা পরিহার করে দীর্ঘমেয়াদী দায়িত্ব পালনে নিষ্ঠাবান হওয়া।",
    },
    6: {
        "planet": "Venus (শুক্র)",
        "summary": "ভালোবাসা, সেবা, শিল্প ও নান্দনিকতার সুরক্ষা। পরিবার ও সমাজের সামগ্রিক লালন-পালন।",
        "strengths": ["নিঃস্বার্থ দায়িত্ববোধ", "নান্দনিক রুচি", "নিরাময়ী উপস্থিতি", "পারিবারিক ঐক্য"],
        "karmic_lessons": "অন্যের জীবন নিয়ন্ত্রণ না করে তাদের নিজস্ব স্বাধীনতাকে সম্মান জানানো।",
    },
    7: {
        "planet": "Ketu (কেতু)",
        "summary": "সত্যের অনুসন্ধান, মহাবিশ্বের রহস্য উদঘাটন এবং গভীর আধ্যাত্মিক মুক্তির পথপ্রদর্শন।",
        "strengths": ["তীক্ষ্ণ অন্তর্দৃষ্টি", "গবেষণাধর্মী মন", "আধ্যাত্মিক গভীরতা", "স্বাধীন চিন্তা"],
        "karmic_lessons": "অতিরিক্ত নিভৃতবাস ও সংশয় পরিহার করে মানবিক যোগাযোগ বজায় রাখা।",
    },
    8: {
        "planet": "Saturn (শনি)",
        "summary": "বস্তুগত প্রাচুর্য অর্জন, ন্যায় প্রতিষ্ঠা এবং মহৎ প্রাতিষ্ঠানিক দায়িত্বভার বহন।",
        "strengths": ["বিশাল সংগঠন ক্ষমতা", "ধৈর্য ও সহনশীলতা", "কঠোর ন্যায়পরায়ণতা", "আর্থিক বিচক্ষণতা"],
        "karmic_lessons": "ক্ষমতা ও ধনের মোহমুক্ত হয়ে নিঃস্বার্থ সেবায় নিয়োজিত হওয়া।",
    },
    9: {
        "planet": "Mars (মঙ্গল)",
        "summary": "মানবধর্মী সেবা, শোষিতের মুক্তি এবং মহৎ আদর্শের জন্য সর্বোচ্চ ত্যাগ স্বীকার।",
        "strengths": ["সাহস ও বীরত্ব", "সার্বজনীন সহানুভূতি", "উচ্চ আদর্শ", "অকুতোভয় সংগ্রাম"],
        "karmic_lessons": "ক্রোধ ও অধৈর্য ত্যাগ করে অহিংস নেতৃত্বের বিকাশ ঘটানো।",
    },
}

# ---------------------------------------------------------------------------
# Digit Repetition Effects from `vedic numero.docx`
# ---------------------------------------------------------------------------
REPETITION_EFFECTS: dict[int, dict[int, str]] = {
    1: {
        1: "১ বার: অন্তর্মুখী, অনুভূতি প্রকাশে কিছুটা সীমাবদ্ধ তবে স্বতন্ত্র ব্যক্তিত্ব।",
        2: "২ বার: চমৎকার যোগাযোগ ক্ষমতা, ভারসাম্যপূর্ণ দৃষ্টিভঙ্গি এবং সহানুভূতিশীল মন।",
        3: "৩ বার: অতিরিক্ত বাচালতা, আত্মকেন্দ্রীকতা এবং আবেগপ্রবণ অস্থিরতা দেখা দিতে পারে।",
        4: "৪+ বার: চরম অহংকার, অসহনশীলতা এবং অন্যের পরামর্শ উপেক্ষা করার প্রবণতা।",
    },
    2: {
        1: "১ বার: সূক্ষ্ম অন্তর্দৃষ্টি, সহানুভূতি ও সহযোগিতামূলক চেতনা।",
        2: "২ বার: উচ্চ সংবেদনশীলতা, গভীর কল্পনাশক্তি তবে অতিরিক্ত আবেগে দ্রুত আঘাত পাওয়া।",
        3: "৩ বার: ঘন ঘন মেজাজ পরিবর্তন, মানসিক বিষণ্নতা ও অনিরাপত্তাবোধ।",
        4: "৪+ বার: অতিরিক্ত নির্ভরতা, সিদ্ধান্তহীনতা এবং অতি-কাল্পনিক ভীতি।",
    },
    3: {
        1: "১ বার: ইতিবাচক আশাবাদ, চমৎকার স্মৃতিশক্তি এবং আত্মবিশ্বাস।",
        2: "২ বার: উচ্চ সৃজনশীলতা, সাহিত্য ও শিল্পে প্রতিভা, আধ্যাত্মিক আগ্রহ।",
        3: "৩ বার: অতিরিক্ত আত্মম্ভরিতা, অবাস্তব পরিকল্পনায় কালক্ষেপণ।",
        4: "৪+ বার: অহংকার, অতিরিক্ত খরুচে মনোভাব ও অধৈর্য।",
    },
    4: {
        1: "১ বার: সুশৃঙ্খল, হস্তশিল্প ও বাস্তব কাজে দক্ষ, বিশ্বস্ত কর্মী।",
        2: "২ বার: নিখুঁত পরিকল্পনাকারী, নিয়মানুবর্তী, তবে কিছুটা গোঁয়ার প্রকৃতির।",
        3: "৩ বার: অতিরিক্ত রক্ষণশীল, পরিবর্তন গ্রহণে অনীহা এবং একগুঁয়েমি।",
        4: "৪+ বার: চরম শারীরিক ও মানসিক ক্লান্তি, কাজেকর্মে স্থবিরতা ও বাধা।",
    },
    5: {
        1: "১ বার: আবেগীয় ভারসাম্য, স্বাধীনতা ও চমৎকার বাচনভঙ্গি।",
        2: "২ বার: প্রচণ্ড উদ্যম, ব্যবসায় বিচক্ষণতা, বহুভাষী প্রতিভা।",
        3: "৩ বার: অতিরিক্ত ঝুঁকি গ্রহণ, অস্থিরতা এবং দায়িত্ব এড়ানোর প্রবণতা।",
        4: "৪+ বার: আচরণে অনিয়ন্ত্রণ, মাদকাসক্তি বা অপচয়ের ঝুঁকি।",
    },
    6: {
        1: "১ বার: পারিবারিক দায়িত্ববোধ, মমতা ও সৌন্দর্যবোধ।",
        2: "২ বার: পরিবারের জন্য গভীর ত্যাগ, নান্দনিক রুচি তবে অতিরিক্ত দুশ্চিন্তা।",
        3: "৩ বার: অতিরিক্ত অধিকারবোধ, অন্যের ব্যক্তিস্বাধীনতায় হস্তক্ষেপ।",
        4: "৪+ বার: অতি-ভোগবিলাসিতা, অলসতা এবং সম্পর্কের অবনতি।",
    },
    7: {
        1: "১ বার: জীবনের অভিজ্ঞতার মাধ্যমে শিক্ষা গ্রহণ, আধ্যাত্মিক অনুসন্ধান।",
        2: "২ বার: গভীর অন্তর্দৃষ্টি, রহস্যবিদ্যায় আকর্ষণ, দার্শনিক প্রজ্ঞা।",
        3: "৩ বার: চরম মানসিক বিচ্ছিন্নতা, সম্পর্কের প্রতি অনীহা ও বিষাদ।",
        4: "৪+ বার: বাস্তবতাবিবর্জিত বৈরাগ্য ও জীবনে বহু আঘাত সহ্য করা।",
    },
    8: {
        1: "১ বার: পুঙ্খানুপুঙ্খ বিশ্লেষণী মন, আর্থিক দায়িত্ববোধ ও কর্তব্যনিষ্ঠা।",
        2: "২ বার: বস্তুগত ও আধ্যাত্মিক জগতের চমৎকার সমন্বয়, সফল সংগঠক।",
        3: "৩ বার: কঠোর একনায়কতন্ত্র, অতিরিক্ত বস্তুবাদিতা ও মানসিক একাকিত্ব।",
        4: "৪+ বার: আর্থিক টানাপোড়েন, মামলা-মোকদ্দমা ও ভাগ্যের নিষ্ঠুর পরিহাস।",
    },
    9: {
        1: "১ বার: মানবকল্যাণকামী, উচ্চাকাঙ্ক্ষী ও দায়িত্বশীল নাগরিক।",
        2: "২ বার: মহৎ আদর্শবাদী, পরোপকারী, তবে সমালোচনা সহ্য করতে না পারা।",
        3: "৩ বার: প্রচণ্ড রাগ, অতিরিক্ত আবেগে বিভ্রান্তি এবং হঠকারিতা।",
        4: "৪+ বার: ধ্বংসাত্মক ক্রোধ, সংঘর্ষপ্রবণতা এবং অহেতুক বিরোধে লিপ্ত হওয়া।",
    },
}

# ---------------------------------------------------------------------------
# Missing Number Remedies from `vedic numero.docx`
# ---------------------------------------------------------------------------
MISSING_REMEDIES: dict[int, dict[str, str]] = {
    1: {
        "element": "Water (উত্তর)",
        "impact": "সিদ্ধান্তহীনতা, আত্মবিশ্বাসের অভাব এবং নিজেকে প্রকাশে ভয়।",
        "remedy": "সূর্যদেবকে তামার পাত্রে জল অর্পণ করুন। পূর্ব দিকে লাল বা তামাটে রঙের সূর্য প্রতিস্থাপন করুন।",
        "rudraksha": "১ মুখী রুদ্রাক্ষ",
        "crystal": "Red Jasper বা Ruby Stone",
    },
    2: {
        "element": "Earth (দক্ষিণ-পশ্চিম)",
        "impact": "ধৈর্যের ঘাটতি, মানসিক ভারসাম্যহীনতা ও সম্পর্কের স্থায়িত্বে বিঘ্ন।",
        "remedy": "রৌপ্যের পাত্রে জল পান করুন। পূর্ণিমায় শিবলিঙ্গে কাঁচা দুধ অর্পণ করুন ও মায়ের চরণ স্পর্শ করুন।",
        "rudraksha": "২ মুখী রুদ্রাক্ষ",
        "crystal": "Moonstone বা White Quartz",
    },
    3: {
        "element": "Wood (পূর্ব)",
        "impact": "জ্ঞানের সঠিক প্রয়োগে বাধা, আত্মসন্দেহ এবং সুযোগ চিহ্নিত করতে ব্যর্থতা।",
        "remedy": "হলুদ রঙের পোশাক পরিধান করুন, বৃহস্পতিবার বিষ্ণু সহস্রনাম পাঠ করুন ও গুরুজনদের সেবা করুন।",
        "rudraksha": "৫ মুখী রুদ্রাক্ষ",
        "crystal": "Yellow Citrine বা Tiger Eye",
    },
    4: {
        "element": "Wood (দক্ষিণ-পূর্ব)",
        "impact": "শৃঙ্খলার অভাব, অর্থনৈতিক পরিকল্পনাহীনতা এবং অবাস্তব দিবাস্বপ্ন।",
        "remedy": "হাতে কাঠের মালা বা তুলসী মালা ধারণ করুন। দক্ষিণ-পূর্ব কোণে সবুজ গাছপালা রাখুন।",
        "rudraksha": "৮ মুখী রুদ্রাক্ষ",
        "crystal": "Green Aventurine বা Smoky Quartz",
    },
    5: {
        "element": "Earth (কেন্দ্র / ব্রহ্মস্থান)",
        "impact": "যোগাযোগে জড়তা, ব্যবসায়িক অস্থিরতা এবং মানসিক ভারসাম্যের অভাব।",
        "remedy": "বুধবারে গরুকে সবুজ ঘাস খাওয়ান। বাড়িতে তুলসী গাছ রোপণ ও নিয়মিত পরিচর্যা করুন।",
        "rudraksha": "৪ মুখী রুদ্রাক্ষ",
        "crystal": "Green Jade বা Emerald",
    },
    6: {
        "element": "Metal (উত্তর-পশ্চিম)",
        "impact": "পারিবারিক বন্ধনহীনতা, নান্দনিকতার অভাব ও গৃহসুখের ঘাটতি।",
        "remedy": "সুগন্ধি ও সুবাসিত দ্রব্য ব্যবহার করুন। বাড়িতে সাদা ফুল ও স্ফটিকের শ্রীযন্ত্র স্থাপন করুন।",
        "rudraksha": "৬ মুখী রুদ্রাক্ষ",
        "crystal": "Clear Quartz বা Rose Quartz",
    },
    7: {
        "element": "Metal (পশ্চিম)",
        "impact": "আধ্যাত্মিক অস্থিরতা, একাগ্রতার অভাব ও সন্তান সুখের বিলম্ব।",
        "remedy": "গণেশজির উপাসনা ও প্রতিদিন অথর্বশীর্ষ পাঠ করুন। কুকুরকে খাবার খাওয়ান।",
        "rudraksha": "৯ মুখী রুদ্রাক্ষ",
        "crystal": "Cat's Eye বা Amethyst",
    },
    8: {
        "element": "Earth (উত্তর-পূর্ব)",
        "impact": "আর্থিক পরিকল্পনাহীনতা, ধৈর্যচ্যুতি ও কর্মে স্থায়িত্বের অভাব।",
        "remedy": "শনিবার পিপল গাছে সর্ষের তেলের প্রদীপ প্রজ্জ্বলন করুন। দরিদ্রদের কালো তিল ও কম্বল দান করুন।",
        "rudraksha": "৭ মুখী বা ১৪ মুখী রুদ্রাক্ষ",
        "crystal": "Blue Lace Agate বা Black Tourmaline",
    },
    9: {
        "element": "Fire (দক্ষিণ)",
        "impact": "সাহস ও আত্মপ্রত্যয়ের অভাব, অন্যায়ের প্রতিবাদে কণ্ঠরোধ।",
        "remedy": "প্রতি মঙ্গলবার হনুমান চালিসা পাঠ করুন। লাল রঙের বস্ত্র ও মিষ্টি অভাবীদের মাঝে দান করুন।",
        "rudraksha": "৩ মুখী রুদ্রাক্ষ",
        "crystal": "Carnelian বা Red Coral",
    },
}

# ---------------------------------------------------------------------------
# Negative Syllables Dictionary
# ---------------------------------------------------------------------------
NEGATIVE_SYLLABLES: list[str] = [
    "SAD", "MAR", "WAR", "DIE", "ILL", "END", "LOSS", "NO", "CRY", "DOWN", "FALL"
]


# ---------------------------------------------------------------------------
# Core Helper Functions
# ---------------------------------------------------------------------------

def reduce_to_single_digit(n: int, preserve_master: bool = False) -> int:
    """Reduces an integer to a single digit 1-9 (optionally preserving 11, 22, 33)."""
    if n <= 0:
        return 0
    while n > 9:
        if preserve_master and n in (11, 22, 33):
            return n
        n = sum(int(ch) for ch in str(n))
    return n


def calculate_mulank(birth_day: int) -> int:
    """Driver/Birth number (1-9) from day of month."""
    return reduce_to_single_digit(birth_day)


def calculate_bhagyank(birth_date_str: str) -> int:
    """Conductor/Destiny number (1-9) from full birth date YYYY-MM-DD."""
    digits = [int(ch) for ch in birth_date_str if ch.isdigit()]
    return reduce_to_single_digit(sum(digits))


def calculate_kua_number(birth_year: int, gender: str) -> int:
    """Calculates Kua number based on birth year and gender."""
    year_sum = reduce_to_single_digit(birth_year)
    gender_clean = gender.strip().lower()
    if birth_year >= 2000:
        if gender_clean == "male":
            val = (9 - year_sum) % 9
            return 9 if val == 0 else val
        else:
            val = (year_sum + 6) % 9
            return 9 if val == 0 else val
    else:
        if gender_clean == "male":
            val = (10 - year_sum) % 9
            return 9 if val == 0 else val
        else:
            val = (year_sum + 5) % 9
            return 9 if val == 0 else val


def calculate_year_prediction(birth_date_str: str, target_year: int | None = None) -> tuple[int, str]:
    """Calculates Personal Year Number: (Birth Day + Birth Month + Target Year) % 9."""
    parts = birth_date_str.split("-")
    b_day = int(parts[2])
    b_month = int(parts[1])
    year = target_year or date.today().year

    total = b_day + b_month + sum(int(ch) for ch in str(year))
    p_year = reduce_to_single_digit(total)

    forecasts: dict[int, str] = {
        1: "নতুন সূচনা ও উদ্যোগের বছর। নতুন পরিকল্পনা বাস্তবায়ন, নেতৃত্ব ও আত্মবিশ্বাস প্রদর্শনের উপযুক্ত সময়।",
        2: "সহযোগিতা, সম্পর্ক ও শান্তির বছর। যৌথ উদ্যোগ, ধৈর্য এবং কূটনৈতিক দৃষ্টিভঙ্গি আপনাকে সমৃদ্ধ করবে।",
        3: "সৃজনশীলতা, আত্মপ্রকাশ ও সামাজিক যোগাযোগের বছর। জ্ঞান বৃদ্ধি, ভ্রমণ এবং শিল্পকলার ক্ষেত্রে বিশেষ শুভ।",
        4: "কঠোর শ্রম, ভিত্তিপ্রস্তর স্থাপন ও শৃঙ্খলার বছর। ধৈর্য ধরে ভবিষ্যৎ সাফল্যের শক্ত জমিন তৈরি করার সময়।",
        5: "গতিশীল রূপান্তর ও স্বাধীনতার বছর। নতুন সুযোগ, ব্যবসা সম্প্রসারণ ও ভ্রমণের প্রবল সম্ভাবনা।",
        6: "পরিবার, দাম্পত্য ও গৃহসুখের বছর। পারিবারিক দায়িত্ব পালন, সৌন্দর্য বৃদ্ধি ও সম্পর্কে মধুরতা আসবে।",
        7: "আত্মদর্শন, গবেষণা ও আধ্যাত্মিক উন্নতির বছর। বস্তুগত তাড়াহুড়ো ত্যাগ করে আত্মচিন্তায় নিমগ্ন হওয়ার সময়।",
        8: "কর্মের মূল্যায়ন, অর্থপ্রাপ্তি ও সামাজিক কর্তৃত্বের বছর। বিগত বছরের শ্রমের চূড়ান্ত অর্থনৈতিক পুরস্কার মিলবে।",
        9: "সম্পূর্ণতা, সমাপ্তি ও মানবিক সেবার বছর। পুরাতন অপ্রয়োজনীয় বিষয় বিসর্জন দিয়ে নতুন যুগের প্রস্তুতি নিন।",
    }
    return p_year, forecasts.get(p_year, "সাফল্য ও অগ্রগতির বছর।")


# ---------------------------------------------------------------------------
# Name Numerology Calculation
# ---------------------------------------------------------------------------

def calculate_name_numerology(name: str, mulank: int, bhagyank: int) -> NameAnalysisResponse:
    """Calculates complete Chaldean Name Numerology with syllable and compound analysis."""
    clean_name = re.sub(r"[^A-Za-z]", "", name).upper()
    total_val = 0
    letter_profiles: list[LetterSoundProfile] = []

    for ch in clean_name:
        val = CHALDEAN_MAP.get(ch, 0)
        total_val += val
        profile = LETTER_PROFILES.get(ch, {
            "element": "Akash",
            "vibration": "Universal vibrational tone.",
            "health": "General vitality balance.",
            "direction": "Center"
        })
        letter_profiles.append(LetterSoundProfile(
            letter=ch,
            value=val,
            sound_element=profile["element"],
            personality_vibration=profile["vibration"],
            health_tendency=profile["health"],
            direction_affinity=profile["direction"],
        ))

    compound_num = total_val
    single_num = reduce_to_single_digit(compound_num)

    # Compound lookup (fallback to single digit synthesis if > 100)
    compound_info = COMPOUND_NAMES.get(compound_num)
    if not compound_info:
        compound_info = {
            "name": f"Compound {compound_num} (Reduces to {single_num})",
            "quality": "Favorable" if single_num in (1, 3, 5, 6) else "Mixed",
            "meaning": f"A higher dimensional vibration reducing to root number {single_num}. Influenced by primary planetary lord."
        }

    # Syllable warning check
    negative_syllables_found = [syl for syl in NEGATIVE_SYLLABLES if syl in clean_name]

    # First letter vibration
    first_char = clean_name[0] if clean_name else "A"
    first_char_val = CHALDEAN_MAP.get(first_char, 1)
    first_letter_vib = f"আদ্যক্ষর '{first_char}' (মান {first_char_val}): {LETTER_PROFILES.get(first_char, {}).get('vibration', '')}"

    # Harmony with Mulank & Bhagyank via 18 Oct Table
    m_friends = FRIENDSHIP_TABLE.get(mulank, {}).get("friends", [])
    m_enemies = FRIENDSHIP_TABLE.get(mulank, {}).get("enemies", [])
    if single_num in m_friends:
        h_mulank = "উচ্চ সামঞ্জস্যপূর্ণ (Mitra/Friend) — জন্মশক্তির সাথে সম্পূর্ণ অনুকূল।"
    elif single_num in m_enemies:
        h_mulank = "প্রতিকূল (Shatru/Enemy) — কর্মপ্রচেষ্টায় অভ্যন্তরীণ দ্বন্দ্ব তৈরি করতে পারে।"
    else:
        h_mulank = "নিরপেক্ষ (Sama/Neutral) — মোটামুটি সামঞ্জস্যপূর্ণ।"

    b_friends = FRIENDSHIP_TABLE.get(bhagyank, {}).get("friends", [])
    b_enemies = FRIENDSHIP_TABLE.get(bhagyank, {}).get("enemies", [])
    if single_num in b_friends:
        h_bhagyank = "উচ্চ সামঞ্জস্যপূর্ণ (Mitra/Friend) — ভাগ্যপথের সাথে চমৎকার সংগতিপূর্ণ।"
    elif single_num in b_enemies:
        h_bhagyank = "প্রতিকূল (Shatru/Enemy) — ভাগ্যোন্নতিতে অপ্রত্যাশিত বিলম্ব ঘটাতে পারে।"
    else:
        h_bhagyank = "নিরপেক্ষ (Sama/Neutral) — ভারসাম্যপূর্ণ।"

    is_fav = compound_info["quality"] in ("Favorable", "Extremely Favorable") and not negative_syllables_found

    if is_fav and single_num in m_friends and single_num in b_friends:
        verdict = "অত্যন্ত শুভ ও বরকতময় নাম (Supreme Harmonious Name)"
        rec = "নামটি জাতকের জন্ম ও ভাগ্যশক্তি উভয়ের সাথে সম্পূর্ণ ইতিবাচক কম্পনে যুক্ত। কোনো পরিবর্তনের প্রয়োজন নেই।"
    elif single_num in m_enemies or single_num in b_enemies:
        verdict = "নামে কিছুটা সংঘাত বিদ্যমান (Vibrational Conflict)"
        rec = f"নামের টোটাল সংখ্যা {single_num} মূলাঙ্ক বা ভাগ্যাঙ্কের সাথে সম্পূর্ণ সামঞ্জস্যপূর্ণ নয়। একটি উপযুক্ত আদ্যক্ষর বা বানান যোগ করে ১, ৩, ৫ বা ৬ কম্পাউন্ডে রূপান্তর করলে সৌভাগ্য ত্বরান্বিত হবে।"
    else:
        verdict = "সন্তোষজনক নাম (Moderately Auspicious)"
        rec = "নামের ভাইব্রেশন মধ্যম। জীবনে গতি আনতে সামান্য বানানের সামান্য সামঞ্জস্য শুভ হতে পারে।"

    return NameAnalysisResponse(
        full_name=name,
        chaldean_total=compound_num,
        single_number=single_num,
        compound_number=compound_num,
        compound_name=compound_info["name"],
        compound_description=compound_info["meaning"],
        is_favorable_compound=is_fav,
        letters=letter_profiles,
        negative_syllables_found=negative_syllables_found,
        first_letter_vibration=first_letter_vib,
        harmony_with_mulank=h_mulank,
        harmony_with_bhagyank=h_bhagyank,
        overall_name_verdict=verdict,
        recommendation=rec,
    )


# ---------------------------------------------------------------------------
# Mobile Numerology Engine
# ---------------------------------------------------------------------------

def calculate_mobile_numerology(mobile_str: str, mulank: int, bhagyank: int, birth_date_str: str = "") -> MobileAnalysisResponse:
    """Calculates complete Mobile Numerology with 60%/40% dominance law, Sepharial grid & 16 L-shapes."""
    clean_mob = re.sub(r"[^0-9]", "", mobile_str)
    if len(clean_mob) < 10:
        clean_mob = clean_mob.ljust(10, "0")
    elif len(clean_mob) > 10:
        clean_mob = clean_mob[-10:]

    digits = [int(ch) for ch in clean_mob]
    total_sum = sum(digits)
    compound_num = total_sum
    single_num = reduce_to_single_digit(total_sum)

    # 1. King Number Compatibility Table from `01.pdf`
    king_lucky = {
        1: [1, 2, 3, 5, 9], 2: [1, 3, 5], 3: [1, 2, 3, 5, 7],
        4: [1, 6, 7], 5: [1, 2, 3, 5, 6], 6: [4, 5, 6, 7],
        7: [1, 4, 5, 6], 8: [3, 5, 6], 9: [1, 3, 5]
    }
    king_enemy = {
        1: [8], 2: [4, 8, 9], 3: [6],
        4: [2, 4, 8, 9], 5: [], 6: [3],
        7: [], 8: [1, 2, 4, 8], 9: [2, 4]
    }

    if single_num in king_lucky.get(mulank, []):
        m_comp = f"চমৎকার অনুকূল (Lucky Number for King {mulank})"
    elif single_num in king_enemy.get(mulank, []):
        m_comp = f"প্রতিকূল ও শত্রুভাবাপন্ন (Enemy Number for King {mulank})"
    else:
        m_comp = f"নিরপেক্ষ (Neutral for King {mulank})"

    if single_num in king_lucky.get(bhagyank, []):
        b_comp = f"চমৎকার অনুকূল (Lucky for Destiny {bhagyank})"
    elif single_num in king_enemy.get(bhagyank, []):
        b_comp = f"প্রতিকূল (Enemy for Destiny {bhagyank})"
    else:
        b_comp = f"নিরপেক্ষ (Neutral for Destiny {bhagyank})"

    # 2. Conjunction Pairs (9 consecutive pairs) with the 60%/40% Dominance Law
    GOOD_PAIRS = {
        "12": "আকর্ষণীয় মুখশ্রী, সঞ্চয়শীল মানসিকতা, সহায়ক জীবনসঙ্গী।",
        "13": "আধ্যাত্মিক পরামর্শদাতা, উচ্চ শিক্ষা, খ্যাতি ও সামাজিক সম্মান।",
        "31": "উচ্চ পেশাদারিত্ব, বাস্তববাদী জ্ঞান, প্রাতিষ্ঠানিক খ্যাতি।",
        "15": "বাবার খ্যাতি বৃদ্ধি, পিতৃসম্পদ থেকে সৌভাগ্য ও সহজে ধনলাভ।",
        "51": "কম পরিশ্রমে চমৎকার আয়, সমাজে প্রতিপত্তি ও সম্মান।",
        "25": "হাতে শেফা (Shaffa), হিলিং বা চিকিৎসায় দারুণ সাফল্য, বিমান ভ্রমণে লাভ।",
        "52": "আধ্যাত্মিক ও গুপ্তবিদ্যায় উন্নতি, রোগ নিরাময় শক্তি।",
        "29": "সততা দ্বারা প্রচুর অর্থোপার্জন, স্বচ্ছ ও মর্যাদাপূর্ণ আর্থিক প্রবাহ।",
        "92": "পর্যাপ্ত অর্থপ্রবাহ, স্বাধীন চিন্তা, তবে সম্পর্কে অহংকার এড়ানো উচিত।",
        "37": "পরিপূর্ণ ব্যক্তিত্ব, প্রজ্ঞা থেকে বাস্তব কর্তৃত্ব লাভ, উচ্চ পদমর্যাদা।",
        "73": "প্রজ্ঞাবান নেতা, জ্ঞানের গভীরতা, সমাজে সর্বোচ্চ পরামর্শক।",
        "38": "রিয়েল এস্টেট, জমি-জমা মধ্যস্থতাকারী, বিবাদ মীমাংসাকারী ব্যক্তিত্ব।",
        "83": "সম্পত্তি বিষয়ক কনসালটেন্সি ও টেকসই আর্থিক প্রতিপত্তি।",
        "47": "সততা, তীক্ষ্ণ মেধা, চারিত্রিক দৃঢ়তা, রাহু-কেতু ভারসাম্য।",
        "74": "অখণ্ড সততা ও কারিগরি ক্ষেত্রে বিশাল সাফল্য।",
        "57": "জ্যোতিষী ও পরামর্শকদের জন্য অপরিহার্য, দুর্দান্ত বাচনভঙ্গি ও লেখক প্রতিভা।",
        "75": "বিখ্যাত বক্তা, জনসম্পর্ক ও উচ্চ পরামর্শমূলক খ্যাতি।",
        "69": "সৃজনশীল ম্যানেজমেন্ট, ইভেন্ট ডিজাইন, বিপরীত লিঙ্গের সাথে চমৎকার সাফল্য।",
        "96": "কৌশলী পরিকল্পনাকারী, আধুনিক মিডিয়া ও ডিজাইনিংয়ে সাফল্য।",
        "78": "আধ্যাত্মিক নিরাময়কারী (Reiki/Healer), নিজস্ব শক্তিতে সংকট মোচন।",
        "87": "আদর্শবাদী, ধ্যানের মাধ্যমে অন্তর্শক্তি জাগ্রত করার ক্ষমতা।",
    }
    MALEFIC_PAIRS = {
        "14": "ঋণ ও দায়ের ফাঁদ, লিগ্যাল নোটিস, অতিরিক্ত শারীরিক পরিশ্রম তবে কম প্রাপ্তি।",
        "41": "অযথা অর্থদণ্ড, আইনি জটিলতা, অপরিসীম মানসিক টানাপোড়েন।",
        "16": "চরম অশুভ — দাম্পত্য কলহ, জীবনসঙ্গীর তীব্র অসুস্থতা, আয় স্থবিরতা।",
        "61": "দাম্পত্যে বিচ্ছিন্নতা, আর্থিক অবরোধ ও মূত্রাশয় সংক্রান্ত জটিলতা।",
        "18": "চরম প্রতিকূল — পিতা-পুত্রের তীব্র মতবিরোধ, সরকারি তদন্ত, ঘনঘন চাকরি বদল।",
        "81": "সরকারি কাজে জটিলতা, দাম্পত্যে ভুল বোঝাবুঝি, পিতার সাথে বিচ্ছেদ।",
        "23": "সন্তানের সাথে দূরত্ব বা বিবাদ, প্রচুর গুপ্ত শত্রু।",
        "32": "পারিবারিক বিবাদ, তবে শত্রু কেউ জাতকের ক্ষতি করতে পারে না।",
        "26": "শিক্ষায় বাধা, মেয়েদের শাশুড়ির সাথে বিবাদ, ছেলেদের অতিরিক্ত নারী আকর্ষণ।",
        "62": "পড়াশোনায় ড্রপআউট, ডায়াবেটিসের ঝুঁকি, দাম্পত্য অসন্তোষ।",
        "27": "বাত, জয়েন্ট ও হাঁটুর ব্যথা, কর্মজীবনে বারবার উত্থান-পতন।",
        "72": "মূত্রাশয়ের রোগ, বাতের ব্যথা ও তীব্র আবেগীয় অস্থিরতা।",
        "28": "বিষ যোগ — তীব্র বিষণ্নতা, মাত্রাতিরিক্ত হাসপাতালের খরচ, ঘরে জল চুইয়ে পড়া।",
        "82": "মেডিক্যাল খরচায় সঞ্চয় নাশ, সম্পর্কের ক্ষেত্রে চরম বিষাদ।",
        "34": "পায়ে কাঁপুনি, শ্বাসকষ্ট, পরিবারে পক্ষাঘাতের ঝুঁকি।",
        "43": "অস্থির সিদ্ধান্ত, স্নায়বিক দৌর্বল্য ও পারিবারিক স্বাস্থ্যে আঘাত।",
        "45": "হাসপাতাল ও আদালতের ঘনঘন চক্কর, জীবন নানারূপ নিষেধাজ্ঞায় বন্দি।",
        "54": "অপ্রত্যাশিত আইনি ঝামেলা ও স্বাস্থ্য খাতে অর্থের অপচয়।",
        "46": "বিবাহবহির্ভূত সম্পর্কের জটিলতা, ইউরিনারি ইনফেকশন, সামাজিক কেলেঙ্কারি।",
        "64": "দাম্পত্য টানাপোড়েন ও সম্পর্কের বিশ্বাসভঙ্গ।",
        "48": "চরম অশুভ — রক্তের রোগ, নিরাময়হীন জটিলতা, শয্যাসুখের চরম ঘাটতি।",
        "84": "অব্যক্ত শারীরিক পীড়া, মানসিক বিষাদ ও দাম্পত্য সুখ নাশ।",
        "67": "দাম্পত্য জীবনে ভাঙন, জীবনসঙ্গীর শারীরিক পীড়া।",
        "76": "প্রেমের সম্পর্কে ভুল বোঝাবুঝি ও মানসিক অশান্তি।",
        "68": "চোখের দৃষ্টিতে ত্রুটি, শরীরের নির্দিষ্ট কোনো অঙ্গে দীর্ঘস্থায়ী ব্যাধি।",
        "86": "চক্ষু পীড়া ও শারীরিক দুর্বলতা।",
        "89": "তর্কপ্রবণ স্বভাব, অতি-অনমনীয়তা, বার্ধক্যে ক্রনিক অসুস্থতা।",
        "98": "ভাইয়ে ভাইয়ে বিবাদ, অতিরিক্ত রাগ ও দীর্ঘমেয়াদী বাতের ব্যথা।",
    }

    dob_digits_set = set(birth_date_str.replace("-", "")) if birth_date_str else set()
    conjunction_pairs: list[MobileConjunctionPair] = []

    for i in range(len(clean_mob) - 1):
        pair_str = clean_mob[i:i+2]
        d1 = int(pair_str[0])
        d2 = int(pair_str[1])
        resonance = (str(d1) in dob_digits_set and str(d2) in dob_digits_set)

        if pair_str in GOOD_PAIRS:
            cat = "Good"
            desc = GOOD_PAIRS[pair_str]
        elif pair_str in MALEFIC_PAIRS:
            cat = "Malefic"
            desc = MALEFIC_PAIRS[pair_str]
        else:
            cat = "Neutral"
            desc = f"মিশ্র ফলপ্রসূ জোড়া ({d1} ও {d2}) — ৬০% প্রভাব {d1}-এর এবং ৪০% প্রভাব {d2}-এর।"

        conjunction_pairs.append(MobileConjunctionPair(
            pair=pair_str,
            first_digit=d1,
            second_digit=d2,
            dominance_formula=f"১ম সংখ্যা {d1} (৬০% প্রভাব) / ২য় সংখ্যা {d2} (৪০% প্রভাব)",
            category=cat,
            manifestation=desc,
            dob_resonance=resonance,
        ))

    # 3. Digit Repetitions in Mobile
    digit_counts: dict[int, int] = {}
    for d in digits:
        digit_counts[d] = digit_counts.get(d, 0) + 1

    mobile_repetitions: list[DigitRepetitionItem] = []
    warnings: list[str] = []

    for d in range(10):
        c = digit_counts.get(d, 0)
        if c >= 2:
            if c == 2:
                eff = f"{d} সংখ্যাটি ২ বার আছে — স্বাভাবিক ও ভারসাম্যপূর্ণ শক্তি।"
            else:
                eff = f"{d} সংখ্যাটি {c} বার পুনরাবৃত্ত হয়েছে — অতিরিক্ত মাত্রায় অস্থিরতা বা নেতিবাচকতা তৈরি করে।"
                if d in (4, 8, 9, 2):
                    warnings.append(f"মোবাইলে {d} সংখ্যাটি {c} বার এসেছে, যা ক্লায়েন্ট রুল অনুযায়ী পরিহারযোগ্য।")
            mobile_repetitions.append(DigitRepetitionItem(digit=d, count=c, effect=eff))

    # Check zero
    zero_count = digit_counts.get(0, 0)
    if zero_count >= 2:
        warnings.append(f"মোবাইল নম্বরে শূন্য ({zero_count} বার) রয়েছে — একাধিক শূন্য সৌভাগ্য শক্তি শূন্যে পরিণত করে।")

    # 4. Vedic Sepharial 3x3 Mobile Grid & 16 L-Shapes
    sepharial_grid = {str(d): digit_counts.get(d, 0) for d in range(1, 10)}
    l_shapes_formed: list[MobileLShape] = []

    has_d = lambda x: digit_counts.get(x, 0) > 0

    if has_d(1) and has_d(7) and has_d(5):
        l_shapes_formed.append(MobileLShape(corner_digit=1, arm_digits=[7, 5], shape_code="1-7-5", meaning="লজিক্যাল মাইন্ড, তীক্ষ্ণ ও উচ্চস্তরের চিন্তাশক্তি।"))
    if has_d(1) and has_d(6) and has_d(7):
        l_shapes_formed.append(MobileLShape(corner_digit=1, arm_digits=[6, 7], shape_code="1-6-7", meaning="প্রেম বিবাহের প্রবল সম্ভাবনা ও আকর্ষণীয় ব্যক্তিত্ব।"))
    if has_d(3) and has_d(1) and has_d(7):
        l_shapes_formed.append(MobileLShape(corner_digit=1, arm_digits=[3, 7], shape_code="3-1-7", meaning="উচ্চ শিক্ষিত, সমাজে সম্মানিত ও বিশ্বস্ত উপদেষ্টা।"))
    if has_d(1) and has_d(9) and has_d(7):
        l_shapes_formed.append(MobileLShape(corner_digit=1, arm_digits=[9, 7], shape_code="1-9-7", meaning="ভাগ্য বৃদ্ধি ও শুভ সুযোগের আগমন।"))
    if has_d(7) and has_d(5) and has_d(4):
        l_shapes_formed.append(MobileLShape(corner_digit=5, arm_digits=[7, 4], shape_code="7-5-4", meaning="ঋণ ও দায়ের সমস্যায় জড়িয়ে পড়ার ঝুঁকি।"))
    if has_d(7) and has_d(8) and has_d(4):
        l_shapes_formed.append(MobileLShape(corner_digit=8, arm_digits=[7, 4], shape_code="7-8-4", meaning="চতুর ও বাস্তববাদী ব্যক্তিত্ব, কাজ আদায় করার ক্ষমতা।"))
    if has_d(5) and has_d(8) and has_d(4):
        l_shapes_formed.append(MobileLShape(corner_digit=8, arm_digits=[5, 4], shape_code="5-8-4", meaning="ক্ষতি হওয়ার ক্রমাগত ভীতি ও আর্থিক অনিরাপত্তা।"))
    if has_d(6) and has_d(2) and has_d(8):
        l_shapes_formed.append(MobileLShape(corner_digit=2, arm_digits=[6, 8], shape_code="6-2-8", meaning="সৎ কর্মের মাধ্যমে বিশাল ধনপ্রাপ্তির সম্ভাবনা।"))
    if has_d(7) and has_d(5) and has_d(8):
        l_shapes_formed.append(MobileLShape(corner_digit=5, arm_digits=[7, 8], shape_code="7-5-8", meaning="চমৎকার পাবলিক স্পিকার ও প্রভাবশালী বক্তা।"))
    if has_d(7) and has_d(2) and has_d(8):
        l_shapes_formed.append(MobileLShape(corner_digit=8, arm_digits=[7, 2], shape_code="7-2-8", meaning="বিষণ্নতা, একাকিত্ব ও মানসিক বিচ্ছিন্নতা।"))
    if has_d(3) and has_d(6) and has_d(7):
        l_shapes_formed.append(MobileLShape(corner_digit=6, arm_digits=[3, 7], shape_code="3-6-7", meaning="বহুমুখী প্রতিভাধর, ধার্মিক ও গুরুর আশীর্বাদপ্রাপ্ত।"))
    if has_d(6) and has_d(7) and has_d(8):
        l_shapes_formed.append(MobileLShape(corner_digit=7, arm_digits=[6, 8], shape_code="6-7-8", meaning="আধ্যাত্মিক নিরাময়কারী (Spiritual Healer)।"))
    if has_d(9) and has_d(7) and has_d(5):
        l_shapes_formed.append(MobileLShape(corner_digit=5, arm_digits=[9, 7], shape_code="9-7-5", meaning="অতুলনীয় কারিগরি ও প্রযুক্তিগত জ্ঞান।"))
    if has_d(3) and has_d(1) and has_d(6):
        l_shapes_formed.append(MobileLShape(corner_digit=1, arm_digits=[3, 6], shape_code="3-1-6", meaning="উচ্চমানের শিক্ষা ও মর্যাদাপূর্ণ পেশা।"))
    if has_d(1) and has_d(9) and has_d(5):
        l_shapes_formed.append(MobileLShape(corner_digit=1, arm_digits=[9, 5], shape_code="1-9-5", meaning="বাবার সহযোগিতা ও পিতৃসম্পদ থেকে সমৃদ্ধি।"))
    if has_d(6) and has_d(7) and has_d(2):
        l_shapes_formed.append(MobileLShape(corner_digit=7, arm_digits=[6, 2], shape_code="6-7-2", meaning="সন্তান ধারণে জটিলতা বা স্ত্রীরোগ সংক্রান্ত সতর্কতা।"))

    # 5. Compound quality check
    if single_num == 1:
        c_qual = "শুভ কম্পাউন্ড (Preference: 46 > 64 > 37 > 55)" if compound_num in (46, 64, 37, 55) else ("অত্যন্ত অশুভ (২৮)" if compound_num == 28 else "সাধারণ ১ টোটাল")
    elif single_num == 3:
        c_qual = "শুভ কম্পাউন্ড (Preference: 66 > 39 > 30)" if compound_num in (66, 39, 30) else ("অশুভ (৪৮)" if compound_num == 48 else "সাধারণ ৩ টোটাল")
    elif single_num == 5:
        c_qual = "শুভ কম্পাউন্ড (Preference: 41 > 32 > 50 > 59)" if compound_num in (41, 32, 50, 59, 23) else "সাধারণ ৫ টোটাল"
    elif single_num == 6:
        c_qual = "শুভ কম্পাউন্ড (Preference: 42 > 24 > 33 > 60)" if compound_num in (42, 24, 33, 60, 51) else "সাধারণ ৬ টোটাল"
    else:
        c_qual = f"টোটাল {single_num} (কম্পাউন্ড {compound_num})"

    # Profession Affinity
    prof_affinity: list[str] = []
    if has_d(1) and (has_d(9) or has_d(7)):
        prof_affinity.append("চিকিৎসক / ফার্মাসিস্ট / মেডিক্যাল লাইন (১৯, ৩, ৭)")
    if (has_d(5) and has_d(7)) or (has_d(3) and has_d(1)):
        prof_affinity.append("আইটি / সফটওয়্যার / ইঞ্জিনিয়ার (১৯, ৭৫, ৫৭)")
    if (has_d(6) and has_d(7)) or has_d(2):
        prof_affinity.append("মিডিয়া / গ্ল্যামার / ফ্যাশন / ডিজাইনার (৬৭, ৭১, ৬৯)")
    if has_d(3) and has_d(1):
        prof_affinity.append("অধ্যাপনা / শিক্ষকতা / পরামর্শক (৩১, ৭৫, ৩৩)")
    if has_d(3) and has_d(8):
        prof_affinity.append("রিয়েল এস্টেট / জমিজমা / কনস্ট্রাকশন (৩৮, ৮৩, ৪, ৮)")
    if has_d(1) and has_d(7):
        prof_affinity.append("সরকারি চাকরি / রাজনীতি / শীর্ষ প্রশাসন (১, ১৭, ৭১)")
    if has_d(5):
        prof_affinity.append("ব্যবসা / ট্রেডিং / ব্যাংকিং ও ফিনান্স (৫, ৫১, ৫৬)")

    # Remedial Injections
    remedial_injections: list[str] = [
        "কোর্ট কেস বা আইনি বিবাদ দ্রুত মেটাতে মোবাইল নম্বরে '৩৩' অন্তর্ভুক্তি শুভ।",
        "বিদেশে স্থায়ী বসবাস বা পিআর লাভের জন্য '১, ৫, ৮, ৬' একসাথে রাখা ফলপ্রসূ।",
        "বিবাহে বিলম্ব দূর করতে '১৭', '৭১' বা '১৩১৭' জোড়া ধারণ করা যায় (বিবাহের পর পরিবর্তনীয়)।",
        "জ্যোতিষ ও পরামর্শক হিসেবে সুনাম অর্জনে '৫৭' বা '৭৫' জোড়া ধারণ করা অত্যন্ত ফলপ্রসূ।"
    ]

    malefic_count = sum(1 for p in conjunction_pairs if p.category == "Malefic")
    is_rec = (single_num in king_lucky.get(mulank, []) and
              single_num in king_lucky.get(bhagyank, []) and
              malefic_count == 0 and
              compound_num not in (28, 48) and
              zero_count < 2)

    if is_rec:
        overall_v = "চমৎকার ও উচ্চ শুভদায়ক মোবাইল নম্বর (Highly Auspicious & Lucky)"
    elif malefic_count >= 2 or compound_num in (28, 48):
        overall_v = "অশুভ ও প্রতিকূল নম্বর (Negative Pairs & Affliction Detected)"
    else:
        overall_v = "মাঝারি নম্বর (Average - Certain Adjustments Recommended)"

    return MobileAnalysisResponse(
        mobile_number=clean_mob,
        total_sum=total_sum,
        single_digit=single_num,
        compound_number=compound_num,
        compound_quality=c_qual,
        mulank_compatibility=m_comp,
        bhagyank_compatibility=b_comp,
        is_recommended=is_rec,
        digit_repetitions=mobile_repetitions,
        conjunction_pairs=conjunction_pairs,
        sepharial_grid=sepharial_grid,
        l_shapes_formed=l_shapes_formed,
        remedial_injections=remedial_injections,
        profession_affinity=prof_affinity,
        warnings_avoid=warnings,
        overall_verdict=overall_v,
    )


# ---------------------------------------------------------------------------
# Lo Shu 3x3 Grid & Dasha Calculation
# ---------------------------------------------------------------------------

def calculate_lo_shu_grid(birth_date_str: str, mulank: int, bhagyank: int, kua: int) -> tuple[list[LoShuGridCell], list[LoShuPlane], list[RajYogaItem], list[DigitRepetitionItem], list[MissingNumberRemedy]]:
    """Calculates full 3x3 Lo Shu Grid (3-1-9, 6-7-5, 2-8-4), Planes, Yogas, and Missing remedies."""
    # Digits from DOB + Mulank + Bhagyank + Kua
    dob_digits = [int(ch) for ch in birth_date_str if ch.isdigit() and ch != "0"]
    all_digits = dob_digits + [mulank, bhagyank, kua]

    counts: dict[int, int] = {d: 0 for d in range(1, 10)}
    for d in all_digits:
        if 1 <= d <= 9:
            counts[d] += 1

    # Grid Cell Definitions (Coordinates: row 0: 3, 1, 9; row 1: 6, 7, 5; row 2: 2, 8, 4)
    cell_metadata: dict[int, dict[str, str]] = {
        3: {"element": "Wood", "direction": "East", "meaning": "জ্ঞান, আধ্যাত্মিকতা ও পারিবারিক ঐতিহ্য"},
        1: {"element": "Water", "direction": "North", "meaning": "যোগাযোগ, কর্মজীবন ও নতুন সুযোগ"},
        9: {"element": "Fire", "direction": "South", "meaning": "খ্যাতি, তেজ ও সামাজিক স্বীকৃতি"},
        6: {"element": "Metal", "direction": "North-West", "meaning": "সহায়তাকারী বন্ধু, বৈভব ও বিদেশ ভ্রমণ"},
        7: {"element": "Metal", "direction": "West", "meaning": "সন্তান, সৃজনশীলতা ও অন্তর্দৃষ্টি"},
        5: {"element": "Earth", "direction": "Center", "meaning": "ভারসাম্য, সুস্বাস্থ্য ও কেন্দ্রবিন্দু"},
        2: {"element": "Earth", "direction": "South-West", "meaning": "দাম্পত্য, সম্পর্ক ও স্থায়িত্ব"},
        8: {"element": "Earth", "direction": "North-East", "meaning": "মেধা, স্মৃতিশক্তি ও শৃঙ্খলা"},
        4: {"element": "Wood", "direction": "South-East", "meaning": "ধনসম্পদ, আর্থিক শৃঙ্খলা ও প্রবৃদ্ধি"},
    }

    grid_cells: list[LoShuGridCell] = []
    # Display order: 3, 1, 9, 6, 7, 5, 2, 8, 4
    for d in [3, 1, 9, 6, 7, 5, 2, 8, 4]:
        meta = cell_metadata[d]
        grid_cells.append(LoShuGridCell(
            digit=d,
            count=counts[d],
            element=meta["element"],
            direction=meta["direction"],
            meaning=meta["meaning"],
        ))

    # Planes
    planes_def = [
        {"name": "Mental / Thought Plane (মানসিক স্তর)", "digits": [3, 1, 9], "desc": "চিন্তাভাবনা, স্মৃতিশক্তি ও বৌদ্ধিক বিশ্লেষণ ক্ষমতা।"},
        {"name": "Emotional / Will Plane (আবেগ ও সংকল্প স্তর)", "digits": [6, 7, 5], "desc": "মানসিক অনুভূতি, চারিত্রিক দৃঢ়তা ও ভালোবাসা।"},
        {"name": "Practical / Action Plane (ব্যবহারিক স্তর)", "digits": [2, 8, 4], "desc": "বাস্তব কর্মক্ষমতা, শারীরিক পরিশ্রম ও অর্থনৈতিক ব্যবস্থাপনা।"},
        {"name": "Thought Column (পরিকল্পনা স্তম্ভ)", "digits": [3, 6, 2], "desc": "পরিকল্পনা প্রণয়ন ও ভবিষ্যৎ দর্শনের ক্ষমতা।"},
        {"name": "Will Column (ইচ্ছাশক্তি স্তম্ভ)", "digits": [1, 7, 8], "desc": "অদম্য সংকল্প, ধৈর্য ও যেকোনো বাধায় অবিচল থাকা।"},
        {"name": "Action Column (কর্মদক্ষতা স্তম্ভ)", "digits": [9, 5, 4], "desc": "চিন্তাকে বাস্তবে রূপ দেওয়া ও তাৎক্ষণিক সিদ্ধান্ত গ্রহণ।"},
    ]

    planes: list[LoShuPlane] = []
    for p in planes_def:
        present = [d for d in p["digits"] if counts[d] > 0]
        pct = int((len(present) / len(p["digits"])) * 100)
        status = "Complete" if pct == 100 else ("Partial" if pct > 0 else "Missing")
        planes.append(LoShuPlane(
            name=p["name"],
            digits=p["digits"],
            present_digits=present,
            status=status,
            percentage=pct,
            significance=p["desc"],
        ))

    # Raj Yogas
    raj_yogas: list[RajYogaItem] = [
        RajYogaItem(
            name="Golden Raj Yoga (সুবর্ণ রাজযোগ - 3-7-4)",
            digits=[3, 7, 4],
            is_active=all(counts[d] > 0 for d in [3, 7, 4]),
            description="নাম, যশ, বিপুল ভূসম্পত্তি ও দীর্ঘস্থায়ী ঐশ্বর্য প্রদানের রাজযোগ।",
        ),
        RajYogaItem(
            name="Silver Raj Yoga (রৌপ্য রাজযোগ - 2-7-9)",
            digits=[2, 7, 9],
            is_active=all(counts[d] > 0 for d in [2, 7, 9]),
            description="সামাজিক জনপ্রিয়তা, বৈষয়িক সমৃদ্ধি ও আকস্মিক উন্নতির রাজযোগ।",
        ),
    ]

    # Digit Repetitions
    digit_repetitions: list[DigitRepetitionItem] = []
    for d in range(1, 10):
        c = counts[d]
        if c > 0:
            eff = REPETITION_EFFECTS.get(d, {}).get(min(c, 4), f"{d} সংখ্যাটি {c} বার উপস্থিত।")
            digit_repetitions.append(DigitRepetitionItem(digit=d, count=c, effect=eff))

    # Missing Numbers Remedies
    missing_remedies: list[MissingNumberRemedy] = []
    for d in range(1, 10):
        if counts[d] == 0:
            m_data = MISSING_REMEDIES.get(d, {})
            missing_remedies.append(MissingNumberRemedy(
                digit=d,
                element=m_data.get("element", ""),
                impact=m_data.get("impact", ""),
                remedy=m_data.get("remedy", ""),
                rudraksha=m_data.get("rudraksha", ""),
                crystal=m_data.get("crystal", ""),
            ))

    return grid_cells, planes, raj_yogas, digit_repetitions, missing_remedies


def calculate_numerology_dasha(birth_date_str: str, mulank: int, bhagyank: int) -> list[NumerologyDashaPeriod]:
    """Calculates Vedic Numerology Dasha hierarchy (MD, AD, PD) using the exact /45 formula from `vedic numero.docx`."""
    b_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
    today = date.today()

    PLANET_NAMES = {
        1: "Sun (সূর্য)", 2: "Moon (চন্দ্র)", 3: "Jupiter (বৃহস্পতি)",
        4: "Rahu (রাহু)", 5: "Mercury (বুধ)", 6: "Venus (শুক্র)",
        7: "Ketu (কেতু)", 8: "Saturn (শনি)", 9: "Mars (মঙ্গল)"
    }

    # MD cycle: Starts with Mulank number, duration = MD number of years
    # Sequence follows 1 through 9 cyclically
    dasha_timeline: list[NumerologyDashaPeriod] = []
    curr_start = b_date

    # Find the current active MD for today
    curr_md_num = mulank
    while True:
        md_years = curr_md_num
        # Approximation of years in days (accounting for leap years)
        md_days = md_years * 365.25
        curr_end = curr_start + timedelta(days=md_days)
        if curr_start <= today < curr_end or curr_start > today:
            break
        curr_start = curr_end
        curr_md_num = (curr_md_num % 9) + 1

    # Record Active Mahadasha
    m_friends = FRIENDSHIP_TABLE.get(mulank, {}).get("friends", [])
    m_enemies = FRIENDSHIP_TABLE.get(mulank, {}).get("enemies", [])
    f_score = "Favorable" if curr_md_num in m_friends else ("Unfavorable" if curr_md_num in m_enemies else "Neutral")

    dasha_timeline.append(NumerologyDashaPeriod(
        level="MD (Mahadasha)",
        planet=PLANET_NAMES[curr_md_num],
        number=curr_md_num,
        start_date=curr_start.isoformat(),
        end_date=curr_end.isoformat(),
        duration_days=round(md_days, 1),
        friendship_score=f_score,
        guidance=f"{PLANET_NAMES[curr_md_num]}-এর মহাদশা চলছে ({curr_md_num} বছর)। সামগ্রিক জীবনধারায় এর প্রভাব প্রধান থাকবে।",
    ))

    # Calculate Antardashas within this MD
    # Formula from docx: AD duration (years) = (MD_years * AD_num) / 45
    # Total AD sum across 1 to 9 = MD_years * (1+2+...+9)/45 = MD_years * 45 / 45 = MD_years!
    ad_start = curr_start
    active_ad_num = 1
    active_ad_start = ad_start
    active_ad_days = 0.0

    for ad_num in range(1, 10):
        ad_years = (curr_md_num * ad_num) / 45.0
        ad_days = ad_years * 365.25
        ad_end = ad_start + timedelta(days=ad_days)

        if ad_start <= today < ad_end:
            active_ad_num = ad_num
            active_ad_start = ad_start
            active_ad_days = ad_days
            ad_score = "Favorable" if ad_num in m_friends else ("Unfavorable" if ad_num in m_enemies else "Neutral")
            dasha_timeline.append(NumerologyDashaPeriod(
                level="AD (Antardasha)",
                planet=PLANET_NAMES[ad_num],
                number=ad_num,
                start_date=ad_start.isoformat(),
                end_date=ad_end.isoformat(),
                duration_days=round(ad_days, 1),
                friendship_score=ad_score,
                guidance=f"বর্তমানে সক্রিয় অন্তর্দশা: {PLANET_NAMES[ad_num]}। এই সময়ে অন্তর্দশাপতি গ্রহের কারকতা ফলিত হবে।",
            ))
            break
        ad_start = ad_end

    # Calculate Pratyantardashas within active AD
    # Formula: PD days = (AD_days * PD_num) / 45
    pd_start = active_ad_start
    for pd_num in range(1, 10):
        pd_days = (active_ad_days * pd_num) / 45.0
        pd_end = pd_start + timedelta(days=pd_days)

        if pd_start <= today < pd_end:
            pd_score = "Favorable" if pd_num in m_friends else ("Unfavorable" if pd_num in m_enemies else "Neutral")
            dasha_timeline.append(NumerologyDashaPeriod(
                level="PD (Pratyantardasha)",
                planet=PLANET_NAMES[pd_num],
                number=pd_num,
                start_date=pd_start.isoformat(),
                end_date=pd_end.isoformat(),
                duration_days=round(pd_days, 1),
                friendship_score=pd_score,
                guidance=f"প্রত্যন্তর্দশা: {PLANET_NAMES[pd_num]}। প্রতিদিনের কার্যক্রমে এই গ্রহের শক্তি ক্রিয়াশীল থাকবে।",
            ))
            break
        pd_start = pd_end

    return dasha_timeline


# ---------------------------------------------------------------------------
# Master Numerology Execution Function
# ---------------------------------------------------------------------------

def calculate_full_numerology(
    full_name: str,
    birth_date_str: str,
    gender: str = "male",
    mobile_number: str | None = None,
    prediction_year: int | None = None,
) -> NumerologyCalculateResponse:
    """Executes end-to-end Numerology calculation adhering strictly to client rules."""
    parts = birth_date_str.split("-")
    b_year = int(parts[0])
    b_month = int(parts[1])
    b_day = int(parts[2])

    mulank = calculate_mulank(b_day)
    bhagyank = calculate_bhagyank(birth_date_str)
    kua = calculate_kua_number(b_year, gender)
    p_year, p_forecast = calculate_year_prediction(birth_date_str, prediction_year)

    # Core profiles
    m_raw = MULANK_MASTER[mulank]
    mulank_prof = MulankProfile(
        number=mulank,
        planet=m_raw["planet"],
        planet_hi=m_raw["planet_hi"],
        deity=m_raw["deity"],
        metal=m_raw["metal"],
        colors=m_raw["colors"],
        unlucky_colors=m_raw["unlucky_colors"],
        direction=m_raw["direction"],
        lucky_numbers=m_raw["lucky_numbers"],
        unlucky_numbers=m_raw["unlucky_numbers"],
        beej_mantra=m_raw["beej_mantra"],
        jap_count=m_raw["jap_count"],
        gemstone=m_raw["gemstone"],
        lucky_days=m_raw["lucky_days"],
        lucky_months=m_raw["lucky_months"],
        grains_daan=m_raw["grains_daan"],
        health_traits=m_raw["health_traits"],
        profession=m_raw["profession"],
    )

    b_raw = BHAGYANK_MASTER[bhagyank]
    bhagyank_prof = BhagyankProfile(
        number=bhagyank,
        planet=b_raw["planet"],
        life_path_summary=b_raw["summary"],
        strengths=b_raw["strengths"],
        karmic_lessons=b_raw["karmic_lessons"],
    )

    # Grid & Yogas
    grid_cells, planes, raj_yogas, digit_reps, missing_remedies = calculate_lo_shu_grid(
        birth_date_str, mulank, bhagyank, kua
    )

    # Dasha timeline
    dasha_timeline = calculate_numerology_dasha(birth_date_str, mulank, bhagyank)

    # Name analysis
    name_analysis = calculate_name_numerology(full_name, mulank, bhagyank)

    # Mobile analysis
    mobile_analysis = None
    if mobile_number and len(re.sub(r"[^0-9]", "", mobile_number)) >= 10:
        mobile_analysis = calculate_mobile_numerology(mobile_number, mulank, bhagyank, birth_date_str)

    return NumerologyCalculateResponse(
        name=full_name,
        birth_date=birth_date_str,
        mulank=mulank_prof,
        bhagyank=bhagyank_prof,
        kua_number=kua,
        year_prediction_number=p_year,
        year_prediction_summary=p_forecast,
        lo_shu_grid=grid_cells,
        planes=planes,
        raj_yogas=raj_yogas,
        digit_repetitions=digit_reps,
        missing_numbers_remedies=missing_remedies,
        dasha_timeline=dasha_timeline,
        name_analysis=name_analysis,
        mobile_analysis=mobile_analysis,
    )
