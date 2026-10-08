import pytest

from app.events import EventType, OutputEvent
from app.runtime import (
    ExperienceContext,
    ExperienceManager,
    InteractiveExperience,
)
from app.runtime.simulator import EventSimulator


class CaptureExperience(InteractiveExperience):
    slug = "capture"
    name = "Capture Experience"

    def __init__(self):
        self.received = []

    async def handle_event(
        self,
        event,
        context,
    ):
        self.received.append(event)

        return [
            OutputEvent(
                type="EVENT_CAPTURED",
                experience=self.slug,
                event_id=event.event_id,
                data={
                    "type": event.type.value,
                    "username": (
                        event.viewer.username
                        if event.viewer
                        else None
                    ),
                    "payload": event.payload,
                },
            )
        ]

    async def get_state(self):
        return {
            "received": len(self.received)
        }


@pytest.mark.asyncio
async def test_simulator_creates_comment_event():
    manager = ExperienceManager()

    experience = CaptureExperience()

    await manager.start(
        experience,
        ExperienceContext(
            experience_slug="capture"
        ),
    )

    simulator = EventSimulator(manager)

    outputs = await simulator.comment(
        username="gabriel",
        text="A",
    )

    assert len(outputs) == 1

    event = experience.received[0]

    assert event.type is EventType.COMMENT
    assert event.viewer.username == "@gabriel"
    assert event.payload["text"] == "A"


@pytest.mark.asyncio
async def test_simulator_creates_generic_gift_event():
    manager = ExperienceManager()

    experience = CaptureExperience()

    await manager.start(
        experience,
        ExperienceContext(
            experience_slug="capture"
        ),
    )

    simulator = EventSimulator(manager)

    outputs = await simulator.gift(
        username="maria",
        gift_name="Rose",
        quantity=3,
    )

    assert len(outputs) == 1

    event = experience.received[0]

    assert event.type is EventType.GIFT
    assert event.viewer.username == "@maria"
    assert event.payload["gift_name"] == "Rose"
    assert event.payload["quantity"] == 3