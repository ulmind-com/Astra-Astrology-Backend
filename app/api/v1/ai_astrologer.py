"""Astra AI Astrologer API: Chat endpoints, voice transcription, custom rules & feedback."""

import uuid
from typing import Annotated

import httpx
from loguru import logger
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.api.dependencies import AdminUser, get_optional_user
from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError, UnauthorizedError
from app.models.ai_astrologer import (
    AIChatFeedback,
    AIChatSession,
    AICustomRule,
    AIKnowledgeDoc,
    ChatMessageItem,
)
from app.models.user import User
from app.schemas.ai_astrologer import (
    AIChatRequest,
    AIChatResponse,
    AICustomRuleCreateRequest,
    AICustomRuleUpdateRequest,
    AIFeedbackApproveRequest,
    AIFeedbackRequest,
)
from app.schemas.common import ApiResponse
from app.services.ai.groq_service import generate_astrology_response
from app.services.ai.knowledge_service import (
    approve_feedback_and_learn,
    save_user_feedback,
    seed_initial_knowledge_from_resources,
)

router = APIRouter(tags=["ai-astrologer"])



async def _resolve_birth_details(payload, user, session):
    """Work out which birth details this reading should use.

    Three sources, in order of how specific they are: what the session
    already holds, flat fields sent with this request, and finally the
    user's saved profile. Extracted so the streaming and non-streaming
    endpoints cannot disagree about whose chart is being read.
    """
    # If flat birth parameters were provided, parse them into birth_details
    effective_birth = session.birth_details
    if not effective_birth and payload.birth_date:
        try:
            parts = [p.strip() for p in payload.birth_date.replace("/", "-").split("-") if p.strip()]
            if len(parts) == 3:
                if len(parts[0]) == 4:
                    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                else:
                    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            else:
                day, month, year = 1, 1, 2000

            hour = 12
            minute = 0
            if payload.birth_time:
                t_parts = payload.birth_time.strip().split(":")
                if len(t_parts) >= 2:
                    hour = int(t_parts[0])
                    minute = int(t_parts[1])

            effective_birth = {
                "name": (user.full_name if user else "User") or "User",
                "gender": "male",
                "day": day,
                "month": month,
                "year": year,
                "hour": hour,
                "minute": minute,
                "place": payload.birth_place or "Kolkata",
                "lat": float(payload.latitude or 22.5726),
                "lon": float(payload.longitude or 88.3639),
            }
            session.birth_details = effective_birth
        except Exception:
            pass

    # If still no birth details passed, check if logged in user has birth profile saved
    if not effective_birth and user and user.profile:
        p = user.profile
        if p.birth_date:
            try:
                hour = p.birth_time.hour if p.birth_time else 12
                minute = p.birth_time.minute if p.birth_time else 0
                effective_birth = {
                    "name": user.full_name or "Native",
                    "gender": p.gender or "male",
                    "day": p.birth_date.day,
                    "month": p.birth_date.month,
                    "year": p.birth_date.year,
                    "hour": hour,
                    "minute": minute,
                    "place": p.birth_place or "Kolkata",
                    "lat": p.latitude or 22.5726,
                    "lon": p.longitude or 88.3639,
                }
                session.birth_details = effective_birth
            except Exception:
                pass

    return effective_birth


