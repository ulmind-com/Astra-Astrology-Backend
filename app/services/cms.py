"""CMS management services."""

from loguru import logger
from app.models.cms import (
    CMS_KEY_HOMEPAGE,
    HomePageCMS,
    HeroSlideConfig,
    HeroCardConfig,
    TrustStatConfig,
    CinematicHeroSlideConfig,
    default_hero_slides,
    default_hero_cards,
    default_trust_stats,
    default_cinematic_hero_slides,
)
from app.schemas.cms import (
    HomePageCMSOut,
    HomePageCMSUpdate,
    HeroSlideItem,
    HeroCardItem,
    TrustStatItem,
    CinematicHeroSlideItem,
)


def to_homepage_out(doc: HomePageCMS) -> HomePageCMSOut:
    return HomePageCMSOut(
        cinematic_hero_slides=[
            CinematicHeroSlideItem(
                id=s.id,
                photo=s.photo,
                position=s.position,
                thumb=s.thumb,
                layout=s.layout,
                title_en=s.title_en,
                title_bn=s.title_bn,
                title_hi=s.title_hi,
                heading_en=s.heading_en,
                heading_bn=s.heading_bn,
                heading_hi=s.heading_hi,
                description_en=s.description_en,
                description_bn=s.description_bn,
                description_hi=s.description_hi,
            )
            for s in (doc.cinematic_hero_slides or default_cinematic_hero_slides())
        ],
        hero_slides=[
            HeroSlideItem(
                id=s.id,
                title=s.title,
                subtitle=s.subtitle,
                description=s.description,
                cta_text=s.cta_text,
                cta_link=s.cta_link,
                badge_text=s.badge_text,
                badge_rating="Swiss Ephemeris" if s.badge_rating == "500k+ Created" else "Certified" if s.badge_rating == "4.9/5" else "3D Palmistry" if s.badge_rating == "99% Precision" else s.badge_rating,
                image_url=s.image_url,
                bg_gradient=s.bg_gradient,
                border_color=s.border_color,
            )
            for s in doc.hero_slides
        ],
        hero_eyebrow=doc.hero_eyebrow,
        hero_title_line1=doc.hero_title_line1,
        hero_title_line2=doc.hero_title_line2,
        hero_title_highlight=doc.hero_title_highlight,
        hero_description=doc.hero_description,
        hero_cta_primary_text=doc.hero_cta_primary_text,
        hero_cta_primary_link=doc.hero_cta_primary_link,
        hero_cta_secondary_text=doc.hero_cta_secondary_text,
        hero_cta_secondary_link=doc.hero_cta_secondary_link,
        hero_chakra_image_url=doc.hero_chakra_image_url,
        hero_chakra_speed_seconds=doc.hero_chakra_speed_seconds,
        hero_chakra_enabled=doc.hero_chakra_enabled,
        hero_cards=[
            HeroCardItem(
                title=c.title,
                subtitle=c.subtitle,
                link=c.link,
                icon=c.icon,
            )
            for c in doc.hero_cards
        ],
        trust_stats=[
            TrustStatItem(
                value="100%" if s.value in ("500+", "50K+") else s.value,
                label="VERIFIED JYOTISHIS" if "500+" in s.value or "50K+" in s.value else s.label,
            )
            for s in (doc.trust_stats or default_trust_stats())
        ],
        services_eyebrow=doc.services_eyebrow,
        services_title=doc.services_title,
        services_description=doc.services_description,
        how_it_works_badge=doc.how_it_works_badge,
        how_it_works_title=doc.how_it_works_title,
        step1_title=doc.step1_title,
        step1_body=doc.step1_body,
        step2_title=doc.step2_title,
        step2_body=doc.step2_body,
        step3_title=doc.step3_title,
        step3_body=doc.step3_body,
        cta_badge=doc.cta_badge,
        cta_title=doc.cta_title,
        cta_description=doc.cta_description,
        cta_primary_text=doc.cta_primary_text,
        cta_primary_link=doc.cta_primary_link,
        cta_secondary_text=doc.cta_secondary_text,
        cta_secondary_link=doc.cta_secondary_link,
    )


import time

_cached_homepage: HomePageCMS | None = None
_cached_homepage_time: float = 0.0
_HOMEPAGE_CACHE_TTL_SECONDS: float = 120.0


def invalidate_homepage_cache() -> None:
    """Invalidates the in-memory homepage CMS cache upon admin updates."""
    global _cached_homepage, _cached_homepage_time
    _cached_homepage = None
    _cached_homepage_time = 0.0


async def get_or_create_homepage(force_refresh: bool = False) -> HomePageCMS:
    global _cached_homepage, _cached_homepage_time

    now = time.monotonic()
    if not force_refresh and _cached_homepage is not None and (now - _cached_homepage_time < _HOMEPAGE_CACHE_TTL_SECONDS):
        return _cached_homepage

    try:
        doc = await HomePageCMS.find_one(HomePageCMS.key == CMS_KEY_HOMEPAGE)
        if doc is None:
            doc = HomePageCMS()
            await doc.insert()
        _cached_homepage = doc
        _cached_homepage_time = now
        return doc
    except Exception as exc:
        logger.warning("Could not load homepage CMS from database ({}). Returning memory defaults.", exc)
        return _cached_homepage or HomePageCMS()


async def update_homepage(payload: HomePageCMSUpdate) -> HomePageCMS:
    doc = await get_or_create_homepage(force_refresh=True)
    update_data = payload.model_dump(exclude_unset=True)

    for field, val in update_data.items():
        if val is None:
            continue
        if field == "hero_slides":
            doc.hero_slides = [HeroSlideConfig(**item) if isinstance(item, dict) else HeroSlideConfig(**item.model_dump()) for item in val]
        elif field == "cinematic_hero_slides":
            doc.cinematic_hero_slides = [
                CinematicHeroSlideConfig(**item) if isinstance(item, dict) else CinematicHeroSlideConfig(**item.model_dump())
                for item in val
            ]
        elif field == "hero_cards":
            doc.hero_cards = [HeroCardConfig(**item) if isinstance(item, dict) else HeroCardConfig(**item.model_dump()) for item in val]
        elif field == "trust_stats":
            doc.trust_stats = [TrustStatConfig(**item) if isinstance(item, dict) else TrustStatConfig(**item.model_dump()) for item in val]
        else:
            setattr(doc, field, val)

    try:
        await doc.save()
        invalidate_homepage_cache()
    except Exception as exc:
        logger.error("Failed to save homepage CMS doc: {}", exc)
        raise

    return doc


async def reset_homepage() -> HomePageCMS:
    doc = await get_or_create_homepage(force_refresh=True)
    defaults = HomePageCMS()

    for field in defaults.model_fields.keys():
        if field in ("id", "created_at", "updated_at", "key"):
            continue
        setattr(doc, field, getattr(defaults, field))

    try:
        await doc.save()
        invalidate_homepage_cache()
    except Exception as exc:
        logger.error("Failed to reset homepage CMS doc: {}", exc)
        raise

    return doc
