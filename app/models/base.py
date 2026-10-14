"""Base Beanie document with timestamps shared by every collection."""

from datetime import UTC, datetime
from typing import Any

from beanie import Document, Insert, Replace, SaveChanges, Update, before_event
from pydantic import Field


def utcnow() -> datetime:
    return datetime.now(UTC)


class TimestampedDocument(Document):
    """Adds `created_at` / `updated_at` and keeps `updated_at` fresh on writes."""

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @before_event(Insert)
    def _set_created_at(self) -> None:
        now = utcnow()
        self.created_at = now
        self.updated_at = now

    @before_event(Replace, Update, SaveChanges)
    def _touch_updated_at(self) -> None:
        self.updated_at = utcnow()

    class Settings:
        use_state_management = True
        state_management_save_previous = True
        validate_on_save = True

    def public_dict(self, **kwargs: Any) -> dict[str, Any]:
        """Serialises the document with `id` as a string, ready for a response."""
        data = self.model_dump(mode="json", by_alias=False, **kwargs)
        data["id"] = str(self.id)
        return data
