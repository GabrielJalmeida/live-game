import pytest

from app.events import OutputEvent
from app.realtime.realtime_manager import RealtimeManager


class FakeConnectionManager:
    def __init__(self):
        self.messages = []

    async def broadcast(
        self,
        message: dict,
    ):
        self.messages.append(message)


def test_build_message_wraps_output_event():
    output = OutputEvent(
        type="CITIZEN_SPAWNED",
        experience="world001",
        data={
            "citizen_id": "citizen-001",
            "name": "@gabriel",
        },
    )

    message = RealtimeManager.build_message(
        output
    )

    assert message["type"] == "EXPERIENCE_EVENT"
    assert message["experience"] == "world001"

    assert message["data"]["event"] == (
        "CITIZEN_SPAWNED"
    )

    assert message["data"]["citizen_id"] == (
        "citizen-001"
    )

    assert message["data"]["name"] == (
        "@gabriel"
    )

    assert message["message_id"].startswith(
        "msg_"
    )


@pytest.mark.asyncio
async def test_publish_broadcasts_output_event():
    connection_manager = FakeConnectionManager()

    realtime = RealtimeManager(
        connection_manager
    )

    output = OutputEvent(
        type="PET_FED",
        experience="pet_world",
        data={
            "target": "dog",
            "amount": 1,
        },
    )

    message = await realtime.publish(
        output
    )

    assert len(
        connection_manager.messages
    ) == 1

    assert (
        connection_manager.messages[0]
        == message
    )

    assert message["experience"] == (
        "pet_world"
    )

    assert message["data"]["event"] == (
        "PET_FED"
    )

    assert message["data"]["target"] == (
        "dog"
    )