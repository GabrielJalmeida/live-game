import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class LiveEvent(Base):
    __tablename__ = "live_events"

    __table_args__ = (
        Index(
            "ux_live_events_provider_event",
            "provider",
            "provider_event_id",
            unique=True
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    provider: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    provider_event_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    live_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("live_users.id"),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="RECEIVED"
    )

    payload_minimal: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    error_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )