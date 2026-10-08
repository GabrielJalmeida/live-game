import pytest

from app.events import EventType, OutputEvent
from app.api.dev_engine_events import (
    DevEventRequest,
    DevViewerRequest,
    build_live_event,
    receive_dev_event,
)


def test_build_live_event_creates_generic_gift():
    request = DevEventRequest(
        type=EventType.GIFT,
        provider="dev",
        provider_event_id="gift-001",
        viewer=DevViewerRequest(
            provider_user_id="user-001",
            username="gabriel",
        ),
        payload={
            "gift_id": 5655,
            "gift_name": "Rose",
            "quantity": 3,
        },
    )

    event = build_live_event(request)

    assert event.provider_event_id == "gift-001"

    assert event.type == EventType.GIFT
    assert event.provider == "dev"
    assert event.provider == "dev"

    assert event.viewer is not None
    assert event.viewer.username == "@gabriel"

    assert event.payload == {
        "gift_id": 5655,
        "gift_name": "Rose",
        "quantity": 3,
    }


def test_build_live_event_supports_event_without_viewer():
    request = DevEventRequest(
        type=EventType.JOIN,
        provider="dev",
        payload={},
    )

    event = build_live_event(request)

    assert event.type == EventType.JOIN
    assert event.viewer is None


class FakeDB:
    def __init__(self):
        self.operations = []

    def commit(self):
        self.operations.append("commit")

    def rollback(self):
        self.operations.append("rollback")


class FakeLiveUser:
    id = "live-user-1"


class FakeLiveEventRecord:
    id = "db-event-1"


class FakeEngine:
    def __init__(self):
        self.operations = []
        self.outputs = [
            OutputEvent(
                type="test_output",
                experience="world001",
                data={
                    "ok": True,
                },
            )
        ]

    async def dispatch(
        self,
        event,
        context,
        publish,
    ):
        self.operations.append(
            ("dispatch", publish)
        )

        return self.outputs

    async def publish(self, outputs):
        self.operations.append("publish")


@pytest.mark.asyncio
async def test_dev_event_delegates_to_ingestion_service(
    monkeypatch,
):
    import app.api.dev_engine_events as module

    db = FakeDB()
    calls = []

    class FakeResult:
        status = "processed"
        event_id = "record-1"
        outputs = []

    async def fake_ingest_event(
        db,
        event,
        publish,
    ):
        calls.append(
            {
                "db": db,
                "event": event,
                "publish": publish,
            }
        )

        return FakeResult()

    monkeypatch.setattr(
        module,
        "ingest_event",
        fake_ingest_event,
    )

    request = DevEventRequest(
        type=EventType.GIFT,
        provider="dev",
        provider_event_id="provider-event-1",
        viewer=DevViewerRequest(
            provider_user_id="user-1",
            username="gabriel",
        ),
        payload={
            "gift_name": "Rose",
            "quantity": 3,
        },
    )

    response = await module.receive_dev_event(
        request,
        db,
    )

    assert response == {
        "status": "processed",
        "event_id": "record-1",
        "outputs": [],
    }

    assert len(calls) == 1

    call = calls[0]

    assert call["db"] is db
    assert call["publish"] is True

    assert call["event"].type == EventType.GIFT
    assert call["event"].provider == "dev"
    assert (
        call["event"].provider_event_id
        == "provider-event-1"
    )

    assert call["event"].viewer is not None
    assert call["event"].viewer.username == "@gabriel"