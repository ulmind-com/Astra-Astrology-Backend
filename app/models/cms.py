"""Content Management System (CMS) documents.

Singleton configurations for site content, starting with homepage customization.
"""

from typing import List
import pymongo
from pydantic import BaseModel, Field

from app.models.base import TimestampedDocument

CMS_KEY_HOMEPAGE = "homepage"


class HeroSlideConfig(BaseModel):
    id: str = Field(default="slide-1", max_length=50)
    title: str = Field(default="Enjoy your relationship", max_length=200)
    subtitle: str = Field(default="don't stress over it", max_length=200)
    description: str = Field(
        default="Talk to India's top Vedic astrologers & tarot readers for instant relationship clarity.",
        max_length=1000,
    )
    cta_text: str = Field(default="Consult for FREE", max_length=100)
    cta_link: str = Field(default="/astrologers", max_length=300)
    badge_text: str = Field(default="India's Best Astrology Platform", max_length=200)
    badge_rating: str = Field(default="4.9/5", max_length=50)
    image_url: str = Field(default="/images/hero-couple.jpg", max_length=1000)
    bg_gradient: str = Field(default="from-[#fffbf0] via-[#fff8dc] to-[#fceeb5]", max_length=300)
    border_color: str = Field(default="border-[#ebd881]", max_length=100)


class HeroCardConfig(BaseModel):
    title: str = Field(default="Zodiac Signs", max_length=100)
    subtitle: str = Field(default="READ MORE", max_length=100)
    link: str = Field(default="/rashi-calculator", max_length=300)
    icon: str = Field(default="zodiac", max_length=50)


class TrustStatConfig(BaseModel):
    value: str = Field(default="500+", max_length=50)
    label: str = Field(default="VERIFIED ASTROLOGERS", max_length=100)


def default_hero_slides() -> list[HeroSlideConfig]:
    return [
        HeroSlideConfig(
            id="slide-1",
            title="Enjoy your relationship",
            subtitle="don't stress over it",
            description="Talk to India's top Vedic astrologers & tarot readers for instant relationship clarity.",
            cta_text="Consult for FREE",
            cta_link="/astrologers",
            badge_text="India's Best Astrology Platform",
            badge_rating="4.9/5",
            image_url="/images/hero/hero-couple-exploring.png",
            bg_gradient="from-[#fffbf0] via-[#fff8dc] to-[#fceeb5]",
            border_color="border-[#ebd881]",
        ),
        HeroSlideConfig(
            id="slide-2",
            title="Know your destiny & future",
            subtitle="with free Vedic Janam Kundli",
            description="Accurate planetary calculations, dosha analysis, and personalized remedies by Vedic experts.",
            cta_text="Generate Free Kundli",
            cta_link="/kundli",
            badge_text="100% Free & Accurate Kundli",
            badge_rating="500k+ Created",
            image_url="/images/hero/hero-parchment-kundli.png",
            bg_gradient="from-[#fff9e6] via-[#fff3cc] to-[#fde5a3]",
            border_color="border-[#e8ce6b]",
        ),
        HeroSlideConfig(
            id="slide-3",
            title="Check marriage compatibility",
            subtitle="find your perfect soulmate",
            description="Detailed 36-Gun Milan, Manglik Dosha report & life-long harmony analysis for bride & groom.",
            cta_text="Match Kundli Now",
            cta_link="/kundli-matching",
            badge_text="Trusted Matchmaking",
            badge_rating="36 Gunas Score",
            image_url="/images/hero/hero-indian-wedding.png",
            bg_gradient="from-[#fff6f0] via-[#ffeedd] to-[#ffdcb8]",
            border_color="border-[#f2b992]",
        ),
        HeroSlideConfig(
            id="slide-4",
            title="Unlock secrets in your palm",
            subtitle="with modern 3D AI biometrics",
            description="Explore heart, head & life lines with interactive real-time 3D hand visualization.",
            cta_text="Start Palm Reading",
            cta_link="/palm-reading",
            badge_text="Next-Gen 3D Biometrics",
            badge_rating="99% Precision",
            image_url="/images/hero/hero-mint-mandala.png",
            bg_gradient="from-[#f3faf6] via-[#e2f5ec] to-[#c7eedb]",
            border_color="border-[#93dab7]",
        ),
        HeroSlideConfig(
            id="slide-5",
            title="Discover your true potential",
            subtitle="via 78 Arcana Tarot guidance",
            description="Daily forecasts, love spreads & career clarity synchronized with planetary dasha cycles.",
            cta_text="Get Tarot Reading",
            cta_link="/tarot",
            badge_text="Sacred Arcana Cards",
            badge_rating="78 Cards",
            image_url="/images/hero/hero-mystical-tarot.png",
            bg_gradient="from-[#faf5ff] via-[#f3e8ff] to-[#e4ceff]",
            border_color="border-[#cfa7f7]",
        ),
        HeroSlideConfig(
            id="slide-6",
            title="Harmonize your living space",
            subtitle="attract wealth, peace & health",
            description="Interactive 16-zone Vastu directional compass and elemental balance remedies for home & office.",
            cta_text="Explore Vastu Guide",
            cta_link="/vastu",
            badge_text="Ancient Vedic Architecture",
            badge_rating="16 Zones",
            image_url="/images/hero/hero-golden-compass.png",
            bg_gradient="from-[#fffdf0] via-[#fdf6cc] to-[#fce48b]",
            border_color="border-[#ebd36a]",
        ),
    ]


