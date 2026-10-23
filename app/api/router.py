"""Mounts every v1 router under a single API router."""

from fastapi import APIRouter

from app.api.v1 import (
    admin_astrologers,
    admin_settings,
    admin_wallets,
    appointments,
    astrologers,
    astrology,
    auth,
    calls,
    chats,
    earnings,
    face_reading,
    palm_reading,
    health,
    reviews,
    users,
    wallet,
    ws,
)

api_router = APIRouter()

api_router.include_router(ws.router)
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(astrologers.router)
api_router.include_router(appointments.router)
api_router.include_router(astrology.router)
api_router.include_router(admin_astrologers.router)
api_router.include_router(wallet.router)
api_router.include_router(admin_wallets.router)
api_router.include_router(admin_settings.router)
api_router.include_router(calls.router)
api_router.include_router(calls.maintenance_router)
api_router.include_router(calls.webhook_router)
api_router.include_router(chats.router)
api_router.include_router(chats.maintenance_router)
api_router.include_router(astrologers.maintenance_router)
api_router.include_router(face_reading.router)
api_router.include_router(face_reading.admin_router)
api_router.include_router(palm_reading.router)
api_router.include_router(reviews.router)
api_router.include_router(reviews.admin_router)
api_router.include_router(earnings.router)
api_router.include_router(earnings.admin_router)
api_router.include_router(wallet.webhook_router)