@router.post("/ai-astrologer/chat", response_model=ApiResponse[AIChatResponse])
@router.post("/ai-chat/message", response_model=ApiResponse[AIChatResponse])
async def send_ai_chat_message(
    payload: AIChatRequest,
    user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> ApiResponse[AIChatResponse]:
    """Sends a question to Astra AI Astrologer and receives a 100% verified Vedic response."""
    session_id = payload.session_id or str(uuid.uuid4())

    # Find or create session
    session = await AIChatSession.find_one(AIChatSession.session_id == session_id)
    if not session:
        session = AIChatSession(
            session_id=session_id,
            user_id=user.id if user else None,
            title=(payload.message[:35] + "...") if len(payload.message) > 35 else payload.message,
            birth_details=payload.birth_details.model_dump() if payload.birth_details else None,
            messages=[],
        )
        await session.insert()
    else:
        if payload.birth_details:
            session.birth_details = payload.birth_details.model_dump()
        if user and not session.user_id:
            session.user_id = user.id

    effective_birth = await _resolve_birth_details(payload, user, session)

    # Append user message
    user_msg_item = ChatMessageItem(role="user", content=payload.message)
    session.messages.append(user_msg_item)

    # Prepare message history for reasoning engine (last 8 messages for context)
    history_to_send = [
        {"role": m.role, "content": m.content}
        for m in session.messages[-8:]
    ]

    # Generate AI synthesis via Groq + Swiss Ephemeris
    result = await generate_astrology_response(
        messages=history_to_send,
        user_id=user.id if user else None,
        user_birth_details=effective_birth,
        preferred_language=payload.preferred_language or "bn",
    )

    # Convert citations for chat message item storage
    stored_citations = [
        c["source"] if isinstance(c, dict) and "source" in c else str(c)
        for c in result.get("citations", [])
    ]

    # Append assistant response
    assistant_msg_item = ChatMessageItem(
        role="assistant",
        content=result["reply"],
        citations=stored_citations,
        tools_called=result["tools_called"],
        suggested_followups=result["suggested_followups"],
    )
    session.messages.append(assistant_msg_item)
    await session.save()

    return ApiResponse(
        data=AIChatResponse(
            session_id=session.session_id,
            reply=result["reply"],
            language=payload.preferred_language or "bn",
            tools_called=result["tools_called"],
            citations=result["citations"],
            suggested_followups=result["suggested_followups"],
        )
    )



@router.post(
    "/ai-astrologer/chat/stream",
    summary="Ask the astrologer and receive the reply as it is written",
)
async def stream_ai_chat_message(
    payload: AIChatRequest,
    user: Annotated[User | None, Depends(get_optional_user)] = None,
):
    """The same conversation as `/chat`, delivered as server-sent events.

    Waiting ten seconds at an empty bubble is most of what makes an assistant
    feel like a form rather than a person. The answer is identical; it simply
    arrives as it is written, with a line of status while the chart is being
    read so the pause is explained rather than blank.

    The session is saved once, when the stream finishes. A reader who closes
    the tab halfway leaves no half-written reply in their history.
    """
    import json as _json

    from fastapi.responses import StreamingResponse

    from app.services.ai.groq_service import stream_astrology_response

    session_id = payload.session_id or str(uuid.uuid4())
    session = await AIChatSession.find_one(AIChatSession.session_id == session_id)
    if not session:
        session = AIChatSession(
            session_id=session_id,
            user_id=user.id if user else None,
            title=(payload.message[:35] + "...") if len(payload.message) > 35 else payload.message,
            birth_details=payload.birth_details.model_dump() if payload.birth_details else None,
            messages=[],
        )
        await session.insert()

    effective_birth = await _resolve_birth_details(payload, user, session)

    session.messages.append(ChatMessageItem(role="user", content=payload.message))
    history_to_send = [{"role": m.role, "content": m.content} for m in session.messages[-8:]]

    async def events():
        final: dict | None = None
        try:
            async for event in stream_astrology_response(
                messages=history_to_send,
                user_birth_details=effective_birth,
                preferred_language=payload.preferred_language or "bn",
                user_id=user.id if user else None,
            ):
                if event.get("type") == "done":
                    final = event
                payload_out = dict(event)
                payload_out["session_id"] = session.session_id
                yield f"data: {_json.dumps(payload_out, ensure_ascii=False)}\n\n"
        except Exception as exc:  # noqa: BLE001 - the reader must not get a dead stream
            logger.exception("AI stream failed")
            yield (
                "data: "
                + _json.dumps(
                    {
                        "type": "error",
                        "message": "Something went wrong while answering. Please try again.",
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )

        if final and final.get("reply"):
            try:
                session.messages.append(
                    ChatMessageItem(
                        role="assistant",
                        content=final["reply"],
                        citations=[
                            c["source"] if isinstance(c, dict) and "source" in c else str(c)
                            for c in final.get("citations", [])
                        ],
                        tools_called=final.get("tools_called", []),
                        suggested_followups=final.get("suggested_followups", []),
                    )
                )
                await session.save()
            except Exception:  # noqa: BLE001 - the answer was delivered either way
                logger.exception("Could not save the streamed session")

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Nginx buffers proxied responses by default, which would hold the
            # whole stream back and deliver it as one lump — the exact problem
            # this endpoint exists to solve.
            "X-Accel-Buffering": "no",
        },
    )

@router.get("/ai-astrologer/session/{session_id}", response_model=ApiResponse[dict])
@router.get("/ai-chat/session/{session_id}", response_model=ApiResponse[dict])
async def get_ai_chat_session(session_id: str) -> ApiResponse[dict]:
    """Retrieves conversation history for a given session."""
    session = await AIChatSession.find_one(AIChatSession.session_id == session_id)
    if not session:
        raise NotFoundError("Session not found", error_code="session_not_found")

    return ApiResponse(
        data={
            "session_id": session.session_id,
            "title": session.title,
            "birth_details": session.birth_details,
            "messages": [m.model_dump() for m in session.messages],
            "updated_at": session.updated_at,
        }
    )


@router.get("/ai-astrologer/sessions", response_model=ApiResponse[list[dict]])
@router.get("/ai-chat/sessions", response_model=ApiResponse[list[dict]])
async def list_user_ai_sessions(
    user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> ApiResponse[list[dict]]:
    """Lists past AI sessions for the authenticated user."""
    if not user:
        return ApiResponse(data=[])

    sessions = (
        await AIChatSession.find(AIChatSession.user_id == user.id)
        .sort(-AIChatSession.updated_at)
        .limit(20)
        .to_list()
    )

    return ApiResponse(
        data=[
            {
                "session_id": s.session_id,
                "title": s.title,
                "message_count": len(s.messages),
                "updated_at": s.updated_at,
            }
            for s in sessions
        ]
    )


@router.delete("/ai-astrologer/session/{session_id}", response_model=ApiResponse[dict])
@router.delete("/ai-chat/session/{session_id}", response_model=ApiResponse[dict])
async def delete_ai_chat_session(session_id: str) -> ApiResponse[dict]:
    """Deletes an AI chat session."""
    session = await AIChatSession.find_one(AIChatSession.session_id == session_id)
    if session:
        await session.delete()
    return ApiResponse(data={"deleted": True})


@router.post("/ai-astrologer/feedback", response_model=ApiResponse[dict])
@router.post("/ai-chat/feedback", response_model=ApiResponse[dict])
async def submit_ai_feedback(payload: AIFeedbackRequest) -> ApiResponse[dict]:
    """Submits thumbs up or thumbs down feedback for continuous self-learning."""
    session = await AIChatSession.find_one(AIChatSession.session_id == payload.session_id)
    user_query = payload.user_query or ""
    ai_response = payload.ai_response or ""

    if session and len(session.messages) > payload.message_index:
        msg = session.messages[payload.message_index]
        if not ai_response:
            ai_response = msg.content
        if payload.message_index > 0 and not user_query:
            user_query = session.messages[payload.message_index - 1].content

    feedback = await save_user_feedback(
        session_id=payload.session_id,
        message_index=payload.message_index,
        user_query=user_query,
        ai_response=ai_response,
        rating=payload.rating,
        feedback_reason=payload.feedback_reason,
    )

    return ApiResponse(data={"feedback_id": str(feedback.id), "status": "recorded"})


@router.post("/ai-chat/voice-transcribe", response_model=ApiResponse[dict])
async def transcribe_voice_message(file: UploadFile = File(...)) -> ApiResponse[dict]:
    """Transcribes user speech (Bengali / English / Hindi) to text using Groq Whisper Large v3 Turbo."""
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured")

    contents = await file.read()
    files = {"file": (file.filename or "audio.webm", contents, file.content_type or "audio/webm")}
    data = {
        "model": "whisper-large-v3-turbo",
        "temperature": "0.0",
        "response_format": "json",
    }
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers=headers,
            files=files,
            data=data,
        )
        resp.raise_for_status()
        res_data = resp.json()

    return ApiResponse(data={"text": res_data.get("text", "").strip()})


# -----------------------------------------------------------------------------
# Admin Management Endpoints
# -----------------------------------------------------------------------------


@router.get("/admin/ai/knowledge", response_model=ApiResponse[dict])
async def list_admin_knowledge(
    admin: AdminUser,
    category: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
) -> ApiResponse[dict]:
    """Lists knowledge documents indexed in the database."""
    query = {}
    if category:
        query["category"] = category

    total = await AIKnowledgeDoc.find(query).count()
    docs = (
        await AIKnowledgeDoc.find(query)
        .sort(-AIKnowledgeDoc.created_at)
        .skip(skip)
        .limit(limit)
        .to_list()
    )

    return ApiResponse(
        data={
            "total": total,
            "docs": [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "category": d.category,
                    "source_file": d.source_file,
                    "snippet": d.content[:180] + "...",
                    "created_at": d.created_at,
                }
                for d in docs
            ],
        }
    )


