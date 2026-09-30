import httpx
import asyncio

from app.logging_config import get_logger

from TikTokLive.client.errors import UserOfflineError
from TikTokLive import TikTokLiveClient
from TikTokLive.events import (
    ConnectEvent,
    DisconnectEvent,
    GiftEvent,
    CommentEvent,
)


TIKTOK_USERNAME = "@beyondway"

BACKEND_ROSE_URL = (
    "http://127.0.0.1:8000/api/v1/dev/events/rose"
)

BACKEND_COMMENT_URL = (
    "http://127.0.0.1:8000/api/v1/dev/events/comment"
)


client = TikTokLiveClient(
    unique_id=TIKTOK_USERNAME
)

live_integration_log = get_logger(
    "live_integration"
)

error_log = get_logger(
    "error"
)

def normalize_username(username: str) -> str:
    username = username.strip()

    if not username.startswith("@"):
        username = f"@{username}"

    return username


async def send_rose_to_backend(
    username: str,
    quantity: int = 1,
    provider: str = "tiktok",
    provider_user_id: str | None = None,
    provider_event_id: str | None = None,
    display_name: str | None = None,
):
    payload = {
        "username": username,
        "quantity": quantity,
        "provider": provider,
        "provider_user_id": provider_user_id,
        "provider_event_id": provider_event_id,
        "display_name": display_name,
    }

    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(
            BACKEND_ROSE_URL,
            json=payload,
            timeout=10.0,
        )

        response.raise_for_status()

        return response.json()


async def process_rose(
    username: str,
    quantity: int = 1,
    provider: str = "tiktok",
    provider_user_id: str | None = None,
    provider_event_id: str | None = None,
    display_name: str | None = None,
):
    username = normalize_username(username)

    try:
        result = await send_rose_to_backend(
            username=username,
            quantity=quantity,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_event_id=provider_event_id,
            display_name=display_name,
        )

        if result.get("status") == "duplicate":
            print(
                "♻️ Evento TikTok duplicado ignorado:",
                provider_event_id,
            )

            return

        print(
            "🌹 Rosa processada:",
            username,
            "| quantidade:",
            quantity,
            "| evento:",
            provider_event_id,
        )

    except Exception as error:
        print(
            "❌ Erro ao processar Rosa:",
            error,
        )


async def send_comment_to_backend(
    username: str,
    comment: str,
):
    username = normalize_username(username)

    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                BACKEND_COMMENT_URL,
                json={
                    "username": username,
                    "comment": comment,
                },
                timeout=5.0,
            )

        if response.status_code == 200:
            print(
                f"✅ Comentário de {username} "
                f"enviado para o WORLD 001"
            )

        else:
            print(
                "❌ Erro enviando comentário: "
                f"{response.status_code}: "
                f"{response.text}"
            )

    except Exception as error:
        print(
            f"❌ Falha ao enviar comentário: {error}"
        )


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
    user = event.user

    if user is None:
        return

    username = normalize_username(
        user.unique_id
    )

    comment = event.comment.strip()

    if not comment:
        return

    print(
        f"💬 {username}: {comment}"
    )

    await send_comment_to_backend(
        username,
        comment,
    )

    if comment.lower() == "!rose":
        print(
            f"🌹 ROSA DE TESTE recebida de {username}"
        )

        await process_rose(
            username=username,
            provider="tiktok",
            provider_user_id=str(
                getattr(user, "id", "")
                or username
            ),
        )


@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    gift = event.gift
    user = event.user

    if gift is None:
        return

    if user is None:
        return

    # Presentes que podem formar sequência geram
    # vários eventos. Processamos somente o evento
    # final da sequência.
    if gift.streakable and event.streaking:
        return

    username_value = (
        getattr(user, "unique_id", None)
        or getattr(user, "display_id", None)
    )

    if not username_value:
        return

    username = normalize_username(
        username_value
    )

    provider_user_id = str(
        getattr(user, "id", "")
        or getattr(user, "user_id", "")
        or username_value
    )

    provider_event_id = (
        getattr(event, "order_id", None)
        or getattr(event, "log_id", None)
    )

    if provider_event_id:
        provider_event_id = str(
            provider_event_id
        )

    display_name = getattr(
        user,
        "nickname",
        None,
    )

    gift_name = gift.name
    quantity = event.repeat_count or 1

    print(
        f"🎁 {username} enviou "
        f"{quantity}x {gift_name}"
    )

    if gift_name.lower() == "rose":
        await process_rose(
            username=username,
            quantity=quantity,
            provider="tiktok",
            provider_user_id=provider_user_id,
            provider_event_id=provider_event_id,
            display_name=display_name,
        )


async def run_with_reconnect():
    retry_delay = 5

    while True:
        try:
            print()
            print(
                f"🔎 Tentando conectar em "
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
            f"🔄 Nova tentativa em "
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