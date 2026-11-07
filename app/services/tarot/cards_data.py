"""Canonical 78-Card Tarot Deck Database adhering 100% to Deepali / Psychdoor Master Course.

Contains all 22 Major Arcana and 56 Minor Arcana (Wands, Cups, Swords, Pentacles).
Every single card includes:
- Authentic Numerology vibration (0-9, 10-14, master numbers)
- Chrono-Astrological Ingress Windows & Sidereal Solar Timing
- Elemental Speeds (Wands = Hours-Days, Swords = Days-Weeks, Cups = Weeks-Months, Pentacles = Months-Years)
- Seasons (Summer, Spring, Autumn, Winter)
- Canonical Yes / No Divine Verdict
- One-Liner Core Meaning from Master Course
- Sacred Esoteric Symbols
- Real-World Career & Profession Archetypes
- Multi-Domain Interpretations across 5 Life Arenas (General, Love, Career, Finance, Spiritual)
- Dual Polarities (Upright & Reversed)
- Vedic Graha resonance and actionable metaphysical remedies.
"""

from __future__ import annotations
from typing import Any

MAJOR_ARCANA: list[dict[str, Any]] = [   {   'id': 'the_fool',
        'name': 'The Fool',
        'arcana': 'major',
        'suit': None,
        'number': 0,
        'element': 'Air',
        'astrology': 'Uranus / Aquarius',
        'vedic_graha': 'Rahu',
        'image_slug': 'the-fool',
        'numerology': '0 or 22',
        'timing_window': 'February 12 – March 12 (Aquarius)',
        'timing_season': 'Late Winter / Spring',
        'timing_speed': 'Instant / Sudden',
        'yes_no': 'YES Card',
        'one_liner': 'Starting from scratch, spontaneous leap of faith, exploring and discovering, risk-taker.',
        'symbols': [   'White dog (instinctive loyalty & guardian warning of danger)',
                       'White rose (pure intentions, innocence, freedom from desire)',
                       'Small knapsack (latent memories, tools of past lives yet unused)',
                       'Red feather in cap (vital life force, fiery passion, optimism)',
                       'Cliff edge (the precipice of the unknown, courage to take leaps of faith)',
                       'Radiant yellow sun (divine illumination and cosmic protection)'],
        'professions': [   'Creative careers',
                           'Startups and innovative ventures',
                           'Power plants, technology, electricity',
                           'Social media and unconventional creators',
                           'Adventurers and pioneers'],
        'upright': {   'keywords': ['New Beginnings', 'Innocence', 'Spontaneity', 'Free Spirit', 'Leap of Faith'],
                       'general': 'The Fool heralds a profound zero-point transition. You stand on the precipice of an '
                                  'auspicious adventure, invited to trust the universe implicitly.',
                       'love': 'Fresh romantic horizons, carefree magnetic attraction, or letting go of past '
                               'relationship baggage with courageous open-heartedness.',
                       'career': 'Innovative career pivot, uncharted venture, startup leap, or pioneering an '
                                 'unconventional path with fresh enthusiasm.',
                       'finance': 'New financial avenues opening up; take calculated risks while avoiding reckless '
                                  'neglect of practical details.',
                       'spiritual': 'Pristine spiritual awakening, stepping out of dogmatic beliefs into pure '
                                    'intuitive discovery.'},
        'reversed': {   'keywords': ['Recklessness', 'Naivety', 'Hesitation', 'Foolish Risk', 'Holding Back'],
                        'general': 'Reversed, The Fool cautions against blind impulsive plunges without foresight, or '
                                   'paradoxically, paralyzing dread that freezes you on the edge.',
                        'love': 'Impulsive commitments, fear of vulnerability, or falling for illusionary promises '
                                'without emotional grounding.',
                        'career': 'Rushing into unvetted contracts or procrastinating on a brilliant idea out of '
                                  'self-doubt.',
                        'finance': 'Careless spending, speculative gambles, or overlooking fine print in financial '
                                   'documents.',
                        'spiritual': 'Spiritual cynicism or chasing spiritual fads rather than cultivating authentic '
                                     'inner discipline.'},
        'remedy': "Wear yellow or sky blue. Chant 'Om Som Somaya Namah' to ground emotional impulsiveness and meditate "
                  'before major decisions.',
        'affirmation': 'I step forward with childlike wonder, guided by divine wisdom and inner clarity.'},
    {   'id': 'the_magician',
        'name': 'The Magician',
        'arcana': 'major',
        'suit': None,
        'number': 1,
        'element': 'Air',
        'astrology': 'Mercury / Gemini & Virgo',
        'vedic_graha': 'Budha',
        'image_slug': 'the-magician',
        'numerology': '1',
        'timing_window': 'June 15 – July 14 (Gemini) & September 16 – October 15 (Virgo)',
        'timing_season': 'Summer & Autumn',
        'timing_speed': 'Rapid / Mental',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Manifestation, resourcefulness, inspired action, translating thoughts into tangible reality.',
        'symbols': [   'Infinity sign (Lemniscate, eternal cosmic consciousness and mental power)',
                       'Ouroboros snake belt (cycles of wisdom and eternal life)',
                       "Right hand pointing to heaven, left to earth ('As Above, So Below')",
                       'Four elemental altar tools (Wand, Cup, Sword, Pentacle / fire, water, air, earth)',
                       'Red robe over white tunic (passion wrapped in purity of conscious intent)',
                       'Garden of red roses and white lilies (manifested desire harmonized with pure thought)'],
        'professions': [   'Sales, marketing, and communication',
                           'Information technology and computing',
                           'Public speaking and coaching',
                           'Magicians, illusionists, and entertainers',
                           'Entrepreneurs and strategic negotiators'],
        'upright': {   'keywords': ['Manifestation', 'Resourcefulness', 'Power', 'Inspired Action', 'Mental Mastery'],
                       'general': 'As Above, So Below. You hold all four elemental tools—wand, cup, sword, and '
                                  'pentacle. The universe confirms you have everything required to materialize your '
                                  'vision.',
                       'love': 'Magnetic communication, mutual intellectual spark, and the power to manifest your '
                               'ideal partnership dynamics.',
                       'career': 'Peak eloquence, successful presentations, entrepreneurial breakthrough, and '
                                 'mastering diverse professional skills.',
                       'finance': 'Active financial creation; translating intellectual acumen and creativity into '
                                  'tangible income streams.',
                       'spiritual': 'Direct connection between conscious intention and physical reality; working with '
                                    'cosmic energy purposefully.'},
        'reversed': {   'keywords': ['Manipulation', 'Untapped Potential', 'Deception', 'Scattered Focus', 'Trickery'],
                        'general': 'Reversed, warns of misdirected willpower, illusionary salesmanship, or squandering '
                                   'potent talents on trivial pursuits.',
                        'love': 'Mixed signals, superficial charm masking insecurity, or manipulative relationship '
                                'dynamics.',
                        'career': 'Imposter syndrome, broken professional promises, or brilliant ideas left unexecuted '
                                  'due to lack of focus.',
                        'finance': 'Guarding against get-rich-quick schemes, deceitful contracts, or miscalculated '
                                   'investments.',
                        'spiritual': 'Misusing mental energy for ego validation rather than selfless spiritual '
                                     'alignment.'},
        'remedy': 'Offer green leaves (Durva) to Lord Ganesha on Wednesdays. Wear emerald or green tourmaline to '
                  "strengthen Budha's intellect.",
        'affirmation': 'I channel cosmic energy into tangible form with pure intent, integrity, and focused mastery.'},
    {   'id': 'the_high_priestess',
        'name': 'The High Priestess',
        'arcana': 'major',
        'suit': None,
        'number': 2,
        'element': 'Water',
        'astrology': 'Moon / Cancer',
        'vedic_graha': 'Chandra',
        'image_slug': 'the-high-priestess',
        'numerology': '2',
        'timing_window': 'July 15 – August 14 (Cancer)',
        'timing_season': 'Summer',
        'timing_speed': 'Lunar Cycle (28 Days) / Intuitive',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Intuition, sacred mysteries, subconscious wisdom, divine feminine knowledge.',
        'symbols': [   "Solomon's temple pillars (B = Boaz / Strength / Black / Passive, J = Jachin / Establishment / "
                       'White / Active)',
                       'Pomegranates and palms tapestry (sacred fertility and esoteric veil)',
                       'TORA scroll partially concealed in mantle (divine cosmic law revealed only to the initiated)',
                       'Horned crown with lunar orb (Triple Goddess / Hathor / lunar phases)',
                       'Crescent moon resting at feet (mastery of tidal subconscious and emotional depths)'],
        'professions': [   'Healers and holistic therapists',
                           'Astrologers, tarot readers, and numerologists',
                           'Psychologists and psychoanalysts',
                           'Spiritual counselors and confidential advisors',
                           'Researchers of esoteric and occult subjects'],
        'upright': {   'keywords': ['Intuition', 'Sacred Knowledge', 'Divine Feminine', 'Subconscious', 'Mystery'],
                       'general': 'The guardian of the cosmic veil. Answers will not come from loud logic today, but '
                                  'from quiet introspection, psychic whispers, and vivid dreams.',
                       'love': 'Deep soulful telepathic resonance, unspoken mutual understanding, or uncovering sacred '
                               'hidden feelings.',
                       'career': 'Trusting gut instinct in strategic decisions; keeping critical projects confidential '
                                 'until fully formed.',
                       'finance': 'Maintain discretion regarding wealth; trust your intuition when sensing hidden '
                                  'clauses in negotiations.',
                       'spiritual': 'Akashic access, deep meditation, kundalini awakening, and honoring the divine '
                                    'receptive wisdom within.'},
        'reversed': {   'keywords': [   'Secrets',
                                        'Suppressed Intuition',
                                        'Superficiality',
                                        'Emotional Isolation',
                                        'Deceit'],
                        'general': 'Reversed, indicates silencing your inner knowing to satisfy external expectations, '
                                   'leading to confusion and doubt.',
                        'love': 'Hidden agendas, emotional withdrawal, or ignoring glaring red flags your intuition '
                                'warned you about.',
                        'career': 'Hidden workplace politics, gossip, or disregarding inner warnings about a toxic '
                                  'collaborator.',
                        'finance': 'Information being withheld from you; do not commit funds without independent '
                                   'audit.',
                        'spiritual': 'Disconnection from dreams, mental chatter drowning out the sacred whisper of the '
                                     'soul.'},
        'remedy': "Drink water from a silver cup. Meditate during twilight (Sandhya) chanting 'Om Chandraya Namah' to "
                  'balance lunar Prana.',
        'affirmation': 'I honor the quiet sanctuary of my intuition; all sacred knowledge reveals itself in divine '
                       'timing.'},
    {   'id': 'the_empress',
        'name': 'The Empress',
        'arcana': 'major',
        'suit': None,
        'number': 3,
        'element': 'Earth',
        'astrology': 'Venus / Taurus & Libra',
        'vedic_graha': 'Shukra',
        'image_slug': 'the-empress',
        'numerology': '3',
        'timing_window': 'May 15 – June 14 (Taurus) & October 16 – November 14 (Libra)',
        'timing_season': 'Spring & Autumn',
        'timing_speed': 'Gestational / Steady',
        'yes_no': 'YES Card',
        'one_liner': 'Abundance, fertility, unconditional love, creative fruition, sensory luxury.',
        'symbols': [   'Crown of 12 twelve-pointed stars (the twelve zodiac signs and celestial dominion)',
                       'Heart-shaped stone shield inscribed with Venus symbol (unconditional love and sovereign '
                       'beauty)',
                       'Golden wheat field in foreground (bountiful harvest, nourishment, agricultural wealth)',
                       'Cascading waterfall and winding river (life-giving emotional abundance and subconscious '
                       'fertility)',
                       'Pomegranate-patterned loose robe (maternal pregnancy, sensuality, and creative conception)'],
        'professions': [   'Beauty, cosmetics, and fashion design',
                           'Interior design and home architecture',
                           'Hospitality, culinary arts, and luxury lodging',
                           'Childcare, obstetrics, and maternal healthcare',
                           'Organic agriculture and horticulture'],
        'upright': {   'keywords': ['Abundance', 'Fertility', 'Sensuality', 'Nurturing', 'Creative Flowering'],
                       'general': 'The supreme archetype of Mother Nature and luxury. Projects, relationships, and '
                                  'finances are entering a lush season of fruitful harvest.',
                       'love': 'Unconditional affection, blossoming romance, marital harmony, pregnancy, or deep '
                               'emotional fulfillment.',
                       'career': 'Creative projects blossoming, artistic recognition, cultivating a supportive and '
                                 'prosperous work atmosphere.',
                       'finance': 'Bountiful material abundance, profitable investments, and enjoying luxurious '
                                  'comfort with gratitude.',
                       'spiritual': 'Connecting with Mother Earth, revering the sacred beauty of embodiment and '
                                    'sensual gratitude.'},
        'reversed': {   'keywords': ['Creative Block', 'Dependence', 'Smothering', 'Neglect', 'Material Emptiness'],
                        'general': 'Reversed, signifies feeling emotionally depleted, over-giving to others while '
                                   'starving your own soul.',
                        'love': 'Codependency, feeling unappreciated, or suffocating love with possessiveness.',
                        'career': 'Burnout, creative stagnation, or a hostile work environment devoid of aesthetic '
                                  'appreciation.',
                        'finance': 'Extravagant overspending to compensate for inner emotional void, or financial '
                                   'neglect.',
                        'spiritual': 'Neglecting body health as a temple; alienation from natural grounding rhythms.'},
        'remedy': "Donate white flowers or rice on Fridays. Chant 'Om Shukraya Namah' to invoke Venusian luxury and "
                  'grace.',
        'affirmation': 'I am an open channel of cosmic abundance, beauty, and nourishing love.'},
    {   'id': 'the_emperor',
        'name': 'The Emperor',
        'arcana': 'major',
        'suit': None,
        'number': 4,
        'element': 'Fire',
        'astrology': 'Aries',
        'vedic_graha': 'Mangal',
        'image_slug': 'the-emperor',
        'numerology': '4',
        'timing_window': 'April 13 – May 14 (Aries)',
        'timing_season': 'Spring',
        'timing_speed': 'Decisive / Direct',
        'yes_no': 'YES Card',
        'one_liner': 'Authority, structure, discipline, sovereign leadership, protective power.',
        'symbols': [   'Stone cube throne carved with 4 ram heads (Aries / unyielding martial leadership)',
                       'Golden orb in left hand and Crux Ansata (Ankh) in right (sovereignty over matter and life '
                       'force)',
                       'Iron armor beneath crimson mantle (readiness for strategic battle and sovereign statecraft)',
                       'Barren, jagged stone mountains in background (rock-solid boundaries and stoic endurance)',
                       'Long white beard (elder wisdom, established authority, and proven competence)'],
        'professions': [   'Executive leadership, CEOs, and founders',
                           'Self-employment and independent contractors',
                           'Government officials, civil service, and state administration',
                           'Military officers, police superintendents, and defense chiefs',
                           'Judges, legal authorities, and institutional regulators'],
        'upright': {   'keywords': ['Authority', 'Structure', 'Leadership', 'Discipline', 'Solid Foundation'],
                       'general': 'The archetype of divine masculine order. It is time to organize your realm, '
                                  'establish healthy boundaries, and lead with unwavering integrity.',
                       'love': 'Stability, steadfast commitment, protective devotion, and building a secure domestic '
                               'empire together.',
                       'career': 'Executive promotion, entrepreneurial sovereignty, strategic organization, and '
                                 'commanding professional respect.',
                       'finance': 'Rock-solid financial architecture, long-term budgeting, and disciplined wealth '
                                  'preservation.',
                       'spiritual': 'Spiritual discipline (Tapasya), daily ritual practice, and mastering mental '
                                    'self-governance.'},
        'reversed': {   'keywords': ['Tyranny', 'Rigidity', 'Lack of Discipline', 'Power Struggle', 'Domination'],
                        'general': 'Reversed, signals authoritarian control, micromanagement, or conversely, complete '
                                   'chaos due to lack of self-discipline.',
                        'love': 'Power struggles, emotional coldness, demanding submission, or an unyielding partner.',
                        'career': 'Clashes with domineering superiors, bureaucratic gridlock, or ineffective '
                                  'rebellious leadership.',
                        'finance': 'Financial disorganization, tax penalties, or rigid refusal to adapt to market '
                                   'shifts.',
                        'spiritual': 'Dogmatic fundamentalism, mistaking harsh asceticism for true spiritual '
                                     'enlightenment.'},
        'remedy': "Perform Surya Namaskar at dawn. Chant 'Om Bhaumaya Namah' to elevate Mars energy into noble "
                  'courage.',
        'affirmation': 'I govern my life with calm authority, disciplined strength, and benevolent wisdom.'},
    {   'id': 'the_hierophant',
        'name': 'The Hierophant',
        'arcana': 'major',
        'suit': None,
        'number': 5,
        'element': 'Earth',
        'astrology': 'Taurus',
        'vedic_graha': 'Guru',
        'image_slug': 'the-hierophant',
        'numerology': '5',
        'timing_window': 'May 15 – June 14 (Taurus)',
        'timing_season': 'Spring',
        'timing_speed': 'Measured / Institutional',
        'yes_no': 'YES Card',
        'one_liner': 'Traditional wisdom, spiritual guidance, mentorship, moral integrity, institutional blessings.',
        'symbols': [   'Triple-tiered papal crown (sovereignty over physical, astral, and spiritual realms)',
                       'Triple cross scepter in left hand (the three spiritual worlds and virtues)',
                       'Two crossed golden and silver keys at feet (conscious knowledge and subconscious mysteries)',
                       'Two kneeling priests / acolytes (direct transmission of sacred doctrine from guru to disciple)',
                       'Twin grey stone pillars (tradition and structural endurance of sacred truth)'],
        'professions': [   'Teachers, professors, and educational leaders',
                           'Spiritual gurus, priests, and institutional clergy',
                           'Mentors, counselors, and vocational guides',
                           'Historians, archivists, and cultural preservationists',
                           'Corporate ethics officers and compliance advisors'],
        'upright': {   'keywords': ['Spiritual Wisdom', 'Tradition', 'Mentorship', 'Institutions', 'Conformity'],
                       'general': 'The bridge between heaven and earth. Seek trusted counsel, honor time-tested '
                                  'principles, and align your endeavors with ethical wisdom.',
                       'love': 'Traditional courtship, shared spiritual values, formal marriage vows, and lasting '
                               'commitment.',
                       'career': 'Success within established institutions, seeking professional mentors, '
                                 'certification, and pedagogical excellence.',
                       'finance': 'Conservative, institutional investments; seek advice from reputable certified '
                                  'financial advisors.',
                       'spiritual': 'Adhering to lineage teachings, studying sacred scriptures, and participating in '
                                    'uplifting communal rituals.'},
        'reversed': {   'keywords': ['Rebellion', 'Unconventional Beliefs', 'Dogma', 'Hypocrisy', 'New Paradigms'],
                        'general': 'Reversed, challenges stifling dogmas, outdated societal scripts, and corrupt '
                                   'institutions that impede authentic spiritual growth.',
                        'love': 'Unconventional relationship models, breaking free from familial marriage pressure, or '
                                'mismatched core values.',
                        'career': 'Stifled by corporate red tape, questioning industry ethics, or departing rigid '
                                  'hierarchical organizations.',
                        'finance': 'Exploring alternative investments (crypto, grassroots cooperatives) while avoiding '
                                   'rogue unvetted schemes.',
                        'spiritual': 'Forging your own personalized spiritual path, discarding dogmas, and becoming '
                                     'your own inner priest.'},
        'remedy': "Donate yellow grains (Chana Dal) or holy books to students on Thursdays. Chant 'Om Brihaspataye "
                  "Namah'.",
        'affirmation': 'I anchor eternal wisdom into my daily life, guided by truth, reverence, and righteous action.'},
    {   'id': 'the_lovers',
        'name': 'The Lovers',
        'arcana': 'major',
        'suit': None,
        'number': 6,
        'element': 'Air',
        'astrology': 'Gemini',
        'vedic_graha': 'Shukra',
        'image_slug': 'the-lovers',
        'numerology': '6',
        'timing_window': 'June 15 – July 14 (Gemini)',
        'timing_season': 'Summer',
        'timing_speed': 'Immediate Choice',
        'yes_no': 'YES Card',
        'one_liner': 'Soul connection, divine harmony, values alignment, crossroads of moral choice.',
        'symbols': [   'Archangel Raphael (angel of healing, air, and divine blessings over human hearts)',
                       'Tree of Life with 12 fiery fruit behind the man (solar consciousness and divine spark)',
                       'Tree of Knowledge of Good and Evil with serpent behind the woman (subconscious wisdom and '
                       'primal temptation)',
                       'Volcanic mountain peak in background (passionate ascent and dynamic balance of duality)',
                       'Naked figures standing before each other (unmasked authenticity and divine vulnerability)'],
        'professions': [   'Marriage and relationship counseling',
                           'Creative partnerships and artistic duos',
                           'Human resources and workplace mediation',
                           'Diplomats and international peacemakers',
                           'Matchmakers and aesthetic stylists'],
        'upright': {   'keywords': ['Sacred Union', 'Soul Connection', 'Harmony', 'Values Alignment', 'Moral Choice'],
                       'general': 'The cosmic union of opposites. You are standing at a profound crossroads where '
                                  'authentic love and aligned values must guide your choices.',
                       'love': 'Profound soulmate connection, mutual devotion, unconditional acceptance, and ecstatic '
                               'sexual/emotional harmony.',
                       'career': 'Harmonious business partnerships, shared vision with colleagues, and aligning work '
                                 'with your true soul values.',
                       'finance': 'Joint financial ventures, ethical investment decisions, and financial peace '
                                  'achieved through mutual transparency.',
                       'spiritual': 'Internal alchemy; balancing the inner sacred masculine and sacred feminine '
                                    'energies within yourself.'},
        'reversed': {   'keywords': ['Disharmony', 'Values Misalignment', 'Conflict', 'Indecision', 'Temptation'],
                        'general': 'Reversed, exposes dissonance between two partners or internal conflict between ego '
                                   'desires and spiritual principles.',
                        'love': 'Communication breakdown, conflicting life visions, emotional infidelity, or staying '
                                'in a bond out of codependency.',
                        'career': 'Friction between business partners, conflicting work ethics, or compromises that '
                                  'violate your integrity.',
                        'finance': 'Financial disagreements between spouses, hidden debts, or hasty joint investments '
                                   'ending in regret.',
                        'spiritual': 'Internal fragmentation, projecting disowned shadow traits onto your partner '
                                     'instead of integrating them.'},
        'remedy': "Offer fragrant lotus flowers or rose water to Lakshmi-Narayana on Fridays. Chant 'Om Shukraya "
                  "Namah'.",
        'affirmation': 'I choose love rooted in truth, honoring the sacred reflection of the divine within myself and '
                       'my partner.'},
    {   'id': 'the_chariot',
        'name': 'The Chariot',
        'arcana': 'major',
        'suit': None,
        'number': 7,
        'element': 'Water',
        'astrology': 'Cancer',
        'vedic_graha': 'Mangal',
        'image_slug': 'the-chariot',
        'numerology': '7',
        'timing_window': 'July 15 – August 14 (Cancer)',
        'timing_season': 'Summer',
        'timing_speed': 'Rapid Once Directed',
        'yes_no': 'YES Card',
        'one_liner': 'Triumphant willpower, overcoming obstacles, focused momentum, self-mastery.',
        'symbols': [   'Two sphinxes (black and white, representing conflicting polarities steered without reins by '
                       'willpower alone)',
                       'Canopy of blue celestial stars (divine guidance and alignment with higher cosmic laws)',
                       'Armor with crescent moons and square breastplate (earthly will protecting tender emotional '
                       'depths)',
                       'Winged sun disk on chariot front (triumph of divine solar spirit over earthly matter)',
                       'Walled city left behind (transcending past comfort zones to venture into heroic conquest)'],
        'professions': [   'Transportation, logistics, and automotive engineering',
                           'Professional athletics and sports management',
                           'Project managers and high-velocity coordinators',
                           'Military drivers, aviators, and navigators',
                           'Ambitious venture leads and turnaround specialists'],
        'upright': {   'keywords': ['Victory', 'Willpower', 'Determination', 'Overcoming Obstacles', 'Focused Drive'],
                       'general': 'Triumphant forward momentum. You possess the mental mastery and disciplined will '
                                  'required to steer conflicting forces to absolute victory.',
                       'love': 'Pursuing romantic goals with confidence, navigating emotional turbulence together, and '
                               'overcoming relationship obstacles.',
                       'career': 'Decisive career breakthrough, triumphing over fierce competition, promotions, and '
                                 'executing complex projects with precision.',
                       'finance': 'Financial momentum, achieving aggressive savings goals, disciplined debt '
                                  'elimination, and purchasing transport/assets.',
                       'spiritual': "Harnessing the mind's unruly desires; directing the chariot of the body toward "
                                    'spiritual self-realization.'},
        'reversed': {   'keywords': ['Loss of Direction', 'Aggression', 'Lack of Control', 'Obstacles', 'Burnout'],
                        'general': 'Reversed, warns of erratic momentum, road rage, aggressive impatience, or losing '
                                   'the reins of your endeavors.',
                        'love': 'Pushing an agenda too aggressively, power struggles, or emotional insensitivity '
                                'alienating your partner.',
                        'career': 'Stalled projects, aggressive workplace conflict, burnout from relentless pushing, '
                                  'or derailment.',
                        'finance': 'Impulsive expenditures, aggressive risky speculation, or costly '
                                   'vehicular/transport breakdowns.',
                        'spiritual': 'Spiritual egoism, using spiritual practices to dominate others rather than '
                                     'cultivating humility and surrender.'},
        'remedy': "Donate food or jaggery to laborers on Tuesdays. Chant 'Om Angarakaya Namah' to align martial drive "
                  'with righteous purpose.',
        'affirmation': 'With unwavering focus and disciplined will, I overcome every obstacle and triumph in my '
                       'purpose.'},
    {   'id': 'strength',
        'name': 'Strength',
        'arcana': 'major',
        'suit': None,
        'number': 8,
        'element': 'Fire',
        'astrology': 'Leo',
        'vedic_graha': 'Surya',
        'image_slug': 'strength',
        'numerology': '8',
        'timing_window': 'August 15 – September 15 (Leo)',
        'timing_season': 'Summer',
        'timing_speed': 'Enduring / Steady',
        'yes_no': 'YES Card',
        'one_liner': 'Compassionate courage, gentle mastery over animal instincts, moral fortitude, patience.',
        'symbols': [   "Gentle maiden closing the red lion's jaw (compassion and spiritual power conquering raw animal "
                       'force)',
                       "Infinity symbol (Lemniscate over maiden's head representing infinite spiritual mastery)",
                       'Garland of fresh roses encircling maiden and lion (sweet harmony between higher mind and '
                       'primal instinct)',
                       'White robe (purity of conscious motive and moral integrity)',
                       'Lush green hills and blue sky (peaceful vitality and grounded calm)'],
        'professions': [   'Animal trainers, handlers, and veterinarians',
                           'Psychotherapists, trauma counselors, and behavioral specialists',
                           'Hospice care, nursing, and rehabilitation professionals',
                           'Mediation experts and non-violent conflict resolvers',
                           'Humanitarian leaders and patient negotiators'],
        'upright': {   'keywords': ['Inner Strength', 'Courage', 'Compassion', 'Patience', 'Gentle Mastery'],
                       'general': 'True strength is quiet, gentle, and unshakable. You tame raw passions, fear, and '
                                  'adversity through compassion and enduring patience.',
                       'love': "Patient devotion, unconditional acceptance of partner's flaws, soothing explosive "
                               'temperaments with loving kindness.',
                       'career': 'Steady professional resilience, handling difficult personalities with tact, and '
                                 'commanding respect through calm composure.',
                       'finance': 'Disciplined financial temperament; resisting impulse urges and methodically '
                                  'building long-term security.',
                       'spiritual': 'Conquering primal instincts (Kama, Krodha, Lobha) through love and devotional '
                                    'Prana rather than violent suppression.'},
        'reversed': {   'keywords': ['Self-Doubt', 'Weakness', 'Explosive Temper', 'Insecurity', 'Overwhelmed'],
                        'general': 'Reversed, indicates giving in to fear, self-sabotaging doubt, explosive temper '
                                   'outbursts, or feeling overwhelmed by base instincts.',
                        'love': 'Insecurity triggering jealous tirades, emotionally codependent submission, or letting '
                                'pride ruin intimacy.',
                        'career': 'Cracking under workplace pressure, imposter syndrome, or letting anger destroy '
                                  'professional relationships.',
                        'finance': 'Compulsive spending driven by emotional distress, financial anxiety, or lack of '
                                   'financial self-discipline.',
                        'spiritual': 'Feeling spiritually depleted, succumbing to depressive self-criticism, or '
                                     'disconnecting from inner courage.'},
        'remedy': "Feed stray animals, especially dogs and cows. Chant the Aditya Hridaya Stotra or 'Om Suryaya Namah' "
                  'to revitalize inner fire.',
        'affirmation': 'I master all inner challenges with quiet grace, love, and unshakable inner strength.'},
    {   'id': 'the_hermit',
        'name': 'The Hermit',
        'arcana': 'major',
        'suit': None,
        'number': 9,
        'element': 'Earth',
        'astrology': 'Virgo',
        'vedic_graha': 'Ketu',
        'image_slug': 'the-hermit',
        'numerology': '9',
        'timing_window': 'September 16 – October 15 (Virgo)',
        'timing_season': 'Autumn',
        'timing_speed': 'Patient / Contemplative',
        'yes_no': 'MAYBE / WAIT (YES for solitary soul-searching)',
        'one_liner': 'Soul-searching, solitary reflection, inner guidance, shining light in darkness.',
        'symbols': [   "Lantern holding 6-pointed Star of David (Merkaba / Seal of Solomon illuminating the seeker's "
                       'path)',
                       'Tall golden staff in left hand (grounded spiritual authority and stability on treacherous '
                       'peaks)',
                       'Grey hooded cloak (detachment, ascetic modesty, and invisibility from worldly distractions)',
                       'Snow-covered mountain peak (lofty pinnacle of spiritual achievement, solitude, and purity)',
                       "Downward gaze (humility, introspection, and watching one's steps with care)"],
        'professions': [   'Independent researchers, archivists, and scholars',
                           'Spiritual monks, ascetics, and meditation teachers',
                           'Data analysts, diagnostic clinicians, and philosophers',
                           'Authors, editors, and solitary creators',
                           'Lighthouse keepers, forest rangers, and watchmen'],
        'upright': {   'keywords': [   'Introspection',
                                       'Soul-Searching',
                                       'Solitude',
                                       'Inner Guidance',
                                       'Spiritual Mentor'],
                       'general': 'Withdraw from external noise. The beacon of wisdom you seek is not outside in the '
                                  'marketplace, but inside the sanctuary of your own soul.',
                       'love': 'A period of healthy soul-searching, taking time to understand your relationship needs, '
                               'or connecting on a deep intellectual level.',
                       'career': 'Mastery through solitary research, consulting an experienced elder mentor, and '
                                 'stepping back from corporate politics.',
                       'finance': 'Frugal living, reviewing accounts with meticulous care, and ignoring speculative '
                                  'market hype.',
                       'spiritual': 'Deep meditative retreat, silence (Mauna), uncovering esoteric wisdom, and holding '
                                    'up your lantern to guide seekers.'},
        'reversed': {   'keywords': ['Isolation', 'Loneliness', 'Anti-Social', 'Stubbornness', 'Paranoia'],
                        'general': 'Reversed, warns against toxic isolation, bitterness toward humanity, refusing wise '
                                   'counsel, or losing yourself in escapist seclusion.',
                        'love': 'Cold emotional withdrawal, walling yourself off from intimacy, or painful feelings of '
                                'loneliness within a partnership.',
                        'career': 'Professional stagnation due to poor communication, stubborn resistance to team '
                                  'collaboration, or feeling invisible.',
                        'finance': 'Excessive penny-pinching leading to misery, or conversely, neglecting financial '
                                   'duties due to aloof detachment.',
                        'spiritual': 'Spiritual pride, judging others as un-enlightened, or falling into nihilistic '
                                     'despair.'},
        'remedy': "Observe silence (Mauna) for one hour on Saturdays. Chant 'Om Ketave Namah' and meditate in a quiet, "
                  'dark sanctuary.',
        'affirmation': 'In the quiet sanctum of my soul, divine truth shines brightly to illuminate my path.'},
    {   'id': 'wheel_of_fortune',
        'name': 'The Wheel of Fortune',
        'arcana': 'major',
        'suit': None,
        'number': 10,
        'element': 'Fire',
        'astrology': 'Jupiter / Sagittarius',
        'vedic_graha': 'Guru',
        'image_slug': 'wheel-of-fortune',
        'numerology': '10 (1)',
        'timing_window': 'December 15 – January 13 (Sagittarius)',
        'timing_season': 'Winter',
        'timing_speed': 'Karmic Turning Point',
        'yes_no': 'YES Card',
        'one_liner': 'Karmic turning point, stroke of divine luck, cyclical evolution, cosmic destiny.',
        'symbols': [   'Golden wheel with Hebrew letters Y-H-V-H and letters T-O-R-A / R-O-T-A (Taro / Cosmic Law)',
                       'Sphinx atop wheel with sword (divine equilibrium and solving the riddle of destiny)',
                       'Hermanubis rising on right (wisdom and soul ascending through spiritual evolution)',
                       'Typhon snake descending on left (primal matter and chaos descending into rebirth)',
                       'Four winged creatures in corners (Lion, Bull, Eagle, Human studying holy books / 4 fixed '
                       'signs)'],
        'professions': [   'Financial market traders, stockbrokers, and venture capitalists',
                           'Trend forecasters, data actuaries, and economic analysts',
                           'Gaming, lottery, and casino operations',
                           'Meteorologists and climate cycle scientists',
                           'Astrologers, karmic readers, and life cycle strategists'],
        'upright': {   'keywords': ['Destiny', 'Karmic Turning Point', 'Good Luck', 'Life Cycles', 'Inevitable Change'],
                       'general': 'The great wheel turns in your favor. A sudden stroke of divine serendipity is '
                                  'arriving; embrace the upward swing with humility and gratitude.',
                       'love': 'Karmic fated meeting, serendipitous romantic encounter, turning a corner toward joy, '
                               'and positive shifts in bond.',
                       'career': 'Sudden career breakthrough, fortuitous promotion, right place at the right time, and '
                                 'favorable industry shifts.',
                       'finance': 'Unexpected windfall, lucrative speculative gains, and sudden relief from financial '
                                  'bottlenecks.',
                       'spiritual': 'Understanding the laws of Karma; realizing that external cycles are temporary '
                                    'classrooms for soul evolution.'},
        'reversed': {   'keywords': ['Bad Luck', 'Negative Cycle', 'Resistance to Change', 'Setbacks', 'Delayed Karma'],
                        'general': 'Reversed, signals a temporary downward dip of the cycle, requiring patience, '
                                   'acceptance, and learning the lesson without panic.',
                        'love': 'Challenging relationship phase, feeling like luck is against you, or repeating old '
                                'toxic karmic loops.',
                        'career': 'Sudden corporate restructuring, unfavorable timing for expansion, or temporary '
                                  'setbacks in ventures.',
                        'finance': 'Financial downturn, avoiding gambles, budgeting conservatively until the wheel '
                                   'turns again.',
                        'spiritual': 'Feeling victimized by destiny; learning surrender and recognizing that night '
                                     'always precedes dawn.'},
        'remedy': "Donate yellow split peas (Chana Dal) and bananas to temples on Thursdays. Chant 'Om Brihaspataye "
                  "Namah'.",
        'affirmation': 'I ride the cycles of cosmic destiny with grace, knowing all turns of the wheel serve my '
                       'highest evolution.'},
    {   'id': 'justice',
        'name': 'Justice',
        'arcana': 'major',
        'suit': None,
        'number': 11,
        'element': 'Air',
        'astrology': 'Libra',
        'vedic_graha': 'Shani',
        'image_slug': 'justice',
        'numerology': '11 (2)',
        'timing_window': 'October 16 – November 14 (Libra)',
        'timing_season': 'Autumn',
        'timing_speed': 'Measured / Legal Timing',
        'yes_no': 'MAYBE Card (Depends on truth & ethical conduct)',
        'one_liner': 'Karmic justice, balanced truth, legal victory for the righteous, objective clarity.',
        'symbols': [   'Scales of balance in left hand (impartial, rigorous weighing of deeds and motivations)',
                       'Double-edged upright sword in right hand (cleaving through falsehood, logical clarity and '
                       'two-fold consequence)',
                       'Purple veil suspended between grey stone pillars (sanctity of divine law and moral '
                       'objectivity)',
                       'Square crown clasp (foundation, earthly order, and uncorrupted governance)',
                       'Slightly revealed white slipper (stepping forward with clean, unblemished motives)'],
        'professions': [   'Judges, magistrates, and appellate attorneys',
                           'Arbitrators, mediators, and legal consultants',
                           'Compliance officers, forensic auditors, and tax specialists',
                           'Civil rights champions and ethical watchdogs',
                           'Philosophy professors and moral ethicists'],
        'upright': {   'keywords': ['Justice', 'Fairness', 'Truth', 'Karmic Balance', 'Legal Victory'],
                       'general': 'The cosmic law of cause and effect. Truth prevails, legal matters resolve fairly, '
                                  'and ethical integrity is rewarded with vindication.',
                       'love': 'Fair give-and-take, honest transparency, legal marriage contracts, and treating your '
                               'partner with mutual respect.',
                       'career': 'Legal dispute resolved in your favor, ethical contracts signed, fair workplace '
                                 'evaluations, and professional integrity.',
                       'finance': 'Equitable financial settlements, fair contracts, recovering debts, and balanced '
                                  'accounting.',
                       'spiritual': 'Karmic accountability; taking complete ownership of your deeds and living in '
                                    'alignment with universal cosmic law (Rita).'},
        'reversed': {   'keywords': [   'Injustice',
                                        'Dishonesty',
                                        'Unfair Blame',
                                        'Legal Complications',
                                        'Avoiding Responsibility'],
                        'general': 'Reversed, warns of unfair accusations, biased rulings, unethical conduct, or '
                                   'evading personal accountability for past errors.',
                        'love': 'Unfair criticism, blame games, dishonest motives, or messy legal divorce disputes.',
                        'career': 'Unfair performance review, workplace discrimination, dishonest colleagues, or legal '
                                  'contractual disputes.',
                        'finance': 'Unfair financial penalties, fraudulent dealings, or disputes over inheritance and '
                                   'shared assets.',
                        'spiritual': 'Hypocrisy, preaching virtues you fail to practice, and attempting to bargain '
                                     'with universal karmic law.'},
        'remedy': "Donate black sesame seeds or iron utensils to the needy on Saturdays. Chant 'Om Sham Shanaicharaya "
                  "Namah'.",
        'affirmation': 'I stand firmly in truth, trusting the unerring balance of cosmic justice in all my affairs.'},
    {   'id': 'the_hanged_man',
        'name': 'The Hanged Man',
        'arcana': 'major',
        'suit': None,
        'number': 12,
        'element': 'Water',
        'astrology': 'Neptune / Pisces',
        'vedic_graha': 'Ketu',
        'image_slug': 'the-hanged-man',
        'numerology': '12 (3)',
        'timing_window': 'March 13 – April 12 (Pisces)',
        'timing_season': 'Spring',
        'timing_speed': 'Suspended / Surrender',
        'yes_no': 'NO Card (Wait / Pause / Sacrifice required)',
        'one_liner': 'Willing surrender, paradigm shift, pausing the worldly rush to attain higher enlightenment.',
        'symbols': [   'Suspended upside-down from living T-shaped tree (world turned on its head, seeing reality from '
                       'higher dimension)',
                       'Golden halo of radiant light around head (enlightenment achieved through ego surrender)',
                       'Right leg crossed behind left forming number 4 (manifested world suspended in spiritual '
                       'contemplation)',
                       'Calm, serene, blissful facial expression (willing self-sacrifice and spiritual peace, not '
                       'suffering)',
                       'Blue tunic and red tights (primal passion subdued beneath calm spiritual tranquility)'],
        'professions': [   'Yoga gurus, spiritual monks, and ascetics',
                           'Meditation practitioners and breathwork therapists',
                           'Surrealist painters, avant-garde artists, and poets',
                           'Hospice caregivers and humanitarian volunteers',
                           'Deep philosophers and independent paradigm shifters'],
        'upright': {   'keywords': ['Surrender', 'New Perspective', 'Letting Go', 'Pause', 'Spiritual Enlightenment'],
                       'general': 'A willing pause. Forcing worldly outcomes now is futile. Surrender control, shift '
                                  'your perspective 180 degrees, and divine clarity will dawn.',
                       'love': "Letting go of relationship control, pausing to see things from your partner's "
                               'viewpoint, and making sacred compromises.',
                       'career': 'A temporary project hiatus, stepping back to re-evaluate strategies, and sacrificing '
                                 'short-term gains for long-term vision.',
                       'finance': 'Financial freeze or pause; do not make aggressive moves, re-evaluate priorities and '
                                  'practice non-attachment.',
                       'spiritual': 'Surrendering the ego to the divine will (Ishvara Pranidhana); spiritual awakening '
                                    'through non-resistance.'},
        'reversed': {   'keywords': ['Resistance', 'Futile Martyrdom', 'Stall', 'Stubbornness', 'Disillusionment'],
                        'general': 'Reversed, indicates stubborn resistance to necessary change, playing the martyr, '
                                   'or useless procrastination disguised as spirituality.',
                        'love': 'Resentment from one-sided sacrifices, staying in a dead connection out of guilt, or '
                                'refusing to compromise.',
                        'career': 'Spinning wheels without progress, complaining without taking action, or refusing to '
                                  'adapt to unavoidable industry pivots.',
                        'finance': 'Financial sacrifices that yield zero return; bailing out others at the expense of '
                                   'your own security.',
                        'spiritual': 'Spiritual bypassing; pretending to be detached while seething with suppressed '
                                     'frustration.'},
        'remedy': 'Offer pure water to a Peepal tree on Saturdays. Practice Yoga Nidra or deep breath surrender to '
                  'release chronic tension.',
        'affirmation': 'I surrender egoic control; in letting go, I discover the limitless peace and clarity of divine '
                       'wisdom.'},
    {   'id': 'death',
        'name': 'Death',
        'arcana': 'major',
        'suit': None,
        'number': 13,
        'element': 'Water',
        'astrology': 'Scorpio',
        'vedic_graha': 'Ketu',
        'image_slug': 'death',
        'numerology': '13 (4)',
        'timing_window': 'November 15 – December 14 (Scorpio)',
        'timing_season': 'Autumn',
        'timing_speed': 'Inevitable / Transformative',
        'yes_no': 'NO Card (Radical Transformation)',
        'one_liner': 'Radical transformation, ending of an old cycle, profound shedding, rebirth from ashes.',
        'symbols': [   'Black armored skeleton rider on magnificent white horse (unstoppable cosmic transition carried '
                       'by pure vital life force)',
                       'Black banner bearing the 5-petaled Mystic White Rose (purity, immortality, and sacred rebirth)',
                       'Fallen king on ground with crown rolling away (mortality of worldly status before cosmic '
                       'transition)',
                       'Bishop, maiden, and child pleading (inevitability before all strata of human society)',
                       'Rising golden sun between twin pillars in distance (the dawn of immortality and glorious '
                       'rebirth beyond the veil)'],
        'professions': [   'Crisis turnaround experts and organizational restructuring leads',
                           'Grief counselors, palliative therapists, and hospice directors',
                           'Surgeons, trauma specialists, and emergency physicians',
                           'Demolition engineers and hazardous cleanup directors',
                           'Probate attorneys, estate executors, and mortuary directors'],
        'upright': {   'keywords': [   'Transformation',
                                       'End of a Cycle',
                                       'Rebirth',
                                       'Letting Go',
                                       'Inevitable Transition'],
                       'general': 'The great clearing. An outworn phase of your life has fulfilled its karmic purpose '
                                  'and must be released so that glorious new life can be born.',
                       'love': 'End of an obsolete relationship pattern, amicable closure, or profound rebirth of an '
                               'existing bond from its ashes.',
                       'career': 'Leaving a stagnant job, radical industry transition, corporate restructuring, or '
                                 'stepping into a completely new vocation.',
                       'finance': 'Closing unviable ventures, clearing debts, liquidating legacy baggage, and laying '
                                  'fresh financial foundations.',
                       'spiritual': 'Ego-death; shedding old spiritual dogmas and experiencing profound metaphysical '
                                    'regeneration.'},
        'reversed': {   'keywords': [   'Fear of Change',
                                        'Clinging to Past',
                                        'Stagnation',
                                        'Prolonged Agony',
                                        'Resisting Rebirth'],
                        'general': 'Reversed, warns against desperately clinging to what is already spiritually dead, '
                                   'dragging out inevitable pain.',
                        'love': 'Refusing to accept a breakup, staying in a toxic dead bond out of fear of being '
                                'alone, or chronic emotional stagnation.',
                        'career': 'Refusing to look for new work despite clear dead-ends, clinging to obsolete skills, '
                                  'or prolonged organizational rot.',
                        'finance': 'Pouring money into a failing venture, ignoring bankruptcy warnings, or stubborn '
                                   'financial denial.',
                        'spiritual': 'Terror of the unknown; clinging to comforting spiritual illusions rather than '
                                     'embracing transformative truth.'},
        'remedy': "Chant the Maha Mrityunjaya Mantra 'Om Tryambakam Yajamahe...'. Donate old blankets or clothes to "
                  'the needy on Saturdays.',
        'affirmation': 'I fearlessly release what no longer serves me, trusting the radiant rebirth that is already '
                       'unfolding.'},
    {   'id': 'temperance',
        'name': 'Temperance',
        'arcana': 'major',
        'suit': None,
        'number': 14,
        'element': 'Fire',
        'astrology': 'Sagittarius',
        'vedic_graha': 'Guru',
        'image_slug': 'temperance',
        'numerology': '14 (5)',
        'timing_window': 'December 15 – January 13 (Sagittarius)',
        'timing_season': 'Winter',
        'timing_speed': 'Gradual Alchemy',
        'yes_no': 'YES Card',
        'one_liner': 'Divine balance, emotional alchemy, patience, synthesizing opposites into harmony.',
        'symbols': [   'Archangel Michael with flame-red wings (divine fire of higher consciousness and spiritual '
                       'protection)',
                       'Pouring water continuously between two golden cups (harmonizing conscious logic with '
                       'subconscious feeling)',
                       'One foot in water, one foot on dry land (firmly grounded in physical reality while plugged '
                       'into psychic flow)',
                       'Golden solar crown on forehead and winding path to radiant mountain sun (the narrow path of '
                       'spiritual mastery)',
                       'Blooming yellow irises on riverbank (hope, purity, and natural medicinal healing)'],
        'professions': [   'Pharmacists, biochemists, and medicinal chemists',
                           'Holistic healers, naturopaths, and acupuncturists',
                           'Diplomats, peace mediators, and cross-cultural coordinators',
                           'Mixologists, master chefs, and culinary alchemists',
                           'Behavioral therapists and addiction recovery guides'],
        'upright': {   'keywords': ['Balance', 'Moderation', 'Patience', 'Alchemy', 'Divine Harmony'],
                       'general': 'Divine alchemy. You are invited to find the golden mean, blend opposing forces with '
                                  'graceful patience, and heal all discord.',
                       'love': 'Harmonious balance, mutual compromise, peaceful understanding, and soothing emotional '
                               'volatility.',
                       'career': 'Managing complex projects with steady diplomacy, harmonizing diverse team members, '
                                 'and patient progress.',
                       'finance': 'Balanced budgeting, sustainable investments, living comfortably within means, and '
                                  'financial peace of mind.',
                       'spiritual': 'Synthesizing the masculine and feminine, balancing the Chakras, and maintaining '
                                    'serene inner equilibrium.'},
        'reversed': {   'keywords': ['Imbalance', 'Excess', 'Impatience', 'Clashing Extremes', 'Discord'],
                        'general': 'Reversed, warns of extremes, reckless overindulgence, volatile mood swings, and '
                                   'forcing outcomes prematurely.',
                        'love': 'Lack of compromise, explosive emotional overreactions, personality clashes, or '
                                'demanding all-or-nothing terms.',
                        'career': 'Team friction, chaotic multitasking, inability to find common ground, or rushing a '
                                  'delicate project to failure.',
                        'finance': 'Binge spending followed by extreme deprivation; chaotic cash flow due to lack of '
                                   'moderation.',
                        'spiritual': 'Spiritual burn-out; swinging wildly between rigid asceticism and sensory '
                                     'overindulgence.'},
        'remedy': "Drink water stored overnight in a pure copper vessel. Chant 'Om Namo Bhagavate Vasudevaya' on "
                  'Thursdays.',
        'affirmation': 'I blend the opposing currents of my life into perfect divine harmony, peace, and sacred '
                       'balance.'},
    {   'id': 'the_devil',
        'name': 'The Devil',
        'arcana': 'major',
        'suit': None,
        'number': 15,
        'element': 'Earth',
        'astrology': 'Capricorn',
        'vedic_graha': 'Shani',
        'image_slug': 'the-devil',
        'numerology': '15 (6)',
        'timing_window': 'January 14 – February 11 (Capricorn)',
        'timing_season': 'Winter',
        'timing_speed': 'Entangled / Chronic',
        'yes_no': 'NO Card',
        'one_liner': 'Unhealthy attachments, illusions of entrapment, toxic materialism, confronting the shadow.',
        'symbols': [   'Baphomet horned goat demon on half-cube pedestal (perverted material throne of illusion)',
                       'Inverted pentagram over forehead (spirit enslaved to base animal passions)',
                       'Torch pointing downward (burning vital Prana wastefully into lower realms)',
                       'Chained male and female with horned tails (loose neck chains that can be removed at will / '
                       'voluntary bondage)',
                       'Black backdrop (ignorance, darkness of ego, and unexamined subconscious shadow)'],
        'professions': [   'Criminal defense attorneys and legal advocates',
                           'Addiction therapists, detox counselors, and rehab staff',
                           'Debt collection, high-interest lending, and predatory finance',
                           'Entertainment nightlife, nightclub management, and gaming industries',
                           'Shadow therapists and forensic psychological researchers'],
        'upright': {   'keywords': ['Bondage', 'Addiction', 'Materialism', 'Shadow Self', 'Illusion of Trap'],
                       'general': 'Confronting the shadow. You feel trapped by circumstances, but the chains around '
                                  'your neck are loose. Recognize that you hold the power to walk free.',
                       'love': 'Toxic obsession, codependency, sexual manipulation, jealousy, or staying in an abusive '
                               'dynamic out of fear.',
                       'career': 'Feeling trapped in a soulless corporate job for golden handcuffs; unethical '
                                 'workplace practices or toxic bosses.',
                       'finance': 'Crushing debt, predatory loans, gambling losses, or obsessive hoarding of money '
                                  'without joy.',
                       'spiritual': 'Confronting your lower animal nature (Maya and Moha); breaking free from '
                                    'spiritual guilt and self-sabotaging addictions.'},
        'reversed': {   'keywords': [   'Breaking Chains',
                                        'Liberation',
                                        'Reclaiming Power',
                                        'Overcoming Addiction',
                                        'Freedom'],
                        'general': 'Reversed, heralds the glorious breaking of chains, waking up from toxic illusions, '
                                   'and taking your sovereignty back.',
                        'love': 'Leaving a toxic or abusive relationship, overcoming codependency, and establishing '
                                'fierce self-respect.',
                        'career': 'Quitting an exploitative job, refusing unethical compromises, and walking away from '
                                  'toxic workplace politics.',
                        'finance': 'Aggressive debt elimination, overcoming compulsive retail therapy, and regaining '
                                   'financial autonomy.',
                        'spiritual': 'Liberation from guilt and dogmatic fear; integrating the shadow into conscious '
                                     'spiritual strength.'},
        'remedy': 'Recite the Hanuman Chalisa daily at dusk. Light a mustard or sesame oil lamp under a Peepal tree on '
                  'Saturdays.',
        'affirmation': 'I break the chains of illusion and fear; I reclaim my divine power and walk in freedom and '
                       'truth.'},
    {   'id': 'the_tower',
        'name': 'The Tower',
        'arcana': 'major',
        'suit': None,
        'number': 16,
        'element': 'Fire',
        'astrology': 'Mars / Aries',
        'vedic_graha': 'Mangal',
        'image_slug': 'the-tower',
        'numerology': '16 (7)',
        'timing_window': 'April 13 – May 14 (Aries)',
        'timing_season': 'Spring',
        'timing_speed': 'Lightning-Fast / Sudden',
        'yes_no': 'NO Card',
        'one_liner': 'Sudden structural collapse, lightning strike of truth, shattered illusions leading to '
                     'liberation.',
        'symbols': [   'Stone tower struck by jagged lightning bolt (shattering of arrogant ego structures and false '
                       'security)',
                       'Golden crown blasted off turret (abrupt downfall of false pride and superficial status)',
                       '22 Yods / flames of divine fire falling (divine intervention purifying falsehood through '
                       'sacred grace)',
                       'Two figures plummeting into the abyss (abrupt, shocking ejection from outworn comfort zones)',
                       'Black clouds and lightning flash (uncompromising illumination cutting through darkness)'],
        'professions': [   'Emergency first responders, EMTs, and disaster relief workers',
                           'Demolition engineers and structural failure specialists',
                           'Crisis PR managers and corporate turnaround officers',
                           'Forensic auditors and whistleblower investigators',
                           'Radical innovators and disruptive technological creators'],
        'upright': {   'keywords': [   'Sudden Upheaval',
                                       'Shattered Illusions',
                                       'Revelation',
                                       'Breakthrough',
                                       'Liberation'],
                       'general': 'The lightning bolt of cosmic truth strikes. What was built on false foundations '
                                  'collapses abruptly, clearing the ground for indestructible reality.',
                       'love': 'Sudden shocking truth revealed, dramatic breakup of an unsustainable relationship, or '
                               'shattering of illusions.',
                       'career': 'Unexpected termination, corporate upheaval, sudden business disruption, or radical '
                                 'restructuring.',
                       'finance': 'Sudden financial shock, market crash, unexpected emergency expenses, or collapse of '
                                  'speculative schemes.',
                       'spiritual': 'Kundalini breakthrough shattering dogmatic ego structures; painful yet liberating '
                                    'spiritual awakening.'},
        'reversed': {   'keywords': [   'Disaster Averted',
                                        'Delaying the Inevitable',
                                        'Fear of Suffering',
                                        'Internal Upheaval'],
                        'general': 'Reversed, indicates narrowly averting catastrophe, or conversely, desperately '
                                   'clinging to a crumbling edifice whose collapse is inevitable.',
                        'love': 'Holding together a broken partnership through denial, walking on eggshells, or '
                                'internal emotional turmoil.',
                        'career': 'Surviving layoffs with lingering dread, propping up an obsolete business model, or '
                                  'internal crises.',
                        'finance': 'Narrowly escaping bankruptcy, temporary financial bailout, or postponing needed '
                                   'fiscal restructuring.',
                        'spiritual': 'Suppressing an existential spiritual crisis; trying to re-erect ego defenses '
                                     'against divine truth.'},
        'remedy': "Donate blood or red lentils (Masoor Dal) on Tuesdays. Chant 'Om Krim Kalikaye Namah' to dissolve "
                  'obstructions safely.',
        'affirmation': 'As false structures fall away, I stand unshaken upon the indestructible bedrock of eternal '
                       'truth.'},
    {   'id': 'the_star',
        'name': 'The Star',
        'arcana': 'major',
        'suit': None,
        'number': 17,
        'element': 'Air',
        'astrology': 'Aquarius',
        'vedic_graha': 'Shani',
        'image_slug': 'the-star',
        'numerology': '17 (8)',
        'timing_window': 'February 12 – March 12 (Aquarius)',
        'timing_season': 'Late Winter / Spring',
        'timing_speed': 'Guiding / Hopeful',
        'yes_no': 'YES Card',
        'one_liner': 'Renewed hope, cosmic inspiration, healing after the storm, serene faith in destiny.',
        'symbols': [   'Large eight-pointed golden star surrounded by seven smaller stars (Chakras / Pleiades / cosmic '
                       'guidance)',
                       'Naked maiden pouring water from two urns onto earth and sea (nourishing collective unconscious '
                       'and earth without depletion)',
                       'Sacred Ibis bird resting in blooming tree (Thoth / wisdom, divine intellect, and spiritual '
                       'rebirth)',
                       "Clear peaceful night sky (deep serenity, cosmic grace, and calmness following the Tower's "
                       'storm)',
                       'Five streams of living water watering the fertile earth (the five senses purified and '
                       'blessed)'],
        'professions': [   'Astrologers, astronomers, and celestial navigators',
                           'Humanitarian leaders, NGO coordinators, and philanthropists',
                           'Musicians, poets, film directors, and entertainment creators',
                           'Visionary technologists, renewable energy pioneers, and futurists',
                           'Energy healers, Reiki masters, and acupuncture practitioners'],
        'upright': {   'keywords': ['Hope', 'Faith', 'Inspiration', 'Healing', 'Serenity', 'Cosmic Blessing'],
                       'general': 'The peaceful morning star rises after the darkest night. Divine grace, '
                                  'rejuvenation, serene optimism, and boundless creative inspiration flood your life.',
                       'love': 'Deep emotional healing, forgiveness, trusting love again, spiritual soul connection, '
                               'and profound romantic peace.',
                       'career': 'Inspiring creative projects, visionary acclaim, career opportunities aligned with '
                                 'your authentic soul purpose.',
                       'finance': 'Financial recovery, unexpected blessings, peace of mind regarding resources, and '
                                  'steady compounding wealth.',
                       'spiritual': 'Pure spiritual faith, direct connection to the cosmic matrix, opening of the '
                                    'higher chakras, and divine peace.'},
        'reversed': {   'keywords': ['Despair', 'Loss of Faith', 'Discouragement', 'Cynicism', 'Blocked Creativity'],
                        'general': 'Reversed, indicates feeling hopeless, disconnected from the divine, cynical, or '
                                   'failing to see the blessings surrounding you.',
                        'love': 'Pessimism in romance, feeling unworthy of love, carrying past wounds into current '
                                'connection, or emotional despair.',
                        'career': 'Creative block, feeling unappreciated, disillusionment with professional goals, or '
                                  'lack of inspiration.',
                        'finance': 'Worrying about money despite adequate resources; pessimism blinding you to '
                                   'practical economic solutions.',
                        'spiritual': 'Dark night of the soul; feeling abandoned by the universe, skepticism, and '
                                     'spiritual exhaustion.'},
        'remedy': 'Offer pure water to the rising sun daily. Wear aquamarine or lapis lazuli, and chant the Gayatri '
                  'Mantra at dawn.',
        'affirmation': 'My soul shines with radiant hope and cosmic grace; I am guided, protected, and divinely '
                       'blessed.'},
    {   'id': 'the_moon',
        'name': 'The Moon',
        'arcana': 'major',
        'suit': None,
        'number': 18,
        'element': 'Water',
        'astrology': 'Pisces',
        'vedic_graha': 'Chandra',
        'image_slug': 'the-moon',
        'numerology': '18 (9)',
        'timing_window': 'March 13 – April 12 (Pisces)',
        'timing_season': 'Spring',
        'timing_speed': 'Fluctuating / Tidal',
        'yes_no': 'NO Card (Deception / Confusion / Fog)',
        'one_liner': 'Deep subconscious illusions, psychic sensitivity, hidden truths, navigating emotional fog.',
        'symbols': [   'Full moon with weeping face shedding 15 Yods of light (subconscious intuition and hidden '
                       'grief)',
                       'Two towers guarding the misty gateway (boundaries of rational conscious mind entering the '
                       'mysterious unknown)',
                       'Tamed dog and wild wolf howling at the lunar disk (the domesticated ego and primitive primal '
                       'instincts)',
                       'Crayfish / lobster crawling out of deep dark waters (primitive fears and latent psychic '
                       'memories emerging)',
                       'Winding path into distant shadowy hills (the mysterious journey through the psychic '
                       'subconscious)'],
        'professions': [   'Psychologists, dream analysts, and depth psychotherapists',
                           'Maritime navigators, oceanographers, and naval workers',
                           'Psychiatric nurses, mental health clinicians, and sleep specialists',
                           'Mystery writers, fantasy novelists, and cinematic illusionists',
                           'Private detectives, forensic interrogators, and undercover agents'],
        'upright': {   'keywords': ['Illusion', 'Subconscious', 'Intuition', 'Hidden Deception', 'Psychic Depth'],
                       'general': 'Walking through the misty psychic night. Things are not what they seem on the '
                                  'surface. Rely on subtle intuition and refrain from hasty major decisions.',
                       'love': 'Unspoken insecurities, romantic illusions, hidden secrets, or navigating emotional '
                               'mood swings.',
                       'career': 'Workplace ambiguity, hidden political agendas, lack of transparency in contracts, or '
                                 'imposter feelings.',
                       'finance': 'Financial fog; do not sign agreements without independent auditing; guard against '
                                  'deceptive pitches.',
                       'spiritual': 'Deep shadow-work, vivid prophetic dreams, exploring the psychic subconscious, and '
                                    'facing primal fears.'},
        'reversed': {   'keywords': ['Clarity Emerging', 'Uncovering Deceit', 'Overcoming Fear', 'Dispelling Paranoia'],
                        'general': 'Reversed, indicates the fog lifting, hidden truths stepping into light, overcoming '
                                   'baseless paranoia, and restoring clarity.',
                        'love': 'Secrets exposed leading to honest resolution, dispelling romantic delusions, and '
                                'clarity in relationships.',
                        'career': 'Uncovering fraudulent colleagues, clarity on ambiguous project terms, and '
                                  'navigating out of professional fog.',
                        'finance': 'Catching accounting errors, uncovering hidden fees, and emerging from financial '
                                   'uncertainty with clear plans.',
                        'spiritual': 'Emerging from psychic confusion; grounding spiritual practice in somatic, waking '
                                     'reality.'},
        'remedy': "Drink water from a pure silver vessel. Chant 'Om Som Somaya Namah' and avoid major contractual "
                  'decisions on Full Moon nights.',
        'affirmation': 'I walk through the fog of illusion with trust; my inner light illuminates every shadow and '
                       'reveals the truth.'},
    {   'id': 'the_sun',
        'name': 'The Sun',
        'arcana': 'major',
        'suit': None,
        'number': 19,
        'element': 'Fire',
        'astrology': 'Sun / Leo',
        'vedic_graha': 'Surya',
        'image_slug': 'the-sun',
        'numerology': '19 (1)',
        'timing_window': 'August 15 – September 15 (Leo)',
        'timing_season': 'Summer',
        'timing_speed': 'Radiant / Illumination',
        'yes_no': 'YES Card (Highest affirmative card in deck)',
        'one_liner': 'Radiant joy, supreme vitality, unquestionable success, warm celebration, authentic vitality.',
        'symbols': [   'Radiant golden sun with 21 beams and benign face (supreme cosmic illumination, vitality, and '
                       'divine light)',
                       'Naked child riding white horse without reins (pure innocence, soul freedom, and complete trust '
                       'in life)',
                       "Red banner in child's left hand (vital life force, courage, and exuberant passion celebrated)",
                       'Stone garden wall with 4 blooming sunflowers (earthly stability and flourishing manifestation '
                       'across all 4 elements)',
                       "Crown of flowers and red feather on child's head (innocence crowned with triumph and creative "
                       'vitality)'],
        'professions': [   'Pediatricians, childcare specialists, and youth mentors',
                           'Performing artists, theatrical actors, and entertainers',
                           'Solar energy engineers and renewable technology pioneers',
                           'Tourism, resort management, and recreational hospitality',
                           'Motivational keynote speakers, executive coaches, and elite leaders'],
        'upright': {   'keywords': ['Joy', 'Success', 'Vitality', 'Radiance', 'Warmth', 'Celebration'],
                       'general': 'The supreme card of radiant light, unquestionable success, and pure joy. Clouds '
                                  'vanish, health blooms, and everything you touch flourishes.',
                       'love': 'Ecstatic romance, mutual warmth, authentic vulnerability, joyous wedding, conception, '
                               'or renewed marital bliss.',
                       'career': 'Public triumph, outstanding promotions, creative breakthroughs, and commanding '
                                 'luminous professional respect.',
                       'finance': 'Bountiful financial abundance, profitable ventures, clear economic visibility, and '
                                  'generous prosperity.',
                       'spiritual': 'Direct connection to the divine solar consciousness (Atma Vidya); radiant '
                                    'gratitude, vitality, and enlightenment.'},
        'reversed': {   'keywords': ['Temporary Cloudiness', 'Delayed Joy', 'Over-Optimism', 'Egoism', 'Burnout'],
                        'general': 'Reversed, does not negate success, but indicates temporary clouds obscuring the '
                                   'sun, slight burnout, or childish over-confidence.',
                        'love': 'Temporary coolness in warmth, slight misunderstandings, or needing to appreciate your '
                                'partner more openly.',
                        'career': 'Delays in public acknowledgment, slight creative fatigue, or being unrealistic '
                                  'about project deadlines.',
                        'finance': 'Temporary delay in expected payout, minor budget overruns due to extravagant '
                                   'celebration.',
                        'spiritual': 'Spiritual pride or ego vanity; remember to reflect the divine light rather than '
                                     "claim it as ego's possession."},
        'remedy': 'Perform Surya Arghya at dawn offering water with red kumkum and sandalwood. Chant the Aditya '
                  "Hridaya Stotra or 'Om Suryaya Namah'.",
        'affirmation': 'I radiate joyful confidence, health, and abundant vitality; divine blessings illuminate my '
                       'entire world.'},
    {   'id': 'judgement',
        'name': 'Judgement',
        'arcana': 'major',
        'suit': None,
        'number': 20,
        'element': 'Fire',
        'astrology': 'Pluto / Scorpio',
        'vedic_graha': 'Ketu',
        'image_slug': 'judgement',
        'numerology': '20 (2)',
        'timing_window': 'November 15 – December 14 (Scorpio)',
        'timing_season': 'Autumn',
        'timing_speed': 'Final Reckoning / Rebirth',
        'yes_no': 'YES Card (Reckoning / Higher Calling)',
        'one_liner': 'Spiritual awakening, answering higher calling, karmic absolution, rising from the past.',
        'symbols': [   'Archangel Gabriel in radiant clouds blowing golden trumpet with red-cross banner (call of '
                       'higher consciousness)',
                       'Resurrected figures rising from open floating graves (man, woman, child with arms raised in '
                       'thanksgiving)',
                       'Grey ocean and icy blue mountains in background (eternal standards of truth and karmic '
                       'dissolution of past barriers)',
                       'Cross on banner (union of horizontal human realm with vertical divine grace)',
                       'Naked bodies of the risen (complete absolution, rebirth, and stepping out of past karmic '
                       'coffins)'],
        'professions': [   'Judges, magistrates, and appellate review officers',
                           'Spiritual revivalists, retreat leaders, and transformation coaches',
                           'Vocational career counselors and life-pivot strategists',
                           'Historical restoration specialists and genealogists',
                           'Emergency medical revivalists and cardiac resuscitation physicians'],
        'upright': {   'keywords': ['Rebirth', 'Higher Calling', 'Absolution', 'Karmic Awakening', 'Decisive Verdict'],
                       'general': 'The trumpet of divine awakening sounds. It is time to forgive the past, answer your '
                                  'higher calling, and rise into a magnificent new octave of existence.',
                       'love': 'Profound relationship renewal, clearing old karmic grudges through forgiveness, and '
                               'stepping into mature devotion.',
                       'career': 'Answering your true vocational calling, major career pivot, vindication after '
                                 'audits, and promotion to leadership.',
                       'finance': 'Resolving long-standing debts, legal financial verdicts in your favor, and fresh '
                                  'fiscal rebirth.',
                       'spiritual': "Awakening to your soul's divine mission; profound forgiveness, spiritual rebirth, "
                                    'and karmic liberation.'},
        'reversed': {   'keywords': [   'Self-Doubt',
                                        'Harsh Self-Criticism',
                                        'Ignoring the Call',
                                        'Guilt',
                                        'Fear of Rebirth'],
                        'general': 'Reversed, indicates ignoring the inner calling, wallowing in self-condemnation, '
                                   'paralyzing guilt, or dreading necessary life evaluations.',
                        'love': 'Dragging old resentments into present connection, refusing to forgive past mistakes, '
                                'or repeating toxic karmic patterns.',
                        'career': 'Procrastinating on a major career pivot out of self-doubt, fearing performance '
                                  'evaluations, or feeling inadequate.',
                        'finance': 'Ignoring financial notices, repeating fiscal blunders due to denial, or failing to '
                                   'settle past obligations.',
                        'spiritual': 'Harsh spiritual guilt, self-condemnation, or silencing the whispering calling of '
                                     'your higher self.'},
        'remedy': "Perform ancestral gratitude (Tarpan or feeding needy people / birds) on Amavasya. Chant 'Om Namah "
                  "Shivaya'.",
        'affirmation': 'I awaken to my higher purpose; with an open heart, I rise above the past into eternal '
                       'renewal.'},
    {   'id': 'the_world',
        'name': 'The World',
        'arcana': 'major',
        'suit': None,
        'number': 21,
        'element': 'Earth',
        'astrology': 'Saturn / Capricorn',
        'vedic_graha': 'Shani',
        'image_slug': 'the-world',
        'numerology': '21 (3)',
        'timing_window': 'January 14 – February 11 (Capricorn)',
        'timing_season': 'Winter',
        'timing_speed': 'Completion / Mastery',
        'yes_no': 'YES Card',
        'one_liner': 'Ultimate cosmic completion, worldly mastery, global integration, celebratory wholeness.',
        'symbols': [   'Dancing figure wrapped in purple scarf (androgynous cosmic dancer in ecstatic balance and '
                       'wholeness)',
                       'Green laurel oval wreath tied with red infinity ribbons (triumphant completion and eternal '
                       'cyclic renewal)',
                       'Two golden wands in hands (mastery over cosmic involution and evolution, conscious and '
                       'subconscious realms)',
                       'Four mystical beasts in corners (Lion, Bull, Eagle, Angel / 4 fixed signs and elemental '
                       'mastery)',
                       'Clear open sky within wreath (limitless infinite potential and cosmic homecoming)'],
        'professions': [   'International diplomacy, foreign ambassadors, and UN delegates',
                           'Global trade, cross-border commerce, and worldwide logistics',
                           'International travel directors, travel journalists, and documentarians',
                           'Master craftsmen, professors emeritus, and lifelong achievement awardees',
                           'Holistic ecosystem architects and global summit organizers'],
        'upright': {   'keywords': ['Completion', 'Wholeness', 'Global Travel', 'Mastery', 'Triumph', 'Fulfillment'],
                       'general': "The triumphant completion of the hero's journey. You have integrated all lessons, "
                                  'mastered the four elements, and step into cosmic wholeness.',
                       'love': 'Culmination in lasting marriage, deep soulful wholeness, international travel with '
                               'beloved, and profound satisfaction.',
                       'career': 'Reaching the apex of professional career, international recognition, completing '
                                 'major milestones, and industry acclaim.',
                       'finance': 'Complete financial independence, global diversified assets, lasting wealth legacy, '
                                  'and material freedom.',
                       'spiritual': 'Enlightenment, cosmic consciousness (Samadhi), realizing your oneness with the '
                                    'universe, and absolute peace.'},
        'reversed': {   'keywords': ['Unfinished Business', 'Near Completion', 'Lack of Closure', 'Delayed Mastery'],
                        'general': 'Reversed, indicates being inches from the finish line but hesitating, dragging out '
                                   'old cycles, or resisting the closure needed to step into mastery.',
                        'love': 'Lingering ex-partner baggage, fear of final marriage commitment, or unresolved '
                                'emotional threads preventing wholeness.',
                        'career': 'A project 95% finished but stalled on final sign-offs, delayed '
                                  'graduation/licensing, or fear of stepping into master status.',
                        'finance': 'Tying up final loose ends in contracts, minor delays in expected closing of deals '
                                   'or asset sales.',
                        'spiritual': 'Spiritual plateau; integrating the final lesson before the next cycle begins, '
                                     'seeking closure within.'},
        'remedy': "Donate food, blue blankets, or support to elderly homes on Saturdays. Chant 'Om Shanaicharaya "
                  "Namah' to seal karmic completion.",
        'affirmation': 'I celebrate the magnificent wholeness of my journey; I am one with the universe, triumphant '
                       'and fulfilled.'}]

