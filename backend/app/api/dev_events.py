from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.realtime.connection_manager import manager
from app.services.citizen_service import create_or_support_citizen
from app.services.world_service import get_or_create_world

from app.services.live_user_service import get_or_create_live_user
from app.services.live_event_service import (
    register_live_event,
    mark_processed,
    mark_failed,
)

from app.logging_config import get_logger

router = APIRouter()

world_event_log = get_logger("world_event")
error_log = get_logger("error")

class CommentEventRequest(BaseModel):
    username: str = Field(
        min_length=1,
        max_length=100
    )

    comment: str = Field(
        min_length=1,
        max_length=500
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError(
                "username não pode estar vazio"
            )

        if not value.startswith("@"):
            value = f"@{value}"

        return value

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError(
                "comment não pode estar vazio"
            )

        return value

class RoseEventRequest(BaseModel):
    username: str = Field(
        min_length=1,
        max_length=100
    )

    quantity: int = Field(
        default=1,
        ge=1,
        le=100000
    )

    provider: str = Field(
        default="dev",
        min_length=1,
        max_length=30
    )

    provider_user_id: str | None = Field(
        default=None,
        max_length=100
    )

    provider_event_id: str | None = Field(
        default=None,
        max_length=150
    )

    display_name: str | None = Field(
        default=None,
        max_length=150
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError(
                "username não pode estar vazio"
            )

        if not value.startswith("@"):
            value = f"@{value}"

        return value

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError(
                "provider não pode estar vazio"
            )

        return value

    @field_validator(
        "provider_user_id",
        "provider_event_id",
        "display_name"
    )
    @classmethod
    def normalize_optional_strings(
        cls,
        value
    ):
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return value

@router.post("/dev/events/comment")
async def receive_comment(
    payload: CommentEventRequest
):
    await manager.broadcast({
        "type": "comment_received",
        "username": payload.username,
        "comment": payload.comment
    })

    return {
        "status": "received"
    }

@router.post("/dev/events/rose")
async def receive_rose(
    payload: RoseEventRequest,
    db: Session = Depends(get_db)
):
    world = get_or_create_world(db)

    provider_user_id = (
        payload.provider_user_id
        or payload.username
    )

    live_user = get_or_create_live_user(
        db=db,
        provider=payload.provider,
        provider_user_id=provider_user_id,
        username=payload.username,
        display_name=payload.display_name
    )

    live_event, is_new_event = register_live_event(
        db=db,
        provider=payload.provider,
        provider_event_id=payload.provider_event_id,
        event_type="ROSE",
        live_user=live_user,
        payload={
            "username": payload.username,
            "quantity": payload.quantity
        }
    )

    world_event_log.info(
        "rose_received "
        f"event_id={live_event.id} "
        f"provider={payload.provider} "
        f"provider_event_id={payload.provider_event_id} "
        f"live_user={live_user.id} "
        f"username={payload.username} "
        f"quantity={payload.quantity}"
    )

    if not is_new_event:
        world_event_log.warning(
            "rose_duplicate "
            f"event_id={live_event.id} "
            f"provider={payload.provider} "
            f"provider_event_id={payload.provider_event_id} "
            f"username={payload.username}"
        )

        return {
            "status": "duplicate",
            "event_id": live_event.id
        }

    try:
        citizen, created = create_or_support_citizen(
            db=db,
            world=world,
            name=payload.username,
            quantity=payload.quantity,
            commit=False
)

        citizen_data = {
            "id": citizen.id,
            "name": citizen.name,
            "x": citizen.x,
            "y": citizen.y,
            "status": citizen.status,
            "total_roses": citizen.total_roses,
            "wealth": citizen.wealth
        }

        world_event_log.info(
            "citizen_rose_applied "
            f"event_id={live_event.id} "
            f"citizen={citizen.id} "
            f"username={citizen.name} "
            f"created={created} "
            f"quantity={payload.quantity} "
            f"total_roses={citizen.total_roses} "
            f"wealth={citizen.wealth}"
        )

        mark_processed(
            db,
            live_event,
            commit=False
        )

        db.commit()

        db.refresh(citizen)
        db.refresh(live_event)

        world_event_log.info(
            "rose_processed "
            f"event_id={live_event.id} "
            f"citizen={citizen.id} "
            f"status=PROCESSED"
        )

    except Exception as error:
        db.rollback()

        mark_failed(
            db,
            live_event,
            "ROSE_PROCESSING_FAILED"
        )

        error_log.exception(
            "rose_processing_failed "
            f"event_id={live_event.id} "
            f"provider={payload.provider} "
            f"provider_event_id={payload.provider_event_id} "
            f"username={payload.username} "
            f"error={error}"
        )

        raise

    # O estado já está persistido.
    # Falha de WebSocket não deve transformar
    # o LiveEvent em FAILED.
    try:
        if created:
            await manager.broadcast({
                "type": "citizen_spawned",
                "citizen": citizen_data
            })

        else:
            await manager.broadcast({
                "type": "citizen_supported",
                "citizen": citizen_data,
                "quantity": payload.quantity
            })

    except Exception as error:
        error_log.exception(
            "rose_broadcast_failed "
            f"event_id={live_event.id} "
            f"citizen={citizen.id} "
            f"error={error}"
        )

    return {
        "status": (
            "created"
            if created
            else "supported"
        ),
        "event_id": live_event.id,
        "citizen": citizen_data
    }