import pytest

from app.events import EventType
from app.providers.tiktok import listener as module


class FakeViewer:
    unique_id = "gabriel"
    id = 123
    nickname = "Gabriel"


class FakeCommentEvent:
    user = FakeViewer()
    comment = "hello engine"


class FakeGift:
    name = "Rose"
    gift_id = 5655
    streakable = False


class FakeGiftEvent:
    user = FakeViewer()
    gift = FakeGift()
    gift_id = 5655
    repeat_count = 3
    streaking = False
    order_id = "gift-order-123"
    log_id = "gift-log-123"


class FakeResult:
    status = "processed"


@pytest.mark.asyncio
async def test_on_comment_sends_generic_live_event(
    monkeypatch,
):
    received = []

    async def fake_ingest(event):
        received.append(event)
        return FakeResult()

    monkeypatch.setattr(
        module,
        "ingest_tiktok_event",
        fake_ingest,
    )

    await module.on_comment(
        FakeCommentEvent()
    )

    assert len(received) == 1

    event = received[0]

    assert event.type == EventType.COMMENT
    assert event.provider == "tiktok"
    assert event.viewer.username == "@gabriel"
    assert event.payload == {
        "text": "hello engine",
    }


@pytest.mark.asyncio
async def test_on_comment_does_not_create_rose_from_command(
    monkeypatch,
):
    received = []

    async def fake_ingest(event):
        received.append(event)
        return FakeResult()

    monkeypatch.setattr(
        module,
        "ingest_tiktok_event",
        fake_ingest,
    )

    class RoseCommandEvent:
        user = FakeViewer()
        comment = "!rose"

    await module.on_comment(
        RoseCommandEvent()
    )

    assert len(received) == 1
    assert received[0].type == EventType.COMMENT
    assert received[0].payload == {
        "text": "!rose",
    }


@pytest.mark.asyncio
async def test_on_gift_sends_generic_gift_event(
    monkeypatch,
):
    received = []

    async def fake_ingest(event):
        received.append(event)
        return FakeResult()

    monkeypatch.setattr(
        module,
        "ingest_tiktok_event",
        fake_ingest,
    )

    await module.on_gift(
        FakeGiftEvent()
    )

    assert len(received) == 1

    event = received[0]

    assert event.type == EventType.GIFT
    assert event.provider == "tiktok"
    assert event.provider_event_id == "gift-order-123"

    assert event.viewer.username == "@gabriel"

    assert event.payload == {
        "gift_id": 5655,
        "gift_name": "Rose",
        "quantity": 3,
    }


@pytest.mark.asyncio
async def test_on_gift_does_not_process_intermediate_streak(
    monkeypatch,
):
    received = []

    async def fake_ingest(event):
        received.append(event)
        return FakeResult()

    monkeypatch.setattr(
        module,
        "ingest_tiktok_event",
        fake_ingest,
    )

    class StreakGift:
        name = "Rose"
        gift_id = 5655
        streakable = True

    class StreakEvent:
        user = FakeViewer()
        gift = StreakGift()
        gift_id = 5655
        repeat_count = 2
        streaking = True
        order_id = "streak-order"
        log_id = "streak-log"

    await module.on_gift(
        StreakEvent()
    )

    assert received == []