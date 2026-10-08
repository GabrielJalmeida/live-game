import asyncio
import uuid

import httpx


BACKEND_URL = (
    "http://127.0.0.1:8000/api/v1/dev/events"
)


async def main():
    provider_event_id = (
        f"fake-tiktok-{uuid.uuid4()}"
    )

    payload = {
        "type": "GIFT",
        "provider": "tiktok",
        "provider_event_id": provider_event_id,
        "viewer": {
            "provider_user_id": "fake-user-001",
            "username": "@teste_tiktok",
            "display_name": "Teste TikTok",
        },
        "payload": {
            "gift_id": 5655,
            "gift_name": "Rose",
            "quantity": 1,
        },
    }

    async with httpx.AsyncClient() as client:
        print("\n=== PRIMEIRO ENVIO ===")

        response_1 = await client.post(
            BACKEND_URL,
            json=payload,
            timeout=10.0,
        )

        print(
            "Provider Event ID:",
            provider_event_id,
        )
        print(
            "Status HTTP:",
            response_1.status_code,
        )
        print(
            "Resposta:",
            response_1.json(),
        )

        print("\n=== SEGUNDO ENVIO ===")

        response_2 = await client.post(
            BACKEND_URL,
            json=payload,
            timeout=10.0,
        )

        print(
            "Provider Event ID:",
            provider_event_id,
        )
        print(
            "Status HTTP:",
            response_2.status_code,
        )
        print(
            "Resposta:",
            response_2.json(),
        )


if __name__ == "__main__":
    asyncio.run(main())