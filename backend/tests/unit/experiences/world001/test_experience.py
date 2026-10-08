from types import SimpleNamespace

import pytest

from app.events import EventType, LiveEvent, Viewer
from app.experiences.world001.experience import World001Experience
from app.runtime.experience_context import ExperienceContext


class FakeWorldService:
    def __init__(self):
        self.calls = []

    def __call__(self, db):
        self.calls.append(db)
        return SimpleNamespace(id="world-1")


class FakeCitizenService:
    def __init__(self, created=True):
        self.created = created
        self.calls = []

    def __call__(
        self,
        *,
        db,
        world,
        name,
        quantity,
        commit,
    ):
        self.calls.append(
            {
                "db": db,
                "world": world,
                "name": name,
                "quantity": quantity,
                "commit": commit,
            }
        )

        citizen = SimpleNamespace(
            id="citizen-1",
            name=name,
            x=10.0,
            y=20.0,
            status="ACTIVE",
            total_roses=quantity,
            wealth=quantity * 10,
        )

        return citizen, self.created


def build_context(
    world_service,
    citizen_service,
):
    return ExperienceContext(
        experience_slug="world001",
        session="fake-db",
        services={
            "world_service": world_service,
            "citizen_service": citizen_service,
        },
    )


def build_event(
    event_type=EventType.GIFT,
    gift_name="Rose",
    quantity=3,
):
    return LiveEvent.create(
        type=event_type,
        provider="dev",
        viewer=Viewer(
            provider_user_id="dev-1",
            username="@gabriel",
            display_name="Gabriel",
        ),
        payload={
            "gift_name": gift_name,
            "quantity": quantity,
        },
    )


@pytest.mark.asyncio
async def test_rose_creates_citizen_output():
    world_service = FakeWorldService()
    citizen_service = FakeCitizenService(created=True)

    experience = World001Experience()

    outputs = await experience.handle_event(
        build_event(quantity=3),
        build_context(
            world_service,
            citizen_service,
        ),
    )

    assert len(outputs) == 1
    assert outputs[0].type == "citizen_spawned"

    assert outputs[0].data["citizen"]["name"] == "@gabriel"
    assert outputs[0].data["citizen"]["wealth"] == 30

    assert citizen_service.calls == [
        {
            "db": "fake-db",
            "world": SimpleNamespace(id="world-1"),
            "name": "@gabriel",
            "quantity": 3,
            "commit": False,
        }
    ]


@pytest.mark.asyncio
async def test_rose_supports_existing_citizen():
    world_service = FakeWorldService()
    citizen_service = FakeCitizenService(created=False)

    experience = World001Experience()

    outputs = await experience.handle_event(
        build_event(quantity=7),
        build_context(
            world_service,
            citizen_service,
        ),
    )

    assert len(outputs) == 1
    assert outputs[0].type == "citizen_supported"
    assert outputs[0].data["quantity"] == 7


@pytest.mark.asyncio
async def test_non_rose_gift_is_ignored():
    world_service = FakeWorldService()
    citizen_service = FakeCitizenService()

    experience = World001Experience()

    outputs = await experience.handle_event(
        build_event(gift_name="TikTok Universe"),
        build_context(
            world_service,
            citizen_service,
        ),
    )

    assert outputs == []
    assert world_service.calls == []
    assert citizen_service.calls == []


@pytest.mark.asyncio
async def test_non_gift_event_is_ignored():
    world_service = FakeWorldService()
    citizen_service = FakeCitizenService()

    experience = World001Experience()

    outputs = await experience.handle_event(
        build_event(
            event_type=EventType.COMMENT,
        ),
        build_context(
            world_service,
            citizen_service,
        ),
    )

    assert outputs == []
    assert world_service.calls == []
    assert citizen_service.calls == []