"""Shared response schemas."""

from pydantic import BaseModel, ConfigDict, Field


class ApiResponse[T](BaseModel):
    """Every successful endpoint returns this shape."""

    success: bool = True
    message: str = "Success"
    data: T | None = None

    model_config = ConfigDict(populate_by_name=True)


class MessageResponse(BaseModel):
    success: bool = True
    message: str


class HealthStatus(BaseModel):
    status: str
    app: str
    environment: str
    version: str
    database: str
    services: dict[str, bool] = Field(default_factory=dict)
