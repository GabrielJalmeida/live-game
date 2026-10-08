import pytest

from app.events import (
    EventType,
    LiveEvent,
    OutputEvent,
    Viewer,
)
from app.runtime import (
    ExperienceContext,
    ExperienceManager,
    InteractiveExperience,
    NoActiveExperienceError,
)


class EchoExperience(InteractiveExperience):
    slug = "echo"
    name = "Echo Experience"
    version = "0.1.0"

    def __init__(self):
        self.received_events: list[LiveEvent] = []
        self.started = False
        self.stopped = False

    async def start(
        self,
        context: ExperienceContext,
    ) -> None:
        self.started = True

    async def stop(
        self,
        context: ExperienceContext,
    ) -> None:
        self.stopped = True

    async def handle_event(
        self,
        event: LiveEvent,
        context: ExperienceContext,
    ) -> list[OutputEvent]:
        self.received_events.append(event)

        return [
            OutputEvent(
                type="EVENT_RECEIVED",
                experience=self.slug,
                event_id=event.event_id,
                data={
                    "input_type": event.type.value,
                },
            )
        ]

    async def get_state(self) -> dict:
        return {
            "received_events": len(
                self.received_events
            )
        }


@pytest.mark.asyncio
async def test_router_delivers_event_to_active_experience():
    manager = ExperienceManager()

    experience = EchoExperience()

    context = ExperienceContext(
        experience_slug="echo"
    )

    await manager.start(
        experience,
        context,
    )

    event = LiveEvent.create(
        type=EventType.COMMENT,
        provider="dev",
        viewer=Viewer(
            provider_user_id="dev-1",
            username="@gabriel",
        ),
        payload={
            "text": "hello"
        },
    )

    outputs = await manager.dispatch(event)

    assert len(outputs) == 1
    assert outputs[0].type == "EVENT_RECEIVED"
    assert outputs[0].experience == "echo"

    assert experience.received_events == [
        event
    ]


@pytest.mark.asyncio
async def test_experience_lifecycle():
    manager = ExperienceManager()

    experience = EchoExperience()

    await manager.start(
        experience,
        ExperienceContext(
            experience_slug="echo"
        ),
    )

    assert experience.started is True

    await manager.stop()

    assert experience.stopped is True


@pytest.mark.asyncio
async def test_manager_exposes_experience_state():
    manager = ExperienceManager()

    experience = EchoExperience()

    await manager.start(
        experience,
        ExperienceContext(
            experience_slug="echo"
        ),
    )

    state_before = await manager.get_state()

    assert state_before == {
        "received_events": 0
    }

    event = LiveEvent.create(
        type=EventType.GIFT,
        provider="dev",
        viewer=None,
        payload={
            "gift_name": "Rose",
            "quantity": 1,
        },
    )

    await manager.dispatch(event)

    state_after = await manager.get_state()

    assert state_after == {
        "received_events": 1
    }


@pytest.mark.asyncio
async def test_dispatch_without_experience_fails_explicitly():
    manager = ExperienceManager()

    event = LiveEvent.create(
        type=EventType.COMMENT,
        provider="dev",
        viewer=None,
        payload={
            "text": "A"
        },
    )

    with pytest.raises(
        NoActiveExperienceError
    ):
        await manager.dispatch(event)

class FakeRealtimeManager:
    def __init__(self):
        self.published = []

    async def publish(self, output):
        self.published.append(output)


@pytest.mark.asyncio
async def test_dispatch_publishes_outputs_to_realtime():
    realtime_manager = FakeRealtimeManager()
    manager = ExperienceManager(realtime_manager=realtime_manager)

    experience = EchoExperience()
    context = ExperienceContext(experience_slug="echo")

    await manager.start(experience, context)

    event = LiveEvent.create(
        type=EventType.COMMENT,
        provider="dev",
        viewer=Viewer(
            provider_user_id="123",
            username="@gabriel",
        ),
        payload={"text": "A"},
    )

    outputs = await manager.dispatch(event)

    assert len(outputs) == 1
    assert realtime_manager.published == outputs