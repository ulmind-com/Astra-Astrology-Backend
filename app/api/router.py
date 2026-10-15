"""Mounts every v1 router under a single API router."""

from fastapi import APIRouter

from app.api.v1 import admin_astrologers, astrologers, auth, health, users

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(astrologers.router)
api_router.include_router(admin_astrologers.router)
