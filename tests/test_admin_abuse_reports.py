"""Unit tests for the admin AbuseReports trust & safety dashboard endpoints."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from beanie import PydanticObjectId, init_beanie

from app.api.v1.admin_abuse_reports import (
    abuse_report_stats,
    get_abuse_report,
    list_abuse_reports,
    review_abuse_report,
    unblock_client_from_report,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.abuse_report import AbuseReport
from app.models.astrologer import Astrologer
from app.models.user import User
from app.schemas.abuse_report import (
    AbuseReportReviewRequest,
    AbuseReportUnblockRequest,
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
            AbuseReport,
            Astrologer,
            User,
        ],
    )


def _admin_user() -> SimpleNamespace:
    return SimpleNamespace(id=PydanticObjectId(), role="admin", email="admin@astra.com")


def _make_report(
    rid: str | None = None,
    status: str = "pending",
    action_taken: str = "blacklisted",
    created_at: datetime | None = None,
) -> SimpleNamespace:
    rid = rid or PydanticObjectId()
    return SimpleNamespace(
        id=rid,
        astrologer_id=PydanticObjectId(),
        astrologer_user_id=PydanticObjectId(),
        client_user_id=PydanticObjectId(),
        appointment_id=PydanticObjectId(),
        call_id=PydanticObjectId(),
        reason="Abusive language during consultation",
        notes="Client used profanity",
        action_taken=action_taken,
        status=status,
        reviewed_by=None,
        reviewed_at=None,
        admin_notes=None,
        created_at=created_at or datetime.now(UTC),
        updated_at=datetime.now(UTC),
        save=AsyncMock(),
    )


async def test_list_abuse_reports_returns_paginated_items():
    admin = _admin_user()
    report = _make_report()
    astro_profile = SimpleNamespace(
        id=report.astrologer_id,
        user_id=PydanticObjectId(),
        display_name="Pandit Sharma",
    )
    astro_user = SimpleNamespace(id=astro_profile.user_id, email="pandit@astra.com")
    client_user = SimpleNamespace(
        id=report.client_user_id, full_name="Rahul Roy", email="rahul@example.com"
    )
    mock_query = MagicMock()
    mock_query.count = AsyncMock(return_value=1)
    mock_query.sort.return_value.skip.return_value.limit.return_value.to_list = AsyncMock(
        return_value=[report]
    )
    astros_find = MagicMock()
    astros_find.to_list = AsyncMock(return_value=[astro_profile])
    users_find = MagicMock()
    users_find.to_list = AsyncMock(return_value=[astro_user, client_user])
    with patch.object(AbuseReport, "find", return_value=mock_query), patch.object(
        AbuseReport, "find_all", return_value=mock_query
    ), patch.object(Astrologer, "find", return_value=astros_find), patch.object(
        User, "find", return_value=users_find
    ):
        result = await list_abuse_reports(admin=admin, page=1, limit=20)
    assert result.success is True
    assert result.data is not None
    assert len(result.data.items) == 1
    item = result.data.items[0]
    assert item.astrologer_name == "Pandit Sharma"
    assert item.client_name == "Rahul Roy"
    assert item.client_email_masked == "rah***@example.com"
    assert item.status == "pending"
    assert result.data.meta["total"] == 1


async def test_get_abuse_report_returns_full_detail():
    admin = _admin_user()
    report = _make_report()
    astro_profile = SimpleNamespace(
        id=report.astrologer_id,
        user_id=PydanticObjectId(),
        display_name="Pandit Sharma",
    )
    astro_user = SimpleNamespace(id=astro_profile.user_id, email="pandit@astra.com")
    client_user = SimpleNamespace(
        id=report.client_user_id, full_name="Rahul Roy", email="rahul@example.com"
    )
    with patch.object(AbuseReport, "get", AsyncMock(return_value=report)), patch.object(
        Astrologer, "get", AsyncMock(return_value=astro_profile)
    ), patch.object(User, "get", AsyncMock(side_effect=[astro_user, client_user])):
        result = await get_abuse_report(report_id=str(report.id), admin=admin)
    assert result.success is True
    data = result.data
    assert data.id == str(report.id)
    assert data.astrologer_name == "Pandit Sharma"
    assert data.client_name == "Rahul Roy"
    assert data.client_email_masked == "rah***@example.com"
    assert data.status == "pending"


async def test_get_abuse_report_not_found():
    admin = _admin_user()
    with patch.object(AbuseReport, "get", AsyncMock(return_value=None)):
        with pytest.raises(NotFoundError) as exc_info:
            await get_abuse_report(report_id=str(PydanticObjectId()), admin=admin)
    assert exc_info.value.error_code == "abuse_report_not_found"


async def test_get_abuse_report_invalid_id():
    admin = _admin_user()
    with pytest.raises(NotFoundError) as exc_info:
        await get_abuse_report(report_id="not-a-valid-id", admin=admin)
    assert exc_info.value.error_code == "abuse_report_not_found"


async def test_review_abuse_report_changes_status():
    admin = _admin_user()
    report = _make_report(status="pending")
    with patch.object(AbuseReport, "get", AsyncMock(return_value=report)), \
         patch("app.api.v1.admin_abuse_reports._load_astrologer_name", AsyncMock(return_value=("Pandit Sharma", "pandit@astra.com"))), \
         patch("app.api.v1.admin_abuse_reports._load_user_name", AsyncMock(return_value=("Rahul Roy", "rahul@example.com"))):
        payload = AbuseReportReviewRequest(
            status="resolved", admin_notes="Investigated, found valid."
        )
        result = await review_abuse_report(
            report_id=str(report.id), payload=payload, admin=admin
        )
    assert result.success is True
    assert report.status == "resolved"
    assert report.reviewed_by == admin.id
    assert report.reviewed_at is not None
    assert report.admin_notes == "Investigated, found valid."
    assert result.data.status == "resolved"


async def test_review_abuse_report_invalid_status():
    admin = _admin_user()
    report = _make_report()
    with patch.object(AbuseReport, "get", AsyncMock(return_value=report)):
        payload = AbuseReportReviewRequest(status="invalid_status")
        with pytest.raises(BadRequestError) as exc_info:
            await review_abuse_report(
                report_id=str(report.id), payload=payload, admin=admin
            )
    assert exc_info.value.error_code == "invalid_status"


async def test_unblock_client_from_report():
    admin = _admin_user()
    report = _make_report()
    astro = SimpleNamespace(
        id=report.astrologer_id,
        blacklisted_user_ids=[report.client_user_id],
        save=AsyncMock(),
    )
    with patch.object(AbuseReport, "get", AsyncMock(return_value=report)), patch.object(
        Astrologer, "get", AsyncMock(return_value=astro)
    ):
        payload = AbuseReportUnblockRequest(client_user_id=str(report.client_user_id))
        result = await unblock_client_from_report(
            report_id=str(report.id), payload=payload, admin=admin
        )
    assert result.success is True
    assert result.data.unblocked is True
    assert report.client_user_id not in astro.blacklisted_user_ids
    astro.save.assert_awaited_once()


async def test_unblock_client_wrong_client_forbidden():
    admin = _admin_user()
    report = _make_report()
    other_client_id = PydanticObjectId()
    with patch.object(AbuseReport, "get", AsyncMock(return_value=report)):
        payload = AbuseReportUnblockRequest(client_user_id=str(other_client_id))
        with pytest.raises(ForbiddenError) as exc_info:
            await unblock_client_from_report(
                report_id=str(report.id), payload=payload, admin=admin
            )
    assert exc_info.value.error_code == "client_not_in_report"


async def test_abuse_report_stats_returns_aggregates():
    admin = _admin_user()
    mock_find_all = MagicMock()
    mock_find_all.count = AsyncMock(return_value=10)
    mock_find_pending = MagicMock()
    mock_find_pending.count = AsyncMock(return_value=3)
    mock_find_resolved = MagicMock()
    mock_find_resolved.count = AsyncMock(return_value=5)
    mock_find_dismissed = MagicMock()
    mock_find_dismissed.count = AsyncMock(return_value=2)
    mock_find_reviewed = MagicMock()
    mock_find_reviewed.count = AsyncMock(return_value=0)
    call_count = {"n": 0}

    def find_side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return mock_find_pending
        if call_count["n"] == 2:
            return mock_find_reviewed
        if call_count["n"] == 3:
            return mock_find_resolved
        if call_count["n"] == 4:
            return mock_find_dismissed
        return mock_find_all

    with patch.object(AbuseReport, "find_all", return_value=mock_find_all), patch.object(
        AbuseReport, "find", side_effect=find_side_effect
    ), patch.object(
        AbuseReport, "aggregate", return_value=MagicMock(to_list=AsyncMock(return_value=[]))
    ):
        result = await abuse_report_stats(admin=admin)
    assert result.success is True
    data = result.data
    assert data.total_reports == 10
    assert data.pending_reports == 3
    assert data.resolved_reports == 5
    assert data.dismissed_reports == 2


async def test_unblock_client_not_on_blacklist():
    admin = _admin_user()
    report = _make_report()
    astro = SimpleNamespace(
        id=report.astrologer_id,
        blacklisted_user_ids=[],
        save=AsyncMock(),
    )
    with patch.object(AbuseReport, "get", AsyncMock(return_value=report)), patch.object(
        Astrologer, "get", AsyncMock(return_value=astro)
    ):
        payload = AbuseReportUnblockRequest(client_user_id=str(report.client_user_id))
        result = await unblock_client_from_report(
            report_id=str(report.id), payload=payload, admin=admin
        )
    assert result.success is True
    assert result.data.unblocked is False