@router.post("/admin/ai/knowledge/seed", response_model=ApiResponse[dict])
async def trigger_knowledge_seed(admin: AdminUser) -> ApiResponse[dict]:
    """Seeds classical scriptures and client resource documents into MongoDB."""
    count = await seed_initial_knowledge_from_resources()
    return ApiResponse(data={"seeded_count": count})


@router.get("/admin/ai/rules", response_model=ApiResponse[list[dict]])
async def list_custom_rules(admin: AdminUser) -> ApiResponse[list[dict]]:
    """Lists all custom Q&A rules."""
    rules = await AICustomRule.find().sort(-AICustomRule.priority).to_list()
    return ApiResponse(
        data=[
            {
                "id": str(r.id),
                "rule_title": r.rule_title,
                "trigger_keywords": r.trigger_keywords,
                "category": r.category,
                "response_bn": r.response_bn,
                "remedy_bn": r.remedy_bn,
                "priority": r.priority,
                "is_active": r.is_active,
                "created_at": r.created_at,
            }
            for r in rules
        ]
    )


@router.post("/admin/ai/rules", response_model=ApiResponse[dict])
async def create_custom_rule(
    payload: AICustomRuleCreateRequest,
    admin: AdminUser,
) -> ApiResponse[dict]:
    """Creates a new custom rule or verified astrological remedy."""
    rule = AICustomRule(
        rule_title=payload.rule_title,
        trigger_keywords=payload.trigger_keywords,
        category=payload.category,
        response_bn=payload.response_bn,
        response_en=payload.response_en,
        remedy_bn=payload.remedy_bn,
        priority=payload.priority,
        is_active=True,
    )
    await rule.insert()
    return ApiResponse(data={"rule_id": str(rule.id), "status": "created"})


