"""Pydantic schemas for WebAuthn / Passkey biometric authentication."""

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class PasskeyRegistrationVerifyIn(BaseModel):
    credential: dict[str, Any] = Field(..., description="PublicKeyCredential from navigator.credentials.create()")
    device_name: Optional[str] = Field(default=None, max_length=120, description="User friendly device name, e.g. 'Touch ID'")


class PasskeyAuthenticationOptionsIn(BaseModel):
    email: Optional[str] = Field(default=None, description="Optional email to scope credentials, or None for discoverable resident keys")


class PasskeyAuthenticationVerifyIn(BaseModel):
    credential: dict[str, Any] = Field(..., description="PublicKeyCredential from navigator.credentials.get()")


class PasskeyInfoOut(BaseModel):
    id: str
    credential_id: str
    device_name: str
    transports: list[str] = []
    created_at: datetime
    last_used_at: Optional[datetime] = None
