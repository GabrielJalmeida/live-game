from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.events import EventType, LiveEvent, Viewer
from app.runtime.experience_context import ExperienceContext

from app.services.citizen_service import create_or_support_citizen
from app.services.event_ingestion_service import ingest_event
from app.services.world_service import get_or_create_world


router = APIRouter()


class DevViewerRequest(BaseModel):
    provider_user_id: str | None = Field(
        default=None,
        max_length=100,
    )

    username: str = Field(
        min_length=1,
        max_length=100,
    )

    display_name: str | None = Field(
        default=None,
        max_length=150,
    )

    avatar_url: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "username não pode estar vazio"
            )

        if not value.startswith("@"):
            value = f"@{value}"

        return value

    @field_validator(
        "provider_user_id",
        "display_name",
        "avatar_url",
    )
    @classmethod
    def normalize_optional_strings(cls, value):
        if value is None:
            return None

        value = value.strip()

        return value or None


class DevEventRequest(BaseModel):
    type: EventType

    provider: str = Field(
        default="dev",
        min_length=1,
        max_length=30,
    )

    provider_event_id: str | None = Field(
        default=None,
        max_length=150,
    )

    event_id: str | None = Field(
        default=None,
        max_length=150,
    )

    session_id: str | None = Field(
        default=None,
        max_length=150,
    )

    occurred_at: datetime | None = None

    viewer: DevViewerRequest | None = None

    payload: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "provider não pode estar vazio"
            )

        return value

    @field_validator(
        "provider_event_id",
        "event_id",
        "session_id",
    )
    @classmethod
    def normalize_optional_strings(cls, value):
        if value is None:
            return None

        value = value.strip()

        return value or None


def build_live_event(
    payload: DevEventRequest,
) -> LiveEvent:
    viewer = None

    if payload.viewer is not None:
        viewer = Viewer(
            provider_user_id=payload.viewer.provider_user_id,
            username=payload.viewer.username,
            display_name=payload.viewer.display_name,
            avatar_url=payload.viewer.avatar_url,
        )

    return LiveEvent.create(
        event_id=payload.event_id,
        type=payload.type,
        provider=payload.provider,
        provider_event_id=payload.provider_event_id,
        session_id=payload.session_id,
        occurred_at=payload.occurred_at,
        viewer=viewer,
        payload=payload.payload,
    )


@router.post("/dev/events")
async def receive_dev_event(
    payload: DevEventRequest,
    db: Session = Depends(get_db),
):
    event = build_live_event(payload)

    context = ExperienceContext(
        experience_slug="world001",
        session=db,
        services={
            "world_service": get_or_create_world,
            "citizen_service": create_or_support_citizen,
        },
    )

    result = await ingest_event(
        db=db,
        event=event,
        context=context,
        publish=True,
    )

    return {
        "status": result.status,
        "event_id": result.event_id,
        "outputs": [
            output.to_dict()
            for output in result.outputs
        ],
    }