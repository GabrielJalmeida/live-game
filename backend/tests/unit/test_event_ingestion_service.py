import pytest

from app.events import EventType, LiveEvent, Viewer
from app.runtime.experience_context import ExperienceContext
from app.services import event_ingestion_service as module


class FakeDB:
    def __init__(self):
        self.operations = []

    def commit(self):
        self.operations.append("commit")

    def rollback(self):
        self.operations.append("rollback")


class FakeLiveUser:
    id = "user-1"


class FakeRecord:
    id = "record-1"


class FakeEngine:
    def __init__(self):
        self.dispatch_calls = []
        self.publish_calls = []

    async def dispatch(
        self,
        event,
        context,
        publish,
    ):
        self.dispatch_calls.append(
            {
                "event": event,
                "context": context,
                "publish": publish,
            }
        )

        return []  # neste teste queremos só validar o fluxo

    async def publish(self, outputs):
        self.publish_calls.append(outputs)


def build_event():
    return LiveEvent.create(
        type=EventType.GIFT,
        provider="dev",
        provider_event_id="provider-event-1",
        viewer=Viewer(
            provider_user_id="user-1",
            username="@gabriel",
        ),
        payload={
            "gift_name": "Rose",
            "quantity": 3,
        },
    )


@pytest.mark.asyncio
async def test_ingest_event_uses_provider_event_id(
    monkeypatch,
):
    db = FakeDB()
    fake_engine = FakeEngine()

    monkeypatch.setattr(
        module,
        "engine",
        fake_engine,
    )

    monkeypatch.setattr(
        module,
        "get_or_create_live_user",
        lambda **kwargs: FakeLiveUser(),
    )

    register_calls = []

    def fake_register_live_event(**kwargs):
        register_calls.append(kwargs)
        return FakeRecord(), True

    monkeypatch.setattr(
        module,
        "register_live_event",
        fake_register_live_event,
    )

    monkeypatch.setattr(
        module,
        "mark_processed",
        lambda db, event, commit: db.operations.append(
            ("mark_processed", commit)
        ),
    )

    result = await module.ingest_event(
        db=db,
        event=build_event(),
        context=ExperienceContext(
            experience_slug="world001",
        ),
    )

    assert result.status == "processed"
    assert result.event_id == "record-1"

    assert register_calls[0]["provider_event_id"] == (
        "provider-event-1"
    )

    assert fake_engine.dispatch_calls[0]["publish"] is False
    assert fake_engine.publish_calls == [[]]

    assert db.operations == [
        ("mark_processed", False),
        "commit",
    ]


@pytest.mark.asyncio
async def test_duplicate_event_does_not_dispatch(
    monkeypatch,
):
    db = FakeDB()
    fake_engine = FakeEngine()

    monkeypatch.setattr(
        module,
        "engine",
        fake_engine,
    )

    monkeypatch.setattr(
        module,
        "get_or_create_live_user",
        lambda **kwargs: FakeLiveUser(),
    )

    monkeypatch.setattr(
        module,
        "register_live_event",
        lambda **kwargs: (
            FakeRecord(),
            False,
        ),
    )

    result = await module.ingest_event(
        db=db,
        event=build_event(),
        context=ExperienceContext(
            experience_slug="world001",
        ),
    )

    assert result.status == "duplicate"
    assert result.event_id == "record-1"
    assert result.outputs == []

    assert fake_engine.dispatch_calls == []
    assert fake_engine.publish_calls == []