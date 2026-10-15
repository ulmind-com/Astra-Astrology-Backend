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


class PageMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class Paginated[T](BaseModel):
    items: list[T]
    meta: PageMeta


def build_page[T](items: list[T], total: int, page: int, limit: int) -> Paginated[T]:
    from math import ceil

    total_pages = ceil(total / limit) if limit else 0
    return Paginated[T](
        items=items,
        meta=PageMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


class HealthStatus(BaseModel):
    status: str
    app: str
    environment: str
    version: str
    database: str
    services: dict[str, bool] = Field(default_factory=dict)