@router.patch("/admin/ai/rules/{rule_id}", response_model=ApiResponse[dict])
@router.put("/admin/ai/rules/{rule_id}", response_model=ApiResponse[dict])
async def update_custom_rule(
    rule_id: str,
    payload: AICustomRuleUpdateRequest,
    admin: AdminUser,
) -> ApiResponse[dict]:
    """Updates an existing custom rule."""
    rule = await AICustomRule.get(PydanticObjectId(rule_id))
    if not rule:
        raise NotFoundError("Rule not found", error_code="rule_not_found")

    if payload.rule_title is not None:
        rule.rule_title = payload.rule_title
    if payload.trigger_keywords is not None:
        rule.trigger_keywords = payload.trigger_keywords
    if payload.category is not None:
        rule.category = payload.category
    if payload.response_bn is not None:
        rule.response_bn = payload.response_bn
    if payload.remedy_bn is not None:
        rule.remedy_bn = payload.remedy_bn
    if payload.priority is not None:
        rule.priority = payload.priority
    if payload.is_active is not None:
        rule.is_active = payload.is_active

    await rule.save()
    return ApiResponse(data={"rule_id": str(rule.id), "status": "updated"})


@router.delete("/admin/ai/rules/{rule_id}", response_model=ApiResponse[dict])
async def delete_custom_rule(rule_id: str, admin: AdminUser) -> ApiResponse[dict]:
    """Deletes a custom rule."""
    rule = await AICustomRule.get(PydanticObjectId(rule_id))
    if rule:
        await rule.delete()
    return ApiResponse(data={"deleted": True})


