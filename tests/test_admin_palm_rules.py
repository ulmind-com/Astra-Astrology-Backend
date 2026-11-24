"""Unit tests for Admin Palm Reading Rules Engine endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from beanie import PydanticObjectId, init_beanie

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.palm_reading import Condition, PalmFeature, PalmReading, PalmRule, Requirement
from app.models.user import User, UserRole
from app.schemas.palm_reading import PalmRuleCreate, PalmRuleUpdate
from app.api.v1.palm_reading import (
    create_palm_rule,
    delete_palm_rule,
    get_palm_rule,
    list_palm_rules,
    palm_rules_meta,
    seed_palm_rules,
    update_palm_rule,
)


@pytest.fixture(autouse=True)
async def init_mock_beanie():
    """Initializes Beanie DocumentSettings in memory for standalone unit testing."""
    mock_db = MagicMock()
    mock_db.command = AsyncMock(return_value={"version": "6.0.0", "versionArray": [6, 0, 0]})
    mock_db.list_collection_names = AsyncMock(return_value=[])

    mock_coll = MagicMock()
    mock_coll.create_index = AsyncMock()
    mock_coll.create_indexes = AsyncMock()
    mock_coll.index_information = AsyncMock(return_value={})
    mock_db.__getitem__.return_value = mock_coll

    await init_beanie(
        database=mock_db,
        document_models=[
            PalmRule,
            PalmReading,
            User,
        ],
    )


@pytest.fixture
def mock_admin():
    admin = User(
        id=PydanticObjectId(),
        email="admin@astra.internal",
        first_name="Admin",
        last_name="Staff",
        role=UserRole.ADMIN,
    )
    return admin


@pytest.mark.asyncio
async def test_palm_rules_meta(mock_admin):
    with patch("app.models.palm_reading.PalmRule.distinct", AsyncMock(return_value=["Temperament", "Career", "Love"])):
        res = await palm_rules_meta(admin=mock_admin)
        assert res.data is not None
        assert "features" in res.data
        assert "feature_labels" in res.data
        assert "requirements" in res.data
        assert "areas" in res.data
        assert "Temperament" in res.data["areas"]
        assert any(f["value"] == PalmFeature.HEART_LINE.value for f in res.data["features"])


@pytest.mark.asyncio
async def test_create_and_get_palm_rule(mock_admin):
    rule_id = PydanticObjectId()
    dummy_rule = PalmRule(
        id=rule_id,
        feature=PalmFeature.HEART_LINE.value,
        option="curved_steep_vedic",
        label="Steep Emotional Incline",
        meaning="High sensitivity and spiritual emotional devotion.",
        area="Love",
        source="Heart line.docx",
        requires=[Requirement.GEOMETRY.value, Requirement.HEART_LINE.value],
        conditions=[Condition(metric="heart_line.curvature", min=0.5)],
        priority=15,
        is_default=False,
        enabled=True,
        reviewed=True,
    )

    # 1. Successful creation
    payload = PalmRuleCreate(
        feature=PalmFeature.HEART_LINE.value,
        option="curved_steep_vedic",
        label="Steep Emotional Incline",
        meaning="High sensitivity and spiritual emotional devotion.",
        area="Love",
        source="Heart line.docx",
        requires=[Requirement.GEOMETRY.value, Requirement.HEART_LINE.value],
        conditions=[{"metric": "heart_line.curvature", "min": 0.5}],
        priority=15,
        is_default=False,
        enabled=True,
        reviewed=True,
    )

    with patch("app.models.palm_reading.PalmRule.find_one", AsyncMock(return_value=None)), \
         patch.object(PalmRule, "insert", AsyncMock(return_value=dummy_rule)):
        create_res = await create_palm_rule(payload=payload, admin=mock_admin)
        assert create_res.data.label == "Steep Emotional Incline"
        assert create_res.data.priority == 15

    # 2. Duplicate rejection
    with patch("app.models.palm_reading.PalmRule.find_one", AsyncMock(return_value=dummy_rule)):
        with pytest.raises(BadRequestError) as exc_info:
            await create_palm_rule(payload=payload, admin=mock_admin)
        assert exc_info.value.error_code == "rule_already_exists"

    # 3. Get single rule
    with patch.object(PalmRule, "get", AsyncMock(return_value=dummy_rule)):
        get_res = await get_palm_rule(rule_id=rule_id, admin=mock_admin)
        assert get_res.data.id == str(rule_id)
        assert get_res.data.option == "curved_steep_vedic"


@pytest.mark.asyncio
async def test_update_and_delete_palm_rule(mock_admin):
    rule_id = PydanticObjectId()
    dummy_rule = PalmRule(
        id=rule_id,
        feature=PalmFeature.LIFE_LINE.value,
        option="wide_sweeping_earth",
        label="Wide Earth Arc",
        meaning="Robust physical energy and strong ancestral connection.",
        conditions=[Condition(metric="life_line.arc_radius", min=0.6)],
    )

    # 1. Update rule wording & thresholds
    update_payload = PalmRuleUpdate(
        label="Updated Wide Earth Arc",
        meaning="Refined chirological interpretation for vitality.",
        conditions=[{"metric": "life_line.arc_radius", "min": 0.65}],
        reviewed=True,
    )

    with patch.object(PalmRule, "get", AsyncMock(return_value=dummy_rule)), \
         patch.object(PalmRule, "save", AsyncMock(return_value=dummy_rule)):
        update_res = await update_palm_rule(rule_id=rule_id, payload=update_payload, admin=mock_admin)
        assert update_res.data.label == "Updated Wide Earth Arc"
        assert update_res.data.reviewed is True

    # 2. Delete rule
    with patch.object(PalmRule, "get", AsyncMock(return_value=dummy_rule)), \
         patch.object(PalmRule, "delete", AsyncMock()):
        del_res = await delete_palm_rule(rule_id=rule_id, admin=mock_admin)
        assert del_res.data["deleted"] is True

    # 3. Not found handling
    with patch.object(PalmRule, "get", AsyncMock(return_value=None)):
        with pytest.raises(NotFoundError):
            await get_palm_rule(rule_id=rule_id, admin=mock_admin)
        with pytest.raises(NotFoundError):
            await update_palm_rule(rule_id=rule_id, payload=update_payload, admin=mock_admin)
        with pytest.raises(NotFoundError):
            await delete_palm_rule(rule_id=rule_id, admin=mock_admin)


@pytest.mark.asyncio
async def test_seed_palm_rules_endpoint(mock_admin):
    stats = {"created": 120, "updated": 0, "skipped": 0}
    with patch("app.services.palm_reading.seed_rules", AsyncMock(return_value=stats)):
        res = await seed_palm_rules(admin=mock_admin, force=False)
        assert res.data["created"] == 120