def default_hero_cards() -> list[HeroCardConfig]:
    return [
        HeroCardConfig(title="Zodiac Signs", subtitle="READ MORE", link="/rashi-calculator", icon="zodiac"),
        HeroCardConfig(title="Chinese Signs", subtitle="READ MORE", link="modal:chinese", icon="chinese"),
        HeroCardConfig(title="Planets", subtitle="READ MORE", link="/kundli", icon="planets"),
        HeroCardConfig(title="Houses", subtitle="READ MORE", link="/kp-calculator", icon="houses"),
    ]


def default_trust_stats() -> list[TrustStatConfig]:
    return [
        TrustStatConfig(value="500+", label="VERIFIED ASTROLOGERS"),
        TrustStatConfig(value="50K+", label="HAPPY CONSULTATIONS"),
        TrustStatConfig(value="4.8★", label="AVERAGE CLIENT RATING"),
    ]


class HomePageCMS(TimestampedDocument):
    """Singleton document storing all customizable static texts & media on the homepage."""

    key: str = CMS_KEY_HOMEPAGE

    # Hero Slides (carousel banners)
    hero_slides: list[HeroSlideConfig] = Field(default_factory=default_hero_slides)

    # Hero Section
    hero_eyebrow: str = Field(default="Explore the Horoscope", max_length=150)
    hero_title_line1: str = Field(default="WELCOME TO THE", max_length=150)
    hero_title_line2: str = Field(default="WORLD OF", max_length=150)
    hero_title_highlight: str = Field(default="ASTROLOGY", max_length=150)
    hero_description: str = Field(
        default="Learn about astrology, zodiac signs, retrogrades, and more! Your world becomes clear once you understand how the universe influences it.",
        max_length=1000,
    )
    hero_cta_primary_text: str = Field(default="Find an Astrologer", max_length=100)
    hero_cta_primary_link: str = Field(default="/astrologers", max_length=300)
    hero_cta_secondary_text: str = Field(default="Kundli Matching", max_length=100)
    hero_cta_secondary_link: str = Field(default="/kundli-matching", max_length=300)
    hero_chakra_image_url: str = Field(default="/zodiac-chakra.png", max_length=1000)
    hero_chakra_speed_seconds: int = Field(default=60, ge=5, le=3600)
    hero_chakra_enabled: bool = True

    # 4 Feature Cards Grid
    hero_cards: list[HeroCardConfig] = Field(default_factory=default_hero_cards)

    # Trust stats strip
    trust_stats: list[TrustStatConfig] = Field(default_factory=default_trust_stats)

    # Services Section
    services_eyebrow: str = Field(default="What we offer", max_length=100)
    services_title: str = Field(default="What you can ask about", max_length=200)
    services_description: str = Field(
        default="Traditional methods, interpreted by people who practise them every day.",
        max_length=500,
    )

    # How It Works
    how_it_works_badge: str = Field(default="How it works", max_length=100)
    how_it_works_title: str = Field(default="Three steps to clarity", max_length=200)
    step1_title: str = Field(default="Pick your astrologer", max_length=150)
    step1_body: str = Field(
        default="Browse verified profiles, languages spoken, specialties, and real reviews.",
        max_length=500,
    )
    step2_title: str = Field(default="Recharge your wallet", max_length=150)
    step2_body: str = Field(
        default="Transparent per-minute rates. Add what you need via UPI or card.",
        max_length=500,
    )
    step3_title: str = Field(default="Connect instantly", max_length=150)
    step3_body: str = Field(
        default="Start a private 1-on-1 chat or audio/video call. No waiting rooms.",
        max_length=500,
    )

    # Final CTA Banner
    cta_badge: str = Field(default="Get started today", max_length=100)
    cta_title: str = Field(default="Ready when you are", max_length=200)
    cta_description: str = Field(
        default="Create an account, add your birth details once, and every reading after that is a click away.",
        max_length=500,
    )
    cta_primary_text: str = Field(default="Get started — it's free", max_length=100)
    cta_primary_link: str = Field(default="/register", max_length=300)
    cta_secondary_text: str = Field(default="Browse astrologers", max_length=100)
    cta_secondary_link: str = Field(default="/astrologers", max_length=300)

    class Settings:
        name = "cms_homepage"
        indexes = [
            pymongo.IndexModel([("key", pymongo.ASCENDING)], name="cms_homepage_key_unique", unique=True),
        ]


