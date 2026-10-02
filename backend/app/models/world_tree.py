import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WorldTree(Base):
    __tablename__ = "world_trees"

    __table_args__ = (
        Index(
            "ux_world_trees_world_tree_key",
            "world_id",
            "tree_key",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id"),
        nullable=False,
    )

    # ID estável vindo do mapa procedural.
    # Exemplo: tree_18_34
    tree_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    wood_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
        server_default=text("10"),
    )

    max_wood: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
        server_default=text("10"),
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="GROWN",
        server_default=text("'GROWN'"),
    )

    regrow_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )