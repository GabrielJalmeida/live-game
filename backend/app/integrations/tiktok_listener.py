import httpx

from TikTokLive import TikTokLiveClient
from TikTokLive.events import (
    ConnectEvent,
    DisconnectEvent,
    GiftEvent,
    CommentEvent
)


TIKTOK_USERNAME = "@beyondway"

client = TikTokLiveClient(
    unique_id=TIKTOK_USERNAME
)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    print()
    print("====================================")
    print("✅ CONECTADO À TIKTOK LIVE")
    print(f"👤 Conta: {TIKTOK_USERNAME}")
    print(f"🏠 Room ID: {client.room_id}")
    print("====================================")
    print()


@client.on(DisconnectEvent)
async def on_disconnect(event: DisconnectEvent):
    print("❌ Desconectado da TikTok LIVE")

async def process_rose(username: str, quantity: int = 1):
    print(f"🌹 Processando {quantity} Rosa(s) de @{username}")

    for _ in range(quantity):
        await send_rose_to_backend(username)

async def send_rose_to_backend(username: str):
    backend_url = "http://127.0.0.1:8000/api/v1/dev/events/rose"

    if not username.startswith("@"):
        username = f"@{username}"

    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                backend_url,
                json={
                    "username": username
                },
                timeout=5.0
            )

        if response.status_code == 200:
            print(f"✅ {username} enviado para o WORLD 001")
        else:
            print(
                f"❌ Backend respondeu com "
                f"{response.status_code}: {response.text}"
            )

    except Exception as error:
        print(f"❌ Erro ao comunicar com o backend: {error}")

@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    username = event.user.unique_id
    comment = event.comment.strip()

    print(f"💬 @{username}: {comment}")

    if comment.lower() == "!rose":
        print(f"🌹 ROSA DE TESTE recebida de @{username}")
        await process_rose(username)

@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    gift = event.gift

    if gift is None:
        return

    # type == 1 significa que o gift pode ser enviado em sequência.
    # Enquanto a sequência estiver acontecendo, não processamos.
    if gift.type == 1 and event.streaking:
        return

    username = event.user.unique_id
    gift_name = gift.name
    quantity = event.repeat_count or 1

    print(
        f"🎁 @{username} enviou "
        f"{quantity}x {gift_name}"
    )

    if gift_name.lower() == "rose":
        await process_rose(
            username,
            quantity
        )

if __name__ == "__main__":
    print(f"🔎 Tentando conectar em {TIKTOK_USERNAME}...")
    client.run()