CMS_KEY_SHOP = "shop"


def default_shop_hero_banners() -> list[dict]:
    return [
        {
            "id": "banner-1",
            "title": "WEAR YOUR ZODIAC",
            "subtitle": "Discover the new zodiac ring collection handcrafted in sterling silver and energized with Vedic rituals.",
            "cta_text": "SHOP NOW",
            "cta_link": "/shop?category=zodiac",
            "badge_text": "NEW LAUNCH",
            "image_url": "/images/banners/banner-zodiac.jpg",
            "is_active": True,
        },
        {
            "id": "banner-2",
            "title": "SACRED NEPALI RUDRAKSHA",
            "subtitle": "1 to 14 Mukhi divine Rudraksha beads collected from the high Himalayas with government lab certification.",
            "cta_text": "EXPLORE MALAS",
            "cta_link": "/shop?category=karungali",
            "badge_text": "100% PRANA-PRATISHTHIT",
            "image_url": "/images/banners/banner-rudraksha.jpg",
            "is_active": True,
        },
        {
            "id": "banner-3",
            "title": "SUPER DHAN YOG BAND",
            "subtitle": "Activate Mahalakshmi and Kuber vibrations to attract financial breakthroughs, wealth retention, and business growth.",
            "cta_text": "ORDER NOW",
            "cta_link": "/shop?category=bracelets",
            "badge_text": "BESTSELLER",
            "image_url": "/images/banners/banner-dhanyog.jpg",
            "is_active": True,
        },
        {
            "id": "banner-4",
            "title": "ORIGINAL KARUNGALI MALA",
            "subtitle": "Pure black ebony wood beads for shielding against malefic Rahu, evil eye, negative entities and karmic blocks.",
            "cta_text": "VIEW KARUNGALI",
            "cta_link": "/shop?category=karungali",
            "badge_text": "DIVINE SHIELD",
            "image_url": "/images/banners/banner-karungali.jpg",
            "is_active": True,
        },
        {
            "id": "banner-5",
            "title": "PRAN-PRATISHTHIT RATNA",
            "subtitle": "Unheated, untreated natural gemstones tested and certified by government recognized gemological laboratories.",
            "cta_text": "DISCOVER RATNA",
            "cta_link": "/shop?category=zodiac",
            "badge_text": "LAB CERTIFIED",
            "image_url": "/images/banners/banner-gemstones.jpg",
            "is_active": True,
        },
    ]


