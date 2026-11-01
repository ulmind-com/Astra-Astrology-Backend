"""Schemas for CMS configuration."""

from typing import List, Optional
from pydantic import BaseModel, Field


class HeroCardItem(BaseModel):
    title: str = Field(..., max_length=100)
    subtitle: str = Field(..., max_length=100)
    link: str = Field(..., max_length=300)
    icon: str = Field(default="zodiac", max_length=50)


class TrustStatItem(BaseModel):
    value: str = Field(..., max_length=50)
    label: str = Field(..., max_length=100)


class HomePageCMSOut(BaseModel):
    # Hero Section
    hero_eyebrow: str
    hero_title_line1: str
    hero_title_line2: str
    hero_title_highlight: str
    hero_description: str
    hero_cta_primary_text: str
    hero_cta_primary_link: str
    hero_cta_secondary_text: str
    hero_cta_secondary_link: str
    hero_chakra_image_url: str
    hero_chakra_speed_seconds: int
    hero_chakra_enabled: bool

    # 4 Feature Cards Grid
    hero_cards: list[HeroCardItem]

    # Trust stats strip
    trust_stats: list[TrustStatItem]

    # Services Section
    services_eyebrow: str
    services_title: str
    services_description: str

    # How It Works
    how_it_works_badge: str
    how_it_works_title: str
    step1_title: str
    step1_body: str
    step2_title: str
    step2_body: str
    step3_title: str
    step3_body: str

    # Final CTA Banner
    cta_badge: str
    cta_title: str
    cta_description: str
    cta_primary_text: str
    cta_primary_link: str
    cta_secondary_text: str
    cta_secondary_link: str


class HomePageCMSUpdate(BaseModel):
    # Hero Section
    hero_eyebrow: Optional[str] = None
    hero_title_line1: Optional[str] = None
    hero_title_line2: Optional[str] = None
    hero_title_highlight: Optional[str] = None
    hero_description: Optional[str] = None
    hero_cta_primary_text: Optional[str] = None
    hero_cta_primary_link: Optional[str] = None
    hero_cta_secondary_text: Optional[str] = None
    hero_cta_secondary_link: Optional[str] = None
    hero_chakra_image_url: Optional[str] = None
    hero_chakra_speed_seconds: Optional[int] = None
    hero_chakra_enabled: Optional[bool] = None

    # 4 Feature Cards Grid
    hero_cards: Optional[list[HeroCardItem]] = None

    # Trust stats strip
    trust_stats: Optional[list[TrustStatItem]] = None

    # Services Section
    services_eyebrow: Optional[str] = None
    services_title: Optional[str] = None
    services_description: Optional[str] = None

    # How It Works
    how_it_works_badge: Optional[str] = None
    how_it_works_title: Optional[str] = None
    step1_title: Optional[str] = None
    step1_body: Optional[str] = None
    step2_title: Optional[str] = None
    step2_body: Optional[str] = None
    step3_title: Optional[str] = None
    step3_body: Optional[str] = None

    # Final CTA Banner
    cta_badge: Optional[str] = None
    cta_title: Optional[str] = None
    cta_description: Optional[str] = None
    cta_primary_text: Optional[str] = None
    cta_primary_link: Optional[str] = None
    cta_secondary_text: Optional[str] = None
    cta_secondary_link: Optional[str] = None


class UploadImageOut(BaseModel):
    url: str
    public_id: str