@router.get("/admin/ai/feedback", response_model=ApiResponse[list[dict]])
async def list_flagged_feedback(
    admin: AdminUser,
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[list[dict]]:
    """Lists user feedback (especially thumbs-down) for human-in-the-loop review and learning."""
    feedbacks = (
        await AIChatFeedback.find(AIChatFeedback.rating == -1)
        .sort(-AIChatFeedback.created_at)
        .limit(limit)
        .to_list()
    )

    return ApiResponse(
        data=[
            {
                "id": str(f.id),
                "session_id": f.session_id,
                "user_query": f.user_query,
                "ai_response": f.ai_response,
                "rating": f.rating,
                "feedback_reason": f.feedback_reason,
                "reviewed_by_admin": f.reviewed_by_admin,
                "admin_corrected_response": f.admin_corrected_response,
                "added_to_knowledge": f.added_to_knowledge,
                "created_at": f.created_at,
            }
            for f in feedbacks
        ]
    )


@router.post("/admin/ai/feedback/{feedback_id}/approve", response_model=ApiResponse[dict])
async def approve_and_learn_feedback(
    feedback_id: str,
    payload: AIFeedbackApproveRequest,
    admin: AdminUser,
) -> ApiResponse[dict]:
    """Admin corrects an AI response and permanently adds it as a learned custom rule."""
    rule = await approve_feedback_and_learn(
        feedback_id=feedback_id,
        admin_corrected_response=payload.admin_corrected_response,
        rule_title=payload.rule_title,
        keywords=payload.keywords,
    )
    return ApiResponse(data={"rule_id": str(rule.id), "status": "learned"})


@router.post(
    "/ai-astrologer/transcribe",
    response_model=ApiResponse[dict],
    summary="Turn a spoken question into text",
)
async def transcribe_audio(
    file: Annotated[UploadFile, File(description="A short audio clip")],
    user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> ApiResponse[dict]:
    """Transcribe a recording so it can be sent as a chat message.

    Separate from the chat endpoint on purpose: the browser holds the audio and
    the text, the user gets to see what was heard before it is sent, and a
    mis-heard word can be corrected rather than silently answered.

    Open to signed-out visitors, like the chat itself. Whisper is metered in
    audio-seconds on its own budget, so this costs nothing that the readings
    compete for.
    """
    from app.services.ai import speech

    audio = await file.read()
    if len(audio) > speech.MAX_BYTES:
        raise BadRequestError(
            "That recording is too long. Please keep it under two minutes.",
            error_code="audio_too_large",
        )

    try:
        text = await speech.transcribe(audio, file.filename or "audio.webm")
    except speech.SpeechError as exc:
        raise BadRequestError(str(exc), error_code="transcription_failed") from exc

    return ApiResponse(message="Transcribed.", data={"text": text})


@router.delete(
    "/ai-astrologer/memory",
    response_model=ApiResponse[dict],
    summary="Forget everything the assistant remembers about me",
)
async def forget_memory(
    user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> ApiResponse[dict]:
    """Erase this user's remembered facts.

    Exists because people are entitled to ask, and because an assistant that
    cannot forget is one they stop telling things to.
    """
    from app.services.ai import memory as ai_memory

    if user is None:
        raise UnauthorizedError("Sign in to manage what is remembered about you.")
    cleared = await ai_memory.forget(user.id)
    return ApiResponse(
        message="Forgotten." if cleared else "There was nothing remembered.",
        data={"cleared": cleared},
    )
