"""CMS management services."""

from loguru import logger
from app.models.cms import (
    CMS_KEY_HOMEPAGE,
    HomePageCMS,
    HeroCardConfig,
    TrustStatConfig,
    default_hero_cards,
    default_trust_stats,
)
from app.schemas.cms import (
    HomePageCMSOut,
    HomePageCMSUpdate,
    HeroCardItem,
    TrustStatItem,
)


def to_homepage_out(doc: HomePageCMS) -> HomePageCMSOut:
    return HomePageCMSOut(
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
                value=s.value,
                label=s.label,
            )
            for s in doc.trust_stats
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


async def get_or_create_homepage() -> HomePageCMS:
    try:
        doc = await HomePageCMS.find_one(HomePageCMS.key == CMS_KEY_HOMEPAGE)
        if doc is None:
            doc = HomePageCMS()
            await doc.insert()
        return doc
    except Exception as exc:
        logger.warning("Could not load homepage CMS from database ({}). Returning memory defaults.", exc)
        return HomePageCMS()


async def update_homepage(payload: HomePageCMSUpdate) -> HomePageCMS:
    doc = await get_or_create_homepage()
    update_data = payload.model_dump(exclude_unset=True)

    for field, val in update_data.items():
        if val is None:
            continue
        if field == "hero_cards":
            doc.hero_cards = [HeroCardConfig(**item) if isinstance(item, dict) else HeroCardConfig(**item.model_dump()) for item in val]
        elif field == "trust_stats":
            doc.trust_stats = [TrustStatConfig(**item) if isinstance(item, dict) else TrustStatConfig(**item.model_dump()) for item in val]
        else:
            setattr(doc, field, val)

    try:
        await doc.save()
    except Exception as exc:
        logger.error("Failed to save homepage CMS doc: {}", exc)
        raise

    return doc


async def reset_homepage() -> HomePageCMS:
    doc = await get_or_create_homepage()
    defaults = HomePageCMS()

    for field in defaults.model_fields.keys():
        if field in ("id", "created_at", "updated_at", "key"):
            continue
        setattr(doc, field, getattr(defaults, field))

    try:
        await doc.save()
    except Exception as exc:
        logger.error("Failed to reset homepage CMS doc: {}", exc)
        raise

    return doc
