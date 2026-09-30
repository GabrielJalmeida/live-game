import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.live_event import LiveEvent
from app.models.live_user import LiveUser


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def find_live_event(
    db: Session,
    provider: str,
    provider_event_id: str
) -> LiveEvent | None:

    statement = select(LiveEvent).where(
        LiveEvent.provider == provider,
        LiveEvent.provider_event_id == provider_event_id
    )

    return db.scalar(statement)


def register_live_event(
    db: Session,
    provider: str,
    provider_event_id: str | None,
    event_type: str,
    live_user: LiveUser | None,
    payload: dict | None = None
) -> tuple[LiveEvent, bool]:

    # Se existe ID externo, verificamos antes.
    if provider_event_id:
        existing_event = find_live_event(
            db,
            provider,
            provider_event_id
        )

        if existing_event:
            return existing_event, False

    event = LiveEvent(
        id=str(uuid.uuid4()),
        provider=provider,
        provider_event_id=provider_event_id,
        event_type=event_type,
        live_user_id=(
            live_user.id
            if live_user
            else None
        ),
        status="RECEIVED",
        payload_minimal=(
            json.dumps(
                payload,
                ensure_ascii=False
            )
            if payload is not None
            else None
        )
    )

    db.add(event)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        # Pode acontecer se dois eventos idênticos
        # chegarem praticamente ao mesmo tempo.
        if provider_event_id:
            existing_event = find_live_event(
                db,
                provider,
                provider_event_id
            )

            if existing_event:
                return existing_event, False

        raise

    db.refresh(event)

    return event, True


def mark_processed(
    db: Session,
    event: LiveEvent,
    commit: bool = True
):
    event.status = "PROCESSED"
    event.processed_at = utc_now()

    if commit:
        db.commit()
        db.refresh(event)

    else:
        db.flush()


def mark_failed(
    db: Session,
    event: LiveEvent,
    error_code: str
):
    event.status = "FAILED"
    event.error_code = error_code

    db.commit()
    db.refresh(event)