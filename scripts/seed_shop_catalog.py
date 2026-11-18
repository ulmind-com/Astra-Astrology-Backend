"""Seed high-fidelity consecrated shop products matching Astrotalk Store.

    .venv/bin/python -m scripts.seed_shop_catalog

Seeds categories (Zodiac, Bracelets & Rings, Rudraksha, Karungali, Vastu & Home)
and 20+ verified products with authentic images, INR pricing, and Vedic benefits.
"""

import asyncio
from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.models.enums import ProductCategoryType
from app.models.shop import Product, ProductCategory


async def main() -> int:
    print("Connecting to MongoDB...")
    await connect_to_mongo()

    try:
        categories_def = [
            {
                "name": "Zodiac Collection",
                "slug": "zodiac",
                "type": ProductCategoryType.GEMSTONE,
                "description": "Handcrafted 925 sterling silver zodiac rings and gemstone talisman jewelry.",
                "display_order": 1,
            },
            {
                "name": "Bracelets & Rings",
                "slug": "bracelets",
                "type": ProductCategoryType.CRYSTAL_BRACELET,
                "description": "Dhan Yog abundance bands, pyrite stud rings, and numerology crystal bracelets.",
                "display_order": 2,
            },
            {
                "name": "Nepali Rudraksha",
                "slug": "rudraksha",
                "type": ProductCategoryType.RUDRAKSHA,
                "description": "100% lab-certified 1 to 14 Mukhi divine Himalayan beads consecrated at Varanasi.",
                "display_order": 3,
            },
            {
                "name": "Original Karungali",
                "slug": "karungali",
                "type": ProductCategoryType.MALA_ROSARY,
                "description": "Pure black ebony wood malas and bracelets for negative energy and evil eye defense.",
                "display_order": 4,
            },
            {
                "name": "Vastu & Home",
                "slug": "vastu-home",
                "type": ProductCategoryType.VASTU_FENGSHUI,
                "description": "Consecrated Sri Yantras, raw selenite charging plates, and positive aura remedies.",
                "display_order": 5,
            },
        ]

        cat_map = {}
        for cdef in categories_def:
            existing = await ProductCategory.find_one(ProductCategory.slug == cdef["slug"])
            if not existing:
                cat = ProductCategory(
                    name=cdef["name"],
                    slug=cdef["slug"],
                    category_type=cdef["type"],
                    description=cdef["description"],
                    display_order=cdef["display_order"],
                    is_active=True,
                )
                await cat.insert()
                cat_map[cdef["slug"]] = cat
                print(f"Created category: {cdef['name']}")
            else:
                existing.name = cdef["name"]
                existing.description = cdef["description"]
                existing.is_active = True
                await existing.save()
                cat_map[cdef["slug"]] = existing
                print(f"Updated category: {cdef['name']}")

        products_data = [
            # 1. Bestseller Zodiac
            {
                "title": "Leo Zodiac Metal Bracelet with FREE Selenite Plate",
                "slug": "leo-zodiac-metal-bracelet",
                "sku": "ASTRA-LEO-01",
                "category_slug": "zodiac",
                "short_description": "Sacred eight-metal Leo talisman with authentic Tiger Eye and Citrine beads.",
                "detailed_description": "Handcrafted for Leo (Simha Rashi) to amplify confidence, leadership charisma, and solar aura. Consecrated with Aditya Hridaya Stotra. Includes FREE Raw Selenite Plate worth ₹729.",
                "ruling_planet": "Sun",
                "deity": "Surya Dev",
                "mrp": 1700.0,
                "sale_price": 999.0,
                "stock_quantity": 40,
                "featured_image": "https://images.unsplash.com/photo-1611591475879-166258f33cf2?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["zodiac", "confidence", "career"],
                "free_gift_badge": "FREE Selenite Plate worth ₹729",
                "free_gift_title": "Raw Selenite Charging Plate",
                "free_gift_value": 729.0,
                "cashback_percent": 100,
                "is_featured": True,
            },
            {
                "title": "Aries Mars Red Coral & Carnelian Energy Ring",
                "slug": "aries-mars-red-coral-ring",
                "sku": "ASTRA-ARI-02",
                "category_slug": "zodiac",
                "short_description": "925 silver adjustable astrological ring set with natural energizing Carnelian.",
                "detailed_description": "Ignites inner courage, eliminates hesitation, and enhances vitality. Consecrated during Mars Mangala hora. Comes with certificate of authenticity.",
                "ruling_planet": "Mars",
                "deity": "Lord Kartikeya / Hanuman",
                "mrp": 1499.0,
                "sale_price": 899.0,
                "stock_quantity": 30,
                "featured_image": "https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["zodiac", "courage", "health"],
                "cashback_percent": 100,
                "is_featured": True,
            },
            {
                "title": "Taurus Venus Rose Quartz & White Zircon Pendant",
                "slug": "taurus-venus-rose-quartz-pendant",
                "sku": "ASTRA-TAU-03",
                "category_slug": "zodiac",
                "short_description": "Attracts romantic harmony, creative charm, and material luxuries.",
                "detailed_description": "Specially designed for Vrishabha and Tula rashis. Natural unheated Rose Quartz charged with Shukra Beej Mantras.",
                "ruling_planet": "Venus",
                "deity": "Goddess Lakshmi",
                "mrp": 1699.0,
                "sale_price": 949.0,
                "stock_quantity": 25,
                "featured_image": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["zodiac", "love", "wealth"],
                "cashback_percent": 100,
            },
            {
                "title": "Scorpio Mars & Ketu Black Tourmaline Protection Band",
                "slug": "scorpio-black-tourmaline-band",
                "sku": "ASTRA-SCO-04",
                "category_slug": "zodiac",
                "short_description": "Total grounding and shielding against evil eye and negative envy.",
                "detailed_description": "Raw volcanic lava and polished black tourmaline for Vrishchik rashi natives.",
                "ruling_planet": "Mars",
                "deity": "Lord Shiva",
                "mrp": 1599.0,
                "sale_price": 899.0,
                "stock_quantity": 35,
                "featured_image": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["zodiac", "protection"],
                "cashback_percent": 100,
            },

            # 2. Bracelets & Rings (Astrotalk Bestsellers)
            {
                "title": "Pyrite Stud Ring",
                "slug": "pyrite-stud-ring",
                "sku": "ASTRA-PYR-01",
                "category_slug": "bracelets",
                "short_description": "Handcrafted 925 sterling silver ring set with genuine sparkling Peruvian Pyrite.",
                "detailed_description": "Known as the ultimate Money Magnet stone. Pyrite attracts golden wealth vibrations, aids wise business investments, and shields from financial leakage. Consecrated with Kuber and Kanakadhara rituals.",
                "ruling_planet": "Jupiter",
                "deity": "Maha Lakshmi & Kuber",
                "mrp": 1400.0,
                "sale_price": 799.0,
                "stock_quantity": 50,
                "featured_image": "https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["wealth", "career"],
                "cashback_percent": 100,
                "is_featured": True,
            },
            {
                "title": "Mulank 4 Rahu Crystal Bracelet with Free Selenite Plate",
                "slug": "mulank-4-rahu-crystal-bracelet",
                "sku": "ASTRA-MUL-04",
                "category_slug": "bracelets",
                "short_description": "Formulated for birth dates 4, 13, 22, 31 with Labradorite and Black Tourmaline.",
                "detailed_description": "Mitigates sudden obstacles caused by malefic Rahu while amplifying sharp intuitive foresight, breakthrough tech career success, and mental balance. Includes FREE Selenite Charging Plate worth ₹729.",
                "ruling_planet": "Rahu",
                "deity": "Lord Bhairava & Saraswati",
                "mrp": 2700.0,
                "sale_price": 999.0,
                "stock_quantity": 45,
                "featured_image": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["wealth", "protection", "career"],
                "free_gift_badge": "FREE Selenite Plate worth ₹729",
                "free_gift_title": "Raw Selenite Charging Plate",
                "free_gift_value": 729.0,
                "cashback_percent": 100,
                "is_featured": True,
            },
            {
                "title": "Super Dhan Yog Band",
                "slug": "super-dhan-yog-band",
                "sku": "ASTRA-DHY-01",
                "category_slug": "bracelets",
                "short_description": "Our #1 most powerful abundance remedy combining Pyrite, Citrine, and Green Aventurine.",
                "detailed_description": "Engineered according to ancient Vedic gemstone synergy. Clears blocked cashflows, revitalizes stagnant businesses, and invites unexpected prosperity into your household. Lab certified beads with 100% moneyback authenticity.",
                "ruling_planet": "Mercury & Jupiter",
                "deity": "Goddess Mahalakshmi",
                "mrp": 1700.0,
                "sale_price": 1099.0,
                "stock_quantity": 60,
                "featured_image": "https://images.unsplash.com/photo-1611591475879-166258f33cf2?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["wealth", "career", "luck"],
                "cashback_percent": 100,
                "is_featured": True,
            },
            {
                "title": "7-Chakra Healing Lava Bead Bracelet",
                "slug": "7-chakra-healing-lava-bracelet",
                "sku": "ASTRA-CHK-07",
                "category_slug": "bracelets",
                "short_description": "Restores full energetic equilibrium across all seven physical and spiritual chakras.",
                "detailed_description": "Features Amethyst, Lapis Lazuli, Turquoise, Imperial Stone, Tiger Eye, Amber, and Red Agate on porous grounding lava beads.",
                "ruling_planet": "All 9 Grahas",
                "deity": "Cosmic Shiva",
                "mrp": 1299.0,
                "sale_price": 699.0,
                "stock_quantity": 40,
                "featured_image": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["health", "peace"],
                "cashback_percent": 100,
            },

            # 3. Rudraksha
            {
                "title": "Certified Nepali 5-Mukhi Rudraksha Silver Pendant",
                "slug": "nepali-5-mukhi-rudraksha-pendant",
                "sku": "ASTRA-RUD-05",
                "category_slug": "rudraksha",
                "short_description": "Collected from high Himalayan altitude with Government X-Ray Lab Certificate.",
                "detailed_description": "5-Mukhi Rudraksha represents Lord Kalagni Rudra. Calms blood pressure, alleviates cardiovascular stress, and promotes profound peaceful meditation.",
                "ruling_planet": "Jupiter",
                "deity": "Lord Shiva",
                "mrp": 2999.0,
                "sale_price": 1499.0,
                "stock_quantity": 25,
                "featured_image": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["peace", "health"],
                "cashback_percent": 100,
                "is_featured": True,
            },
            {
                "title": "7-Mukhi Nepali Rudraksha for Shani Sade Sati Defense",
                "slug": "7-mukhi-nepali-rudraksha",
                "sku": "ASTRA-RUD-07",
                "category_slug": "rudraksha",
                "short_description": "Consecrated bead blessed by Goddess Mahalakshmi to overcome Saturn hurdles.",
                "detailed_description": "Essential remedy for natives going through Shani Mahadasha, Sade Sati or Dhaiya. Brings sudden career advancements and health stability.",
                "ruling_planet": "Saturn",
                "deity": "Maha Lakshmi",
                "mrp": 3499.0,
                "sale_price": 1899.0,
                "stock_quantity": 20,
                "featured_image": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["dosha", "wealth", "career"],
                "cashback_percent": 100,
            },

            # 4. Karungali
            {
                "title": "Original Karungali Malai (108 Beads Silver Capped)",
                "slug": "original-karungali-malai",
                "sku": "ASTRA-KAR-108",
                "category_slug": "karungali",
                "short_description": "100% pure black ebony wood mala handcrafted by temple artisans in South India.",
                "detailed_description": "Karungali acts as a natural electromagnetic shield against negative vibrations, black magic, and drishti (evil eye). Enhances memory power and brings victory in legal affairs.",
                "ruling_planet": "Mars",
                "deity": "Lord Murugan & Varahi Amman",
                "mrp": 2499.0,
                "sale_price": 1299.0,
                "stock_quantity": 30,
                "featured_image": "https://images.unsplash.com/photo-1590736969955-71cc94801759?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["protection", "career"],
                "cashback_percent": 100,
                "is_featured": True,
            },
            {
                "title": "Karungali Wood Hand Carved Kada Bracelet",
                "slug": "karungali-wood-kada-bracelet",
                "sku": "ASTRA-KAR-KAD",
                "category_slug": "karungali",
                "short_description": "Smooth cylindrical ebony links reinforced with silver spacers for daily wear.",
                "detailed_description": "Worn on the dominant right wrist to deflect hostile gaze, envy in the workplace, and chronic energy drain.",
                "ruling_planet": "Mars",
                "deity": "Lord Murugan",
                "mrp": 1699.0,
                "sale_price": 899.0,
                "stock_quantity": 40,
                "featured_image": "https://images.unsplash.com/photo-1590736969955-71cc94801759?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["protection", "health"],
                "cashback_percent": 100,
            },

            # 5. Vastu & Home
            {
                "title": "Brass Meru Sri Yantra 3D Pyramid",
                "slug": "brass-meru-sri-yantra",
                "sku": "ASTRA-SRI-01",
                "category_slug": "vastu-home",
                "short_description": "Sacred three-dimensional Mahameru consecrated with Sri Suktam rituals.",
                "detailed_description": "Places divine Lakshmi frequencies in northeast (Ishanya) corner of house or workplace to clear all directional Vastu doshas and attract constant wealth flow.",
                "ruling_planet": "Jupiter & Venus",
                "deity": "Tripura Sundari",
                "mrp": 2500.0,
                "sale_price": 1399.0,
                "stock_quantity": 25,
                "featured_image": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["wealth", "peace"],
                "cashback_percent": 100,
                "is_featured": True,
            },
            {
                "title": "Raw Moroccan Selenite Charging Tower (15cm)",
                "slug": "raw-selenite-charging-tower",
                "sku": "ASTRA-SEL-TW",
                "category_slug": "vastu-home",
                "short_description": "High-vibration crystal spire that continuously cleanses rooms and gemstones.",
                "detailed_description": "Self-cleansing mineral beacon that purifies the aura, dissipates domestic arguments, and infuses angelic peace throughout your meditation space.",
                "ruling_planet": "Moon",
                "deity": "Chandra Dev",
                "mrp": 1499.0,
                "sale_price": 799.0,
                "stock_quantity": 35,
                "featured_image": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["peace", "protection"],
                "cashback_percent": 100,
            },
            {
                "title": "Natural Gomti Chakra Set of 11 (Vedic Energized)",
                "slug": "natural-gomti-chakra-set",
                "sku": "ASTRA-GMT-11",
                "category_slug": "vastu-home",
                "short_description": "Sacred rare marine spiral shells from Gomati river for safe & cash-box blessings.",
                "detailed_description": "Place in your shop cash counter, locker or puja altar wrapped in yellow silk cloth on Diwali or Pushya Nakshatra.",
                "ruling_planet": "Jupiter",
                "deity": "Lord Krishna & Maha Lakshmi",
                "mrp": 999.0,
                "sale_price": 499.0,
                "stock_quantity": 50,
                "featured_image": "https://images.unsplash.com/photo-1611591475879-166258f33cf2?auto=format&fit=crop&w=800&q=80",
                "purpose_tags": ["wealth", "luck"],
                "cashback_percent": 100,
            },
        ]

        inserted_count = 0
        updated_count = 0

        for pdata in products_data:
            cat = cat_map[pdata["category_slug"]]
            existing_prod = await Product.find_one(Product.slug == pdata["slug"])

            if not existing_prod:
                prod = Product(
                    title=pdata["title"],
                    slug=pdata["slug"],
                    sku=pdata["sku"],
                    category_id=cat.id,
                    category_slug=cat.slug,
                    category_type=cat.category_type,
                    short_description=pdata["short_description"],
                    detailed_description=pdata["detailed_description"],
                    ruling_planet=pdata.get("ruling_planet"),
                    deity=pdata.get("deity"),
                    mrp=pdata["mrp"],
                    sale_price=pdata["sale_price"],
                    stock_quantity=pdata["stock_quantity"],
                    featured_image=pdata["featured_image"],
                    images=[pdata["featured_image"]],
                    purpose_tags=pdata.get("purpose_tags", []),
                    free_gift_badge=pdata.get("free_gift_badge"),
                    free_gift_title=pdata.get("free_gift_title"),
                    free_gift_value=pdata.get("free_gift_value"),
                    cashback_percent=pdata.get("cashback_percent", 100),
                    is_active=True,
                    is_featured=pdata.get("is_featured", False),
                    is_energized=True,
                )
                await prod.insert()
                inserted_count += 1
                print(f"Inserted: {prod.title} (₹{prod.sale_price})")
            else:
                existing_prod.category_id = cat.id
                existing_prod.category_slug = cat.slug
                existing_prod.category_type = cat.category_type
                existing_prod.mrp = pdata["mrp"]
                existing_prod.sale_price = pdata["sale_price"]
                existing_prod.featured_image = pdata["featured_image"]
                existing_prod.images = [pdata["featured_image"]]
                existing_prod.stock_quantity = pdata["stock_quantity"]
                existing_prod.is_active = True
                existing_prod.is_featured = pdata.get("is_featured", False)
                existing_prod.free_gift_badge = pdata.get("free_gift_badge")
                existing_prod.free_gift_title = pdata.get("free_gift_title")
                existing_prod.free_gift_value = pdata.get("free_gift_value")
                await existing_prod.save()
                updated_count += 1
                print(f"Updated: {existing_prod.title}")

        print(f"\nDone! Inserted {inserted_count} products, updated {updated_count} products.")
        return 0

    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
