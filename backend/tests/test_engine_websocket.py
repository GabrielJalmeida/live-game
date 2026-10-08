import pytest
from fastapi.testclient import TestClient

from app.events import EventType, LiveEvent, OutputEvent, Viewer
from app.main import app
from app.runtime.engine import engine
from app.runtime.experience import InteractiveExperience
from app.runtime.experience_context import ExperienceContext


class WebSocketTestExperience(InteractiveExperience):
    slug = "websocket-test"
    name = "WebSocket Test"

    async def start(self, context):
        pass

    async def stop(self, context):
        pass

    async def handle_event(self, event, context):
        return [
            OutputEvent(
                type="websocket_test",
                experience=self.slug,
                data={
                    "text": event.payload.get("text"),
                },
            )
        ]

    async def get_state(self):
        return {}


@pytest.mark.asyncio
async def test_engine_output_reaches_websocket():
    experience = WebSocketTestExperience()

    try:
        with TestClient(app) as client:
            with client.websocket_connect("/ws/events") as websocket:

                await engine.start(
                    experience,
                    ExperienceContext(
                        experience_slug=experience.slug,
                    ),
                )

                event = LiveEvent.create(
                    type=EventType.COMMENT,
                    provider="dev",
                    viewer=Viewer(
                        provider_user_id="ws-user",
                        username="@gabriel",
                    ),
                    payload={
                        "text": "hello websocket",
                    },
                )

                outputs = await engine.dispatch(
                    event,
                )

                assert len(outputs) == 1

                message = websocket.receive_json()

                assert message["type"] == "EXPERIENCE_EVENT"
                assert message["experience"] == "websocket-test"
                assert message["data"]["event"] == "websocket_test"
                assert message["data"]["text"] == "hello websocket"

    finally:
        await engine.stop()

        await engine.start(
            engine.experience_loader.create("world001"),
            ExperienceContext(
                experience_slug="world001",
            ),
        )