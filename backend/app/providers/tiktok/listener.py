import asyncio

from TikTokLive import TikTokLiveClient
from TikTokLive.client.errors import UserOfflineError
from TikTokLive.events import (
    CommentEvent,
    ConnectEvent,
    DisconnectEvent,
    GiftEvent,
)

from app.db.session import SessionLocal
from app.logging_config import get_logger
from app.providers.tiktok.adapter import (
    from_comment,
    from_gift,
)
from app.runtime.experience_context import ExperienceContext
from app.services.citizen_service import create_or_support_citizen
from app.services.event_ingestion_service import ingest_event
from app.services.world_service import get_or_create_world


TIKTOK_USERNAME = "@beyondway"


client = TikTokLiveClient(
    unique_id=TIKTOK_USERNAME
)


live_integration_log = get_logger(
    "live_integration"
)

error_log = get_logger(
    "error"
)


def build_context(db) -> ExperienceContext:
    return ExperienceContext(
        experience_slug="world001",
        session=db,
        services={
            "world_service": get_or_create_world,
            "citizen_service": create_or_support_citizen,
        },
    )


async def ingest_tiktok_event(event):
    db = SessionLocal()

    try:
        context = build_context(db)

        result = await ingest_event(
            db=db,
            event=event,
            context=context,
            publish=True,
        )

        return result

    finally:
        db.close()


@client.on(ConnectEvent)
async def on_connect(event):
    live_integration_log.info(
        "tiktok_connected "
        f"username={TIKTOK_USERNAME}"
    )


@client.on(DisconnectEvent)
async def on_disconnect(event):
    live_integration_log.warning(
        "tiktok_disconnected "
        f"username={TIKTOK_USERNAME}"
    )


@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    live_event = from_comment(event)

    if live_event is None:
        return

    username = (
        live_event.viewer.username
        if live_event.viewer is not None
        else "unknown"
    )

    comment = live_event.payload.get(
        "text",
        "",
    )

    print(
        f"💬 {username}: {comment}"
    )

    try:
        result = await ingest_tiktok_event(
            live_event
        )

        if result.status == "duplicate":
            print(
                "⚠ Evento TikTok duplicado ignorado:",
                live_event.provider_event_id,
            )

    except Exception as error:
        error_log.exception(
            "tiktok_comment_processing_failed "
            f"provider_event_id="
            f"{live_event.provider_event_id} "
            f"username={username} "
            f"error={error}"
        )


@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    live_event = from_gift(event)

    if live_event is None:
        return

    username = (
        live_event.viewer.username
        if live_event.viewer is not None
        else "unknown"
    )

    gift_name = live_event.payload.get(
        "gift_name",
        "unknown",
    )

    quantity = live_event.payload.get(
        "quantity",
        1,
    )

    print(
        f"🎁 {username} enviou "
        f"{quantity}x {gift_name}"
    )

    try:
        result = await ingest_tiktok_event(
            live_event
        )

        if result.status == "duplicate":
            print(
                "⚠ Evento TikTok duplicado ignorado:",
                live_event.provider_event_id,
            )

    except Exception as error:
        error_log.exception(
            "tiktok_gift_processing_failed "
            f"provider_event_id="
            f"{live_event.provider_event_id} "
            f"username={username} "
            f"gift_name={gift_name} "
            f"error={error}"
        )


async def run_with_reconnect():
    retry_delay = 5

    while True:
        try:
            print()
            print(
                f"🔌 Tentando conectar em "
                f"{TIKTOK_USERNAME}..."
            )

            await client.connect()

            live_integration_log.warning(
                "tiktok_connection_ended "
                f"username={TIKTOK_USERNAME}"
            )

            retry_delay = 5

        except UserOfflineError:
            retry_delay = 30

            live_integration_log.warning(
                "tiktok_live_offline "
                f"username={TIKTOK_USERNAME} "
                f"retry_delay={retry_delay}"
            )

        except Exception as error:
            error_log.exception(
                "tiktok_connection_failed "
                f"username={TIKTOK_USERNAME} "
                f"retry_delay={retry_delay} "
                f"error={error}"
            )

        live_integration_log.info(
            "tiktok_reconnect_scheduled "
            f"username={TIKTOK_USERNAME} "
            f"retry_delay={retry_delay}"
        )

        print(
            f"🔁 Nova tentativa em "
            f"{retry_delay} segundos..."
        )

        await asyncio.sleep(
            retry_delay
        )

        retry_delay = min(
            retry_delay * 2,
            60
        )


if __name__ == "__main__":
    try:
        asyncio.run(
            run_with_reconnect()
        )

    except KeyboardInterrupt:
        print()
        print(
            "🛑 Listener TikTok encerrado."
        )