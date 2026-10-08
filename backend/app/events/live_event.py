from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from app.events.types import EventType
from app.events.viewer import Viewer


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class LiveEvent:
    event_id: str
    type: EventType
    provider: str
    provider_event_id: str | None
    session_id: str | None
    occurred_at: datetime
    viewer: Viewer | None
    payload: dict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        event_id: str | None = None,
        type: EventType,
        provider: str,
        provider_event_id: str | None = None,
        session_id: str | None = None,
        occurred_at: datetime | None = None,
        viewer: Viewer | None = None,
        payload: dict | None = None,
    ):
        return cls(
            event_id=event_id or f"evt_{uuid4()}",
            type=type,
            provider=provider,
            provider_event_id=provider_event_id,
            session_id=session_id,
            occurred_at=occurred_at or utc_now(),
            viewer=viewer,
            payload=dict(payload or {}),
        )

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "type": self.type.value,
            "provider": self.provider,
            "provider_event_id": self.provider_event_id,
            "session_id": self.session_id,
            "occurred_at": self.occurred_at.isoformat(),
            "viewer": self.viewer.to_dict() if self.viewer else None,
            "payload": self.payload.copy(),
        }