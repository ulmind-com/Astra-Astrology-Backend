"""Sessions that outlive a day, and a gate that says what it means.

Both halves of one bug. The access token lasts a day, nothing could renew it,
and the course routes answered an expired token as though nobody were signed
in — so a student who had paid for a course was told to enroll in it.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.course import Course, CourseEnrollment, CourseLesson, CourseSection
from app.models.user import User
from tests.test_calls import signed_in

P = "/api/v1"
pytestmark = pytest.mark.usefixtures("fake_firebase")


async def _user_for(headers: dict) -> User:
    from beanie import PydanticObjectId

    token = headers["Authorization"].removeprefix("Bearer ")
    user = await User.get(PydanticObjectId(decode_token(token)["sub"]))
    assert user is not None
    return user


async def _course_with_lesson(*, free_preview: bool = False):
    """A published paid course with one section and one lesson."""
    course = await Course(
        title="Paid Masterclass",
        slug=f"paid-masterclass-{datetime.now(UTC).timestamp()}",
        price=1999.0,
        mrp=4999.0,
    ).insert()
    section = await CourseSection(course_id=course.id, title="Module 1", order=1).insert()
    lesson = await CourseLesson(
        course_id=course.id,
        section_id=section.id,
        title="Lesson 1",
        order=1,
        video_provider="youtube_unlisted",
        video_id="abc123",
        is_free_preview=free_preview,
    ).insert()
    return course, lesson


# ------------------------------------------------------------------ refresh
async def test_a_refresh_token_buys_a_new_pair(client: AsyncClient) -> None:
    headers = await signed_in(client, "refresh1@test.dev")
    user = await _user_for(headers)
    refresh, _ = create_refresh_token(str(user.id))

    resp = await client.post(f"{P}/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200, resp.text
    tokens = resp.json()["data"]

    assert tokens["access_token"] and tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"
    # The new access token really works.
    me = await client.get(
        f"{P}/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 200, me.text
    assert me.json()["data"]["email"] == "refresh1@test.dev"


async def test_the_refresh_token_is_rotated(client: AsyncClient) -> None:
    """A new refresh token comes back, so a long-running session keeps going."""
    headers = await signed_in(client, "refresh2@test.dev")
    user = await _user_for(headers)
    first, _ = create_refresh_token(str(user.id))

    resp = await client.post(f"{P}/auth/refresh", json={"refresh_token": first})
    second = resp.json()["data"]["refresh_token"]
    assert second != first

    again = await client.post(f"{P}/auth/refresh", json={"refresh_token": second})
    assert again.status_code == 200, again.text


async def test_an_access_token_cannot_be_used_to_refresh(client: AsyncClient) -> None:
    """Otherwise a stolen access token would renew itself forever."""
    headers = await signed_in(client, "refresh3@test.dev")
    user = await _user_for(headers)
    access, _ = create_access_token(str(user.id))

    resp = await client.post(f"{P}/auth/refresh", json={"refresh_token": access})
    assert resp.status_code == 401, resp.text
    assert resp.json()["error_code"] == "invalid_token_type"


async def test_an_expired_refresh_token_is_refused(client: AsyncClient) -> None:
    import jwt

    from app.core.config import settings as app_settings

    headers = await signed_in(client, "refresh4@test.dev")
    user = await _user_for(headers)
    expired = jwt.encode(
        {
            "sub": str(user.id),
            "type": "refresh",
            "exp": int((datetime.now(UTC) - timedelta(days=1)).timestamp()),
        },
        app_settings.JWT_SECRET_KEY,
        algorithm=app_settings.JWT_ALGORITHM,
    )

    resp = await client.post(f"{P}/auth/refresh", json={"refresh_token": expired})
    assert resp.status_code == 401, resp.text
    assert resp.json()["error_code"] == "token_expired"


async def test_a_forged_refresh_token_is_refused(client: AsyncClient) -> None:
    resp = await client.post(f"{P}/auth/refresh", json={"refresh_token": "a.b.cdefghij"})
    assert resp.status_code == 401, resp.text
    assert resp.json()["error_code"] == "invalid_token"


async def test_a_suspended_account_cannot_refresh_its_way_back_in(
    client: AsyncClient,
) -> None:
    from app.models.enums import AccountStatus

    headers = await signed_in(client, "refresh5@test.dev")
    user = await _user_for(headers)
    refresh, _ = create_refresh_token(str(user.id))

    user.status = AccountStatus.SUSPENDED
    await user.save()

    resp = await client.post(f"{P}/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 403, resp.text
    assert resp.json()["error_code"] == "account_suspended"


# -------------------------------------------------------------- the gate
async def test_an_expired_session_is_401_not_a_lecture_about_enrolling(
    client: AsyncClient,
) -> None:
    """The bug, in one test.

    An enrolled student whose access token expired used to be told to enroll
    in the course they had already paid for. It must now read as what it is:
    a session that ended.
    """
    import jwt

    from app.core.config import settings as app_settings

    headers = await signed_in(client, "student1@test.dev")
    user = await _user_for(headers)
    course, lesson = await _course_with_lesson()
    await CourseEnrollment(
        user_id=user.id, course_id=course.id, amount_paid=1999.0, payment_id="pay_x"
    ).insert()

    # Live token: the lesson plays.
    ok = await client.get(
        f"{P}/courses/{course.id}/lessons/{lesson.id}/stream", headers=headers
    )
    assert ok.status_code == 200, ok.text

    expired = jwt.encode(
        {
            "sub": str(user.id),
            "type": "access",
            "exp": int((datetime.now(UTC) - timedelta(hours=1)).timestamp()),
        },
        app_settings.JWT_SECRET_KEY,
        algorithm=app_settings.JWT_ALGORITHM,
    )
    stale = await client.get(
        f"{P}/courses/{course.id}/lessons/{lesson.id}/stream",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert stale.status_code == 401, stale.text
    assert stale.json()["error_code"] == "token_expired"
    assert "enroll" not in stale.json()["message"].lower()


async def test_a_visitor_with_no_token_is_asked_to_sign_in(client: AsyncClient) -> None:
    course, lesson = await _course_with_lesson()
    resp = await client.get(f"{P}/courses/{course.id}/lessons/{lesson.id}/stream")
    assert resp.status_code == 401, resp.text
    assert resp.json()["error_code"] == "sign_in_required"


async def test_a_signed_in_stranger_is_told_to_enroll(client: AsyncClient) -> None:
    """The one case where "you must enroll" is the truth."""
    headers = await signed_in(client, "stranger@test.dev")
    course, lesson = await _course_with_lesson()

    resp = await client.get(
        f"{P}/courses/{course.id}/lessons/{lesson.id}/stream", headers=headers
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["error_code"] == "not_enrolled"
    assert "enroll" in resp.json()["message"].lower()


async def test_a_free_preview_still_opens_for_anyone(client: AsyncClient) -> None:
    """Signed out, no token: the sample lesson must keep working."""
    course, lesson = await _course_with_lesson(free_preview=True)
    resp = await client.get(f"{P}/courses/{course.id}/lessons/{lesson.id}/stream")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["embed_url"]


async def test_the_course_pages_still_open_for_a_signed_out_visitor(
    client: AsyncClient,
) -> None:
    """The catalogue is marketing. No token must mean anonymous, not an error."""
    course, _ = await _course_with_lesson()

    listing = await client.get(f"{P}/courses")
    assert listing.status_code == 200, listing.text

    detail = await client.get(f"{P}/courses/detail/{course.slug}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"]["is_enrolled"] is False


async def test_a_stale_token_on_the_catalogue_is_401_so_the_client_can_refresh(
    client: AsyncClient,
) -> None:
    """It used to answer 200-as-anonymous, which hid the dead session."""
    import jwt

    from app.core.config import settings as app_settings

    headers = await signed_in(client, "student2@test.dev")
    user = await _user_for(headers)
    await _course_with_lesson()

    expired = jwt.encode(
        {
            "sub": str(user.id),
            "type": "access",
            "exp": int((datetime.now(UTC) - timedelta(hours=1)).timestamp()),
        },
        app_settings.JWT_SECRET_KEY,
        algorithm=app_settings.JWT_ALGORITHM,
    )
    stale = {"Authorization": f"Bearer {expired}"}

    assert (await client.get(f"{P}/courses", headers=stale)).status_code == 401
    assert (
        await client.get(f"{P}/courses/detail/nonexistent-slug", headers=stale)
    ).status_code == 401


async def test_a_suspended_student_is_told_why(client: AsyncClient) -> None:
    from app.models.enums import AccountStatus

    headers = await signed_in(client, "student3@test.dev")
    user = await _user_for(headers)
    course, lesson = await _course_with_lesson()
    await CourseEnrollment(user_id=user.id, course_id=course.id).insert()

    user.status = AccountStatus.SUSPENDED
    await user.save()

    resp = await client.get(
        f"{P}/courses/{course.id}/lessons/{lesson.id}/stream", headers=headers
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["error_code"] == "account_not_active"
    assert "enroll" not in resp.json()["message"].lower()


# ------------------------------------------------------- the signed embed
async def test_the_signed_video_url_outlasts_a_long_sitting(
    client: AsyncClient,
) -> None:
    """Bunny serves its own 403 page the moment the token expires.

    It arrives as HTTP 200 with a 403 page inside the player, so it never
    showed up in our logs — students just saw "403" on a course they had
    paid for. The URL has to outlast a long lesson with pauses.
    """
    from app.core.config import settings as app_settings

    headers = await signed_in(client, "watcher@test.dev")
    user = await _user_for(headers)
    course, lesson = await _course_with_lesson()
    lesson.video_provider = "bunny_stream"
    lesson.video_id = "9781fca4-8d13-4c04-b6ef-946db6fd2ade"
    lesson.library_id = app_settings.BUNNY_STREAM_LIBRARY_ID
    await lesson.save()
    await CourseEnrollment(user_id=user.id, course_id=course.id).insert()

    resp = await client.get(
        f"{P}/courses/{course.id}/lessons/{lesson.id}/stream", headers=headers
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]

    remaining = data["expires_at"] - int(datetime.now(UTC).timestamp())
    assert remaining > 6 * 3600, (
        f"the signed URL dies in {remaining / 3600:.1f}h — long enough for a "
        "student to be shown Bunny's 403 mid-course"
    )


async def test_the_signed_url_carries_a_token_bunny_can_check(
    client: AsyncClient,
) -> None:
    """The token is what Bunny validates; an unsigned URL is simply refused."""
    import hashlib

    from app.core.config import settings as app_settings

    headers = await signed_in(client, "watcher2@test.dev")
    user = await _user_for(headers)
    course, lesson = await _course_with_lesson()
    lesson.video_provider = "bunny_stream"
    lesson.video_id = "9781fca4-8d13-4c04-b6ef-946db6fd2ade"
    lesson.library_id = app_settings.BUNNY_STREAM_LIBRARY_ID
    await lesson.save()
    await CourseEnrollment(user_id=user.id, course_id=course.id).insert()

    data = (
        await client.get(
            f"{P}/courses/{course.id}/lessons/{lesson.id}/stream", headers=headers
        )
    ).json()["data"]

    if not app_settings.BUNNY_STREAM_TOKEN_KEY:
        pytest.skip("No Bunny token key configured in this environment")

    expected = hashlib.sha256(
        f"{app_settings.BUNNY_STREAM_TOKEN_KEY}"
        f"{lesson.video_id}"
        f"{data['expires_at']}".encode()
    ).hexdigest()
    assert data["token"] == expected
    assert f"token={expected}" in data["embed_url"]
    assert f"expires={data['expires_at']}" in data["embed_url"]