MINOR_ARCANA: list[dict[str, Any]] = [   {   'id': 'ace_of_wands',
        'name': 'Ace of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 1,
        'element': 'Fire',
        'astrology': 'Aries, Leo, Sagittarius',
        'vedic_graha': 'Surya',
        'image_slug': 'ace-of-wands',
        'numerology': '1',
        'timing_window': 'Summer | Hours to Days | April 13 – May 14 (Aries Decan)',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'News, Male fertility, and beginnings',
        'symbols': [   'Hand emerging from white cloud holding flourishing wooden staff (divine offering of vital '
                       'spark)',
                       'Sprouting green leaves and buds (virile life force, primordial energy, and organic growth)',
                       'Falling leaves like golden Yods (creative sparks descending from heaven)',
                       'Hilltop castle in background (latent ambition, kingdom to be built, and high achievement)',
                       'Flowing river and lush green landscape (emotional and material fertility supporting creative '
                       'fire)'],
        'professions': [   'Entrepreneurs, inventors, and startup founders',
                           'Creative directors, designers, and innovators',
                           'Sports coaches, athletes, and fitness motivators',
                           'Inspirational keynote speakers and leaders',
                           'Adventure pioneers and exploration leads'],
        'upright': {   'keywords': [   'New Beginnings',
                                       'Male Fertility',
                                       'Creative Spark',
                                       'Vitality',
                                       'Inspired Action'],
                       'general': 'Ace of Wands manifests: News, Male fertility, and beginnings. A surge of divine '
                                  'creative fire and breakthrough inspiration ignites your path.',
                       'love': 'Passionate spark, magnetic instant chemistry, and exciting shared romantic beginnings '
                               'in pure fire energy.',
                       'career': 'High-octane ambition, entrepreneurial initiative, pioneering venture, and rapid '
                                 'leadership strides.',
                       'finance': 'Bold investments yielding proactive growth; backing creative ventures with '
                                  'enthusiastic confidence.',
                       'spiritual': 'Pranic vitality surging, creative Kundalini fire awakening through decisive and '
                                    'purposeful action.'},
        'reversed': {   'keywords': [   'Creative Block',
                                        'Delays',
                                        'Low Self-Esteem',
                                        'Cancelled Travel',
                                        'Misdirected Energy'],
                        'general': 'Ace of Wands reversed cautions: Creative blocks, lack of motivation, canceled '
                                   'travel, and delayed beginnings.',
                        'love': 'Fleeting attraction, hot-tempered spats, lack of passion, or fizzled romantic '
                                'momentum.',
                        'career': 'Creative block, workplace friction, or pushing projects without strategic clarity '
                                  'and conviction.',
                        'finance': 'Impulsive speculative spending; slow down and audit financial risks to prevent '
                                   'unnecessary waste.',
                        'spiritual': 'Burnout from hyper-activity; balance your inner fire with restorative meditation '
                                     'and grounding mindfulness.'},
        'remedy': 'Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Surya Dev: '
                  "'Om Suryaya Namah'.",
        'affirmation': 'I channel the sacred fire of inspiration with passion, vitality, and creative purpose.'},
    {   'id': 'two_of_wands',
        'name': 'Two of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 2,
        'element': 'Fire',
        'astrology': 'Mars in Aries (April 13 – May 14)',
        'vedic_graha': 'Mangal',
        'image_slug': 'two-of-wands',
        'numerology': '2 (Balance, choice, partnership)',
        'timing_window': 'Summer | Hours to Days | April 13 – May 14 (Aries)',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'YES Card (Only if decision is right; Reversed: NO Card)',
        'one_liner': 'Making Plans',
        'symbols': [   'Figure standing on castle battlements (elevated perspective, place in your head, ambition and '
                       'hunger)',
                       'Small terrestrial globe held in right hand (world at your command, global vision and '
                       'expansion)',
                       'One wand fixed in iron ring, one wand held in hand (comfort of the known vs daring the '
                       'unknown)',
                       'Vast view of bay, ocean, and mountains (uncharted horizons, overseas prospects, and future '
                       'travel)',
                       'Rose and lily emblem on wall (balance between active passion and pure deliberate choice)'],
        'professions': [   'Corporate strategists, executive planners, and analysts',
                           'Urban planners, architects, and civil developers',
                           'International business developers and global merchants',
                           'Travel coordinators and exchange officers',
                           'Venture scouts and feasibility consultants'],
        'upright': {   'keywords': [   'Making Plans',
                                       'Visionary Foresight',
                                       'Expanding Horizons',
                                       'Decisive Choice',
                                       'Personal Power'],
                       'general': 'Two of Wands manifests: Making Plans. You hold the world in your hands, weighing '
                                  'choices and planning expansive long-term moves.',
                       'love': 'Planning a future together, discussing long-term commitment, travel, and harmonizing '
                               'personal ambitions with partner.',
                       'career': 'Strategic career planning, exploring international business, weighing two promising '
                                 'offers, and visionary moves.',
                       'finance': 'Sound financial planning, diversifying assets globally, and preparing capital for '
                                  'future expansion.',
                       'spiritual': 'Stepping out of spiritual complacency; charting the next frontier of conscious '
                                    'self-discovery.'},
        'reversed': {   'keywords': [   'Fear of the Unknown',
                                        'Bad Planning',
                                        'Indecision',
                                        'Hesitation',
                                        'Restricted Horizons'],
                        'general': 'Two of Wands reversed cautions: Over-planning without action, fear of stepping out '
                                   'of the comfort zone, and delayed decisions.',
                        'love': 'Fear of commitment, diverging life paths, reluctance to relocate for love, or '
                                'romantic stagnation.',
                        'career': 'Analysis paralysis, missing strategic opportunities due to hesitation, or fear of '
                                  'leadership responsibility.',
                        'finance': 'Poor financial planning, reluctance to invest in necessary tools, or unexpected '
                                   'delays in overseas ventures.',
                        'spiritual': 'Feeling spiritually confined by rigid beliefs; fear of questioning outdated '
                                     'spiritual dogma.'},
        'remedy': "Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Mangal: 'Om "
                  "Mangalaya Namah'.",
        'affirmation': 'I step boldly into my power, making clear and visionary choices that expand my world.'},
    {   'id': 'three_of_wands',
        'name': 'Three of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 3,
        'element': 'Fire',
        'astrology': 'Sun in Aries (April 13 – May 14)',
        'vedic_graha': 'Surya',
        'image_slug': 'three-of-wands',
        'numerology': '3 (Creativity, growth, collaboration)',
        'timing_window': 'Summer | Hours to Days | April 13 – May 14 (Aries)',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'YES Card',
        'one_liner': 'Travel',
        'symbols': [   'Figure standing on cliff edge gazing out to sea (leap of faith, ambition, looking forward to '
                       'rewards)',
                       'Three sturdy sprouted wands planted in ground (solid foundations, 3 branches = good fortune '
                       'and expansion)',
                       'Ships sailing on golden sea (commercial ventures, travel, cargo coming into port, payoff of '
                       'past efforts)',
                       'Red and green mantle (vitality, dynamic fire, and patient organic growth)',
                       'Sheerness of cliff edge (overcoming initial obstacles, waiting for harvest while standing '
                       'tall)'],
        'professions': [   'Global trade, export-import, and maritime commerce',
                           'International shipping, logistics, and supply chain managers',
                           'Travel agencies, tour operators, and overseas liaisons',
                           'Foreign exchange brokers and cross-border consultants',
                           'Creative collaborators and multi-hub enterprise directors'],
        'upright': {   'keywords': [   'Travel',
                                       'Overseas Expansion',
                                       'Ships Coming In',
                                       'Foresight Rewarded',
                                       'Commercial Growth'],
                       'general': 'Three of Wands manifests: Travel and expansion. Your ships have set sail; past '
                                  'efforts are gaining momentum and rewards are on the horizon.',
                       'love': 'Long-distance romance thriving, travel with beloved, expanding relationship horizons, '
                               'and mutual adventurous optimism.',
                       'career': 'Overseas business expansion, lucrative export opportunities, career milestones '
                                 'manifesting, and commercial triumph.',
                       'finance': 'Investments beginning to pay dividends; foreign investments and trade ventures '
                                  'yielding solid returns.',
                       'spiritual': 'Broadening spiritual understanding through travel, cross-cultural study, and '
                                    'expanding your consciousness.'},
        'reversed': {   'keywords': [   'Delayed Payoff',
                                        'Travel Obstacles',
                                        'Frustrated Ambition',
                                        'Lack of Foresight',
                                        'Isolation'],
                        'general': 'Three of Wands reversed cautions: Delays in shipping, cancelled or postponed '
                                   'travel, and frustration over delayed payoff.',
                        'love': 'Challenges in long-distance romance, travel cancellations disrupting meetings, or '
                                'feeling emotionally distant.',
                        'career': 'Delays in overseas contracts, supply chain bottlenecks, or disappointment over '
                                  'delayed promotional payoff.',
                        'finance': 'Delayed returns on speculative investments; cash flow locked in overseas ventures '
                                   'requiring patience.',
                        'spiritual': 'Feeling spiritually isolated; clinging to parochial views instead of exploring '
                                     'universal cosmic truths.'},
        'remedy': "Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Surya: 'Om "
                  "Suryaya Namah'.",
        'affirmation': 'My vision is clear, my foundations are strong, and my ventures expand with divine grace.'},
    {   'id': 'four_of_wands',
        'name': 'Four of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 4,
        'element': 'Fire',
        'astrology': 'Venus in Aries (April 13 – May 14)',
        'vedic_graha': 'Shukra',
        'image_slug': 'four-of-wands',
        'numerology': '4 (Structure, stability, foundation)',
        'timing_window': 'Summer | Hours to Days | April 13 – May 14 (Aries)',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'YES Card',
        'one_liner': 'A holiday',
        'symbols': [   'Four wands entwined with floral bower (Chuppah / celebratory canopy, grapes, peaches, harmony)',
                       'Two dancing maidens holding bouquets of flowers (joyous celebration, homecoming, welcoming '
                       'community)',
                       'Welcoming castle bridge and festive crowd (security, domestic harmony, and prosperous '
                       'sanctuary)',
                       'Lush golden and green foreground (harvest fruits, fertility, and stable material foundations)',
                       'Clear sunny sky (pure unclouded joy, auspiciousness, and celebration of milestone)'],
        'professions': [   'Event management, festival production, and celebration planning',
                           'Property investors, real estate developers, and home builders',
                           'Hospitality, luxury resorts, and banquet catering',
                           'Wedding planners, officiants, and floral stylists',
                           'Community directors, civic organizers, and cultural coordinators'],
        'upright': {   'keywords': ['A Holiday', 'Homecoming', 'Celebration', 'Wedding / Milestone', 'Domestic Bliss'],
                       'general': 'Four of Wands manifests: A holiday. Time to rejoice in a major milestone, '
                                  'harmonious family gathering, wedding, or homecoming.',
                       'love': 'Engagement, joyful wedding, moving in together, domestic peace, and celebration of '
                               'harmonious love.',
                       'career': 'Celebrating workplace milestone, completing major phase of enterprise, warm team '
                                 'camaraderie, and holiday bonuses.',
                       'finance': 'Purchasing a home, investing in property, financial stability allowing comfortable '
                                  'vacations and celebrations.',
                       'spiritual': 'Celebrating spiritual milestones, harmonious community satsang, and feeling '
                                    'rooted in divine peace.'},
        'reversed': {   'keywords': [   'Postponed Holiday',
                                        'Transient Family Friction',
                                        'Feeling Unwelcome',
                                        'Social Awkwardness'],
                        'general': 'Four of Wands reversed cautions: Postponed celebrations, slight domestic tension, '
                                   'or feeling like an outsider at an event.',
                        'love': 'Wedding planning stress, minor domestic squabbles over living arrangements, or '
                                'postponement of a romantic getaway.',
                        'career': 'Office gathering awkwardness, delayed celebratory bonuses, or project celebration '
                                  'cut short by new deadlines.',
                        'finance': 'Unexpected expenses during holidays, budget overruns for home renovations, or '
                                   'minor property settlement delays.',
                        'spiritual': 'Feeling disconnected from your spiritual community; creating an inner sanctuary '
                                     'when external community is fractious.'},
        'remedy': "Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Shukra: 'Om "
                  "Shukraya Namah'.",
        'affirmation': 'I celebrate the joyous harmony of my home, community, and soul milestones with gratitude.'},
    {   'id': 'five_of_wands',
        'name': 'Five of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 5,
        'element': 'Fire',
        'astrology': 'Saturn in Leo (August 15 – September 15)',
        'vedic_graha': 'Shani',
        'image_slug': 'five-of-wands',
        'numerology': '5 (Change, conflict, challenges)',
        'timing_window': 'Summer | Hours to Days | August 15 – September 15 (Leo)',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'MAYBE Card (Conflict / Competition; Reversed: NO Card)',
        'one_liner': 'Strong Opinions',
        'symbols': [   'Five youths brandishing wands in mock battle (strong opinions, competing egos, and athletic '
                       'rivalry)',
                       'Multicolored contrasting tunics (clashing perspectives, diversity of agendas, and loud '
                       'debates)',
                       'Uneven terrain and chaotic crossing of wands (lack of clear unified leadership, creative '
                       'brainstorming friction)',
                       'No blood or lethal weapons (spirited competition, sparring of ideas rather than malice)',
                       'Dynamic athletic postures (vital fire, competitive adrenaline, and asserting oneself)'],
        'professions': [   'Professional sports, athletics, and talent agents',
                           'Litigation attorneys, court debaters, and dispute negotiators',
                           'Competitive sales teams, bidding specialists, and auctioneers',
                           'Political debate managers and campaign war rooms',
                           'Startup accelerators and fast-paced tech hackathons'],
        'upright': {   'keywords': ['Strong Opinions', 'Competition', 'Rivalry', 'Brainstorming Clash', 'Adrenaline'],
                       'general': 'Five of Wands manifests: Strong Opinions. Healthy competition, clashing viewpoints, '
                                  'and spirited debates test your stamina and clarity.',
                       'love': 'Playful sparring, passionate differences of opinion, managing competitive egos, or '
                               "competing for partner's attention.",
                       'career': 'Intense workplace brainstorming, competing for client bids, asserting your voice in '
                                 'a crowded room, and market rivalry.',
                       'finance': 'Competitive bidding, price wars, multiple bids on property, or managing financial '
                                  'disagreements in business.',
                       'spiritual': 'Overcoming internal cognitive dissonance; spiritual debates sharpening your '
                                    'philosophical discernment.'},
        'reversed': {   'keywords': [   'Destructive Infighting',
                                        'Backstabbing',
                                        'Conflict Avoidance',
                                        'Hostility',
                                        'Fatigue'],
                        'general': 'Five of Wands reversed cautions: Destructive infighting, avoidance of necessary '
                                   'debate, toxic gossip, or exhaustion from friction.',
                        'love': 'Exhausting petty arguments, passive-aggressive resentment, or avoiding crucial '
                                'conversations out of fear of confrontation.',
                        'career': 'Toxic office politics, backstabbing colleagues, sabotage, or complete breakdown of '
                                  'team collaboration.',
                        'finance': 'Costly legal fees from disputes, bidding wars causing overpayment, or financial '
                                   'exhaustion from fighting partners.',
                        'spiritual': 'Spiritual fundamentalism; arguing over theological dogma instead of practicing '
                                     'love and compassion.'},
        'remedy': "Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Shani: 'Om "
                  "Sham Shanaicharaya Namah'.",
        'affirmation': 'I assert my truth with dignity, transform competition into excellence, and maintain inner '
                       'calm.'},
    {   'id': 'six_of_wands',
        'name': 'Six of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 6,
        'element': 'Fire',
        'astrology': 'Jupiter in Leo (August 15 – September 15)',
        'vedic_graha': 'Guru',
        'image_slug': 'six-of-wands',
        'numerology': '6 (Harmony, communication, cooperation)',
        'timing_window': 'Summer | Hours to Days | August 15 – September 15 (Leo)',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Victory',
        'symbols': [   'Heroic rider on caparisoned white horse (triumph, purity of intent, public recognition, and '
                       'noble bearing)',
                       "Laurel wreath on rider's head and tied to upright staff (victory crowned, justified acclaim, "
                       'and success)',
                       'Foot soldiers carrying wands walking alongside (loyal team, supportive community, and '
                       'collective victory)',
                       'Clear sunny blue sky (unblemished success, bright horizons, and public celebration)',
                       'Noble horse with green blanket (organic vitality, peace, and dignified manifestation of '
                       'power)'],
        'professions': [   'Public relations directors and celebrity managers',
                           'Award-winning creators, authors, and performing artists',
                           'Elected political representatives and community heroes',
                           'Triumphant athletic champions and sports coaches',
                           'Executive leadership awardees and visionary industry spokespersons'],
        'upright': {   'keywords': ['Victory', 'Public Acclaim', 'Recognition', 'Triumph', 'Confidence'],
                       'general': 'Six of Wands manifests: Victory. You achieve your goals when you believe. Public '
                                  'acclaim, justified confidence, and triumphant praise reward your perseverance.',
                       'love': 'Triumphant romance, public acknowledgment of your relationship, winning the heart of '
                               'your beloved, and pride in each other.',
                       'career': 'Promotion, winning prestigious industry awards, successful public presentation, and '
                                 'becoming the recognized expert in your field.',
                       'finance': 'Lucrative financial recognition, bonus payouts, successful public launch generating '
                                  'substantial revenue.',
                       'spiritual': 'Spiritual triumph over doubt and past trauma; your journey inspires and lights '
                                    'the way for fellow seekers.'},
        'reversed': {   'keywords': [   'Fall from Grace',
                                        'Egotistical Pride',
                                        'Delayed Acclaim',
                                        'Imposter Syndrome',
                                        'Disrepute'],
                        'general': 'Six of Wands reversed cautions: Fall from public favor, pride before the fall, '
                                   'delayed recognition, or superficial applause.',
                        'love': 'Putting up a perfect facade on social media while intimacy is cold, or arrogance '
                                'alienating your partner.',
                        'career': 'Passed over for promotion, stolen credit, public criticism, or feeling like an '
                                  'imposter despite success.',
                        'finance': 'Spending money excessively to maintain a wealthy public image; status anxiety '
                                   'draining actual wealth.',
                        'spiritual': 'Spiritual vanity; seeking guru worship and external validation rather than '
                                     'cultivating genuine humility.'},
        'remedy': "Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Guru: 'Om "
                  "Gurave Namah'.",
        'affirmation': 'I accept success with humble grace and celebrate the triumphant victory of truth and hard '
                       'work.'},
    {   'id': 'seven_of_wands',
        'name': 'Seven of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 7,
        'element': 'Fire',
        'astrology': 'Mars in Leo (August 15 – September 15)',
        'vedic_graha': 'Mangal',
        'image_slug': 'seven-of-wands',
        'numerology': '7 (Assessment, reflection, courage)',
        'timing_window': 'Summer | Hours to Days | August 15 – September 15 (Leo)',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Advocacy, standing strong',
        'symbols': [   'Man standing on high rocky ridge defending his ground (holding strategic advantage, courage '
                       'under fire)',
                       'Six wands thrusting upward from unseen opponents below (external challenges, jealousy, and '
                       'competition)',
                       'Mismatched shoes (caught by surprise, impromptu battle, courage regardless of preparation)',
                       'Green tunic (desire for balance, growth, and righteous protective duty)',
                       'Firm dynamic stance and raised defensive staff (unyielding determination to protect what has '
                       'been built)'],
        'professions': [   'Human rights advocates and civil liberty champions',
                           'Litigation defense attorneys and legal advocates',
                           'Security consultants, bodyguards, and tactical defense leads',
                           'Independent challengers, whistleblowers, and reformers',
                           'Underdog entrepreneurs defending their market territory'],
        'upright': {   'keywords': [   'Advocacy',
                                       'Standing Strong',
                                       'Courage Under Pressure',
                                       'Defending Integrity',
                                       'Perseverance'],
                       'general': 'Seven of Wands manifests: Advocacy, standing strong. You hold the moral and '
                                  'strategic high ground; do not compromise your principles against the crowd.',
                       'love': 'Defending your relationship against outside critics, protecting boundaries with '
                               'in-laws, and unyielding loyalty.',
                       'career': 'Defending innovative proposals against corporate skeptics, standing firm during '
                                 'audits, and outmaneuvering rivals.',
                       'finance': 'Protecting hard-earned assets against frivolous claims, resisting predatory sales '
                                  'pitches, and securing your wealth.',
                       'spiritual': 'Upholding spiritual values against worldly cynicism; walking the path of '
                                    'integrity despite societal ridicule.'},
        'reversed': {   'keywords': [   'Overwhelmed',
                                        'Surrendering Ground',
                                        'Exhaustion',
                                        'Defenseless',
                                        'Yielding to Pressure'],
                        'general': 'Seven of Wands reversed cautions: Feeling overwhelmed by constant opposition, '
                                   'exhaustion from perpetual fighting, or losing high ground.',
                        'love': 'Giving up fighting for the relationship, yielding to family disapproval, or constant '
                                'defensive fighting destroying love.',
                        'career': 'Caving under executive pressure, backing down from valid convictions, or burning '
                                  'out from endless workplace battles.',
                        'finance': 'Yielding in financial negotiations, failing to defend contract rights, or '
                                   'succumbing to financial pressure.',
                        'spiritual': 'Losing faith due to external criticism; feeling spiritually isolated and '
                                     'exhausted by worldly cynicism.'},
        'remedy': "Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Mangal: 'Om "
                  "Mangalaya Namah'.",
        'affirmation': 'I stand firm in my truth with unwavering courage, protected by divine strength and righteous '
                       'purpose.'},
    {   'id': 'eight_of_wands',
        'name': 'Eight of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 8,
        'element': 'Fire',
        'astrology': 'Mercury in Sagittarius (December 15 – January 13)',
        'vedic_graha': 'Budha',
        'image_slug': 'eight-of-wands',
        'numerology': '8 (Action, accomplishment, velocity)',
        'timing_window': 'Summer | Hours to Days (Fastest in deck) | December 15 – January 13 (Sagittarius)',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'News',
        'symbols': [   'Eight sprouting wooden wands flying in formation through the sky (unobstructed aerodynamic '
                       'velocity)',
                       'Clear blue open sky (no obstacles, rapid communication, and direct linear transmission)',
                       'Peaceful river and green hills below (grounded destination, harmonious touchdown of projects)',
                       'Downward trajectory toward earth (rapid manifestation of ideas from mental realm into physical '
                       'reality)',
                       'Absence of human figures (cosmic forces moving independently of personal effort, momentum '
                       'unleashed)'],
        'professions': [   'Telecommunications, high-speed digital networks, and IT infrastructure',
                           'Aviation, air traffic control, and international flight crews',
                           'Rapid logistics, express shipping, and courier operations',
                           'Viral social media, breaking news journalism, and broadcasters',
                           'Emergency dispatchers and swift response coordinators'],
        'upright': {   'keywords': [   'Swift News',
                                       'Rapid Progress',
                                       'Air Travel',
                                       'Fast Momentum',
                                       'Clear Communication'],
                       'general': 'Eight of Wands manifests: News. Sudden news, rapid progression, fast travel, and '
                                  'long-awaited breakthroughs arriving with great velocity.',
                       'love': 'Passionate communication flurry, whirlwind romance, spontaneous weekend travel '
                               'together, and quick romantic decisions.',
                       'career': 'Fast-tracked promotions, sudden positive replies to applications, swift contract '
                                 'approvals, and international travel.',
                       'finance': 'Rapid inflow of funds, swift closing of pending deals, and immediate liquidity of '
                                  'assets.',
                       'spiritual': 'Rapid spiritual downloads, sudden flashes of intuitive awakening, and '
                                    'high-frequency pranic flow.'},
        'reversed': {   'keywords': [   'Communication Delays',
                                        'Hasty Mistakes',
                                        'Cancelled Travel',
                                        'Impatience',
                                        'Scattered Energy'],
                        'general': 'Eight of Wands reversed cautions: Delays in news, flight cancellations, '
                                   'miscommunications, and errors caused by reckless rushing.',
                        'love': 'Mixed signals, text messages misinterpreted, impatient pushing scaring partner, or '
                                'travel dates falling through.',
                        'career': 'Project delays, bureaucratic red tape stalling momentum, or rushed work leading to '
                                  'costly technical mistakes.',
                        'finance': 'Delays in expected wire transfers, hasty investment decisions leading to regret, '
                                   'or panic-driven economic moves.',
                        'spiritual': 'Restless spiritual hyperactivity; scattered focus preventing deep meditative '
                                     'stillness.'},
        'remedy': "Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Budha: 'Om "
                  "Budhaya Namah'.",
        'affirmation': 'My energy flows with swift clarity, and auspicious news arrives in divine timing.'},
    {   'id': 'nine_of_wands',
        'name': 'Nine of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 9,
        'element': 'Fire',
        'astrology': 'Moon in Sagittarius (December 15 – January 13)',
        'vedic_graha': 'Chandra',
        'image_slug': 'nine-of-wands',
        'numerology': '9 (Fruition, resilience, nearing completion)',
        'timing_window': 'Summer | Hours to Days | December 15 – January 13 (Sagittarius)',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'NO Card (Defensive / Hold the line; Reversed: NO Card)',
        'one_liner': 'Strength',
        'symbols': [   'Bandaged warrior leaning upon sturdy wooden staff (battle-weary, wounded, but unbroken and '
                       'resolute)',
                       'Eight upright wands standing behind like a protective fence (firm boundaries, past battles '
                       'won, defense line)',
                       'Vigilant, watchful sideways glance (alert to danger, refusing to drop guard, near to achieve)',
                       'Green terrain and rolling hills (proximity to safety and final victory, one last push needed)',
                       'White head bandage (resilience through mental adversity, wisdom earned through hardships)'],
        'professions': [   'Paramedics, trauma nurses, and critical care staff',
                           'Border security, prison wardens, and protective guards',
                           'Crisis response leads and resilient startup founders',
                           'Military veterans and frontline resilient personnel',
                           'Risk mitigation analysts and defensive cybersecurity leads'],
        'upright': {   'keywords': ['Strength', 'Resilience', 'Holding Boundaries', 'Final Push', 'Battle-Tested'],
                       'general': 'Nine of Wands manifests: Strength. You are battle-tested and weary, but victory is '
                                  'within reach. Stand your ground and endure this final test.',
                       'love': 'Protecting your heart due to past relationship scars, holding healthy boundaries, and '
                               'learning to trust again gradually.',
                       'career': 'Near the completion of an exhausting project; muster the stamina for the final '
                                 'sprint, protect intellectual property.',
                       'finance': 'Holding financial reserves steady against unexpected drains; resilience during '
                                  'difficult economic conditions.',
                       'spiritual': 'Karmic fortitude; standing firm in your spiritual convictions during spiritual '
                                    'testing and purification.'},
        'reversed': {   'keywords': ['Chronic Paranoia', 'Exhaustion', 'Refusing Help', 'Defensiveness', 'Collapse'],
                        'general': 'Nine of Wands reversed cautions: Chronic defensiveness, seeing enemies where none '
                                   'exist, physical exhaustion, and stubborn isolation.',
                        'love': 'Letting past heartbreak make you paranoid, pushing away genuine love with defensive '
                                'walls, or emotional bitterness.',
                        'career': 'Burnout from refusing to delegate, workplace paranoia, or collapsing right before '
                                  'the finish line due to overexertion.',
                        'finance': 'Financial exhaustion from constant defensive scrambling; failing to see that the '
                                   'crisis has already passed.',
                        'spiritual': 'Spiritual rigidity; defensive dogmatism blinding you to the healing grace '
                                     'available through surrender.'},
        'remedy': "Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Chandra: 'Om "
                  "Som Somaya Namah'.",
        'affirmation': 'I possess infinite resilience; I stand strong in my boundaries, knowing triumph is near.'},
    {   'id': 'ten_of_wands',
        'name': 'Ten of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 10,
        'element': 'Fire',
        'astrology': 'Saturn in Sagittarius (December 15 – January 13)',
        'vedic_graha': 'Shani',
        'image_slug': 'ten-of-wands',
        'numerology': '10 (1) (Completion, burden of cycle)',
        'timing_window': 'Summer | Hours to Days | December 15 – January 13 (Sagittarius)',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'NO Card (Overburdened; Reversed: NO Card)',
        'one_liner': 'A Burden',
        'symbols': [   'Man bent under the heavy weight of 10 wands (carrying too many obligations, overcommitted)',
                       'Face obscured by bundle of sticks (loss of vision, underpaid, and underappreciated toil)',
                       'Trudging toward distant township and castle (destination is in sight, end of the grueling '
                       'journey)',
                       'Fertile golden fields along path (abundance achieved, but obscured by overwhelming labor)',
                       'Straining back and legs (physical burnout, necessity to delegate and lay down excessive '
                       'burdens)'],
        'professions': [   'Overworked executive managers and sole business operators',
                           'Sole family breadwinners and crisis caregivers',
                           'Heavy cargo haulers and physical labor contractors',
                           'Nonprofit directors carrying entire organizational load',
                           'Exhausted perfectionists and overcommitted freelancers'],
        'upright': {   'keywords': ['A Burden', 'Overwhelmed', 'Heavy Responsibility', 'Burnout', 'Nearing Finish'],
                       'general': 'Ten of Wands manifests: A Burden. You are carrying too many obligations alone; you '
                                  'are near the goal, but you must delegate before you collapse.',
                       'love': 'Feeling weighed down by relationship duties, carrying all emotional labor alone, or '
                               'romance smothered by chores.',
                       'career': "Overburdened with unrewarded tasks, taking on everyone's work, burnout, and "
                                 'desperate need for delegation.',
                       'finance': 'Heavy debt obligations, carrying financial burdens of others, and struggling under '
                                  'fiscal overcommitments.',
                       'spiritual': 'Weighed down by spiritual perfectionism; remember that divine grace is effortless '
                                    'and not a grueling chore.'},
        'reversed': {   'keywords': [   'Dropping the Burden',
                                        'Burnout Collapse',
                                        'Delegating Wisely',
                                        'Refusing Exploitation'],
                        'general': 'Ten of Wands reversed cautions: Collapse under crushing stress, or liberating '
                                   'oneself by dropping unnecessary burdens and saying no.',
                        'love': 'Walking away from an emotionally exploitative bond, demanding partner share domestic '
                                'duties, or total exhaustion.',
                        'career': 'Resigning from an exploitative position, dropping secondary projects, learning to '
                                  'say no, or complete burnout.',
                        'finance': 'Defaulting on unsustainable debt, filing for restructuring, or cutting off '
                                   'financial freeloaders.',
                        'spiritual': 'Releasing accumulated emotional baggage; surrendering spiritual ego and '
                                     'discovering lightness of being.'},
        'remedy': "Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Shani: 'Om "
                  "Sham Shanaicharaya Namah'.",
        'affirmation': 'I release all burdens that are not mine to carry; I move forward with lightness, grace, and '
                       'joy.'},
    {   'id': 'page_of_wands',
        'name': 'Page of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 11,
        'element': 'Fire',
        'astrology': 'Fire Signs (Aries, Leo, Sagittarius)',
        'vedic_graha': 'Mangal',
        'image_slug': 'page-of-wands',
        'numerology': '11 (2) (Master vibration / Youthful inspiration)',
        'timing_window': 'Summer | Hours to Days | Fire Archetype',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'A message',
        'symbols': [   'Youthful page holding tall sprouted staff with both hands (curious inspection, grounding '
                       'inspiration)',
                       'Yellow tunic patterned with black salamanders (primal fire element, regeneration, and '
                       'vitality)',
                       'Red feather in brimmed green cap (flamboyant optimism, passion, and youthful eagerness)',
                       'Three pyramids in arid desert landscape (ancient extrasensory power, meditation, and limitless '
                       'manifestation)',
                       'Open curious expression (eagerness to learn, spontaneous new beginnings, and innocence)'],
        'professions': [   'Junior copywriters and creative interns',
                           'Apprentice innovators and tech tinkerers',
                           'Adventure tour guides and camp counselors',
                           'Young actors, messengers, and aspiring creatives',
                           'Spontaneous researchers of esoteric and spiritual arts'],
        'upright': {   'keywords': [   'A Message',
                                       'Curiosity',
                                       'Creative Spark',
                                       'Spontaneous Exploration',
                                       'Inspiration'],
                       'general': 'Page of Wands manifests: A message. Childlike enthusiasm, exciting news, creative '
                                  'sparks, and spontaneous eagerness to explore new horizons.',
                       'love': 'Playful flirting, exciting romantic messages, spontaneous dates, and youthful romantic '
                               'enthusiasm.',
                       'career': 'Enthusiastic new project, junior creative breakthrough, receiving auspicious news '
                                 'regarding job or training.',
                       'finance': 'A small promising financial opportunity, seed money for creative hobby, or news of '
                                  'new income avenues.',
                       'spiritual': 'Innocent spiritual exploration; trying meditation techniques with curiosity and '
                                    'open-minded joy.'},
        'reversed': {   'keywords': [   'Immature Tantrums',
                                        'Unreliable News',
                                        'Lack of Direction',
                                        'Flaking on Promises'],
                        'general': 'Page of Wands reversed cautions: Delayed or disappointing news, lack of creative '
                                   'follow-through, childish impatience, or flakiness.',
                        'love': 'Immature romantic games, ghosting after exciting beginnings, hot-and-cold '
                                'communication, or unreliable suitors.',
                        'career': 'Starting multiple tasks without finishing, careless workplace mistakes, or lack of '
                                  'professional maturity.',
                        'finance': 'Impulsive childish spending on gadgets, get-rich-quick enthusiasm that fizzes out, '
                                   'or minor losses.',
                        'spiritual': 'Chasing spiritual trends without genuine discipline; superficial fascination '
                                     'without practice.'},
        'remedy': "Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Mangal: 'Om "
                  "Mangalaya Namah'.",
        'affirmation': 'I welcome fresh creative inspiration and express my authentic curiosity with joyful '
                       'enthusiasm.'},
    {   'id': 'knight_of_wands',
        'name': 'Knight of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 12,
        'element': 'Fire',
        'astrology': 'Fire Signs (Aries, Leo, Sagittarius)',
        'vedic_graha': 'Surya',
        'image_slug': 'knight-of-wands',
        'numerology': '12 (3) (Dynamic action, 20-35 years masculine)',
        'timing_window': 'Summer | Hours to Days | Fire Archetype',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Speed: an offer',
        'symbols': [   'Armored knight with fiery red plumes charging on rearing chestnut steed (speed, peak energy, '
                       'boldness)',
                       'Yellow tunic patterned with fire salamanders (vitality, passion, and fearless confidence)',
                       'Leafy wooden wand brandished like a lance (readiness for conquest, direct adventurous action)',
                       'Arid desert landscape with rolling dunes (heat, high-octane passion, travel card)',
                       'Full plate armor (protection while dashing into adventurous unknown territory)'],
        'professions': [   'Touring performers, stunt artists, and traveling entertainers',
                           'High-octane sales executives and venture pitchmen',
                           'Emergency transport, rapid field dispatchers, and pilots',
                           'Adventure sports leaders and expedition guides',
                           'Fast-moving entrepreneurs launching aggressive campaigns'],
        'upright': {   'keywords': ['Speed: An Offer', 'Adventurous Action', 'Charisma', 'Bold Pursuit', 'Travel'],
                       'general': 'Knight of Wands manifests: Speed: an offer. Rapid action, charismatic magnetism, '
                                  'bold pursuit of goals, and exciting travel arrive at full speed.',
                       'love': 'Whirlwind courtship, intense magnetic passion, bold pursuit by charismatic lover, and '
                               'adventurous romance.',
                       'career': 'Aggressive career leap, high-energy sales pitch succeeding, business travel, and '
                                 'fearless professional leadership.',
                       'finance': 'Fast-moving financial opportunities, bold profitable investments, and spending on '
                                  'travel and adventure.',
                       'spiritual': 'Passionate spiritual crusade; charging fearlessly toward higher truth and '
                                    'inspiring others.'},
        'reversed': {   'keywords': [   'Reckless Impulsiveness',
                                        'Hot Temper',
                                        'Broken Promises',
                                        'Hasty Departure',
                                        'Arrogance'],
                        'general': 'Knight of Wands reversed cautions: Reckless bravado, temper tantrums, unreliable '
                                   'swagger, hasty departure, and ghosting.',
                        'love': 'Love bombing followed by sudden ghosting, volatile arguments, commitment phobia, or '
                                'reckless infidelity.',
                        'career': 'Rushing into projects without strategy, hot-headed clashes with coworkers, or '
                                  'burning bridges impulsively.',
                        'finance': 'Reckless speculative gambles, blowing funds on impulsive luxuries, or sudden '
                                   'travel expenses.',
                        'spiritual': 'Fanatical spiritual enthusiasm lacking depth; burning out rapidly due to '
                                     'impatience.'},
        'remedy': "Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Surya: 'Om "
                  "Suryaya Namah'.",
        'affirmation': 'I direct my fiery drive with focused wisdom, honoring commitments with passionate integrity.'},
    {   'id': 'queen_of_wands',
        'name': 'Queen of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 13,
        'element': 'Fire',
        'astrology': 'Fire Signs (Aries, Leo, Sagittarius)',
        'vedic_graha': 'Shukra',
        'image_slug': 'queen-of-wands',
        'numerology': '13 (4) (Mature feminine, magnetic creative)',
        'timing_window': 'Summer | Hours to Days | Fire Archetype',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'A creative woman',
        'symbols': [   'Queen seated on lion-carved throne holding golden sunflower (radiance, fertility, joy, always '
                       'in limelight)',
                       'Black cat sitting at feet (mastery of intuition, shadow nature, psychic independence, and '
                       'mystery)',
                       'Tall sprouting wand held firmly in right hand (active creative authority, vitality, and '
                       'passion)',
                       'Loves to dress in golden robes and grey mantle (elegance, royal presence, and self-confidence)',
                       'Lush pyramid landscape behind (mystical mastery, grounded abundance, and regal warmth)'],
        'professions': [   'Female entrepreneurs, creative agency founders, and directors',
                           'Public relations leaders, theatrical directors, and producers',
                           'Fashion stylists, lifestyle influencers, and brand icons',
                           'Motivational coaches, charismatic mentors, and speakers',
                           'Animal rescue leaders and passionate community advocates'],
        'upright': {   'keywords': ['A Creative Woman', 'Magnetic Charisma', 'Confidence', 'Generosity', 'Limelight'],
                       'general': 'Queen of Wands manifests: A creative woman. Vibrant charisma, radiant confidence, '
                                  'fearless self-expression, and warm generosity in the limelight.',
                       'love': 'Passionate, loyal, magnetic romantic presence; inspiring your partner and loving with '
                               'radiant confidence.',
                       'career': 'Executive authority, thriving creative business, captivating presentations, and '
                                 'commanding professional loyalty.',
                       'finance': 'Financial prosperity driven by creativity, generous spending on home and loved '
                                  'ones, and smart business acumen.',
                       'spiritual': 'Owning your divine creative power; radiating spiritual warmth, psychic intuition, '
                                    'and unshakeable self-worth.'},
        'reversed': {   'keywords': [   'Jealous Drama',
                                        'Vanity',
                                        'Manipulative Flare-Ups',
                                        'Overbearing Control',
                                        'Burnout'],
                        'general': 'Queen of Wands reversed cautions: Jealous outbursts, demanding center stage, '
                                   'overbearing vanity, or emotional exhaustion.',
                        'love': 'Insecure demands for constant attention, jealous suspicion, explosive arguments, or '
                                'domineering your partner.',
                        'career': 'Toxic workplace drama, micromanaging colleagues, feeling threatened by other '
                                  'talented peers, or creative burnout.',
                        'finance': 'Extravagant overspending to impress social peers, reckless luxury purchases, or '
                                   'financial status anxiety.',
                        'spiritual': 'Spiritual ego; seeking followers and admiration rather than cultivating quiet '
                                     'authentic inner light.'},
        'remedy': "Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Shukra: 'Om "
                  "Shukraya Namah'.",
        'affirmation': 'I radiate warm confidence, creative brilliance, and magnetic grace in all I do.'},
    {   'id': 'king_of_wands',
        'name': 'King of Wands',
        'arcana': 'minor',
        'suit': 'wands',
        'number': 14,
        'element': 'Fire',
        'astrology': 'Fire Signs (Aries, Leo, Sagittarius)',
        'vedic_graha': 'Surya',
        'image_slug': 'king-of-wands',
        'numerology': '14 (5) (Mature masculine, visionary leader)',
        'timing_window': 'Summer | Hours to Days | Fire Archetype',
        'timing_season': 'Summer',
        'timing_speed': 'Hours to Days',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'A creative man',
        'symbols': [   'Regal king seated on lion and salamander-adorned throne (natural born leader, action-oriented '
                       'mastery)',
                       'Crown of sculpted fire licking upward (unshakable vision, mental brilliance, and sovereign '
                       'executive command)',
                       'Salamander biting its own tail on robe (ouroboros, complete elemental mastery, and boundless '
                       'vitality)',
                       'Flourishing leafy wooden staff gripped firmly (vision translated directly into tangible '
                       'empire)',
                       'Lions carved into throne back and green mantle (courage, nobility, and vital heart '
                       'leadership)'],
        'professions': [   'Corporate founders, visionary CEOs, and managing directors',
                           'Franchise creators, venture capitalists, and industry disruptors',
                           'Film directors, creative producers, and master conductors',
                           'Inspirational statesmen, political figures, and keynote innovators',
                           'Elite sports executives and athletic franchise leaders'],
        'upright': {   'keywords': [   'A Creative Man',
                                       'Visionary Leader',
                                       'Action-Oriented',
                                       'Sovereign Command',
                                       'Enterprise'],
                       'general': 'King of Wands manifests: A creative man. Natural-born leadership, visionary '
                                  'enterprise, decisive execution, and inspiring everyone around you to greatness.',
                       'love': 'Devoted, inspiring, passionate protector; dynamic partnership built on mutual respect '
                               'and shared grand visions.',
                       'career': 'Apex entrepreneurial leadership, launching major business ventures, commanding '
                                 'industry respect, and decisive triumphs.',
                       'finance': 'Wealth generated through visionary enterprise, bold profitable investments, and '
                                  'building an enduring commercial empire.',
                       'spiritual': 'Spiritual leadership; inspiring community through bold righteous action, '
                                    'integrity, and radiant optimism.'},
        'reversed': {   'keywords': [   'Autocratic Bully',
                                        'Arrogance',
                                        'Unrealistic Demands',
                                        'Explosive Wrath',
                                        'Stubborn Pride'],
                        'general': 'King of Wands reversed cautions: Dictatorial temper, ruthless arrogance, '
                                   'unrealistic demands, and reckless blunders.',
                        'love': "Domineering partner, violent temper flare-ups, refusing to listen to beloved's "
                                'feelings, or emotional tyranny.',
                        'career': 'Toxic executive leadership, alienating top talent with unrealistic demands, '
                                  'stubborn refusal to pivot, or hubris.',
                        'finance': 'Reckless commercial gambles, overleveraging enterprise on pride, or financial '
                                   'stubbornness.',
                        'spiritual': 'Dogmatic arrogance; mistaking charismatic personal power for genuine spiritual '
                                     'enlightenment.'},
        'remedy': "Align with Fire element through grounding mindfulness. Chant planetary seed mantra for Surya: 'Om "
                  "Suryaya Namah'.",
        'affirmation': 'I lead with vision, courage, and integrity, transforming inspired dreams into enduring '
                       'reality.'},
    {   'id': 'ace_of_cups',
        'name': 'Ace of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 1,
        'element': 'Water',
        'astrology': 'Cancer, Scorpio, Pisces',
        'vedic_graha': 'Chandra',
        'image_slug': 'ace-of-cups',
        'numerology': '1',
        'timing_window': 'Autumn | Weeks to Months | March 13 – April 12 (Pisces Decan)',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Love, fertility, and beginnings',
        'symbols': [   'Hand emerging from cloud offering golden chalice overflowing with 5 streams of water (5 '
                       'senses, spiritual rebirth)',
                       'Water receives information from the invisible/deep world; 5 senses are intensely aware',
                       '26 Drops of divine dew falling like golden Yods (divine help, guidance, and spiritual grace)',
                       'White dove descending with Eucharistic communion wafer inscribed with cross (divine love and '
                       'peace)',
                       'Calm lotus pond with blooming water lilies (purity of intention, soul star chakra, Akashic '
                       'records)'],
        'professions': [   'Beauty industry, aesthetic wellness, and cosmetics',
                           'Hospitality, catering, and luxury guest relations',
                           'Creative, artistic, and musical vocations',
                           'Spiritual healers, Reiki masters, and psychic counselors',
                           'Female-oriented vocations, obstetrics, and maternal wellness'],
        'upright': {   'keywords': ['Love', 'Fertility', 'New Romance', 'Spiritual Grace', 'Emotional Peace'],
                       'general': 'Ace of Cups manifests: Love, fertility, and beginnings. Overflowing emotional '
                                  'grace, pure love, pregnancy or conception, and deep intuitive renewal.',
                       'love': 'Beginning of a relationship, deep soulful romantic spark, tender vulnerability, and '
                               'unconditional soul connection.',
                       'career': 'Fulfilling vocation, empathetic leadership, joyful creative collaboration, and '
                                 'artistic breakthroughs.',
                       'finance': 'Financial peace of mind; wealth serving your true emotional values and loved ones.',
                       'spiritual': 'Heart chakra expansion, intuitive clairvoyance, psychic downloads, and flowing '
                                    'with universal love.'},
        'reversed': {   'keywords': [   'Blocked Emotions',
                                        'Heartbreak',
                                        'Repressed Grief',
                                        'Emotional Drain',
                                        'Self-Doubt'],
                        'general': 'Ace of Cups reversed cautions: Emotional withholding, moodiness, unrealistic '
                                   'fairy-tale expectations, or unrequited love.',
                        'love': 'Emotional withholding, feeling unloved, heartbreak, empty romantic gestures, or '
                                'blocked intimacy.',
                        'career': 'Lack of passion in daily work, toxic workplace drama, or feeling emotionally '
                                  'unfulfilled in role.',
                        'finance': 'Emotional retail therapy; spending compulsively to soothe internal emotional '
                                   'emptiness.',
                        'spiritual': 'Blocked emotional release; allow suppressed tears and feelings to flow without '
                                     'judgment.'},
        'remedy': 'Align with Water element through mindful contemplation. Chant planetary seed mantra for Chandra: '
                  "'Om Som Somaya Namah'.",
        'affirmation': 'My heart is open to receive and radiate boundless love, peace, and divine emotional grace.'},
    {   'id': 'two_of_cups',
        'name': 'Two of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 2,
        'element': 'Water',
        'astrology': 'Venus in Cancer (July 15 – August 14)',
        'vedic_graha': 'Shukra',
        'image_slug': 'two-of-cups',
        'numerology': '2 (Balance, choice, partnership)',
        'timing_window': 'Autumn | Weeks to Months | July 15 – August 14 (Cancer)',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Partnerships',
        'symbols': [   'Young man and woman pledging vows and exchanging golden cups (duality = balance, mutual soul '
                       'respect)',
                       'Caduceus of Hermes rising between them (healing, truthful communication, and divine commerce)',
                       'Winged red lion head atop caduceus (divine passion harmonized with wisdom and spiritual fire)',
                       'Green wreath crowns and classic robes (sacred harmony, pure intention, and equal standing)',
                       'Peaceful home and rolling green hills behind (stable domestic future born of sacred union)'],
        'professions': [   'Marriage counselors, relationship therapists, and family mediators',
                           'Joint business partners, co-founders, and contract negotiators',
                           'Wedding officiants, matchmakers, and event hosts',
                           'Diplomatic arbiters and non-profit collaboration directors',
                           'Artistic collaborators and creative songwriting duos'],
        'upright': {   'keywords': ['Partnerships', 'Mutual Attraction', 'Soulmate Bond', 'Reconciliation', 'Harmony'],
                       'general': 'Two of Cups manifests: Partnerships. A profound meeting of two souls, mutual '
                                  'respect, sacred romantic vows, and harmonious alliances.',
                       'love': 'Soulmate connection, reciprocal romantic devotion, harmonious engagement, or heartfelt '
                               'reconciliation after estrangement.',
                       'career': 'Highly successful business partnership, lucrative joint ventures, perfect co-founder '
                                 'synergy, and collaborative harmony.',
                       'finance': 'Mutually beneficial financial contracts, equal financial contributions, and shared '
                                  'prosperity with partner.',
                       'spiritual': 'Spiritual mirror; seeing the divine reflection of the beloved and balancing inner '
                                    'masculine and feminine polarities.'},
        'reversed': {   'keywords': ['Codependency', 'Broken Trust', 'Disharmony', 'Misunderstandings', 'Imbalance'],
                        'general': 'Two of Cups reversed cautions: Broken agreements, codependent enmeshment, '
                                   'emotional imbalance, or falling out of sync.',
                        'love': 'Communication friction, unequal effort in romance, fading spark, or emotional '
                                'codependency causing resentment.',
                        'career': 'Partnership friction, disagreements on business vision, broken contracts, or '
                                  'dissolution of a joint venture.',
                        'finance': 'Disputes over shared accounts, hidden financial secrets between partners, or '
                                   'unfair business splits.',
                        'spiritual': 'Projecting unhealed emotional wounds onto your partner instead of taking inner '
                                     'spiritual responsibility.'},
        'remedy': "Align with Water element through mindful contemplation. Chant planetary seed mantra for Shukra: 'Om "
                  "Shukraya Namah'.",
        'affirmation': 'I attract and cultivate relationships rooted in mutual love, truth, and sacred reciprocity.'},
    {   'id': 'three_of_cups',
        'name': 'Three of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 3,
        'element': 'Water',
        'astrology': 'Mercury in Cancer (July 15 – August 14)',
        'vedic_graha': 'Budha',
        'image_slug': 'three-of-cups',
        'numerology': '3 (Creativity, growth, collaboration)',
        'timing_window': 'Autumn | Weeks to Months | July 15 – August 14 (Cancer)',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Celebration',
        'symbols': [   'Three maidens dancing joyously in a circle raising golden cups (baby shower, sisterhood, '
                       'creative circle)',
                       'Garlands of flowers in their hair and flowing dresses (abundance, feminine joy, and '
                       'celebration of life)',
                       'Foreground laden with ripe grapes, pumpkins, and fruits (bountiful harvest, fertile abundance, '
                       'and feast)',
                       'Linked hands and uplifted smiles (unwavering friendship, communal support, and mutual '
                       'celebration)',
                       'Clear open sky (unburdened joy, celebratory milestones, and emotional freedom)'],
        'professions': [   'Event managers, festival coordinators, and party producers',
                           'Catering directors, banquet managers, and celebratory hosts',
                           'Social club directors, community circles, and wellness groups',
                           "Women's empowerment organizers and sisterhood circle leaders",
                           'Publicists, creative collaborators, and celebratory entertainers'],
        'upright': {   'keywords': ['Celebration', 'Reunions', 'Friendship', 'Baby Shower', 'Communal Joy'],
                       'general': 'Three of Cups manifests: Celebration. A joyous gathering of cherished friends, '
                                  'celebratory reunions, baby showers, and communal success.',
                       'love': 'Celebration of love with friends and family, engagement parties, baby showers, or '
                               'joyous social events with beloved.',
                       'career': 'Team victory celebrations, successful project launches, supportive collaborative '
                                 'colleagues, and celebratory bonuses.',
                       'finance': 'Financial abundance allowing generous hospitality, sharing wealth with loved ones, '
                                  'and celebratory investments.',
                       'spiritual': 'Communal spiritual joy; celebrating the divine through sacred music (Kirtan), '
                                    'dance, and shared satsang.'},
        'reversed': {   'keywords': [   'Gossip',
                                        'Overindulgence',
                                        'Exclusion from Group',
                                        'Third-Party Drama',
                                        'Hangovers'],
                        'general': 'Three of Cups reversed cautions: Social drama, malicious gossip, feeling excluded '
                                   'from peer groups, or overindulgent partying.',
                        'love': 'Third-party romantic interference, friends meddling in your relationship, or shallow '
                                'partying over intimacy.',
                        'career': 'Workplace cliques, exclusionary gossip, slacking on responsibilities due to social '
                                  'distractions, or team jealousy.',
                        'finance': 'Overspending on extravagant nightlife and social status, split bills causing '
                                   'friction, or party hangovers.',
                        'spiritual': 'Superficial spiritual socializing without depth; gossip disguised as spiritual '
                                     'discussion.'},
        'remedy': "Align with Water element through mindful contemplation. Chant planetary seed mantra for Budha: 'Om "
                  "Budhaya Namah'.",
        'affirmation': 'I surround myself with loyal, uplifting friends and celebrate the abundant blessings of life.'},
    {   'id': 'four_of_cups',
        'name': 'Four of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 4,
        'element': 'Water',
        'astrology': 'Moon in Cancer (July 15 – August 14)',
        'vedic_graha': 'Chandra',
        'image_slug': 'four-of-cups',
        'numerology': '4 (Structure, stability, contemplation)',
        'timing_window': 'Autumn | Weeks to Months | July 15 – August 14 (Cancer)',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': 'NO Card (Boredom / Detached / Apathetic; Reversed: NO Card)',
        'one_liner': 'Boredom',
        'symbols': [   'Young man seated with folded arms beneath shady tree (detachment, contemplation, emotional '
                       'withdrawal)',
                       'Three golden cups standing on grass in front of him (past emotional experiences, existing '
                       'blessings taken for granted)',
                       'A fourth cup offered by a divine hand emerging from a white cloud (new divine gift, ignored '
                       'due to apathy)',
                       'Green rolling landscape (peace and abundance present, yet unrecognized by the contemplative '
                       'mind)',
                       'Downcast, discontented facial expression (boredom, soul weariness, and emotional apathy)'],
        'professions': [   'Meditation retreat guides and contemplative practitioners',
                           'Quality assurance auditors and diagnostic evaluators',
                           'Behavioral therapists and emotional detachment specialists',
                           'Disengaged corporate analysts evaluating systemic flaws',
                           'Philosophy researchers studying existential apathy'],
        'upright': {   'keywords': ['Boredom', 'Apathy', 'Contemplation', 'Detachment', 'Missed Opportunity'],
                       'general': 'Four of Cups manifests: Boredom. Emotional apathy, self-absorption, ignoring '
                                  'blessings right in front of you, and soul weariness.',
                       'love': 'Feeling bored or disconnected in relationship, taking partner for granted, ignoring '
                               'romantic overtures, or romantic rut.',
                       'career': 'Apathy toward current job, feeling uninspired by daily tasks, ignoring promotion '
                                 'offers due to lack of enthusiasm.',
                       'finance': 'Financial disinterest, ignoring lucrative opportunities out of lethargy, or feeling '
                                  'unfulfilled despite adequate income.',
                       'spiritual': 'Spiritual dryness (acedia); feeling flat in meditation, needing to awaken '
                                    'gratitude for existing blessings.'},
        'reversed': {   'keywords': ['Waking from Apathy', 'Accepting Offers', 'Renewed Enthusiasm', 'Gratitude'],
                        'general': 'Four of Cups reversed cautions: Snapping out of emotional numbness, accepting new '
                                   'opportunities, and embracing life again.',
                        'love': 'Reconnecting with partner, waking up to the value of a lover, opening your heart '
                                'after a period of emotional withdrawal.',
                        'career': 'Finding renewed passion for your work, accepting an offer previously overlooked, '
                                  'and active career re-engagement.',
                        'finance': 'Seizing a neglected financial opportunity, auditing investments with fresh eyes, '
                                   'and proactive wealth creation.',
                        'spiritual': 'Breaking through spiritual lethargy; heart re-awakening with fresh gratitude and '
                                     'devotion.'},
        'remedy': 'Align with Water element through mindful contemplation. Chant planetary seed mantra for Chandra: '
                  "'Om Som Somaya Namah'.",
        'affirmation': 'I open my heart to the abundant gifts surrounding me and welcome fresh inspiration with '
                       'gratitude.'},
    {   'id': 'five_of_cups',
        'name': 'Five of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 5,
        'element': 'Water',
        'astrology': 'Mars in Scorpio (November 15 – December 14)',
        'vedic_graha': 'Mangal',
        'image_slug': 'five-of-cups',
        'numerology': '5 (Change, conflict, grief)',
        'timing_window': 'Autumn | Weeks to Months | November 15 – December 14 (Scorpio)',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': 'NO Card (Loss and sadness; Reversed: NO Card)',
        'one_liner': 'Loss and sadness',
        'symbols': [   'Black-cloaked figure weeping with bowed head over three spilled golden cups (loss, sadness, '
                       'mourning spilled wine)',
                       'Two upright golden cups standing behind the figure (unseen blessings, remaining love, not '
                       'thinking about present)',
                       'Arched stone bridge crossing river to distant castle (pathway to safety, home, and recovery '
                       'remains open)',
                       'Red and green wine flowing into earth (emotional energy spent, grief, and necessary mourning)',
                       'Barren grey riverbank (temporary desolate feeling of heartbreak and bereavement)'],
        'professions': [   'Bereavement counselors and grief therapists',
                           'Estate dispute attorneys and probate negotiators',
                           'Crisis social workers and trauma support staff',
                           'Addiction recovery guides and emotional rehabilitation specialists',
                           'Insurance claim adjusters handling catastrophic losses'],
        'upright': {   'keywords': ['Loss and Sadness', 'Grief', 'Regret', 'Heartbreak', 'Remaining Blessings'],
                       'general': 'Five of Cups manifests: Loss and sadness. Mourning over spilled cups and past '
                                  'heartbreak; remember that two cups still stand behind you.',
                       'love': 'Heartache over breakup, dwelling on past mistakes, sorrow, but enduring love and '
                               'reconciliation remain possible.',
                       'career': 'Disappointment over lost contract or failed venture, mourning a missed promotion, or '
                                 'workplace setback.',
                       'finance': 'Financial loss, failed speculative investment, regret over money decisions; turn '
                                  'around to protect remaining capital.',
                       'spiritual': 'Processing sorrow as a sacred initiation of the heart; discovering that '
                                    'compassion is born through deep grieving.'},
        'reversed': {   'keywords': [   'Acceptance of Loss',
                                        'Healing Heartbreak',
                                        'Moving On',
                                        'Forgiveness',
                                        'Recovery'],
                        'general': 'Five of Cups reversed cautions: Turning around to see the remaining cups, healing '
                                   'after sorrow, and moving across the bridge to safety.',
                        'love': 'Healing from heartbreak, forgiving an ex-partner, opening heart to fresh romance, and '
                                'renewed emotional optimism.',
                        'career': 'Recovering from business setback, learning valuable lessons from failure, and '
                                  'starting a promising new enterprise.',
                        'finance': 'Stopping financial bleeding, focusing on remaining assets, and building back with '
                                   'greater wisdom and prudence.',
                        'spiritual': 'Forgiving yourself for past spiritual errors; recognizing the divine light '
                                     'shining through emotional cracks.'},
        'remedy': "Align with Water element through mindful contemplation. Chant planetary seed mantra for Mangal: 'Om "
                  "Mangalaya Namah'.",
        'affirmation': 'I release all sorrow and regret; I turn with gratitude toward the abundant blessings that '
                       'remain.'},
    {   'id': 'six_of_cups',
        'name': 'Six of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 6,
        'element': 'Water',
        'astrology': 'Sun in Scorpio (November 15 – December 14)',
        'vedic_graha': 'Surya',
        'image_slug': 'six-of-cups',
        'numerology': '6 (Harmony, communication, cooperation)',
        'timing_window': 'Autumn | Weeks to Months | November 15 – December 14 (Scorpio)',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Peace, A visitor',
        'symbols': [   'Older boy offering cup filled with white 5-petaled flower to younger girl (peace, a visitor, '
                       'innocence, pure gift)',
                       'Four cups in foreground filled with blooming flowers and sixth on pedestal (creating good '
                       'memories, childhood beauty)',
                       'Ancient castle courtyard and stone architecture (security, ancestral heritage, and enduring '
                       'foundation)',
                       'Guard walking away in the distance (safety, absence of threat, and peaceful protection)',
                       'Golden sunny light bathing the scene (sweet nostalgia, pure intentions, and sweet karmic '
                       'reunions)'],
        'professions': [   'Childhood psychologists, pediatricians, and early educators',
                           'Antique dealers, heritage curators, and museum preservationists',
                           'Historians, genealogists, and ancestral researchers',
                           "Children's book authors, illustrators, and animators",
                           'Family heritage trust officers and charity foundation leads'],
        'upright': {   'keywords': ['Peace', 'A Visitor', 'Sweet Nostalgia', 'Childhood Innocence', 'Good Memories'],
                       'general': 'Six of Cups manifests: Peace, A visitor. Sweet nostalgia, childhood friends '
                                  'returning, innocent affection, and creating good memories.',
                       'love': 'Reconnecting with a childhood sweetheart, pure innocent romantic devotion, sweet '
                               'romantic gestures, and mutual tenderness.',
                       'career': 'Returning to a career you loved in youth, business opportunities with past trusted '
                                 'colleagues, and harmonious mentorship.',
                       'finance': 'Inheritance from family, financial gifts from elders, or profitable returns from '
                                  'vintage/heritage assets.',
                       'spiritual': 'Reclaiming childlike spiritual wonder, healing inner child wounds, and '
                                    'remembering pure soul innocence.'},
        'reversed': {   'keywords': [   'Living in the Past',
                                        'Childish Clinging',
                                        'Refusing to Mature',
                                        'Outgrown Dreams'],
                        'general': 'Six of Cups reversed cautions: Being trapped in rose-tinted nostalgia, clinging to '
                                   'past memories, and refusing to grow up.',
                        'love': 'Comparing current partners to an idealized past lover, clinging to an ex who has '
                                'moved on, or childish dependence.',
                        'career': 'Outdated professional methods, clinging to past glories instead of innovating, or '
                                  'feeling held back by family expectations.',
                        'finance': 'Dependency on family allowance, refusal to take financial responsibility as an '
                                   'adult, or disputes over family trust.',
                        'spiritual': 'Over-idealizing past spiritual gurus; stepping into spiritual maturity and adult '
                                     'personal responsibility.'},
        'remedy': "Align with Water element through mindful contemplation. Chant planetary seed mantra for Surya: 'Om "
                  "Suryaya Namah'.",
        'affirmation': 'I honor sweet memories of the past while stepping joyfully into the present with an open '
                       'heart.'},
    {   'id': 'seven_of_cups',
        'name': 'Seven of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 7,
        'element': 'Water',
        'astrology': 'Venus in Scorpio (November 15 – December 14)',
        'vedic_graha': 'Shukra',
        'image_slug': 'seven-of-cups',
        'numerology': '7 (Assessment, reflection, daydream)',
        'timing_window': 'Autumn | Weeks to Months | November 15 – December 14 (Scorpio)',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': 'MAYBE Card (Confusion / Possibilities; Reversed: NO Card)',
        'one_liner': 'Confusion, possibilities',
        'symbols': [   'Shadowy figure standing before floating cloud of 7 cups (confusion, possibilities, '
                       'daydreaming, choices)',
                       'Cups displaying snake (wisdom/temptation), castle (security), jewels (wealth), wreath (fame), '
                       'dragon (primal fear)',
                       'Covered glowing spirit figure (divine revelation or hidden trap)',
                       'Crown cup (authority, power, status, and worldly ambition)',
                       'Billowing clouds holding the visions (illusions, wishful projections, and mental fantasies)'],
        'professions': [   'Creative visualizers, concept artists, and animators',
                           'Fantasy novelists, fiction writers, and world-builders',
                           'Advertising visual directors and brand mythmakers',
                           'Illusionists, stage magicians, and theatrical producers',
                           'Dream analysts, hypnotherapists, and creative brainstormers'],
        'upright': {   'keywords': [   'Confusion',
                                       'Possibilities',
                                       'Multitude of Choices',
                                       'Illusion vs Reality',
                                       'Daydreams'],
                       'general': 'Seven of Cups manifests: Confusion, possibilities. A multitude of tempting choices '
                                  'and fantasies; ground your visions in reality to avoid traps.',
                       'love': 'Overwhelming romantic options, projection and fantasy in love, falling for an '
                               'idealized illusion rather than real person.',
                       'career': 'Multiple career avenues, shiny object syndrome, creative brainstorms that require '
                                 'filtering down to one grounded project.',
                       'finance': 'Speculative get-rich-quick fantasies, too many risky options; beware of pitches '
                                  'that sound too good to be true.',
                       'spiritual': 'Navigating astral glamour; distinguishing authentic divine intuition from wishful '
                                    'subconscious fantasies.'},
        'reversed': {   'keywords': [   'Dispelling Illusions',
                                        'Making Clear Choice',
                                        'Sobriety',
                                        'Grounding Visions',
                                        'Focus'],
                        'general': 'Seven of Cups reversed cautions: Dispelling glamorous illusions, waking up to '
                                   'practical reality, and committing decisively to one path.',
                        'love': 'Seeing a partner clearly without fantasy goggles, choosing commitment over endless '
                                'dating illusions, and emotional clarity.',
                        'career': 'Cutting through analysis paralysis, choosing one solid career path, executing real '
                                  'tasks rather than endlessly daydreaming.',
                        'finance': 'Rejecting speculative scams, focusing on conservative grounded investments, and '
                                   'realistic financial budgeting.',
                        'spiritual': 'Emerging from psychic confusion; grounding spiritual practice in ethical action '
                                     'and clear meditation.'},
        'remedy': "Align with Water element through mindful contemplation. Chant planetary seed mantra for Shukra: 'Om "
                  "Shukraya Namah'.",
        'affirmation': 'I cut through illusion with clear discernment, choosing the path of truth, reality, and '
                       'purpose.'},
    {   'id': 'eight_of_cups',
        'name': 'Eight of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 8,
        'element': 'Water',
        'astrology': 'Saturn in Pisces (March 13 – April 12)',
        'vedic_graha': 'Shani',
        'image_slug': 'eight-of-cups',
        'numerology': '8 (Action, accomplishment, turning point)',
        'timing_window': 'Autumn | Weeks to Months | March 13 – April 12 (Pisces)',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': 'NO Card (Departure / Walking Away; Reversed: NO Card)',
        'one_liner': 'Departure',
        'symbols': [   'Cloaked pilgrim with walking staff walking away from 8 stacked cups (departure, walking away, '
                       'giving yourself time)',
                       'Stack of 8 cups arranged with a deliberate gap at top (feeling that something essential is '
                       'missing despite material success)',
                       'Barren, rocky mountainous path into the unknown (spiritual quest, leaving the valley of '
                       'comfort for higher truth)',
                       'Eclipsed moon and sun in sky (dark night of soul, deep emotional transition, and spiritual '
                       'realignment)',
                       'River and sea crossed by pilgrim (moving beyond emotional entanglements to higher ground)'],
        'professions': [   'Spiritual wanderers, pilgrims, and monastic seekers',
                           'Sabbatical travelers and solo backpackers',
                           'Detox therapists, rehabilitation directors, and life reset coaches',
                           'Environmental researchers in remote wilderness regions',
                           'Philosophers abandoning corporate life for deeper meaning'],
        'upright': {   'keywords': ['Departure', 'Walking Away', 'Seeking Higher Meaning', 'Letting Go', 'Soul Quest'],
                       'general': 'Eight of Cups manifests: Departure. Walking away from what no longer feeds your '
                                  'soul; giving yourself time and courage to seek higher purpose.',
                       'love': 'Walking away from an unfulfilling relationship, letting go with dignity, seeking a '
                               "partner who aligns with your soul's depth.",
                       'career': 'Resigning from a lucrative but soul-crushing job, walking away from corporate rat '
                                 'race to pursue authentic passion.',
                       'finance': 'Walking away from unviable investments, simplifying lifestyle, shedding material '
                                  'excess to travel light.',
                       'spiritual': 'Renunciation (Vairagya); leaving behind worldly attachments to pursue deep '
                                    'spiritual enlightenment.'},
        'reversed': {   'keywords': [   'Fear of Leaving',
                                        'Staying in Toxic Rut',
                                        'Aimless Drifting',
                                        'Returning to the Past'],
                        'general': 'Eight of Cups reversed cautions: Fear of the unknown keeping you trapped in a dead '
                                   'situation, or aimless wandering without purpose.',
                        'love': 'Staying in a dead relationship out of habit or fear of loneliness, returning to a '
                                'toxic ex repeatedly.',
                        'career': 'Sticking with a dead-end job due to fear of change, complaining endlessly without '
                                  'taking the courage to resign.',
                        'finance': 'Clinging to bad investments hoping they will miraculously recover; financial '
                                   'stagnation caused by indecision.',
                        'spiritual': "Spiritual escapism; running away from life's duties instead of doing genuine "
                                     'inner transformation.'},
        'remedy': "Align with Water element through mindful contemplation. Chant planetary seed mantra for Shani: 'Om "
                  "Sham Shanaicharaya Namah'.",
        'affirmation': 'I have the courage to walk away from what no longer serves my soul, trusting the higher path '
                       'ahead.'},
    {   'id': 'nine_of_cups',
        'name': 'Nine of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 9,
        'element': 'Water',
        'astrology': 'Jupiter in Pisces (March 13 – April 12)',
        'vedic_graha': 'Guru',
        'image_slug': 'nine-of-cups',
        'numerology': '9 (Fruition, fulfillment)',
        'timing_window': 'Autumn | Weeks to Months | March 13 – April 12 (Pisces)',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': "YES Card (The 'Wish Card'; Reversed: NO Card)",
        'one_liner': 'A wish come true',
        'symbols': [   'Contented man seated on wooden bench with folded arms (ultimate satisfaction, success, '
                       'self-sufficiency, wish fulfilled)',
                       'Nine golden cups arranged in arched semicircle on blue banquet table (emotional abundance, '
                       'wealth, and hospitality)',
                       'Feathered red cap and rich tunic (luxury, good fortune, jovial warmth, and sensual enjoyment)',
                       'Radiant, happy facial expression (deep contentment, triumph, and peace of mind)',
                       'Blue drapery covering table (spiritual and emotional depth supporting material satisfaction)'],
        'professions': [   'Luxury restaurateurs, master sommeliers, and private chefs',
                           'Boutique hospitality owners and celebratory hosts',
                           'Aesthetic wellness clinic owners and luxury stylists',
                           'Philanthropic benefactors and feast organizers',
                           'Successful lifestyle authors and motivational figures'],
        'upright': {   'keywords': ['A Wish Come True', 'Fulfillment', 'Satisfaction', 'Abundance', 'Contentment'],
                       'general': "Nine of Cups manifests: A wish come true. The celebrated 'Wish Card' of the Tarot. "
                                  'Emotional fulfillment, success, radiant satisfaction, and good fortune.',
                       'love': 'Romantic bliss, finding your dream partner, deep mutual emotional satisfaction, and '
                               'celebration of true love.',
                       'career': 'Attaining your dream professional role, public praise, financial bonuses, and peak '
                                 'job satisfaction.',
                       'finance': 'Abundant financial comfort, luxurious lifestyle, profitable business returns, and '
                                  'enjoying wealth with joy.',
                       'spiritual': 'Deep soul contentment (Santosha); recognizing that your cup overflows with divine '
                                    'grace and blessing.'},
        'reversed': {   'keywords': [   'Smugness',
                                        'Overindulgence',
                                        'Superficial Satisfaction',
                                        'Gluttony',
                                        'Unfulfilled Longing'],
                        'general': 'Nine of Cups reversed cautions: Smug arrogance, physical overindulgence, gluttony, '
                                   'or realizing material success does not heal inner emptiness.',
                        'love': 'Smug complacency in relationship, taking love for granted, overindulging in '
                                'food/drink instead of emotional intimacy.',
                        'career': 'Complacency at work, resting on past laurels, or discovering that a prestigious '
                                  'role is spiritually hollow.',
                        'finance': 'Excessive hedonistic spending, wasteful luxury splurges, or financial smugness '
                                   'leading to careless budget leaks.',
                        'spiritual': 'Mistaking sensory pleasure for spiritual realization; cultivating authentic '
                                     'inner depth over outer indulgence.'},
        'remedy': "Align with Water element through mindful contemplation. Chant planetary seed mantra for Guru: 'Om "
                  "Gurave Namah'.",
        'affirmation': 'My heart is filled with gratitude; my wishes manifest with divine abundance, joy, and peace.'},
    {   'id': 'ten_of_cups',
        'name': 'Ten of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 10,
        'element': 'Water',
        'astrology': 'Mars in Pisces (March 13 – April 12)',
        'vedic_graha': 'Mangal',
        'image_slug': 'ten-of-cups',
        'numerology': '10 (1) (Completion, renewal)',
        'timing_window': 'Autumn | Weeks to Months | March 13 – April 12 (Pisces)',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Happiness and family',
        'symbols': [   'Loving couple with arms raised in gratitude and two dancing children (happiness and family, '
                       'lasting domestic bliss)',
                       'Ten golden cups arranged across a brilliant rainbow in the sky (divine covenant, spiritual '
                       'blessing, pregnancy/fulfillment)',
                       'Cozy countryside home nestled among lush trees and river (secure domestic sanctuary, lasting '
                       'peace)',
                       'Flowing river in foreground (uninterrupted flow of love, prosperity, and emotional vitality)',
                       'Green landscape and blue sky (radiant peace, harmony across generations, and ultimate '
                       'emotional completion)'],
        'professions': [   'Family counselors, marriage officiants, and adoption specialists',
                           'Domestic residential architects and community sanctuary planners',
                           'Childcare center founders and maternal wellness directors',
                           'Community foundation directors and family legacy managers',
                           'Holiday retreat owners catering to harmonious family reunions'],
        'upright': {   'keywords': [   'Happiness and Family',
                                       'Domestic Bliss',
                                       'Rainbow of Blessings',
                                       'Harmony',
                                       'Completion'],
                       'general': 'Ten of Cups manifests: Happiness and family. Ultimate domestic harmony, peaceful '
                                  'family life, pregnancy or conception, and divine blessings.',
                       'love': 'Marital bliss, soulmate union crowned with family happiness, lasting devotion, and '
                               'shared domestic paradise.',
                       'career': 'Harmonious workplace culture, working with supportive colleagues who feel like '
                                 'family, and achieving work-life balance.',
                       'finance': 'Secure family finances, prosperous home ownership, and intergenerational financial '
                                  'harmony.',
                       'spiritual': 'Living in state of spiritual grace; seeing the divine play (Lila) in family and '
                                    'community relationships.'},
        'reversed': {   'keywords': [   'Domestic Friction',
                                        'Broken Family Vows',
                                        'Unrealistic Expectations',
                                        'Family Disputes'],
                        'general': 'Ten of Cups reversed cautions: Family disputes, domestic friction, unrealistic '
                                   'fairy-tale expectations, or broken domestic peace.',
                        'love': 'Marital arguments, disagreements over parenting or domestic duties, or keeping up a '
                                'happy facade while struggling inside.',
                        'career': 'Workplace hostility undermining team morale, feeling alienated from coworkers, or '
                                  'severe work-life imbalance.',
                        'finance': 'Financial strain on the family, disputes over household budgets, or arguments over '
                                   'supporting extended family.',
                        'spiritual': 'Disillusionment when spiritual community fails to meet unrealistic ideals; '
                                     'cultivating forgiveness.'},
        'remedy': "Align with Water element through mindful contemplation. Chant planetary seed mantra for Mangal: 'Om "
                  "Mangalaya Namah'.",
        'affirmation': 'My home is a sanctuary of love, peace, and mutual respect; divine harmony blesses my family.'},
    {   'id': 'page_of_cups',
        'name': 'Page of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 11,
        'element': 'Water',
        'astrology': 'Water Signs (Cancer, Scorpio, Pisces)',
        'vedic_graha': 'Chandra',
        'image_slug': 'page-of-cups',
        'numerology': '11 (2) (Master intuition / Youthful innocence)',
        'timing_window': 'Autumn | Weeks to Months | Water Archetype',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Fun and socializing',
        'symbols': [   'Youth in floral-embroidered blue tunic standing near ocean (fun and socializing, creative, '
                       'healer, not ready for commitment)',
                       'Curious blue fish peeking out of golden cup (unexpected intuitive messages, psychic surprise, '
                       'creative spark)',
                       'Flowing waves behind the youth (fluid emotions, imaginative depths, and psychic receptivity)',
                       'Beret with floating pink scarf (poetic spirit, romantic imagination, and playful creativity)',
                       'Gentle contemplative posture (innocent curiosity, vulnerability, and sweet affection)'],
        'professions': [   'Poets, lyricists, and creative fiction apprentices',
                           'Junior artists, fashion illustrators, and theatrical performers',
                           'Pediatric counselors and expressive arts therapists',
                           'Social event organizers and creative party planners',
                           'Intuitive card readers and spiritual healing students'],
        'upright': {   'keywords': [   'Fun and Socializing',
                                       'Intuitive Message',
                                       'Creative Spark',
                                       'Sweet Romance',
                                       'Innocence'],
                       'general': 'Page of Cups manifests: Fun and socializing. Unexpected intuitive messages, playful '
                                  'creative sparks, sweet invitations, and heartfelt compliments.',
                       'love': 'Sweet romantic crush, poetic love notes, playful socializing, opening your heart with '
                               'innocent vulnerability.',
                       'career': 'Creative project proposal, receiving compliments on artistic work, intuitive '
                                 'solutions to complex problems.',
                       'finance': 'Small financial gifts, funding for creative artistic hobbies, or promising creative '
                                  'income ventures.',
                       'spiritual': 'Developing psychic intuition, paying attention to synchronistic messages, and '
                                    'trusting gentle gut instincts.'},
        'reversed': {   'keywords': ['Emotional Oversensitivity', 'Childish Tantrums', 'Escapism', 'Broken Promises'],
                        'general': 'Page of Cups reversed cautions: Emotional oversensitivity, mood swings, escapist '
                                   'daydreaming, or flaky unreliability.',
                        'love': 'Immature romantic games, playing the victim in romance, overly dramatic emotional '
                                'outbursts, or fear of commitment.',
                        'career': 'Taking constructive workplace feedback as a personal attack, emotional daydreaming '
                                  'replacing actual work.',
                        'finance': 'Impulsive spending on sentimental knick-knacks, financial daydreams without '
                                   'practical action.',
                        'spiritual': 'Getting lost in ungrounded psychic fantasies; needing to anchor intuition in '
                                     'practical discernment.'},
        'remedy': 'Align with Water element through mindful contemplation. Chant planetary seed mantra for Chandra: '
                  "'Om Som Somaya Namah'.",
        'affirmation': 'I listen to the gentle whispers of my intuition and express my emotions with playful, honest '
                       'grace.'},
    {   'id': 'knight_of_cups',
        'name': 'Knight of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 12,
        'element': 'Water',
        'astrology': 'Water Signs (Cancer, Scorpio, Pisces)',
        'vedic_graha': 'Shukra',
        'image_slug': 'knight-of-cups',
        'numerology': '12 (3) (Romantic idealist, 20-35 years masculine)',
        'timing_window': 'Autumn | Weeks to Months | Water Archetype',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'A dreamer, proposal',
        'symbols': [   'Graceful knight riding gentle grey horse holding golden cup forward (a dreamer, proposal, '
                       'romantic idealist)',
                       'Wings on helmet and heels (freedom, open-minded, Mercury/Hermes, messenger of love and poetry)',
                       'Flowing river and tranquil green landscape (emotional depth, peaceful progress, and noble '
                       'romance)',
                       'Cloak embroidered with red fish (water element, spiritual passion, and creative imagination)',
                       'Gentle pace of the steed (thoughtful, deliberate emotional approach rather than reckless '
                       'rushing)'],
        'professions': [   'Poets, romantic songwriters, and classical musicians',
                           'Artistic emissaries, cultural diplomats, and creative directors',
                           'Proposal consultants, wedding planners, and romantic stylists',
                           'Empathetic mediators and conflict resolution counselors',
                           'Inspirational storytellers and cinematic romantics'],
        'upright': {   'keywords': [   'A Dreamer, Proposal',
                                       'Romantic Charm',
                                       'Creative Offer',
                                       'Following the Heart',
                                       'Poetry'],
                       'general': 'Knight of Cups manifests: A dreamer, proposal. A romantic proposal, poetic charm, '
                                  "creative invitations, and following your heart's calling.",
                       'love': 'Heartfelt romantic proposal, sweep-you-off-your-feet romance, emotional chivalry, and '
                               'deep poetic devotion.',
                       'career': 'Inspiring creative offers, invitations to join an artistic venture, diplomatic '
                                 'workplace success, and following your passion.',
                       'finance': 'Financial backing for an artistic project, harmonious investments in beauty and '
                                  'aesthetics.',
                       'spiritual': 'Walking the path of devotion (Bhakti Yoga); surrendering the heart to divine '
                                    'beauty and compassion.'},
        'reversed': {   'keywords': [   'Unrealistic Delusions',
                                        'Love Bombing',
                                        'Ghosting',
                                        'Manipulative Charm',
                                        'Moodiness'],
                        'general': 'Knight of Cups reversed cautions: Emotional manipulation, superficial romantic '
                                   'charm, love bombing followed by ghosting, or passive unreliability.',
                        'love': 'Partner who makes grandiose promises but never follows through, escapist romantic '
                                'delusions, or emotional deception.',
                        'career': 'All talk and no execution in business proposals, unreliable artistic partners, or '
                                  'letting moods derail commitments.',
                        'finance': 'Falling for charming financial pitches lacking substance, investments driven '
                                   'purely by fantasy.',
                        'spiritual': 'Spiritual romanticism; chasing spiritual highs without the discipline to do real '
                                     'inner shadow work.'},
        'remedy': "Align with Water element through mindful contemplation. Chant planetary seed mantra for Shukra: 'Om "
                  "Shukraya Namah'.",
        'affirmation': 'I follow my heart with integrity, offering my love and creative gifts with grounded devotion.'},
    {   'id': 'queen_of_cups',
        'name': 'Queen of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 13,
        'element': 'Water',
        'astrology': 'Water Signs (Cancer, Scorpio, Pisces)',
        'vedic_graha': 'Chandra',
        'image_slug': 'queen-of-cups',
        'numerology': '13 (4) (Mature feminine, empathetic healer)',
        'timing_window': 'Autumn | Weeks to Months | Water Archetype',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'An intuitive woman',
        'symbols': [   "Queen seated on ornate throne carved with sea-nymphs at the water's edge (an intuitive woman, "
                       'creative and healer, daydreamer, psychic)',
                       'Holding ornate golden covered chalice with two angels on handle (guarding the sacred mysteries '
                       'of the soul)',
                       'Gazing into the cup with deep psychic trance (clairvoyance, telepathic connection, emotional '
                       'mastery)',
                       'Flowing sea and water caressing her feet (intimate communion with the subconscious without '
                       'drowning)',
                       'Robes flowing like water merging with the pebble beach (grounded embodiment of pure water '
                       'element)'],
        'professions': [   'Psychics, clairvoyants, and professional tarot readers',
                           'Spiritual healers, Reiki masters, and energy workers',
                           'Psychiatric nurses, hospice directors, and pediatric counselors',
                           'Poets, lyrical musicians, and expressive watercolor artists',
                           'Empathetic listeners, confidential advisors, and meditation guides'],
        'upright': {   'keywords': [   'An Intuitive Woman',
                                       'Empathetic Healer',
                                       'Psychic Clairvoyance',
                                       'Unconditional Love',
                                       'Depth'],
                       'general': 'Queen of Cups manifests: An intuitive woman. Profound psychic intuition, empathetic '
                                  'healing, unconditional maternal love, and deep emotional wisdom.',
                       'love': "Deep soulful devotion, empathetic understanding of partner's unexpressed feelings, "
                               'emotional sanctuary, and unconditional love.',
                       'career': 'Intuitive career decisions, compassionate leadership, mentoring others with empathy, '
                                 'and creative artistic triumphs.',
                       'finance': 'Financial decisions guided by keen intuition; wealth used to create a peaceful, '
                                  'healing domestic environment.',
                       'spiritual': 'Awakening of high psychic perception, clairvoyance, profound meditation, and '
                                    'merging with the universal heart.'},
        'reversed': {   'keywords': [   'Emotional Manipulation',
                                        'Codependency',
                                        'Melodrama',
                                        'Suffocating Smothering',
                                        'Mood Swings'],
                        'general': 'Queen of Cups reversed cautions: Emotional manipulation, drowning in emotional '
                                   'melodrama, codependency, or neglecting self-care.',
                        'love': 'Suffocating partner with insecurity, playing the emotional martyr, passive-aggressive '
                                'guilt trips, or mood swings.',
                        'career': 'Letting personal emotions cloud professional judgment, becoming the workplace '
                                  "sponge for everyone's toxic complaints.",
                        'finance': 'Financial boundary collapse; lending money to undeserving emotional manipulators, '
                                   'emotional spending.',
                        'spiritual': 'Psychic vulnerability; absorbing negative astral energies without shielding; '
                                     'needing energetic hygiene.'},
        'remedy': 'Align with Water element through mindful contemplation. Chant planetary seed mantra for Chandra: '
                  "'Om Som Somaya Namah'.",
        'affirmation': 'I trust my psychic intuition and hold space for deep healing, grounded in healthy emotional '
                       'boundaries.'},
    {   'id': 'king_of_cups',
        'name': 'King of Cups',
        'arcana': 'minor',
        'suit': 'cups',
        'number': 14,
        'element': 'Water',
        'astrology': 'Water Signs (Cancer, Scorpio, Pisces)',
        'vedic_graha': 'Guru',
        'image_slug': 'king-of-cups',
        'numerology': '14 (5) (Mature masculine, emotional master)',
        'timing_window': 'Autumn | Weeks to Months | Water Archetype',
        'timing_season': 'Autumn',
        'timing_speed': 'Weeks to Months',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'An intuitive man',
        'symbols': [   'King seated on grey stone throne floating over turbulent sea (an intuitive man, grey throne = '
                       'unbiased judgement)',
                       'Throne over ocean (lighthearted nature, mastery over turbulent emotional waves without being '
                       'submerged)',
                       'Golden cup in right hand and lotus scepter in left (balance of feeling with spiritual '
                       'authority)',
                       'Fish leaping from water and ship sailing calmly on horizon (subconscious insights rising, safe '
                       'navigation of storms)',
                       'Fish amulet around neck (deep psychic lineage, emotional mastery, and wisdom)'],
        'professions': [   'Senior clinical psychologists, psychiatrists, and medical directors',
                           'Diplomatic arbiters, high-stakes peace negotiators, and judges',
                           'Ship captains, maritime directors, and oceanic preservationists',
                           'Artistic mentors, music producers, and cultural patrons',
                           'Compassionate spiritual teachers and pastoral leaders'],
        'upright': {   'keywords': [   'An Intuitive Man',
                                       'Emotional Mastery',
                                       'Calm Wisdom',
                                       'Compassionate Leader',
                                       'Equilibrium'],
                       'general': 'King of Cups manifests: An intuitive man. Master of emotions, calm wisdom in the '
                                  'midst of storm, compassionate counsel, and unbiased judgment.',
                       'love': 'Devoted, emotionally mature partner; steady emotional rock, unconditional love, and '
                               'profound mutual understanding.',
                       'career': 'Compassionate executive leadership, handling crises with serene composure, resolving '
                                 'workplace conflicts diplomatically.',
                       'finance': 'Prudent financial stewardship, investing in humanitarian and artistic ventures, and '
                                  'financial peace of mind.',
                       'spiritual': 'Mastery of the emotional body; emotional equanimity (Samatva) in both joy and '
                                    'sorrow.'},
        'reversed': {   'keywords': [   'Emotional Coldness',
                                        'Passive-Aggression',
                                        'Manipulative Tyrant',
                                        'Suppressed Rage',
                                        'Addiction'],
                        'general': 'King of Cups reversed cautions: Emotional coldness, manipulative gaslighting, '
                                   'suppressed rage, passive-aggressive tyranny, or substance escapism.',
                        'love': 'Emotional withholding, playing mind games, volatile moodiness beneath a calm mask, or '
                                'cold detachment in intimacy.',
                        'career': 'Manipulative management, using emotional vulnerabilities against employees, corrupt '
                                  'favoritism.',
                        'finance': 'Financial deception, irresponsible economic decisions made during emotional '
                                   'turmoil, or secret debts.',
                        'spiritual': 'Using spiritual status to manipulate vulnerable seekers emotionally; spiritual '
                                     'hypocrisy.'},
        'remedy': "Align with Water element through mindful contemplation. Chant planetary seed mantra for Guru: 'Om "
                  "Gurave Namah'.",
        'affirmation': 'I master my emotions with calm wisdom, leading with compassion, integrity, and profound '
                       'peace.'},
    {   'id': 'ace_of_swords',
        'name': 'Ace of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 1,
        'element': 'Air',
        'astrology': 'Aquarius, Gemini, Libra',
        'vedic_graha': 'Budha',
        'image_slug': 'ace-of-swords',
        'numerology': '1',
        'timing_window': 'Spring | Days to Weeks | February 12 – March 12 (Aquarius Decan)',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'New ideas, thoughts, success',
        'symbols': [   'Closed fist emerging from white cloud gripping upright double-edged sword (grab opportunity, '
                       'decisive will)',
                       'Hidden thumb (knowledge by flashes of insight, awakening of consciousness)',
                       'Golden crown encircling tip of sword (regality, authority, and triumphant intellect)',
                       'Palm branch on right (immortality, victory) and olive branch on left (peace, growth)',
                       'Six drops of golden dew falling like sparks (creative seeds of thought, ideas from heaven not '
                       'earth, flowing freely)',
                       'Barren purple mountains below (practical objective approach, dry and unemotional clarity '
                       'coming out of fog)'],
        'professions': [   'Legal affairs, contract specialists, and corporate attorneys',
                           'Mental work, research scientists, and academic philosophers',
                           'Surgeons, diagnosticians, and forensic analysts',
                           'Army, police, and intelligence officers (male-dominated work)',
                           'Strategic negotiators and public policy architects'],
        'upright': {   'keywords': ['New Ideas', 'Thoughts', 'Success', 'Mental Clarity', 'Breakthrough Truth'],
                       'general': 'Ace of Swords manifests: New ideas, thoughts, success. Piercing mental clarity, '
                                  'victorious truth, cutting through confusion, and breakthrough intellect.',
                       'love': 'Clear intellectual communication, cutting through illusions, honest boundary setting, '
                               'and authentic transparent dialogue.',
                       'career': 'Brilliant analytical strategy, winning legal arguments, intellectual breakthrough, '
                                 'successful contract signing.',
                       'finance': 'Objective financial budgeting, eliminating wasteful leaks with sharp discipline, '
                                  'and signing profitable clear agreements.',
                       'spiritual': 'Discrimination (Viveka); cutting the cords of mental delusion with the sharp '
                                    'sword of truth.'},
        'reversed': {   'keywords': [   'Clouded Judgement',
                                        'Hostility',
                                        'Brutal Words',
                                        'Deceitful Contracts',
                                        'Mental Fatigue'],
                        'general': 'Ace of Swords reversed cautions: Clouded thinking, intellectual arrogance, brutal '
                                   'verbal attacks, or misleading contracts.',
                        'love': 'Harsh critical words, suspicion, mental mind-games, or refusal to communicate '
                                'honestly.',
                        'career': 'Misunderstandings, paralysis by analysis, workplace hostility, or contract '
                                  'breaches.',
                        'finance': 'Financial disputes, deceitful agreements, or panic-driven economic choices.',
                        'spiritual': 'Obsessive mental loops, anxiety, and sleepless nights; ground the mind in '
                                     'somatic peace.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Budha: 'Om "
                  "Budhaya Namah'.",
        'affirmation': 'I wield the sword of truth with clarity, integrity, and compassionate wisdom.'},
    {   'id': 'two_of_swords',
        'name': 'Two of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 2,
        'element': 'Air',
        'astrology': 'Moon in Libra (October 16 – November 14)',
        'vedic_graha': 'Chandra',
        'image_slug': 'two-of-swords',
        'numerology': '2 (Balance, choice, stalemate)',
        'timing_window': 'Spring | Days to Weeks | October 16 – November 14 (Libra)',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'NO Card (Stalemate / Blocked; Reversed: NO Card)',
        'one_liner': 'Stalemate',
        'symbols': [   'Blindfolded woman seated on stone bench (refusing to see truth, willful blindness, stalemate)',
                       'Two heavy crossed broadswords held over chest (defensive barrier protecting heart, stalemate '
                       'of intellect)',
                       'Calm grey sea with rocky reefs rising from water (hidden emotional perils, navigating '
                       'emotional obstacles)',
                       'Crescent moon in night sky (intuition available, but ignored in favor of mental paralysis)',
                       'Stone bench (rigid position, refusing to budge until forced)'],
        'professions': [   'Legal conflict resolution specialists and neutral arbitrators',
                           'Scientific researchers weighing competing theories',
                           'Contract compliance auditors and treaty negotiators',
                           'Ethical dispute mediators and institutional arbiters',
                           'Philosophical analysts investigating cognitive deadlocks'],
        'upright': {   'keywords': ['Stalemate', 'Truce', 'Difficult Choice', 'Avoiding the Truth', 'Mental Block'],
                       'general': 'Two of Swords manifests: Stalemate. A deadlock between two opposing viewpoints, '
                                  'refusing to see the facts, and avoiding a painful choice.',
                       'love': 'Emotional standoff, refusing to address the elephant in the room, holding up emotional '
                               'walls against partner.',
                       'career': 'Stalemate in negotiations, competing corporate factions locked in deadlock, '
                                 'indecision on strategic paths.',
                       'finance': 'Frozen assets, holding off on major financial decisions until information '
                                  'clarifies, neutral stance.',
                       'spiritual': 'Suppressing intuition; closing your eyes to inner knowing to avoid confronting '
                                    'difficult reality.'},
        'reversed': {   'keywords': ['Lifting the Blindfold', 'Facing the Truth', 'Breaking Deadlock', 'Resolution'],
                        'general': 'Two of Swords reversed cautions: The blindfold comes off; forced to face difficult '
                                   'facts, breaking deadlock, and resolving the stalemate.',
                        'love': 'Finally speaking the unspoken truth, addressing lingering issues, breaking emotional '
                                'standoff.',
                        'career': 'Breaking corporate deadlock, making a tough executive choice, uncovering hidden '
                                  'information.',
                        'finance': 'Unfreezing financial matters, making overdue financial decisions with full '
                                   'visibility.',
                        'spiritual': 'Removing spiritual illusions; acknowledging truth even when it disrupts '
                                     'comfortable mental complacency.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Chandra: 'Om "
                  "Som Somaya Namah'.",
        'affirmation': 'I remove the blindfold of fear; I welcome truth with clarity and make courageous decisions.'},
    {   'id': 'three_of_swords',
        'name': 'Three of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 3,
        'element': 'Air',
        'astrology': 'Saturn in Libra (October 16 – November 14)',
        'vedic_graha': 'Shani',
        'image_slug': 'three-of-swords',
        'numerology': '3 (Creativity, growth through adversity)',
        'timing_window': 'Spring | Days to Weeks | October 16 – November 14 (Libra)',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'NO Card (Heartbreak / Pain; Reversed: NO Card)',
        'one_liner': 'Heartbreak',
        'symbols': [   'Large crimson heart pierced through by three swords (stabbing - pain inflicted by others, '
                       'heartbreak, sorrow)',
                       'Dark storm clouds and torrential rain in background (emotional tempest, grief, and tears shed)',
                       'Swords piercing from opposing angles (conflicting painful truths piercing the emotional '
                       'center)',
                       'Absence of human figures (universal, inescapable human experience of sorrow and purification)',
                       'Rain washing the scene (cathartic cleansing of the heart through necessary grief)'],
        'professions': [   'Divorce attorneys, family court litigators, and custody evaluators',
                           'Trauma therapists, heartbreak counselors, and grief clinicians',
                           'Cardiac surgeons, cardiologists, and thoracic physicians',
                           'Crisis hotline operators and emergency emotional support leads',
                           'Tragedy dramatists, sorrow poets, and expressive mournful artists'],
        'upright': {   'keywords': ['Heartbreak', 'Sorrow', 'Painful Truth', 'Betrayal', 'Emotional Surgery'],
                       'general': 'Three of Swords manifests: Heartbreak. Painful heartbreak, sorrow, betrayal, and '
                                  'harsh truth piercing emotional defenses; necessary release of grief.',
                       'love': 'Painful breakup, discovery of emotional betrayal, harsh words causing deep wounds, or '
                               'bitter separation.',
                       'career': 'Sudden contract termination, painful rejection, workplace betrayal by trusted ally, '
                                 'or cutting criticism.',
                       'finance': 'Painful financial loss, broken financial partnership, costly legal dispute over '
                                  'assets.',
                       'spiritual': 'The sacred wound; realizing that the heart must crack open to let higher divine '
                                    'compassion in.'},
        'reversed': {   'keywords': [   'Healing Heartbreak',
                                        'Releasing Grief',
                                        'Forgiveness',
                                        'Reconciliation',
                                        'Recovery'],
                        'general': 'Three of Swords reversed cautions: Releasing sorrow, the worst of the storm '
                                   'passing, forgiving past betrayal, and emotional healing.',
                        'love': 'Healing after heartbreak, apologizing and making amends, moving past pain toward '
                                'reconciliation or healthy closure.',
                        'career': 'Recovering from job loss, finding new opportunities after setback, letting go of '
                                  'professional resentment.',
                        'finance': 'Recovering from fiscal heartbreak, restructuring debt, and emotional peace '
                                   'returning after monetary crisis.',
                        'spiritual': 'Transmuting personal pain into universal empathy; healing the wounded heart '
                                     'through divine grace.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Shani: 'Om "
                  "Sham Shanaicharaya Namah'.",
        'affirmation': 'I allow my heart to heal; through sorrow, I discover limitless compassion and profound inner '
                       'peace.'},
    {   'id': 'four_of_swords',
        'name': 'Four of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 4,
        'element': 'Air',
        'astrology': 'Jupiter in Libra (October 16 – November 14)',
        'vedic_graha': 'Guru',
        'image_slug': 'four-of-swords',
        'numerology': '4 (Structure, stability, rest)',
        'timing_window': 'Spring | Days to Weeks | October 16 – November 14 (Libra)',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'MAYBE Card (Rest / Recuperation needed; Reversed: NO Card)',
        'one_liner': 'Rest',
        'symbols': [   'Effigy of knight resting in prayer pose on stone tomb inside sanctuary (trying to raise '
                       'consciousness, peaceful rest)',
                       'Three swords hanging on wall pointing downward (past hardships, mental battles laid aside)',
                       "Fourth sword carved horizontally beneath the knight's body (solitary weapon held in reserve "
                       'for future)',
                       'Stained-glass window depicting holy figure (spiritual sanctuary, divine protection, and moral '
                       'refuge)',
                       'Solid stone tomb (stability, quiet recuperation, and protection from the noisy external '
                       'world)'],
        'professions': [   'Hospital doctors, recuperative nurses, and post-surgery rehabilitation staff',
                           'Silent retreat directors, meditation monastery abbots, and monks',
                           'Sleep therapy specialists and chronic fatigue clinicians',
                           'Sanctuary directors and sabbatical program managers',
                           'Philosophers taking intellectual respites to distill findings'],
        'upright': {   'keywords': ['Rest', 'Recuperation', 'Sanctuary', 'Meditation', 'Mental Peace'],
                       'general': 'Four of Swords manifests: Rest. A necessary pause after intense battles; retreat '
                                  'into quiet meditation to recharge your mental and spiritual vitality.',
                       'love': 'Taking a peaceful breather in relationship, stepping back from heated arguments, '
                               'resting together in quiet comfort.',
                       'career': 'Taking overdue vacation, stepping back from workplace stress, recuperating before '
                                 'the next big campaign.',
                       'finance': 'Freezing unnecessary spending, resting financial maneuvers, maintaining steady '
                                  'conservative reserves.',
                       'spiritual': 'Silent meditation (Mauna), deep prayer sanctuary, raising consciousness through '
                                    'quiet contemplative retreat.'},
        'reversed': {   'keywords': ['Forced Bedrest', 'Burnout', 'Restlessness', 'Premature Return to Battle'],
                        'general': 'Four of Swords reversed cautions: Chronic burnout from refusing to pause, '
                                   'insomnia, or rushing back into chaos prematurely.',
                        'love': 'Resuming toxic arguments without healing, inability to find peace with partner, '
                                'chronic anxiety.',
                        'career': 'Exhaustion forcing medical leave, returning to work too early and crashing, '
                                  'workplace panic.',
                        'finance': 'Financial stress causing sleepless nights; inability to find calm despite adequate '
                                   'resources.',
                        'spiritual': 'Mental restlessness disrupting meditation; needing somatic grounding to calm '
                                     'frantic mental chatter.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Guru: 'Om "
                  "Gurave Namah'.",
        'affirmation': 'I honor my need for rest and retreat; in quiet sanctuary, my mind and spirit are restored.'},
    {   'id': 'five_of_swords',
        'name': 'Five of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 5,
        'element': 'Air',
        'astrology': 'Venus in Aquarius (February 12 – March 12)',
        'vedic_graha': 'Shukra',
        'image_slug': 'five-of-swords',
        'numerology': '5 (Change, conflict, defeat)',
        'timing_window': 'Spring | Days to Weeks | February 12 – March 12 (Aquarius)',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'NO Card (Conflict / Betrayal; Reversed: NO Card)',
        'one_liner': 'Conflict',
        'symbols': [   'Smug figure holding three swords looking back mockingly (winning at all costs, arrogance, '
                       'hollow victory)',
                       'Two defeated figures walking away toward choppy sea with bowed heads (given up or betrayed, '
                       'grief, walking away)',
                       'Two discarded swords lying on ground in foreground (weapons dropped in surrender or loss)',
                       'Choppy grey waves and jagged storm clouds (lingering hostility, toxic aftermath of conflict)',
                       'Scornful facial expression (pride, lack of empathy, and winning through unfair means)'],
        'professions': [   'Hostile takeover specialists and corporate raiders',
                           'Aggressive litigation attorneys and confrontational negotiators',
                           'Whistleblower investigators handling organizational corruption',
                           'Labor union dispute litigators and arbitration foes',
                           'Competitive intelligence scouts and forensic interrogators'],
        'upright': {   'keywords': ['Conflict', 'Hollow Victory', 'Betrayal', 'Hostility', 'Walking Away'],
                       'general': 'Five of Swords manifests: Conflict. A toxic battle where winning costs too much; '
                                  'beware of underhanded tactics, betrayal, or walking away from malice.',
                       'love': 'Winning arguments at the expense of love, spiteful words, emotional betrayal, or '
                               'walking away from a toxic partner.',
                       'career': 'Cutthroat office politics, taking credit at the expense of peers, hollow victory '
                                 'that leaves you isolated.',
                       'finance': 'Financial disputes, predatory contracts, winning a legal settlement that leaves '
                                  'bitter aftermath.',
                       'spiritual': 'Spiritual ego battles; arguing to dominate others intellectually rather than '
                                    'seeking humble truth.'},
        'reversed': {   'keywords': ['Desire for Peace', 'Ending Feuds', 'Making Amends', 'Moving Past Spite'],
                        'general': 'Five of Swords reversed cautions: Laying down weapons, realizing conflict is '
                                   'futile, seeking reconciliation, or lingering resentment.',
                        'love': 'Ending toxic fighting, apologizing for cruel words, seeking genuine mutual healing or '
                                'peaceful separation.',
                        'career': 'Ending corporate feuds, resolving labor disputes through fair mediation, moving '
                                  'past toxic office rivalry.',
                        'finance': 'Settling outstanding disputes out of court, cutting losses to achieve peace of '
                                   'mind.',
                        'spiritual': 'Surrendering the need to be right; discovering that inner peace is infinitely '
                                     'more valuable than winning arguments.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Shukra: 'Om "
                  "Shukraya Namah'.",
        'affirmation': 'I choose peace over pride; I release toxic conflict and walk in honor, truth, and harmony.'},
    {   'id': 'six_of_swords',
        'name': 'Six of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 6,
        'element': 'Air',
        'astrology': 'Mercury in Aquarius (February 12 – March 12)',
        'vedic_graha': 'Budha',
        'image_slug': 'six-of-swords',
        'numerology': '6 (Harmony, communication, cooperation)',
        'timing_window': 'Spring | Days to Weeks | February 12 – March 12 (Aquarius)',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Leaving conflict behind',
        'symbols': [   'Ferryman poling boat carrying cloaked woman and child (leaving conflict behind, moving to safe '
                       'sanctuary)',
                       'Six upright swords standing in boat (carrying past memories and mental baggage, but peacefully '
                       'contained)',
                       'Wavy, choppy water on right transitioning to calm, smooth water on left (passage from turmoil '
                       'to serenity)',
                       'Distant peaceful green shoreline (safe arrival, brighter future, and mental stability)',
                       'Quiet solemn posture of passengers (mental recovery, relief after hardship, and silent '
                       'journey)'],
        'professions': [   'Relocation specialists, immigration consultants, and transition coaches',
                           'Refugee aid directors and international humanitarian workers',
                           'Digital nomads, remote workers, and traveling logistics coordinators',
                           'Travel itinerary planners and maritime ferry directors',
                           'Psychological recovery guides aiding trauma transition'],
        'upright': {   'keywords': [   'Leaving Conflict Behind',
                                       'Smooth Waters',
                                       'Transition',
                                       'Mental Recovery',
                                       'Safe Journey'],
                       'general': 'Six of Swords manifests: Leaving conflict behind. Moving from stormy turmoil into '
                                  'calm, tranquil waters; physical travel or mental recovery after adversity.',
                       'love': 'Leaving relationship drama behind, embarking on a peaceful vacation with partner, '
                               'healing together after turbulent times.',
                       'career': 'Transitioning to a healthier workplace, leaving toxic office politics, smooth '
                                 'progression of technical projects.',
                       'finance': 'Recovering from financial turbulence, moving toward fiscal stability, managing '
                                  'debts smoothly.',
                       'spiritual': 'Mental stillness arriving after existential crisis; stepping out of mental storm '
                                    'into inner calm.'},
        'reversed': {   'keywords': ['Emotional Baggage', 'Rough Transition', 'Delayed Voyage', 'Unresolved Past'],
                        'general': 'Six of Swords reversed cautions: Past trauma resurfacing, delayed relocation, '
                                   'dragging old baggage into new situations, or choppy transitions.',
                        'love': 'Bringing baggage from past relationships into present bond, inability to move past '
                                'old arguments, or travel delays.',
                        'career': 'Struggling to adapt to a new job, past workplace drama following you, or stalled '
                                  'transition projects.',
                        'finance': 'Unresolved debts blocking smooth financial transition, unexpected expenses during '
                                   'relocation.',
                        'spiritual': 'Clinging to mental turbulence out of habit; resisting the gentle peace being '
                                     'offered.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Budha: 'Om "
                  "Budhaya Namah'.",
        'affirmation': 'I move calmly into peaceful waters; I leave all turmoil behind and embrace my bright future.'},
    {   'id': 'seven_of_swords',
        'name': 'Seven of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 7,
        'element': 'Air',
        'astrology': 'Moon in Aquarius (February 12 – March 12)',
        'vedic_graha': 'Chandra',
        'image_slug': 'seven-of-swords',
        'numerology': '7 (Assessment, stealth, strategy)',
        'timing_window': 'Spring | Days to Weeks | February 12 – March 12 (Aquarius)',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'MAYBE Card (Caution / Stealth / Possible Deception; Reversed: NO Card)',
        'one_liner': 'Theft and mishandling',
        'symbols': [   'Man sneaking away on tiptoes holding five swords (theft and mishandling, confidence to get '
                       'what you want, stealth)',
                       'Looking back over shoulder at military camp (caution, tactical cleverness, fear of detection)',
                       'Two swords remaining upright in ground behind him (incomplete theft, leaving evidence behind)',
                       'Military encampment with flags (strategic battle, outsmarting opposing force rather than '
                       'frontal assault)',
                       'Smiling sly expression (audacity, unconventional tactics, and intellectual craftiness)'],
        'professions': [   'Cybersecurity experts, ethical hackers, and vulnerability testers',
                           'Private investigators, surveillance specialists, and tactical operatives',
                           'Intellectual property attorneys and copyright protection litigators',
                           'Undercover journalists and investigative forensic reporters',
                           'Strategic risk consultants managing confidential acquisitions'],
        'upright': {   'keywords': ['Strategy', 'Stealth', 'Theft & Mishandling', 'Caution', 'Outsmarting Opposition'],
                       'general': 'Seven of Swords manifests: Theft and mishandling. Need for strategic stealth, '
                                  'guarding your intellectual property, outsmarting obstacles, or caution against '
                                  'deception.',
                       'love': 'Guarding secrets, sneaking around, fear of confrontation, or sensing that a partner is '
                               'withholding critical truth.',
                       'career': 'Guarding proprietary business ideas, strategic solo maneuvering, outsmarting '
                                 'competitors, or office politics.',
                       'finance': 'Protecting financial passwords, guarding against identity theft or embezzlement, '
                                  'keeping financial moves confidential.',
                       'spiritual': 'Examining whether you are deceiving yourself spiritually; honest self-audit '
                                    'without rationalization.'},
        'reversed': {   'keywords': ['Coming Clean', 'Confession', 'Conscience Prevailing', 'Caught in the Act'],
                        'general': 'Seven of Swords reversed cautions: Conscience triumphing over trickery, confessing '
                                   'past secrets, coming clean, or getting caught.',
                        'love': 'Confessing hidden secrets to partner, coming clean about infidelity or lies, clearing '
                                'the air with total honesty.',
                        'career': 'Uncovering corporate fraud, whistleblower revelations, or abandoning deceitful '
                                  'business practices.',
                        'finance': 'Audits catching financial discrepancies, repaying stolen funds, or resolving tax '
                                   'omissions.',
                        'spiritual': 'Total spiritual transparency; dropping all ego masks and standing unvarnished '
                                     'before the divine.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Chandra: 'Om "
                  "Som Somaya Namah'.",
        'affirmation': 'I act with integrity, protect my sacred boundaries, and walk in the brilliant light of truth.'},
    {   'id': 'eight_of_swords',
        'name': 'Eight of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 8,
        'element': 'Air',
        'astrology': 'Jupiter in Gemini (June 15 – July 14)',
        'vedic_graha': 'Guru',
        'image_slug': 'eight-of-swords',
        'numerology': '8 (Action, limitation, mental prison)',
        'timing_window': 'Spring | Days to Weeks | June 15 – July 14 (Gemini)',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'NO Card (Restriction / Trapped; Reversed: NO Card)',
        'one_liner': 'Restriction',
        'symbols': [   'Blindfolded woman bound loosely in red cords (restriction, limit of thoughts, out of comfort '
                       'zone)',
                       'Eight swords planted in ground surrounding her like a cage (self-imposed mental enclosure, '
                       'fear-based imprisonment)',
                       'Cords bound loosely around arms (bonds can be slipped off at will, trap is primarily mental)',
                       'Muddy water pooling at her feet (subconscious emotional stagnation keeping her stuck)',
                       'Castle on high mountain peak behind (safety, intellect, and home are reachable if she steps '
                       'forward)'],
        'professions': [   'Psychotherapists treating phobias, anxiety, and panic disorders',
                           'Civil liberties defense attorneys and wrongful conviction advocates',
                           'Support staff aiding domestic abuse survivors to reclaim autonomy',
                           'Career coaches guiding professionals out of imposter syndrome',
                           'Cognitive behavioral researchers studying self-imposed mental limits'],
        'upright': {   'keywords': ['Restriction', 'Mental Prison', 'Victim Mindset', 'Self-Imposed Limits', 'Fear'],
                       'general': 'Eight of Swords manifests: Restriction. You feel helpless and trapped, but the cage '
                                  'is mental; the bonds are loose and you hold the power to step free.',
                       'love': 'Feeling trapped in a relationship due to fear of change, victim mindset, or letting '
                               "partner's criticism paralyze you.",
                       'career': 'Feeling stuck in a dead-end job, self-doubt paralyzing career moves, imposter '
                                 'syndrome limiting potential.',
                       'finance': 'Feeling financially restricted; catastrophizing financial situation instead of '
                                  'looking for practical solutions.',
                       'spiritual': 'Overcoming the illusion of spiritual limitation (Bandhana); realizing your soul '
                                    'was never bound.'},
        'reversed': {   'keywords': ['Breaking Free', 'Removing Blindfold', 'Reclaiming Power', 'Overcoming Fear'],
                        'general': 'Eight of Swords reversed cautions: Slipping off the cords, removing the mental '
                                   'blindfold, stepping out of limiting beliefs, and reclaiming freedom.',
                        'love': 'Leaving a suffocating relationship, speaking up for yourself, breaking free from '
                                'emotional manipulation.',
                        'career': 'Overcoming imposter syndrome, applying for ambitious jobs, stepping out of '
                                  'workplace paralysis.',
                        'finance': 'Finding practical solutions to debt, realizing financial options exist, proactive '
                                   'budgeting.',
                        'spiritual': 'Liberation from dogmatic fears; recognizing your inherent spiritual sovereignty '
                                     'and freedom.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Guru: 'Om "
                  "Gurave Namah'.",
        'affirmation': 'I release all mental limits; I step out of fear and reclaim my divine freedom, power, and '
                       'clarity.'},
    {   'id': 'nine_of_swords',
        'name': 'Nine of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 9,
        'element': 'Air',
        'astrology': 'Mars in Gemini (June 15 – July 14)',
        'vedic_graha': 'Mangal',
        'image_slug': 'nine-of-swords',
        'numerology': '9 (Fruition, anxiety, mental strain)',
        'timing_window': 'Spring | Days to Weeks | June 15 – July 14 (Gemini)',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'NO Card (Insomnia / Anxiety; Reversed: NO Card)',
        'one_liner': 'Insomnia',
        'symbols': [   'Figure sitting upright in bed with face buried in hands (insomnia, mental anguish, '
                       'over-expectation from people)',
                       'Nine swords mounted horizontally on black wall above bed (looming anxious thoughts, '
                       'catastrophic worries)',
                       'Carved wooden bed base depicting combat and murder (primal fears and violent subconscious '
                       'nightmares)',
                       'Quilt embroidered with roses and astrological glyphs (human suffering, desire, and karmic '
                       'destiny)',
                       'Pure black wall background (dark night of the mind, isolation, and exaggerated nighttime '
                       'dread)'],
        'professions': [   'Sleep medicine specialists, somnologists, and insomnia researchers',
                           'Crisis hotline operators, suicide prevention leads, and counselors',
                           'Anxiety, panic, and obsessive-compulsive clinical psychologists',
                           'Trauma therapists and post-traumatic stress clinicians',
                           'Nighttime emergency psychiatric intervention staff'],
        'upright': {   'keywords': ['Insomnia', 'Anxiety', 'Nightmares', 'Overthinking', 'Mental Anguish'],
                       'general': 'Nine of Swords manifests: Insomnia. Sleepless nights, obsessive worry, guilt, and '
                                  'catastrophizing thoughts; remember that 90% of your fears exist only in the mind.',
                       'love': 'Torturing yourself with relationship insecurities, fear of abandonment, obsessive '
                               'jealousy, or guilt over past mistakes.',
                       'career': 'Workplace panic, imposter dread keeping you awake, fearing catastrophic project '
                                 'failure without evidence.',
                       'finance': 'Paralyzing financial anxiety, dreading bills, magnifying monetary difficulties '
                                  'beyond reality.',
                       'spiritual': 'The agonizing dark night of the mind; learning to observe catastrophic thoughts '
                                    'without believing them.'},
        'reversed': {   'keywords': [   'Light at End of Tunnel',
                                        'Dispelling Nightmares',
                                        'Mental Recovery',
                                        'Seeking Help'],
                        'general': 'Nine of Swords reversed cautions: Waking up from mental nightmare, realizing fears '
                                   'were exaggerated, finding peace, and seeking support.',
                        'love': 'Talking openly with partner to dispel insecurities, realizing fears were unfounded, '
                                'healing from anxiety.',
                        'career': 'Passing a dreaded workplace milestone safely, realizing project fears were '
                                  'groundless, regaining calm.',
                        'finance': 'Discovering financial problems are manageable with practical plan, relief from '
                                   'monetary dread.',
                        'spiritual': 'Surrendering mental torment to the divine; finding the profound peace that lies '
                                     'beyond frantic thoughts.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Mangal: 'Om "
                  "Mangalaya Namah'.",
        'affirmation': 'I release all anxious thoughts into divine light; my mind is peaceful, calm, and serene.'},
    {   'id': 'ten_of_swords',
        'name': 'Ten of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 10,
        'element': 'Air',
        'astrology': 'Sun in Gemini (June 15 – July 14)',
        'vedic_graha': 'Surya',
        'image_slug': 'ten-of-swords',
        'numerology': '10 (1) (End of cycle, rock bottom)',
        'timing_window': 'Spring | Days to Weeks | June 15 – July 14 (Gemini)',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'NO Card (Endings / Rock bottom; Reversed: NO Card)',
        'one_liner': 'Endings',
        'symbols': [   'Figure lying face-down on shoreline pierced by ten swords (bitching, betrayal, rock bottom, '
                       'final ending)',
                       'Red cape draped over lower body (vital life force spent, blood spilled in betrayal, complete '
                       'surrender)',
                       'Pure black stormy sky above, with golden sunrise breaking on horizon (the worst is over, dawn '
                       'arrives)',
                       'Calm, placid blue sea in background (peace returned to the realm, suffering has concluded)',
                       'Right hand curled in blessing gesture (sanctity in closure, forgiveness of betrayal, ready for '
                       'rebirth)'],
        'professions': [   'Forensic pathology examiners and coroner staff',
                           'Corporate bankruptcy trustees and liquidation executives',
                           'Emergency trauma surgeons and spinal rehabilitation clinicians',
                           'Crisis recovery directors helping organizations restart from zero',
                           'End-of-life doulas and bereavement counselors'],
        'upright': {   'keywords': ['Endings', 'Rock Bottom', 'Betrayal', 'Dawn of Renewal', 'Final Closure'],
                       'general': 'Ten of Swords manifests: Endings. Rock bottom reached, finality of a painful cycle, '
                                  'betrayal, and release; the worst is behind you and a glorious golden dawn arrives.',
                       'love': 'Final definitive breakup, betrayal exposed, end of a painful toxic dynamic, closure '
                               'that allows healing.',
                       'career': 'Abrupt ending of an unsustainable job, project cancelled, corporate betrayal, '
                                 'stepping out of the wreckage to restart.',
                       'finance': 'Rock bottom in finances, business failure, insolvency, clearing the slate to build '
                                  'back with clean foundations.',
                       'spiritual': 'Absolute death of mental ego attachments; complete surrender enabling miraculous '
                                    'spiritual resurrection.'},
        'reversed': {   'keywords': [   'Miraculous Recovery',
                                        'Rising from Defeat',
                                        'Resisting Inevitable End',
                                        'New Dawn'],
                        'general': 'Ten of Swords reversed cautions: Surviving the unthinkable, pulling the swords '
                                   'out, miraculous recovery, or clinging to a dead situation.',
                        'love': 'Healing after devastating heartbreak, picking up the pieces, refusing to let betrayal '
                                'destroy your capacity to love.',
                        'career': 'Rising from career defeat, launching a resilient new venture after failure, career '
                                  'phoenix rising.',
                        'finance': 'Slow but steady recovery from bankruptcy, paying off debts, rebuilding financial '
                                   'security.',
                        'spiritual': 'Resurrection; stepping out of past karmic destruction into empowered spiritual '
                                     'clarity.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Surya: 'Om "
                  "Suryaya Namah'.",
        'affirmation': 'The worst is behind me; I rise from the ashes of the past into the radiant dawn of new life.'},
    {   'id': 'page_of_swords',
        'name': 'Page of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 11,
        'element': 'Air',
        'astrology': 'Air Signs (Gemini, Libra, Aquarius)',
        'vedic_graha': 'Budha',
        'image_slug': 'page-of-swords',
        'numerology': '11 (2) (Master intellect / Youthful vigilance)',
        'timing_window': 'Spring | Days to Weeks | Air Archetype',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Gossip, contracts',
        'symbols': [   'Energetic youth standing on rugged green mound holding upright sword with both hands (gossip, '
                       'contracts, practical & logical)',
                       'Looking back over shoulder with keen, vigilant gaze (past and future awareness, watchful for '
                       'hidden dangers)',
                       'Windswept hair, billowing tunic, and ruffled trees (turbulent mental winds, swift ideas, '
                       'intellectual curiosity)',
                       'Flock of wild birds soaring in high clouds (swift communication, high-flying ideas, and '
                       'restless mental energy)',
                       'Dynamic agile stance on tiptoes (readiness for intellectual sparring, quick-witted curiosity, '
                       'and debate)'],
        'professions': [   'Investigative journalists, fact-checkers, and researchers',
                           'Paralegals, legal assistants, and contract reviewers',
                           'Cybersecurity analysts, network monitors, and penetration testers',
                           'Competitive debaters, political speechwriters, and junior analysts',
                           'Data sleuths, market intelligence researchers, and auditors'],
        'upright': {   'keywords': [   'Gossip, Contracts',
                                       'Keen Intellect',
                                       'Vigilance',
                                       'Mental Agility',
                                       'Truth-Seeking'],
                       'general': 'Page of Swords manifests: Gossip, contracts. Sharp intellect, keen observation, '
                                  'thirst for truth, signing contracts, and verifying facts with vigilance.',
                       'love': 'Logical and practical approach in relationship, clear honest communication, '
                               'intellectual attraction, watching for red flags.',
                       'career': 'Reviewing contracts meticulously, junior research breakthrough, mental vigilance, '
                                 'catching critical details.',
                       'finance': 'Carefully reading the fine print of agreements, verifying financial statements, '
                                  'cutting through misleading sales talk.',
                       'spiritual': 'Questioning dogma with intellectual honesty; seeking proof and clarity in '
                                    'spiritual inquiry.'},
        'reversed': {   'keywords': ['Malicious Gossip', 'Spying', 'Sarcastic Attacks', 'Petty Defensiveness'],
                        'general': 'Page of Swords reversed cautions: Malicious gossip, cyberstalking, spying, '
                                   'sarcastic verbal cuts, and defensive arguments.',
                        'love': "Snooping through partner's phone, paranoid suspicion, weaponizing words in petty "
                                'arguments, or emotional sarcasm.',
                        'career': 'Workplace gossip, leaking confidential information, bureaucratic contract '
                                  'squabbles, or careless errors.',
                        'finance': 'Breach of contract, overlooked fine print leading to penalties, or fraudulent '
                                   'small agreements.',
                        'spiritual': 'Intellectual arrogance; arguing over semantics to prove superiority rather than '
                                     'living truth.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Budha: 'Om "
                  "Budhaya Namah'.",
        'affirmation': 'I seek truth with clear observation, speak with integrity, and honor all contracts with '
                       'honor.'},
    {   'id': 'knight_of_swords',
        'name': 'Knight of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 12,
        'element': 'Air',
        'astrology': 'Air Signs (Gemini, Libra, Aquarius)',
        'vedic_graha': 'Mangal',
        'image_slug': 'knight-of-swords',
        'numerology': '12 (3) (Fierce crusader, 20-35 years masculine)',
        'timing_window': 'Spring | Days to Weeks | Air Archetype',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Battles',
        'symbols': [   'Knight in full plate armor charging furiously on galloping white charger (battles, will not '
                       'commit, fiercely driven)',
                       'Sword held high, pointed aggressively forward (unwavering mission, cutting through opposition, '
                       'piercing truth)',
                       'Ripping wind, racing jagged clouds, and bent trees (turbulent velocity, storm of ideas, '
                       'unstoppable momentum)',
                       'Horse harness adorned with butterflies and birds (air element, transformative thought, and '
                       'mental flight)',
                       'Visor raised, fierce determined gaze (focused on the target, oblivious to personal danger or '
                       'emotional feelings)'],
        'professions': [   'Trial litigators, court prosecutors, and cross-examiners',
                           'Emergency trauma surgeons and rapid-response interventionists',
                           'Military tactical strategists and rapid deployment commanders',
                           'Crusading investigative journalists exposing corruption',
                           'High-stakes venture turnaround specialists and corporate reformers'],
        'upright': {   'keywords': ['Battles', 'Fierce Drive', 'Decisive Action', 'Cutting Truth', 'Ambition'],
                       'general': 'Knight of Swords manifests: Battles. Fierce intellectual drive, cutting through '
                                  'delays, unstoppable crusade for truth, and charging decisively into battle.',
                       'love': 'Direct romantic pursuit, intellectual banter, but may struggle with emotional '
                               'commitment and patience.',
                       'career': 'Triumphing in high-stakes negotiations, executing rapid campaigns, crushing '
                                 'corporate competition with sharp strategy.',
                       'finance': 'Aggressive financial moves, swift legal recovery of funds, capitalizing rapidly on '
                                  'market fluctuations.',
                       'spiritual': 'The spiritual warrior; wielding the sword of discrimination (Viveka) to dismantle '
                                    'delusion fearlessly.'},
        'reversed': {   'keywords': ['Blundering Aggression', 'Verbal Cruelty', 'Reckless Rushing', 'Burning Bridges'],
                        'general': 'Knight of Swords reversed cautions: Blundering aggression, verbal cruelty, rushing '
                                   'headlong into disaster, and stubborn arrogance.',
                        'love': 'Cruel words spoken in haste, emotional bullying, charging out of arguments, or '
                                'commitment phobia.',
                        'career': 'Rushing work leading to disastrous blunders, alienating allies through arrogance, '
                                  'or picking unwinnable fights.',
                        'finance': 'Impulsive reckless trading, rushing into litigation without evidence, or costly '
                                   'financial disputes.',
                        'spiritual': 'Fanatical fundamentalism; weaponizing spiritual concepts to attack others with '
                                     'self-righteous wrath.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Mangal: 'Om "
                  "Mangalaya Namah'.",
        'affirmation': 'I direct my intellect with courage, justice, and compassion, championing truth with honor.'},
    {   'id': 'queen_of_swords',
        'name': 'Queen of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 13,
        'element': 'Air',
        'astrology': 'Air Signs (Gemini, Libra, Aquarius)',
        'vedic_graha': 'Budha',
        'image_slug': 'queen-of-swords',
        'numerology': '13 (4) (Mature feminine, independent intellect)',
        'timing_window': 'Spring | Days to Weeks | Air Archetype',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'An Intellectual woman',
        'symbols': [   'Queen seated on grey stone throne carved with butterfly and cherub (an intellectual woman, '
                       'working woman, perceptive)',
                       'Holding sword straight upright in right hand (uncompromising truth, strict boundaries, and '
                       'moral clarity)',
                       'Left hand extended outward in discerning invitation (open to dialogue, but demanding absolute '
                       'honesty)',
                       'Single bird soaring alone in clear high sky (intellectual independence, lofty perspective, and '
                       'solitary strength)',
                       'Crown of butterflies and white mantle (metamorphosis of thought, emotional purity, and wisdom '
                       'born of grief)'],
        'professions': [   'Senior editors, publishers, and literary critics',
                           'Appellate court judges, magistrates, and legal scholars',
                           'Management consultants, organizational evaluators, and auditors',
                           'Senior research scientists and biomedical investigative leads',
                           'Independent executive leaders and high-level strategists'],
        'upright': {   'keywords': [   'An Intellectual Woman',
                                       'Sharp Boundaries',
                                       'Clear Discernment',
                                       'Truthful',
                                       'Independent'],
                       'general': 'Queen of Swords manifests: An intellectual woman. Impeccable boundaries, sharp '
                                  'discernment, brilliant intellect, independent strength, and uncompromising truth.',
                       'love': 'Honest transparent communication, healthy boundaries, intellectual companionship, and '
                               'loving without codependency.',
                       'career': 'Executive authority, incisive professional critique, solving complex organizational '
                                 'dilemmas, and commanding respect.',
                       'finance': 'Astute financial management, independent wealth preservation, and cutting away '
                                  'unnecessary expenses ruthlessly.',
                       'spiritual': 'Clarity of mind; transcending emotional melodrama to abide in the tranquil '
                                    'witness consciousness (Sakshi).'},
        'reversed': {   'keywords': [   'Cold Cynicism',
                                        'Bitter Isolation',
                                        'Hypercritical',
                                        'Weaponized Words',
                                        'Cruelty'],
                        'general': 'Queen of Swords reversed cautions: Cold cynicism, bitter isolation, weaponized '
                                   'intellect, heartless criticism, and emotional walls.',
                        'love': 'Freezing out partner with emotional coldness, hypercritical nagging, cruel verbal '
                                'retaliation, or fear of intimacy.',
                        'career': 'Toxic hypercritical management, terrorizing team with impossible demands, or '
                                  'alienated corporate isolation.',
                        'finance': 'Bitter legal disputes over divorce settlements or family money, miserly hoarding '
                                   'driven by cynicism.',
                        'spiritual': 'Spiritual coldness; substituting dry intellectual analysis for genuine '
                                     'open-hearted devotion.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Budha: 'Om "
                  "Budhaya Namah'.",
        'affirmation': 'I communicate with piercing clarity and loving truth, honoring my boundaries with serene '
                       'dignity.'},
    {   'id': 'king_of_swords',
        'name': 'King of Swords',
        'arcana': 'minor',
        'suit': 'swords',
        'number': 14,
        'element': 'Air',
        'astrology': 'Air Signs (Gemini, Libra, Aquarius)',
        'vedic_graha': 'Shani',
        'image_slug': 'king-of-swords',
        'numerology': '14 (5) (Mature masculine, master of law and logic)',
        'timing_window': 'Spring | Days to Weeks | Air Archetype',
        'timing_season': 'Spring',
        'timing_speed': 'Days to Weeks',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'An Intellectual man',
        'symbols': [   'Authoritative king seated on stone throne carved with butterflies and cherubs (an intellectual '
                       'man, intellect over emotions)',
                       'Takes his responsibilities seriously, seated upright with unwavering judicial gaze',
                       'Holding sword straight in right hand tilted slightly toward head (law, justice, executive '
                       'command, and intellectual rigor)',
                       'Purple mantle over blue tunic (royal sovereignty, spiritual wisdom, and clear analytical '
                       'intellect)',
                       'Two birds flying in distant calm sky (swift logic, mental freedom, and uncorrupted '
                       'perspective)'],
        'professions': [   'Chief Legal Counsel, supreme court justices, and federal prosecutors',
                           'University chancellors, dean of faculties, and senior academics',
                           'Chief Medical Officers, surgical directors, and bioethicists',
                           'High-level strategic defense advisors and geopolitical analysts',
                           'Corporate ethics compliance directors and institutional arbiters'],
        'upright': {   'keywords': [   'An Intellectual Man',
                                       'Judicial Authority',
                                       'Objective Truth',
                                       'Ethical Clarity',
                                       'Mastery'],
                       'general': 'King of Swords manifests: An intellectual man. The apex of intellectual authority, '
                                  'objective truth, ethical clarity, impartial leadership, and rigorous strategic '
                                  'mastery.',
                       'love': 'Intellectually stimulating partnership, mature honest communication, fair problem '
                               'solving, and steadfast integrity.',
                       'career': 'High-level judicial decisions, corporate governance, strategic mastery, and setting '
                                 'the ethical standard for industry.',
                       'finance': 'Strict financial discipline, impartial auditing, making major fiscal decisions '
                                  'based on cold hard facts.',
                       'spiritual': 'The philosopher king; ruling the inner realm with uncorrupted discernment (Jnana '
                                    'Yoga).'},
        'reversed': {   'keywords': [   'Autocratic Rigidity',
                                        'Tyrannical Cynicism',
                                        'Cruel Logic',
                                        'Manipulation of Law'],
                        'general': 'King of Swords reversed cautions: Autocratic cruelty, emotional detachment, '
                                   'manipulation of law and facts, or tyrannical arrogance.',
                        'love': 'Cold, dictatorial partner; emotionally unfeeling, gaslighting with twisted logic, or '
                                'legal cruelty in divorce.',
                        'career': 'Corrupt legal maneuvering, toxic tyrannical executive, ruthless layoffs without '
                                  'empathy, or abusing authority.',
                        'finance': 'Using legal loopholes to defraud partners, financial coldness, or losing assets in '
                                   'legal battles.',
                        'spiritual': 'Intellectual arrogance blinding the soul; mistaking clever debate for living '
                                     'spiritual realization.'},
        'remedy': "Align with Air element through breathwork (Pranayama). Chant planetary seed mantra for Shani: 'Om "
                  "Sham Shanaicharaya Namah'.",
        'affirmation': 'I lead with impartial wisdom, ethical integrity, and truth, placing justice and honor above '
                       'all.'},
    {   'id': 'ace_of_pentacles',
        'name': 'Ace of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 1,
        'element': 'Earth',
        'astrology': 'Taurus, Virgo, Capricorn',
        'vedic_graha': 'Shukra',
        'image_slug': 'ace-of-pentacles',
        'numerology': '1',
        'timing_window': 'Winter | Months to Years | January 14 – February 11 (Capricorn Decan)',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Money, success and beginning',
        'symbols': [   'Hand emerging from white cloud offering large golden coin inscribed with pentagram (open - '
                       'receive whatever offer)',
                       'Lush garden of blooming white lilies and red roses (purity and rebirth, sensory wealth and '
                       'material manifestation)',
                       'Rose-covered garden archway (entrance to new realms of being, gateway to material prosperity)',
                       'Distant blue mountain peaks (spiritual journey, good luck, fortune, and enduring achievements)',
                       'Winding garden path leading to archway (choices, steady methodical steps to wealth)'],
        'professions': [   'Business founders, corporate entrepreneurs, and company builders',
                           'Property developers, real estate investors, and landholders',
                           'Health, well-being, and nutritional wellness specialists',
                           'Banking executives, venture capitalists, and wealth managers',
                           'Agricultural enterprise leads and precious commodity traders'],
        'upright': {   'keywords': [   'Money',
                                       'Success',
                                       'Beginning',
                                       'Financial Stability',
                                       'Abundance',
                                       'Manifestation'],
                       'general': 'Ace of Pentacles manifests: Money, success and beginning. A golden material '
                                  'opportunity, financial stability, tangible new career offer, and grounded '
                                  'prosperity.',
                       'love': 'Stable reliable relationship foundation, shared domestic security, material '
                               'commitments, and tangible acts of loving devotion.',
                       'career': 'Lucrative new job offer, launching a profitable commercial enterprise, promotion '
                                 'with substantial pay raise.',
                       'finance': 'Tangible financial windfall, purchasing real estate, starting a profitable '
                                  'business, and compounding security.',
                       'spiritual': 'Embodied spirituality; treating the physical body as a sacred divine temple and '
                                    'revering Mother Earth.'},
        'reversed': {   'keywords': [   'Financial Blockages',
                                        'Fear of Investing',
                                        'Lost Opportunity',
                                        'Greed',
                                        'Instability'],
                        'general': 'Ace of Pentacles reversed cautions: Financial blockages, fear of investing, '
                                   'squandered opportunities, or reckless greed.',
                        'love': 'Material insecurity causing friction in romance, superficial love based only on '
                                'money, or neglected intimacy.',
                        'career': 'Rescinded job offer, delayed funding for startup, career stagnation, or bad '
                                  'business planning.',
                        'finance': 'Bad investments, cash flow bottlenecks, unexpected property repair expenses, or '
                                   'falling for poor financial advice.',
                        'spiritual': 'Excessive obsession with worldly status and wealth; forgetting that true riches '
                                     'reside within the soul.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Shukra: 'Om Shukraya Namah'.",
        'affirmation': 'I ground my dreams in solid reality and welcome tangible prosperity, wealth, and abundance.'},
    {   'id': 'two_of_pentacles',
        'name': 'Two of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 2,
        'element': 'Earth',
        'astrology': 'Jupiter in Capricorn (January 14 – February 11)',
        'vedic_graha': 'Guru',
        'image_slug': 'two-of-pentacles',
        'numerology': '2 (Balance, choice, adaptability)',
        'timing_window': 'Winter | Months to Years | January 14 – February 11 (Capricorn)',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Decisions',
        'symbols': [   'Youth in red cap dancing and juggling two golden pentacles (decisions, ups and downs, flexible '
                       'adaptability)',
                       'Green infinity cord (Lemniscate) looping around the two coins (eternal flow of resources, '
                       'balancing dual priorities)',
                       'Two high-masted sailing ships riding rolling ocean waves in background (navigating market '
                       'tides, balancing economic storms)',
                       'Light-footed agile dancing stance (staying nimble, not taking stress too seriously, playful '
                       'balance)',
                       'Brimmed tall red hat (focus, ambition, and keeping head above turbulent financial waters)'],
        'professions': [   'Freelancers, multi-hyphenate professionals, and gig economy leaders',
                           'Cash flow managers, bookkeepers, and liquidity coordinators',
                           'Supply chain schedulers, logistics balancers, and dispatchers',
                           'Event multitaskers, production stage managers, and coordinators',
                           'Trading portfolio managers balancing equity and cash reserves'],
        'upright': {   'keywords': [   'Decisions',
                                       'Ups and Downs',
                                       'Adaptability',
                                       'Juggling Priorities',
                                       'Cash Flow Balance'],
                       'general': 'Two of Pentacles manifests: Decisions. Juggling multiple priorities with agile '
                                  "grace, managing cash flow, and staying flexible through life's ups and downs.",
                       'love': 'Balancing romantic relationship with demanding career, making financial decisions '
                               'together, and adapting to life transitions.',
                       'career': 'Managing multiple client projects simultaneously, balancing two jobs or businesses, '
                                 'nimble multitasking success.',
                       'finance': 'Skillful cash flow management, balancing budget, paying off bills while investing, '
                                  'financial agility.',
                       'spiritual': 'Finding divine equilibrium in daily earthly routines; balancing work, family, and '
                                    'spiritual contemplation.'},
        'reversed': {   'keywords': [   'Overcommitted',
                                        'Dropping the Ball',
                                        'Financial Stress',
                                        'Disorganization',
                                        'Debt'],
                        'general': 'Two of Pentacles reversed cautions: Overwhelmed by too many commitments, dropping '
                                   'financial balls, mounting debt, and chaotic disorganization.',
                        'love': 'Neglecting your partner due to work overload, stress spilling over into arguments, or '
                                'lack of quality time.',
                        'career': 'Missing critical deadlines, taking on too many tasks and failing, professional '
                                  'burnout from chaos.',
                        'finance': 'Bouncing checks, juggling credit card debts dangerously, living beyond means, or '
                                   'cash flow freeze.',
                        'spiritual': 'Losing inner peace in the worldly rush; needing to simplify life and eliminate '
                                     'non-essential commitments.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Guru: 'Om Gurave Namah'.",
        'affirmation': 'I balance my responsibilities with ease, joy, and flexible grace, trusting the natural flow of '
                       'life.'},
    {   'id': 'three_of_pentacles',
        'name': 'Three of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 3,
        'element': 'Earth',
        'astrology': 'Mars in Capricorn (January 14 – February 11)',
        'vedic_graha': 'Mangal',
        'image_slug': 'three-of-pentacles',
        'numerology': '3 (Creativity, growth, collaboration)',
        'timing_window': 'Winter | Months to Years | January 14 – February 11 (Capricorn)',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Showing your talent',
        'symbols': [   'Young stonemason standing on bench chiseling stone cathedral (showing your talent, promotion '
                       'and rewards)',
                       'Three golden pentacles carved into stone archway (material, emotional, and spiritual mastery '
                       'aligned)',
                       'Monk and architect holding architectural blueprints consulting mason (collaboration, mutual '
                       'respect, craftsmanship)',
                       'Stone cathedral sanctuary (enduring legacy, monumental craftsmanship built to last '
                       'generations)',
                       "Mason's apron and sculpting hammer (dedication to trade, specialized craftsmanship, and "
                       'professional competence)'],
        'professions': [   'Master architects, civil engineers, and structural designers',
                           'Skilled stonemasons, master carpenters, and specialized artisans',
                           'Contractors, building project directors, and blueprint managers',
                           'Software engineers, technical architects, and system builders',
                           'Collaborative craftsmen, artists, and restoration specialists'],
        'upright': {   'keywords': [   'Showing Your Talent',
                                       'Promotion & Rewards',
                                       'Craftsmanship',
                                       'Teamwork',
                                       'Legacy'],
                       'general': 'Three of Pentacles manifests: Showing your talent. Professional craftsmanship '
                                  'recognized, promotion and rewards, successful collaborative teamwork, and building '
                                  'lasting quality.',
                       'love': 'Building a solid foundation together, working as a harmonious team, mutual respect for '
                               "each other's abilities.",
                       'career': 'Promotion, recognition from senior executives, winning prestigious building '
                                 'contracts, outstanding craftsmanship praised.',
                       'finance': 'Financial growth through specialized professional skills, building valuable assets, '
                                  'and collaborative commercial gain.',
                       'spiritual': 'Building the inner spiritual temple; working with mentors and spiritual community '
                                    'with humble dedication.'},
        'reversed': {   'keywords': ['Shoddy Workmanship', 'Team Conflict', 'Lack of Recognition', 'Disorganization'],
                        'general': 'Three of Pentacles reversed cautions: Clashing workplace egos, shoddy workmanship, '
                                   'lack of teamwork, or unappreciated labor.',
                        'love': 'Failing to work as a team in domestic matters, competing instead of collaborating, or '
                                'lack of mutual appreciation.',
                        'career': 'Poor team communication, missed project specifications, low-quality work hurting '
                                  'reputation, or ego clashes.',
                        'finance': 'Overpaying for poor contracting work, budget disputes among business partners, or '
                                   'delayed milestone payments.',
                        'spiritual': 'Spiritual ego in community; refusing to collaborate humbly with fellow seekers.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Mangal: 'Om Mangalaya Namah'.",
        'affirmation': 'I hone my talents with dedicated mastery, collaborating with others to build enduring '
                       'excellence.'},
    {   'id': 'four_of_pentacles',
        'name': 'Four of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 4,
        'element': 'Earth',
        'astrology': 'Sun in Capricorn (January 14 – February 11)',
        'vedic_graha': 'Surya',
        'image_slug': 'four-of-pentacles',
        'numerology': '4 (Structure, stability, boundaries)',
        'timing_window': 'Winter | Months to Years | January 14 – February 11 (Capricorn)',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'YES Card (Conservative / Stable; Reversed: NO Card)',
        'one_liner': 'Stability',
        'symbols': [   'Man seated on stone chair clutching a coin tightly against chest (stability, heart chakra '
                       'blocked, fear of loss)',
                       'One coin balanced on crown of head (mental obsession with wealth, intellect consumed by asset '
                       'control)',
                       'Two coins firmly pinned under both feet (grounded material security, refusing to let resources '
                       'slip)',
                       'Cityscape with towers in background (worldly realm built, but disconnected from nature and '
                       'community)',
                       'Dark mantle and tightly wrapped arms (defensive posture, conservative preservation, hoarding '
                       'resources)'],
        'professions': [   'Asset preservation specialists, trust officers, and vault managers',
                           'Financial risk auditors, estate conservators, and security chiefs',
                           'Insurance underwriters evaluating maximum risk exposure',
                           'Conservative wealth preservation bankers and gold custodians',
                           'Private archivists guarding rare physical collections'],
        'upright': {   'keywords': [   'Stability',
                                       'Financial Security',
                                       'Holding Ground',
                                       'Conservative Saving',
                                       'Boundaries'],
                       'general': 'Four of Pentacles manifests: Stability. Rock-solid financial security, firm '
                                  'material boundaries, conservative saving, and protecting hard-won assets.',
                       'love': 'Steadfast reliable commitment, protecting relationship privacy, but beware of '
                               'possessiveness or emotional hoarding.',
                       'career': 'Solid job security, holding an unassailable corporate position, protecting '
                                 'intellectual property and patents.',
                       'finance': 'Strong savings cushion, conservative asset allocation, protecting wealth against '
                                  'volatility, eliminating debt.',
                       'spiritual': 'Building a stable foundation for spiritual practice; learning when to hold '
                                    'boundaries and when to open the heart.'},
        'reversed': {   'keywords': ['Greed', 'Stinginess', 'Financial Paranoia', 'Fear of Ruin', 'Releasing Control'],
                        'general': 'Four of Pentacles reversed cautions: Miserly greed, fear of financial ruin, or '
                                   'conversely, learning to open the heart and share generously.',
                        'love': 'Suffocating possessiveness, treating a partner like property, or emotional stinginess '
                                'destroying intimacy.',
                        'career': 'Hoarding information from teammates, refusing to adapt to corporate change out of '
                                  'fear, or losing a secure post.',
                        'finance': 'Compulsive hoarding of money out of deep-seated poverty fear, or conversely, '
                                   'sudden reckless loss of saved capital.',
                        'spiritual': 'Unblocking the heart chakra; letting go of material attachments to experience '
                                     'true spiritual freedom.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Surya: 'Om Suryaya Namah'.",
        'affirmation': 'I am safe and financially secure; I hold healthy boundaries while allowing abundance to flow '
                       'freely.'},
    {   'id': 'five_of_pentacles',
        'name': 'Five of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 5,
        'element': 'Earth',
        'astrology': 'Mercury in Taurus (May 15 – June 14)',
        'vedic_graha': 'Budha',
        'image_slug': 'five-of-pentacles',
        'numerology': '5 (Change, conflict, hardship)',
        'timing_window': 'Winter | Months to Years | May 15 – June 14 (Taurus)',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'NO Card (Financial loss, exclusion; Reversed: NO Card)',
        'one_liner': 'Financial loss, exclusion',
        'symbols': [   'Two destitute figures trudging through heavy snow (financial loss, exclusion, mental '
                       'disturbance, hardship)',
                       'One figure on crutches with bell around neck (physical vulnerability, illness, feeling outcast '
                       'or stigmatized)',
                       'Glowing stained-glass window of church displaying five golden pentacles (spiritual sanctuary, '
                       'warm help available overhead)',
                       'Figures failing to look up at the illuminated window (overlooking available help due to '
                       'despair and mental fog)',
                       'Freezing snowstorm and black night (harsh physical conditions, testing of faith and '
                       'endurance)'],
        'professions': [   'Charity foundation directors, shelter administrators, and aid workers',
                           'Medical debt relief counselors and bankruptcy social workers',
                           'Public health outreach clinicians serving the unhoused',
                           'Disability advocates and vocational rehabilitation specialists',
                           'Crisis welfare case managers and community food bank leads'],
        'upright': {   'keywords': [   'Financial Loss',
                                       'Exclusion',
                                       'Hardship',
                                       'Mental Disturbance',
                                       'Seeking Sanctuary'],
                       'general': 'Five of Pentacles manifests: Financial loss, exclusion. Experiencing cold financial '
                                  'hardship or feeling left out in the cold; look up, spiritual sanctuary and aid are '
                                  'right beside you.',
                       'love': 'Feeling rejected or abandoned, financial stress testing a relationship, or feeling '
                               'emotionally unloved and isolated.',
                       'career': 'Job loss, career setback, business slowdown, or feeling like an unwelcome outsider '
                                 'in your workplace.',
                       'finance': 'Financial hardship, emergency medical expenses, tight cash flow; seek available '
                                  'institutional or community help.',
                       'spiritual': 'Dark night of the physical realm; remembering that your worth is not defined by '
                                    'external money, seeking the divine refuge.'},
        'reversed': {   'keywords': [   'Recovery from Ruin',
                                        'Warmth Returning',
                                        'Finding Assistance',
                                        'Financial Rebirth'],
                        'general': 'Five of Pentacles reversed cautions: Emerging from the cold, recovering from '
                                   'financial loss, warm doors opening, and health returning.',
                        'love': 'Weathering a severe financial storm together and emerging stronger, forgiving past '
                                'neglect, romantic warmth returning.',
                        'career': 'Finding a new job after layoff, rebuilding career after business failure, receiving '
                                  'mentorship and support.',
                        'finance': 'Recovering from insolvency, paying off old debts, receiving financial aid or '
                                   'grants, steady financial recovery.',
                        'spiritual': 'Rediscovering spiritual sanctuary; realizing the divine never abandoned you in '
                                     'your hour of hardship.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Budha: 'Om Budhaya Namah'.",
        'affirmation': 'I step out of the cold into divine warmth, sanctuary, and abundant material restoration.'},
    {   'id': 'six_of_pentacles',
        'name': 'Six of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 6,
        'element': 'Earth',
        'astrology': 'Moon in Taurus (May 15 – June 14)',
        'vedic_graha': 'Chandra',
        'image_slug': 'six-of-pentacles',
        'numerology': '6 (Harmony, communication, cooperation)',
        'timing_window': 'Winter | Months to Years | May 15 – June 14 (Taurus)',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Generosity',
        'symbols': [   'Wealthy merchant in purple robe dispensing gold coins to two kneeling supplicants (generosity, '
                       'flow of charity)',
                       'Holding scales of balance in left hand (unbiased weighing, fair reciprocity, karmic wealth '
                       'distribution)',
                       'Right hand gesture (blessings from heaven, direct benevolent flow of divine prosperity to the '
                       'needy)',
                       'One supplicant receiving coins with gratitude, other awaiting turn (fair distribution, '
                       'dignity, and order)',
                       'Stately town architecture behind (prosperous community built on mutual aid, civic '
                       'philanthropy, and balance)'],
        'professions': [   'Philanthropists, grant makers, and foundation directors',
                           'Scholarship committee chairs and educational benefactors',
                           'Fair lending officers and microfinance coordinators',
                           'Nonprofit development officers and corporate donors',
                           'Ethical financial advisors managing charitable trusts'],
        'upright': {   'keywords': ['Generosity', 'Charity', 'Fair Reciprocity', 'Receiving Aid', 'Karmic Balance'],
                       'general': 'Six of Pentacles manifests: Generosity. The divine flow of giving and receiving; '
                                  'generous charity received or offered, fair reciprocity, and financial blessings.',
                       'love': 'Generous loving support, fair emotional give-and-take, mutual generosity, and '
                               "supporting each other's dreams.",
                       'career': 'Receiving valuable professional mentorship, generous bonus or grant approval, fair '
                                 'performance evaluation.',
                       'finance': 'Receiving financial aid, approved loan or scholarship, generous donations to good '
                                  'causes, and balanced income.',
                       'spiritual': 'Karmic generosity (Dana); sharing your spiritual and material blessings to create '
                                    'positive cosmic karma.'},
        'reversed': {   'keywords': [   'Strings Attached',
                                        'Power Imbalance',
                                        'Financial Dependency',
                                        'Unfair Debt Terms'],
                        'general': 'Six of Pentacles reversed cautions: Charity with strings attached, predatory debt '
                                   'terms, financial dependency, or power imbalances.',
                        'love': "One partner holding money over the other's head to control them, conditional love, or "
                                'financial manipulation.',
                        'career': 'Exploitative unpaid internships, biased bosses distributing bonuses unfairly, or '
                                  'stolen credit.',
                        'finance': 'Predatory loans with exorbitant interest, extortion, unreturned loans causing '
                                   'resentment, or fiscal stinginess.',
                        'spiritual': 'Spiritual bribery; performing charity for social prestige and ego praise rather '
                                     'than selfless love.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Chandra: 'Om Som Somaya Namah'.",
        'affirmation': 'I give and receive with an open, generous heart, participating in the divine flow of universal '
                       'abundance.'},
    {   'id': 'seven_of_pentacles',
        'name': 'Seven of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 7,
        'element': 'Earth',
        'astrology': 'Saturn in Taurus (May 15 – June 14)',
        'vedic_graha': 'Shani',
        'image_slug': 'seven-of-pentacles',
        'numerology': '7 (Assessment, reflection, patience)',
        'timing_window': 'Winter | Months to Years | May 15 – June 14 (Taurus)',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'YES Card (Potential for success; Patience needed; Reversed: NO Card)',
        'one_liner': 'Potential for success',
        'symbols': [   'Farmer leaning on hoe gazing patiently at flourishing vine (potential for success, think '
                       'before taking decisions)',
                       'Seven golden pentacles hanging like ripe fruit on dense green bush (tangible results of past '
                       'long-term toil)',
                       'One coin resting on soil near foot (immediate reward or seed money for the next planting '
                       'cycle)',
                       'Distant blue hills (long-term vision, patience across seasonal cycles, enduring agricultural '
                       'payoff)',
                       'Contemplative, patient posture (assessing yield, evaluating whether to harvest or let grow '
                       'further)'],
        'professions': [   'Long-term agricultural investors and vineyard owners',
                           'Sustainable farming managers and organic agronomists',
                           'Venture equity investors evaluating multi-year milestones',
                           'Pension fund managers and compounding asset strategists',
                           'Patient craftspeople nurturing slow-maturing enterprises'],
        'upright': {   'keywords': [   'Potential for Success',
                                       'Patience',
                                       'Long-Term Investment',
                                       'Assessing Harvest',
                                       'Perseverance'],
                       'general': 'Seven of Pentacles manifests: Potential for success. Long-term investments are '
                                  'maturing; pause to assess your crop, maintain patience, and prepare for harvest.',
                       'love': 'Patient devotion, seeing a relationship grow and mature over time, investing in '
                               'long-term domestic security.',
                       'career': 'Evaluating long-term career growth, diligent groundwork paying off, assessing ROI on '
                                 'major business milestones.',
                       'finance': 'Compounding long-term investments, steady growth of retirement funds, patience '
                                  'yielding substantial wealth.',
                       'spiritual': 'Spiritual patience (Titiksha); trusting that years of quiet meditation are '
                                    'bearing profound inner fruit.'},
        'reversed': {   'keywords': ['Impatience', 'Abandoning Crop', 'Poor ROI', 'Wasted Effort', 'Frustration'],
                        'general': 'Seven of Pentacles reversed cautions: Impatience causing premature harvest, '
                                   'abandoning projects right before fruition, or poor return on effort.',
                        'love': 'Impatience in relationship, frustration over slow progress, questioning whether '
                                'partnership is worth the effort.',
                        'career': 'Quitting right before success arrives, working hard on projects with zero future '
                                  'prospects, career frustration.',
                        'finance': 'Selling investments prematurely at a loss, poor returns on capital, or feeling '
                                   'underpaid for years of toil.',
                        'spiritual': 'Spiritual frustration; demanding instant enlightenment and abandoning practice '
                                     'out of impatience.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Shani: 'Om Sham Shanaicharaya Namah'.",
        'affirmation': 'I nurture my endeavors with patient dedication, trusting the bountiful harvest in divine '
                       'timing.'},
    {   'id': 'eight_of_pentacles',
        'name': 'Eight of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 8,
        'element': 'Earth',
        'astrology': 'Sun in Virgo (September 16 – October 15)',
        'vedic_graha': 'Surya',
        'image_slug': 'eight-of-pentacles',
        'numerology': '8 (Action, power, dedicated skill)',
        'timing_window': 'Winter | Months to Years | September 16 – October 15 (Virgo)',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Money coming',
        'symbols': [   'Craftsman intently chiseling a pentagram onto a golden coin (money coming, enjoying his work, '
                       'dedication)',
                       'Six finished golden coins mounted neatly on tree trunk (track record of proven competence and '
                       'compounding output)',
                       'One coin resting on ground near feet and one in progress on lap (focus on the task at hand, '
                       'step-by-step mastery)',
                       'Distant township on horizon (withdrawing from worldly distractions to achieve master craftsman '
                       'status)',
                       'Blue tunic and red tights (spiritual dedication fueling active, precise physical labor)'],
        'professions': [   'Specialized software developers, coders, and system engineers',
                           'Master watchmakers, jewelers, and precision instrument artisans',
                           'Apprentices undergoing advanced master certification',
                           'Quality assurance craftsmen, editors, and technical specialists',
                           'Medical researchers conducting meticulous lab experiments'],
        'upright': {   'keywords': [   'Money Coming',
                                       'Craftsmanship',
                                       'Enjoying Work',
                                       'Dedication',
                                       'Mastery Compounding'],
                       'general': 'Eight of Pentacles manifests: Money coming. Diligent craftsmanship, enjoying your '
                                  'daily work, developing specialized skills, and steady compounding income.',
                       'love': 'Putting in the daily loving effort to build a strong bond, dedicated loyalty, working '
                               'together on shared goals.',
                       'career': 'Mastering your trade, professional certification, recognized expertise, and taking '
                                 'pride in meticulous work.',
                       'finance': 'Steady compounding income, earning money through specialized skill, paying down '
                                  'debts diligently.',
                       'spiritual': 'Daily spiritual practice (Sadhana); consistent daily meditation perfecting the '
                                    "soul's inner alignment."},
        'reversed': {   'keywords': ['Drudgery', 'Cutting Corners', 'Lack of Passion', 'Perfectionism Paralyzing'],
                        'general': 'Eight of Pentacles reversed cautions: Shoddy workmanship, cutting corners, lack of '
                                   'passion in daily toil, or perfectionism causing paralysis.',
                        'love': 'Neglecting emotional intimacy due to workaholic tendencies, going through the motions '
                                'without passion.',
                        'career': 'Stuck in boring repetitive tasks, lack of career advancement, shoddy work damaging '
                                  'reputation, or burnout.',
                        'finance': 'Underpaid toil, dead-end gig work, or financial stress caused by poor '
                                   'craftsmanship.',
                        'spiritual': 'Mechanical spiritual practice; reciting mantras mindlessly without devotion or '
                                     'presence.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Surya: 'Om Suryaya Namah'.",
        'affirmation': 'I dedicate myself to excellence; my craft brings joy, mastery, and abundant prosperity.'},
    {   'id': 'nine_of_pentacles',
        'name': 'Nine of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 9,
        'element': 'Earth',
        'astrology': 'Venus in Virgo (September 16 – October 15)',
        'vedic_graha': 'Shukra',
        'image_slug': 'nine-of-pentacles',
        'numerology': '9 (Fruition, fulfillment, refined luxury)',
        'timing_window': 'Winter | Months to Years | September 16 – October 15 (Virgo)',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Material comforts',
        'symbols': [   'Elegant woman in golden silk gown standing in lush vineyard (material comforts, profit and '
                       'wealth, self-reliance)',
                       'Nine golden coins hanging among heavy purple grapevines (apex material abundance, sensory '
                       'luxury, and harvest)',
                       'Hooded falcon perched on gloved left hand (tamed intellect, self-discipline, and sovereignty '
                       'over instincts)',
                       'Small snail crawling slowly at bottom of robe (unhurried, steady accumulation of wealth and '
                       'peace)',
                       'Stately manor house in background (ownership, security, refinement, and private sanctuary)'],
        'professions': [   'Independent wealth creators, private estate owners, and investors',
                           'Luxury real estate directors, boutique vineyard proprietors',
                           'Aesthetic curators, fine art collectors, and luxury lifestyle creators',
                           'Self-made female founders and sovereign executives',
                           'Horticultural estate designers and sustainable luxury resort owners'],
        'upright': {   'keywords': [   'Material Comforts',
                                       'Profit and Wealth',
                                       'Financial Independence',
                                       'Refined Luxury',
                                       'Self-Reliance'],
                       'general': 'Nine of Pentacles manifests: Material comforts. Self-made financial independence, '
                                  'refined elegance, profit and wealth, and enjoying the fruits of your labor in '
                                  'peace.',
                       'love': 'High self-worth, loving from a place of wholeness and independence, attracting a '
                               'partner who respects your sovereignty.',
                       'career': 'Apex solo achievement, thriving independent enterprise, financial autonomy, and '
                                 'commanding luxury status.',
                       'finance': 'Substantial private wealth, lucrative real estate, comfortable luxurious living, '
                                  'and financial security.',
                       'spiritual': 'Inner sovereignty; treating the earth as a divine paradise and living in serene '
                                    'harmony with nature.'},
        'reversed': {   'keywords': [   'Overspending for Image',
                                        'Loneliness in Luxury',
                                        'Financial Dependency',
                                        'Shallow Values'],
                        'general': 'Nine of Pentacles reversed cautions: Spending beyond means to maintain '
                                   'appearances, superficial materialism, or loneliness within wealth.',
                        'love': "Valuing partner's bank account over their soul, relationship superficiality, or "
                                'isolating yourself out of pride.',
                        'career': 'Overworking at the expense of personal relationships, financial insecurity masked '
                                  'by luxury facades.',
                        'finance': 'Mounting debts from luxury lifestyle, poor property investments, or financial '
                                   'dependency on others.',
                        'spiritual': 'Material attachment; realizing that golden cages and luxury estates cannot '
                                     'replace genuine inner peace.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Shukra: 'Om Shukraya Namah'.",
        'affirmation': 'I am self-sufficient, prosperous, and grateful; I enjoy the abundant fruits of my labor with '
                       'grace.'},
    {   'id': 'ten_of_pentacles',
        'name': 'Ten of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 10,
        'element': 'Earth',
        'astrology': 'Mercury in Virgo (September 16 – October 15)',
        'vedic_graha': 'Budha',
        'image_slug': 'ten-of-pentacles',
        'numerology': '10 (1) (Completion, dynasty, generational legacy)',
        'timing_window': 'Winter | Months to Years | September 16 – October 15 (Virgo)',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'Inheritance, good business and marriage',
        'symbols': [   'Elderly patriarch in tapestry robe seated under archway of stone estate (inheritance, good '
                       'business, marriage)',
                       'Young couple with child and two playful friendly dogs (intergenerational harmony, marring into '
                       'wealthy family)',
                       'Ten golden coins arranged in Kabbalistic Tree of Life pattern (complete material manifestation '
                       'across generations)',
                       'Carved stone archway displaying family crest (dynasty, ancestral heritage, and permanent '
                       'security)',
                       'City gate and castle turrets (stable civilization, community wealth, and enduring legacy)'],
        'professions': [   'Family office directors, wealth estate planners, and legacy advisors',
                           'Ancestral estate managers, dynasty founders, and trust trustees',
                           'Heritage foundation officers and generational business heads',
                           'Real estate moguls managing multi-generational property portfolios',
                           'Corporate dynasty executives and philanthropic family trust leads'],
        'upright': {   'keywords': [   'Inheritance',
                                       'Good Business',
                                       'Prosperous Marriage',
                                       'Generational Wealth',
                                       'Legacy'],
                       'general': 'Ten of Pentacles manifests: Inheritance, good business and marriage. Apex '
                                  'generational wealth, family legacy, long-term security, prosperous marriage, and '
                                  'enduring dynasty.',
                       'love': 'Marrying into a wealthy supportive family, long-term marital security, building a '
                               'family dynasty, and deep domestic peace.',
                       'career': 'Inheriting a thriving family business, reaching the top of an established '
                                 'enterprise, lasting professional legacy.',
                       'finance': 'Substantial family inheritance, lucrative commercial contracts, generational '
                                  'property wealth, and permanent security.',
                       'spiritual': 'Honoring ancestral blessings; seeing the divine thread connecting generations and '
                                    'leaving a sacred legacy.'},
        'reversed': {   'keywords': [   'Inheritance Feuds',
                                        'Family Business Collapse',
                                        'Loss of Estate',
                                        'Broken Lineage'],
                        'general': 'Ten of Pentacles reversed cautions: Bitter family disputes over inheritance, '
                                   'collapse of family business, loss of estate, or financial estrangement.',
                        'love': 'Family disapproving of marriage, disputes over prenuptial agreements, or marital '
                                'stress caused by in-law meddling.',
                        'career': 'Mismanagement ruining a multi-generational business, nepotism causing workplace '
                                  'rebellion, or lost contracts.',
                        'finance': 'Loss of inheritance through probate disputes, bad property investments, or tax '
                                   'burdens threatening family wealth.',
                        'spiritual': 'Healing ancestral karmic burdens; breaking generational trauma cycles to forge '
                                     'healthy spiritual values.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Budha: 'Om Budhaya Namah'.",
        'affirmation': 'I build a lasting legacy of prosperity, honor, and harmony that blesses generations to come.'},
    {   'id': 'page_of_pentacles',
        'name': 'Page of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 11,
        'element': 'Earth',
        'astrology': 'Earth Signs (Taurus, Virgo, Capricorn)',
        'vedic_graha': 'Budha',
        'image_slug': 'page-of-pentacles',
        'numerology': '11 (2) (Master foundation / Grounded scholar)',
        'timing_window': 'Winter | Months to Years | Earth Archetype',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'An offer',
        'symbols': [   'Youth standing in fertile green field reverently holding up a single golden coin (an offer, '
                       'grounded person, student)',
                       'Gazing intently at coin with ambition, focus, and study (eagerness to learn, practical trade, '
                       'dedicated student)',
                       'Plowed fertile fields and blooming groves behind (ground prepared for long-term harvest, '
                       'organic potential)',
                       'Red turban scarf draped over green tunic (mental focus grounded in earthy practical '
                       'manifestation)',
                       'Distant mountain peaks (lofty goals approached with practical, methodical step-by-step '
                       'diligence)'],
        'professions': [   'Business administration students and trade apprentices',
                           'Junior financial analysts, accounting trainees, and clerks',
                           'Real estate licensing students and appraisal apprentices',
                           'Agronomy students, botany researchers, and environmental interns',
                           'Grounded researchers beginning long-term practical studies'],
        'upright': {   'keywords': [   'An Offer',
                                       'Grounded Student',
                                       'New Career Path',
                                       'Practical Study',
                                       'Financial Foundation'],
                       'general': 'Page of Pentacles manifests: An offer. A practical new career or study offer, '
                                  'grounded ambitions, solid foundation, and eager desire to master tangible skills.',
                       'love': 'Loyal, grounded, reliable partner; slow but steady romantic courtship built on shared '
                               'practical values.',
                       'career': 'Exciting junior job offer, enrolling in lucrative professional certification, laying '
                                 'reliable groundwork for career.',
                       'finance': 'Receiving a solid financial offer, seed money for practical venture, starting a '
                                  'systematic savings habit.',
                       'spiritual': 'Grounding spiritual study in daily life; studying sacred texts with humility, '
                                    'dedication, and practical discipline.'},
        'reversed': {   'keywords': [   'Procrastination',
                                        'Missed Offers',
                                        'Financial Carelessness',
                                        'Unrealistic Schemes'],
                        'general': 'Page of Pentacles reversed cautions: Procrastination on studies, missing practical '
                                   'career offers, financial carelessness, or lack of discipline.',
                        'love': 'Boredom in courtship, lack of ambition frustrating partner, or failure to follow '
                                'through on practical commitments.',
                        'career': 'Slacking off in training, failing professional exams due to lack of focus, or '
                                  'jumping between uncommitted jobs.',
                        'finance': 'Wasting money on frivolous gadgets, unrealistic business schemes, or neglecting '
                                   'financial accounts.',
                        'spiritual': 'Reading spiritual books without practicing; intellectual knowledge lacking '
                                     'practical grounded virtue.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Budha: 'Om Budhaya Namah'.",
        'affirmation': 'I cultivate my skills with focus and dedication, welcoming practical opportunities with '
                       'enthusiasm.'},
    {   'id': 'knight_of_pentacles',
        'name': 'Knight of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 12,
        'element': 'Earth',
        'astrology': 'Earth Signs (Taurus, Virgo, Capricorn)',
        'vedic_graha': 'Shani',
        'image_slug': 'knight-of-pentacles',
        'numerology': '12 (3) (Steadfast builder, 20-35 years masculine)',
        'timing_window': 'Winter | Months to Years | Earth Archetype',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'A dependable man',
        'symbols': [   'Armored knight seated atop stationary, heavy black draft horse (a dependable man, ability to '
                       'overcome obstacles, ground energy)',
                       'Holding golden pentacle in right hand with calm, unwavering focus (patient accumulation, '
                       'tangible results)',
                       'Stationary horse planted firmly on fertile plowed land (slow, methodical, thorough progress; '
                       'no rushing)',
                       'Green oak sprigs in helmet and horse bridle (endurance, strength, wisdom of nature, and steady '
                       'growth)',
                       'Plowed golden fields stretching to horizon (immense diligent labor completed with unwavering '
                       'excellence)'],
        'professions': [   'Project directors, civil site managers, and construction leads',
                           'Agricultural engineers, farm managers, and land developers',
                           'Conservative portfolio managers, index investors, and risk officers',
                           'Quality assurance directors, supply chain managers, and logistics chiefs',
                           'Dependable executive deputies who execute complex operations flawlessly'],
        'upright': {   'keywords': [   'A Dependable Man',
                                       'Methodical Progress',
                                       'Reliability',
                                       'Patient Execution',
                                       'Hard Work'],
                       'general': 'Knight of Pentacles manifests: A dependable man. Methodical progress, unshakeable '
                                  'reliability, patient execution, hard work, and steady accumulation of wealth.',
                       'love': 'Steadfast, loyal, devoted partner; building a secure future together step-by-step, '
                               'reliable acts of service.',
                       'career': 'Flawless project execution, dependable performance commanding executive trust, '
                                 'steady climb up corporate ladder.',
                       'finance': 'Compounding financial wealth through patience, steady savings, conservative '
                                  'investments, and eliminating financial risk.',
                       'spiritual': 'Karma Yoga; selfless dedicated work offered as a sacred sacrifice, grounded in '
                                    'integrity and perseverance.'},
        'reversed': {   'keywords': ['Stubborn Obstinacy', 'Stagnation', 'Workaholic Rigidity', 'Resistance to Change'],
                        'general': 'Knight of Pentacles reversed cautions: Boring stagnation, stubborn refusal to '
                                   'innovate, workaholic exhaustion, or laziness.',
                        'love': 'Relationship falling into predictable boring routine, emotional stubbornness, or '
                                'neglecting romance for endless overtime.',
                        'career': 'Micromanagement, resisting technological innovation, bureaucratic slowness stalling '
                                  'progress, or burnout.',
                        'finance': 'Ultra-conservative paralysis preventing necessary investments, or losing money '
                                   'through stubborn pride.',
                        'spiritual': 'Rigid dogmatism; mistaking mechanical ritual adherence for genuine spiritual '
                                     'growth.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Shani: 'Om Sham Shanaicharaya Namah'.",
        'affirmation': 'I execute my duties with unwavering dedication, patience, and honor, building lasting '
                       'prosperity.'},
    {   'id': 'queen_of_pentacles',
        'name': 'Queen of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 13,
        'element': 'Earth',
        'astrology': 'Earth Signs (Taurus, Virgo, Capricorn)',
        'vedic_graha': 'Shukra',
        'image_slug': 'queen-of-pentacles',
        'numerology': '13 (4) (Mature feminine, nurturing abundance)',
        'timing_window': 'Winter | Months to Years | Earth Archetype',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'A Generous woman',
        'symbols': [   'Queen seated on carved stone throne adorned with cherubs, goats, and fruit (a generous woman, '
                       'nurturing abundance)',
                       'Cradling large golden pentacle lovingly in lap (wealth nurtured with maternal care and '
                       'grounded wisdom)',
                       'Brown hare leaping across right foreground (fertility, rapid growth, instincts, and earthy '
                       'vitality)',
                       'Lush arbor of red roses and blooming vines framing throne (flourishing sensory luxury, '
                       'domestic paradise)',
                       'Golden sky and fertile green valley (peace, hospitality, security, and harmony with Mother '
                       'Earth)'],
        'professions': [   'Female Chief Financial Officers (CFOs), corporate treasurers, and bankers',
                           'Interior designers, landscape architects, and home stylists',
                           'Sustainable organic farm owners, chefs, and restaurateurs',
                           'Nurturing healthcare administrators and maternal wellness leaders',
                           'Generous philanthropic patronesses and community foundation chairs'],
        'upright': {   'keywords': [   'A Generous Woman',
                                       'Nurturing Abundance',
                                       'Practical Hospitality',
                                       'Financial Security',
                                       'Warmth'],
                       'general': 'Queen of Pentacles manifests: A generous woman. Nurturing abundance, practical '
                                  'hospitality, financial security, down-to-earth generosity, and domestic prosperity.',
                       'love': 'Warm, loving, devoted domestic partner; creating a cozy prosperous home, taking care '
                               'of loved ones with generous meals.',
                       'career': 'Prudent executive financial leadership, mentoring employees with warmth, running a '
                                 'flourishing profitable business.',
                       'finance': 'Robust financial abundance, wise investments, luxurious comfortable home, and '
                                  'sharing wealth generously.',
                       'spiritual': 'Honoring the sacred Earth Goddess; spiritual practice rooted in grounding, '
                                    'nourishing the body, and generosity.'},
        'reversed': {   'keywords': [   'Smothering Control',
                                        'Materialism Over Love',
                                        'Financial Paranoia',
                                        'Neglecting Self-Care'],
                        'general': 'Queen of Pentacles reversed cautions: Smothering maternal control, materialism '
                                   'over love, financial paranoia, or neglecting home life.',
                        'love': 'Using financial gifts to control partner, smothering love, neglecting personal '
                                'self-care while over-giving to family.',
                        'career': 'Workplace micromanagement, financial hoarding, neglect of health due to endless '
                                  'corporate stress.',
                        'finance': 'Obsessive anxiety about money despite substantial wealth, or wasteful status '
                                   'spending creating domestic friction.',
                        'spiritual': "Losing connection to nature; physical exhaustion caused by ignoring the body's "
                                     'natural need for rest.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Shukra: 'Om Shukraya Namah'.",
        'affirmation': 'I nurture my home, family, and ventures with generous love, grounded wisdom, and abundant '
                       'prosperity.'},
    {   'id': 'king_of_pentacles',
        'name': 'King of Pentacles',
        'arcana': 'minor',
        'suit': 'pentacles',
        'number': 14,
        'element': 'Earth',
        'astrology': 'Earth Signs (Taurus, Virgo, Capricorn)',
        'vedic_graha': 'Guru',
        'image_slug': 'king-of-pentacles',
        'numerology': '14 (5) (Mature masculine, business magnate)',
        'timing_window': 'Winter | Months to Years | Earth Archetype',
        'timing_season': 'Winter',
        'timing_speed': 'Months to Years',
        'yes_no': 'YES Card (Reversed: NO Card)',
        'one_liner': 'A Prosperous man',
        'symbols': [   'Regal king seated on bull-carved throne in fertile garden (a prosperous man, apex business '
                       'empire)',
                       'Thick robe embroidered with heavy bunches of ripe grapes (luxurious harvest, commercial '
                       'wealth, sensory fruition)',
                       'Golden scepter in right hand and golden pentacle resting on lap (wealth, sovereign command '
                       'over worldly empire)',
                       'Castle turrets rising above verdant garden wall (security, enduring enterprise, commercial '
                       'citadel)',
                       'Armored foot resting on stone carved with flowers (battle-tested business acumen combined with '
                       'grounded peace)'],
        'professions': [   'Industrialists, commercial enterprise titans, and corporate magnates',
                           'Real estate moguls, commercial property developers, and builders',
                           'Chief Investment Officers (CIOs), banking chairs, and hedge fund leads',
                           'Generous philanthropic benefactors funding civic universities and hospitals',
                           'Master agricultural enterprise founders and global commodity barons'],
        'upright': {   'keywords': [   'A Prosperous Man',
                                       'Business Empire',
                                       'Apex Wealth',
                                       'Worldly Stability',
                                       'Generosity'],
                       'general': 'King of Pentacles manifests: A prosperous man. The apex of material success, '
                                  'commercial enterprise, worldly stability, wise financial stewardship, and generous '
                                  'philanthropy.',
                       'love': 'Steadfast, protective, generous partner; providing complete material security and '
                               'luxurious domestic peace.',
                       'career': 'Apex commercial leadership, managing thriving enterprise empires, commanding '
                                 'profound respect in business and finance.',
                       'finance': 'Immense wealth creation, highly profitable diversified portfolio, generational '
                                  'legacy, and philanthropy.',
                       'spiritual': 'The wise steward; recognizing that worldly wealth is a sacred divine trust to be '
                                    'used for the upliftment of humanity.'},
        'reversed': {   'keywords': [   'Ruthless Greed',
                                        'Corrupt Practices',
                                        'Materialistic Pride',
                                        'Bankruptcy',
                                        'Tyranny'],
                        'general': 'King of Pentacles reversed cautions: Ruthless greed, corrupt business practices, '
                                   'measuring human worth solely by money, or financial downfall.',
                        'love': 'Cold, controlling partner who treats loved ones like possessions, emotional '
                                'stinginess beneath wealthy exterior.',
                        'career': 'Corrupt corporate governance, unethical business cuts, ruthless exploitation of '
                                  'workers, or impending bankruptcy.',
                        'finance': 'Disastrous speculative losses, tax evasion fraud, or losing empire through '
                                   'stubbornness and greed.',
                        'spiritual': 'Complete material blindness; worshipping gold while starving the soul of love '
                                     'and truth.'},
        'remedy': 'Align with Earth element through grounding mindfulness in nature. Chant planetary seed mantra for '
                  "Guru: 'Om Gurave Namah'.",
        'affirmation': 'I am a wise steward of abundance; I build enduring prosperity that enriches and blesses the '
                       'world.'}]

# Canonical 78-card list and lookup dictionary
ALL_TAROT_CARDS: list[dict[str, Any]] = MAJOR_ARCANA + MINOR_ARCANA
TAROT_DECK_BY_ID: dict[str, dict[str, Any]] = {card['id']: card for card in ALL_TAROT_CARDS}
