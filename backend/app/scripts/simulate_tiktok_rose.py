import asyncio
import uuid

import httpx


BACKEND_URL = (
    "http://127.0.0.1:8000/api/v1/dev/events/rose"
)


async def main():
    event_id = f"fake-tiktok-{uuid.uuid4()}"

    payload = {
        "username": "@teste_tiktok",
        "quantity": 1,
        "provider": "tiktok",
        "provider_user_id": "fake-user-001",
        "provider_event_id": event_id,
        "display_name": "Teste TikTok",
    }

    async with httpx.AsyncClient() as client:
        print("\n=== PRIMEIRO ENVIO ===")

        response_1 = await client.post(
            BACKEND_URL,
            json=payload,
            timeout=10.0,
        )

        print("Event ID:", event_id)
        print("Status HTTP:", response_1.status_code)
        print("Resposta:", response_1.json())

        print("\n=== SEGUNDO ENVIO ===")

        response_2 = await client.post(
            BACKEND_URL,
            json=payload,
            timeout=10.0,
        )

        print("Event ID:", event_id)
        print("Status HTTP:", response_2.status_code)
        print("Resposta:", response_2.json())


if __name__ == "__main__":
    asyncio.run(main())