def default_shop_reels() -> list[dict]:
    return [
        {
            "id": "reel-1",
            "user_handle": "@sneha_vats",
            "user_name": "Sneha Vats",
            "rating": 5,
            "quote": "Wearing the 7-Mukhi Rudraksha cleared my Saturn Sade Sati career blocks in 3 weeks! 🌟",
            "thumbnail_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80",
            "video_url": "https://assets.mixkit.co/videos/preview/mixkit-hands-holding-a-sparkling-gemstone-41315-large.mp4",
            "likes_count": "4.8k",
            "tagged_product_title": "খাঁটি নেপালি ৭-মুখী রুদ্রাক্ষ",
            "tagged_product_price": 1899,
            "tagged_product_slug": "nepali-7-mukhi-rudraksha",
            "is_active": True,
        },
        {
            "id": "reel-2",
            "user_handle": "@rohit_astroglow",
            "user_name": "Rohit K.",
            "rating": 5,
            "quote": "Unboxing my Super Dhan Yog Band! The energy feel is absolutely authentic and energizing. 💰",
            "thumbnail_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80",
            "video_url": "https://assets.mixkit.co/videos/preview/mixkit-woman-wearing-spiritual-beads-bracelet-43098-large.mp4",
            "likes_count": "3.9k",
            "tagged_product_title": "Super Dhan Yog Band",
            "tagged_product_price": 1099,
            "tagged_product_slug": "super-dhan-yog-band",
            "is_active": True,
        },
        {
            "id": "reel-3",
            "user_handle": "@dr_kunal",
            "user_name": "Dr. Kunal Mehta",
            "rating": 5,
            "quote": "Pyrite Stud Ring transformed my clinic consultation inquiries within a month! ✨",
            "thumbnail_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80",
            "video_url": "https://assets.mixkit.co/videos/preview/mixkit-shiny-gemstones-and-crystals-on-display-42410-large.mp4",
            "likes_count": "5.2k",
            "tagged_product_title": "Pyrite Stud Ring",
            "tagged_product_price": 799,
            "tagged_product_slug": "pyrite-stud-ring",
            "is_active": True,
        },
        {
            "id": "reel-4",
            "user_handle": "@ananya_sen",
            "user_name": "Ananya Sen",
            "rating": 5,
            "quote": "Original Karungali Mala quality is incredible, heavy and pure ebony wood with silver caps. 🙏",
            "thumbnail_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=600&q=80",
            "video_url": "https://assets.mixkit.co/videos/preview/mixkit-close-up-of-hands-holding-rosary-beads-42998-large.mp4",
            "likes_count": "4.1k",
            "tagged_product_title": "Original Karungali Malai (108 Beads)",
            "tagged_product_price": 1299,
            "tagged_product_slug": "original-karungali-malai",
            "is_active": True,
        },
        {
            "id": "reel-5",
            "user_handle": "@vikram_aditya",
            "user_name": "Vikram Aditya",
            "rating": 5,
            "quote": "Mulank 4 Rahu bracelet brought immense mental focus and shielded me from burnout. 🔮",
            "thumbnail_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=600&q=80",
            "video_url": "https://assets.mixkit.co/videos/preview/mixkit-person-meditating-with-crystals-in-front-42350-large.mp4",
            "likes_count": "2.8k",
            "tagged_product_title": "Mulank 4 Rahu Crystal Bracelet",
            "tagged_product_price": 999,
            "tagged_product_slug": "mulank-4-rahu-crystal-bracelet",
            "is_active": True,
        },
    ]


