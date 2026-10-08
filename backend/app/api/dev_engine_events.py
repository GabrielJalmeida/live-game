from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.events import EventType, LiveEvent, Viewer
from app.runtime.engine import engine
from app.runtime.experience_context import ExperienceContext

from app.services.citizen_service import create_or_support_citizen
from app.services.live_event_service import (
    mark_failed,
    mark_processed,
    register_live_event,
)
from app.services.live_user_service import get_or_create_live_user
from app.services.world_service import get_or_create_world
from app.logging_config import get_logger


router = APIRouter()

error_log = get_logger("error")


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
    live_user = None

    if payload.viewer is not None:
        provider_user_id = (
            payload.viewer.provider_user_id
            or payload.viewer.username
        )

        live_user = get_or_create_live_user(
            db=db,
            provider=payload.provider,
            provider_user_id=provider_user_id,
            username=payload.viewer.username,
            display_name=payload.viewer.display_name,
        )

    live_event_record, is_new_event = register_live_event(
        db=db,
        provider=payload.provider,
        provider_event_id=payload.provider_event_id,
        event_type=payload.type.value,
        live_user=live_user,
        payload=payload.payload,
    )

    if not is_new_event:
        return {
            "status": "duplicate",
            "event_id": live_event_record.id,
        }

    event = build_live_event(payload)

    context = ExperienceContext(
        experience_slug="world001",
        session=db,
        services={
            "world_service": get_or_create_world,
            "citizen_service": create_or_support_citizen,
        },
    )

    try:
        outputs = await engine.dispatch(
            event,
            context=context,
            publish=False,
        )

        mark_processed(
            db,
            live_event_record,
            commit=False,
        )

        db.commit()

    except Exception:
        db.rollback()

        mark_failed(
            db,
            live_event_record,
            "EVENT_PROCESSING_FAILED",
        )

        error_log.exception(
            "dev_event_processing_failed "
            f"event_id={live_event_record.id} "
            f"provider={payload.provider} "
            f"provider_event_id={payload.provider_event_id} "
            f"event_type={payload.type.value}"
        )

        raise

    try:
        await engine.publish(outputs)
    except Exception:
        error_log.exception(
            "dev_event_publish_failed "
            f"event_id={live_event_record.id}"
        )

    return {
        "status": "processed",
        "event_id": live_event_record.id,
        "outputs": [
            output.to_dict()
            for output in outputs
        ],
    }