from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.events import LiveEvent, OutputEvent
from app.runtime.engine import engine
from app.runtime.experience_context import ExperienceContext

from app.services.live_event_service import (
    mark_failed,
    mark_processed,
    register_live_event,
)
from app.services.live_user_service import get_or_create_live_user


@dataclass(slots=True)
class EventIngestionResult:
    status: str
    event_id: str
    outputs: list[OutputEvent]


async def ingest_event(
    db: Session,
    event: LiveEvent,
    context: ExperienceContext,
    *,
    publish: bool = True,
) -> EventIngestionResult:

    live_user = None

    if event.viewer is not None:
        provider_user_id = (
            event.viewer.provider_user_id
            or event.viewer.username
        )

        live_user = get_or_create_live_user(
            db=db,
            provider=event.provider,
            provider_user_id=provider_user_id,
            username=event.viewer.username,
            display_name=event.viewer.display_name,
        )

    record, is_new_event = register_live_event(
        db=db,
        provider=event.provider,
        provider_event_id=event.provider_event_id,
        event_type=event.type.value,
        live_user=live_user,
        payload=event.payload,
    )

    if not is_new_event:
        return EventIngestionResult(
            status="duplicate",
            event_id=record.id,
            outputs=[],
        )

    try:
        outputs = await engine.dispatch(
            event,
            context=context,
            publish=False,
        )

        mark_processed(
            db,
            record,
            commit=False,
        )

        db.commit()

    except Exception:
        db.rollback()

        mark_failed(
            db,
            record,
            "EVENT_PROCESSING_FAILED",
        )

        raise

    if publish:
        await engine.publish(outputs)

    return EventIngestionResult(
        status="processed",
        event_id=record.id,
        outputs=outputs,
    )