from datetime import datetime, timezone

from app.events import (
    EventType,
    LiveEvent,
    OutputEvent,
    Viewer,
)


def test_live_event_can_represent_generic_gift():
    viewer = Viewer(
        provider_user_id="123",
        username="@maria",
        display_name="Maria",
    )

    event = LiveEvent.create(
        type=EventType.GIFT,
        provider="tiktok",
        session_id="live-001",
        viewer=viewer,
        payload={
            "gift_id": "5655",
            "gift_name": "Rose",
            "quantity": 1,
        },
    )

    assert event.type is EventType.GIFT
    assert event.provider == "tiktok"
    assert event.viewer.username == "@maria"
    assert event.payload["gift_name"] == "Rose"


def test_rose_is_payload_not_event_type():
    event = LiveEvent.create(
        type=EventType.GIFT,
        provider="tiktok",
        viewer=None,
        payload={
            "gift_name": "Rose",
            "quantity": 1,
        },
    )

    assert event.type is EventType.GIFT
    assert event.payload["gift_name"] == "Rose"


def test_live_event_has_unique_id():
    event_1 = LiveEvent.create(
        type=EventType.COMMENT,
        provider="dev",
        viewer=None,
        payload={"text": "A"},
    )

    event_2 = LiveEvent.create(
        type=EventType.COMMENT,
        provider="dev",
        viewer=None,
        payload={"text": "B"},
    )

    assert event_1.event_id != event_2.event_id


def test_live_event_serializes():
    occurred_at = datetime(
        2026,
        10,
        8,
        16,
        0,
        tzinfo=timezone.utc,
    )

    event = LiveEvent.create(
        event_id="evt_test",
        type=EventType.COMMENT,
        provider="dev",
        session_id="dev-session",
        occurred_at=occurred_at,
        viewer=Viewer(
            provider_user_id="dev-1",
            username="@gabriel",
        ),
        payload={
            "text": "hello",
        },
    )

    data = event.to_dict()

    assert data["event_id"] == "evt_test"
    assert data["type"] == "COMMENT"
    assert data["provider"] == "dev"
    assert data["payload"]["text"] == "hello"


def test_output_event_is_transport_agnostic():
    output = OutputEvent(
        type="CITIZEN_SPAWNED",
        experience="world001",
        data={
            "citizen_id": "citizen-001",
        },
    )

    data = output.to_dict()

    assert data["type"] == "CITIZEN_SPAWNED"
    assert data["experience"] == "world001"
    assert data["data"]["citizen_id"] == "citizen-001"