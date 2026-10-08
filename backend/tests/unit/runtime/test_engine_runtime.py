from app.runtime.engine import EngineRuntime


def test_engine_runtime_shares_realtime_manager():
    runtime = EngineRuntime()

    assert (
        runtime.experience_manager.realtime_manager
        is runtime.realtime_manager
    )

import pytest

from app.events import EventType, LiveEvent, OutputEvent, Viewer
from app.runtime.engine import EngineRuntime
from app.runtime.experience import InteractiveExperience
from app.runtime.experience_context import ExperienceContext


class FakeRealtimeManager:
    def __init__(self):
        self.published = []

    async def publish(self, output):
        self.published.append(output)


class StubExperience(InteractiveExperience):
    slug = "stub"
    name = "Stub Experience"
    version = "0.1.0"

    def __init__(self):
        self.started = False
        self.stopped = False
        self.received_events = []

    async def start(self, context):
        self.started = True

    async def stop(self, context):
        self.stopped = True

    async def handle_event(self, event, context):
        self.received_events.append(event)

        return [
            OutputEvent(
                type="STUB_EVENT",
                experience=self.slug,
                data={"received": True},
            )
        ]

    async def get_state(self):
        return {
            "received_events": len(self.received_events),
        }


@pytest.mark.asyncio
async def test_engine_runtime_dispatches_through_experience_manager():
    realtime_manager = FakeRealtimeManager()
    runtime = EngineRuntime(
        realtime_manager=realtime_manager,
    )

    experience = StubExperience()

    await runtime.start(
        experience,
        ExperienceContext(
            experience_slug="stub",
        ),
    )

    event = LiveEvent.create(
        type=EventType.COMMENT,
        provider="dev",
        viewer=Viewer(
            provider_user_id="123",
            username="@gabriel",
        ),
        payload={
            "text": "hello",
        },
    )

    outputs = await runtime.dispatch(event)

    assert len(outputs) == 1
    assert outputs[0].type == "STUB_EVENT"
    assert experience.received_events == [event]
    assert realtime_manager.published == outputs


@pytest.mark.asyncio
async def test_engine_runtime_controls_experience_lifecycle():
    runtime = EngineRuntime()
    experience = StubExperience()

    await runtime.start(
        experience,
        ExperienceContext(
            experience_slug="stub",
        ),
    )

    assert experience.started is True

    await runtime.stop()

    assert experience.stopped is True

@pytest.mark.asyncio
async def test_engine_runtime_can_start_registered_experience():
    runtime = EngineRuntime()

    experience = StubExperience()

    runtime.register_experience(StubExperience)

    await runtime.start_experience(
        "stub",
        ExperienceContext(
            experience_slug="stub",
        ),
    )

    assert runtime.experience_manager.router._experience is not None
    assert (
        runtime.experience_manager.router._experience.slug
        == "stub"
    )

@pytest.mark.asyncio
async def test_engine_runtime_accepts_event_specific_context():
    runtime = EngineRuntime()
    experience = StubExperience()

    await runtime.start(
        experience,
        ExperienceContext(
            experience_slug="stub",
        ),
    )

    event_context = ExperienceContext(
        experience_slug="stub",
        session="event-session",
    )

    event = LiveEvent.create(
        type=EventType.COMMENT,
        provider="dev",
        viewer=Viewer(
            provider_user_id="123",
            username="@gabriel",
        ),
        payload={
            "text": "hello",
        },
    )

    await runtime.dispatch(
        event,
        context=event_context,
    )

    assert experience.received_events == [event]

from app.experiences.world001.experience import World001Experience


def test_default_engine_registers_world001():
    from app.runtime.engine import engine

    assert "world001" in engine.experience_loader.list_slugs()


def test_default_engine_can_create_world001():
    from app.runtime.engine import engine

    experience = engine.experience_loader.create("world001")

    assert isinstance(experience, World001Experience)

@pytest.mark.asyncio
async def test_engine_runtime_can_dispatch_without_publishing():
    realtime_manager = FakeRealtimeManager()

    runtime = EngineRuntime(
        realtime_manager=realtime_manager,
    )

    experience = StubExperience()

    await runtime.start(
        experience,
        ExperienceContext(
            experience_slug="stub",
        ),
    )

    event = LiveEvent.create(
        type=EventType.COMMENT,
        provider="dev",
        viewer=Viewer(
            provider_user_id="123",
            username="@gabriel",
        ),
        payload={
            "text": "hello",
        },
    )

    outputs = await runtime.dispatch(
        event,
        publish=False,
    )

    assert len(outputs) == 1
    assert realtime_manager.published == []

    await runtime.publish(outputs)

    assert realtime_manager.published == outputs

def test_engine_runtime_builds_context_from_active_experience():
    runtime = EngineRuntime()

    experience = StubExperience()

    runtime.experience_manager.router._experience = experience

    context = runtime.build_context(
        "fake-session"
    )

    assert context.experience_slug == "stub"
    assert context.session == "fake-session"