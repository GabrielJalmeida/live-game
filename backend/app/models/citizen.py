import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Citizen(Base):
    __tablename__ = "citizens"

    __table_args__ = (
        Index(
            "ux_citizens_world_name",
            "world_id",
            "name",
            unique=True
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    x: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    y: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ACTIVE"
    )

    total_roses: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1")
    )

    wealth: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
        server_default=text("10")
    )

    spawned_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )