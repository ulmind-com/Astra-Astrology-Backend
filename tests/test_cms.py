"""Tests for CMS models, schemas, and endpoints."""

import pytest
from app.models.cms import default_hero_cards, default_trust_stats
from app.schemas.cms import (
    HomePageCMSOut,
    HomePageCMSUpdate,
    HeroCardItem,
    TrustStatItem,
)
from tests.conftest import requires_mongo


def test_cms_defaults_and_schemas():
    cards = default_hero_cards()
    assert len(cards) == 4
    assert cards[0].title == "Zodiac Signs"
    assert cards[0].icon == "zodiac"

    stats = default_trust_stats()
    assert len(stats) == 3
    assert stats[0].value == "500+"

    update = HomePageCMSUpdate(
        hero_title_highlight="COSMOS",
        hero_chakra_speed_seconds=45,
        trust_stats=[TrustStatItem(value="1000+", label="TEST STAT")],
    )
    dumped = update.model_dump(exclude_unset=True)
    assert dumped["hero_title_highlight"] == "COSMOS"
    assert dumped["hero_chakra_speed_seconds"] == 45
    assert len(dumped["trust_stats"]) == 1


@requires_mongo
@pytest.mark.asyncio
async def test_cms_homepage_public_endpoint(client):
    res = await client.get("/api/v1/cms/homepage")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["hero_title_highlight"] == "ASTROLOGY"
    assert len(data["data"]["hero_cards"]) == 4
    assert len(data["data"]["trust_stats"]) == 3

    admin_res = await client.get("/api/v1/admin/cms/homepage")
    assert admin_res.status_code == 200
    admin_data = admin_res.json()
    assert admin_data["success"] is True
    assert admin_data["data"]["hero_title_highlight"] == "ASTROLOGY"
