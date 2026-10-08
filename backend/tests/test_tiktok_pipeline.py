import pytest

from app.events import EventType
from app.providers.tiktok import listener


class FakeUser:
    id = 12345
    unique_id = "gabriel"
    nickname = "Gabriel"


class FakeGift:
    name = "Rose"
    gift_id = 5655
    streakable = False


class FakeGiftEvent:
    user = FakeUser()
    gift = FakeGift()
    gift_id = 5655
    repeat_count = 3
    streaking = False
    order_id = "integration-order-001"
    log_id = "integration-log-001"


class FakeResult:
    status = "processed"


@pytest.mark.asyncio
async def test_tiktok_gift_flows_through_adapter_into_ingestion(
    monkeypatch,
):
    received = []

    async def fake_ingest(event):
        received.append(event)
        return FakeResult()

    monkeypatch.setattr(
        listener,
        "ingest_tiktok_event",
        fake_ingest,
    )

    await listener.on_gift(
        FakeGiftEvent()
    )

    assert len(received) == 1

    event = received[0]

    assert event.type == EventType.GIFT
    assert event.provider == "tiktok"

    assert event.provider_event_id == (
        "integration-order-001"
    )

    assert event.viewer is not None
    assert event.viewer.provider_user_id == "12345"
    assert event.viewer.username == "@gabriel"

    assert event.payload == {
        "gift_id": 5655,
        "gift_name": "Rose",
        "quantity": 3,
    }


@pytest.mark.asyncio
async def test_tiktok_comment_flows_through_adapter_into_ingestion(
    monkeypatch,
):
    received = []

    class FakeCommentEvent:
        user = FakeUser()
        comment = "hello engine"

    async def fake_ingest(event):
        received.append(event)
        return FakeResult()

    monkeypatch.setattr(
        listener,
        "ingest_tiktok_event",
        fake_ingest,
    )

    await listener.on_comment(
        FakeCommentEvent()
    )

    assert len(received) == 1

    event = received[0]

    assert event.type == EventType.COMMENT
    assert event.provider == "tiktok"

    assert event.viewer is not None
    assert event.viewer.username == "@gabriel"

    assert event.payload == {
        "text": "hello engine",
    }