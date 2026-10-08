import pytest

from app.events import EventType, LiveEvent, Viewer
from app.providers.tiktok import listener as module


class FakeDB:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeSessionFactory:
    def __init__(self):
        self.created = []

    def __call__(self):
        db = FakeDB()
        self.created.append(db)
        return db


class FakeResult:
    status = "processed"


@pytest.mark.asyncio
async def test_ingest_tiktok_event_creates_and_closes_session(
    monkeypatch,
):
    sessions = FakeSessionFactory()
    calls = []

    monkeypatch.setattr(
        module,
        "SessionLocal",
        sessions,
    )

    async def fake_ingest_event(
        db,
        event,
        context,
        publish,
    ):
        calls.append(
            {
                "db": db,
                "event": event,
                "context": context,
                "publish": publish,
            }
        )

        return FakeResult()

    monkeypatch.setattr(
        module,
        "ingest_event",
        fake_ingest_event,
    )

    event = LiveEvent.create(
        type=EventType.GIFT,
        provider="tiktok",
        provider_event_id="order-123",
        viewer=Viewer(
            provider_user_id="123",
            username="@gabriel",
        ),
        payload={
            "gift_name": "Rose",
            "quantity": 3,
        },
    )

    result = await module.ingest_tiktok_event(
        event
    )

    assert result.status == "processed"

    assert len(sessions.created) == 1
    assert len(calls) == 1

    assert calls[0]["db"] is sessions.created[0]
    assert calls[0]["event"] is event
    assert calls[0]["publish"] is True
    assert (
        calls[0]["context"].experience_slug
        == "world001"
    )
    assert sessions.created[0].closed is True