def default_shop_marquee_items() -> list[str]:
    return [
        "⚡ 100% Cashback in Astra Wallet on All Prepaid Orders",
        "🔱 Consecrated & Energised by Vedic Pandits in Varanasi",
        "💎 100% Natural & Govt. Lab Certified Gemstones & Rudraksha",
        "✨ FREE Raw Selenite Charging Plate worth ₹729 with Zodiac Bracelets",
        "🚚 Free Express Shipping across India on orders above ₹499",
        "🛡️ 7-Day Easy Replacement Guarantee • Cash on Delivery Available",
    ]


class ShopCMS(TimestampedDocument):
    """Singleton document storing customizable store hero banners, announcements, and reels."""

    key: str = CMS_KEY_SHOP

    # Announcement & Marquee
    announcement_bar_text: str | None = Field(
        default="🛍️ Discover Sacred Jewellery & Energised Remedies Based on Your Mulank & Kundli ✨",
        max_length=300,
    )
    announcement_bar_link: str | None = Field(default="/shop", max_length=300)
    announcement_bar_active: bool = True
    marquee_items: list[str] = Field(default_factory=default_shop_marquee_items)
    hero_banners: list[dict] = Field(default_factory=default_shop_hero_banners)
    reels: list[dict] = Field(default_factory=default_shop_reels)

    # 100% Wallet Cashback Hook Controls (Admin Configurable)
    cashback_enabled: bool = True
    cashback_percent: int = Field(default=100, ge=0, le=200, description="Default wallet cashback percentage on prepaid orders")
    cashback_max_cap_inr: float | None = Field(default=None, description="Optional cap in INR for cashback (None = uncapped)")
    cashback_credit_timing: str = Field(
        default="on_delivery",
        description="When cashback coins are credited: 'on_delivery' (safe anti-fraud) or 'on_payment' (instant)",
    )

    # Customer Order Cancellation & Anti-Fraud Policy Controls
    allow_user_cancellation: bool = Field(
        default=True,
        description="Whether customers can cancel orders online before shipment",
    )
    cancellation_grace_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Hours from placement within which customers can cancel before shipment",
    )
    refund_sla_days: int = Field(
        default=3,
        ge=1,
        le=14,
        description="Business days within which cancelled prepaid orders are refunded to customer UPI",
    )

    # High-Value Free Gift Defaults (Admin Configurable)
    free_gift_default_title: str = "Raw Selenite Charging Plate"
    free_gift_default_value: float = 729.0
    free_gift_default_badge: str = "FREE Raw Selenite Plate worth ₹729"
    free_gift_default_image_url: str | None = "https://images.unsplash.com/photo-1611591475879-166258f33cf2?w=600&auto=format&fit=crop&q=80"

    # Shipping & Logistics Controls
    free_shipping_threshold: float = Field(default=499.0, ge=0, description="Order subtotal threshold in ₹ for free shipping")
    standard_shipping_fee: float = Field(default=70.0, ge=0, description="Standard courier shipping fee in ₹ below threshold")
    cod_enabled: bool = True
    cod_extra_charge: float = Field(default=0.0, ge=0, description="Extra fee for Cash on Delivery (0 for free COD)")

    # Stock Reservation & Abandoned Checkout TTL Controls
    checkout_reservation_minutes: int = Field(
        default=20,
        ge=5,
        le=120,
        description="Minutes to hold/reserve inventory for pending Razorpay checkouts before auto-restoring stock",
    )

    # COD Blacklist & Anti-Abuse Controls
    cod_max_rto_allowed: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Number of unreceived COD RTO shipments before phone number is blacklisted from COD",
    )
    cod_blacklisted_phones: list[str] = Field(
        default_factory=list,
        description="List of phone numbers manually or automatically blacklisted from Cash on Delivery",
    )

    class Settings:
        name = "cms_shop"
        indexes = [
            pymongo.IndexModel([("key", pymongo.ASCENDING)], name="cms_shop_key_unique", unique=True),
        ]

