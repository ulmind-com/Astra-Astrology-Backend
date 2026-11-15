"""Content Management System (CMS) documents.

Singleton configurations for site content, starting with homepage customization.
"""

from typing import List
import pymongo
from pydantic import BaseModel, Field

from app.models.base import TimestampedDocument

CMS_KEY_HOMEPAGE = "homepage"


class HeroCardConfig(BaseModel):
    title: str = Field(default="Zodiac Signs", max_length=100)
    subtitle: str = Field(default="READ MORE", max_length=100)
    link: str = Field(default="/rashi-calculator", max_length=300)
    icon: str = Field(default="zodiac", max_length=50)


class TrustStatConfig(BaseModel):
    value: str = Field(default="500+", max_length=50)
    label: str = Field(default="VERIFIED ASTROLOGERS", max_length=100)


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
            "title": "Sacred Certified Nepali Rudraksha",
            "subtitle": "Consecrated with Vedic Pran-Pratishtha by Vedic Pandits for spiritual protection & prosperity.",
            "cta_text": "Explore Rudraksha",
            "cta_link": "/shop?category=rudraksha",
            "badge_text": "100% Authentic & Lab Certified",
            "image_url": "https://images.unsplash.com/photo-1602751584552-8ba73aad10e1?auto=format&fit=crop&w=1200&q=80",
            "is_active": True,
        },
        {
            "id": "banner-2",
            "title": "Natural Astrological Gemstones",
            "subtitle": "Unheated, untreated Vedic gems with government recognized laboratory certification.",
            "cta_text": "Discover Gemstones",
            "cta_link": "/shop?category=gemstone",
            "badge_text": "Govt. Lab Certified",
            "image_url": "https://images.unsplash.com/photo-1599707367072-cd6ada2bc375?auto=format&fit=crop&w=1200&q=80",
            "is_active": True,
        },
        {
            "id": "banner-3",
            "title": "Zodiac & Mulank Crystal Bracelets",
            "subtitle": "Includes FREE Raw Selenite Plate worth ₹729 + 100% Wallet Cashback on all prepaid orders!",
            "cta_text": "Shop Zodiac",
            "cta_link": "/shop?purpose=zodiac",
            "badge_text": "100% Wallet Cashback",
            "image_url": "https://images.unsplash.com/photo-1611591475879-166258f33cf2?auto=format&fit=crop&w=1200&q=80",
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
    """Singleton document storing customizable store hero banners and announcements."""

    key: str = CMS_KEY_SHOP

    # Announcement & Marquee
    announcement_bar_text: str | None = Field(
        default="⚡ 100% Cashback in Astra Wallet on All Prepaid Orders! Consecrated at Varanasi.",
        max_length=300,
    )
    announcement_bar_link: str | None = Field(default="/shop", max_length=300)
    announcement_bar_active: bool = True
    marquee_items: list[str] = Field(default_factory=default_shop_marquee_items)
    hero_banners: list[dict] = Field(default_factory=default_shop_hero_banners)

    # 100% Wallet Cashback Hook Controls (Admin Configurable)
    cashback_enabled: bool = True
    cashback_percent: int = Field(default=100, ge=0, le=200, description="Default wallet cashback percentage on prepaid orders")
    cashback_max_cap_inr: float | None = Field(default=None, description="Optional cap in INR for cashback (None = uncapped)")

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

    # Video Reels & Social Proof
    reels: list[dict] = Field(default_factory=list)

    class Settings:
        name = "cms_shop"
        indexes = [
            pymongo.IndexModel([("key", pymongo.ASCENDING)], name="cms_shop_key_unique", unique=True),
        ]

