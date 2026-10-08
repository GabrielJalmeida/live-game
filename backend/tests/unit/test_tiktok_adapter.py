from types import SimpleNamespace

from app.events import EventType
from app.providers.tiktok.adapter import (
    build_viewer,
    extract_provider_event_id,
    from_comment,
    from_gift,
    normalize_username,
)


def make_user():
    return SimpleNamespace(
        id=12345,
        unique_id="gabriel",
        nickname="Gabriel",
    )


def make_comment_event(
    comment="hello",
):
    return SimpleNamespace(
        user=make_user(),
        comment=comment,
    )


def make_gift_event(
    gift_name="Rose",
    quantity=3,
    streakable=False,
    streaking=False,
):
    gift = SimpleNamespace(
        name=gift_name,
        streakable=streakable,
        gift_id=5655,
    )

    return SimpleNamespace(
        user=make_user(),
        gift=gift,
        gift_id=5655,
        repeat_count=quantity,
        streaking=streaking,
        order_id="order-123",
        log_id="log-123",
    )


def test_normalize_username_adds_at():
    assert normalize_username("gabriel") == "@gabriel"
    assert normalize_username("@gabriel") == "@gabriel"


def test_build_viewer_maps_tiktok_user():
    viewer = build_viewer(make_user())

    assert viewer.provider_user_id == "12345"
    assert viewer.username == "@gabriel"
    assert viewer.display_name == "Gabriel"


def test_extract_provider_event_id_prefers_order_id():
    event = SimpleNamespace(
        order_id="order-123",
        log_id="log-456",
    )

    assert extract_provider_event_id(event) == "order-123"


def test_extract_provider_event_id_falls_back_to_log_id():
    event = SimpleNamespace(
        order_id=None,
        log_id="log-456",
    )

    assert extract_provider_event_id(event) == "log-456"


def test_comment_becomes_generic_live_event():
    event = from_comment(
        make_comment_event("hello"),
        session_id="room-123",
    )

    assert event is not None
    assert event.type == EventType.COMMENT
    assert event.provider == "tiktok"
    assert event.session_id == "room-123"
    assert event.viewer is not None
    assert event.viewer.username == "@gabriel"
    assert event.payload == {
        "text": "hello",
    }


def test_empty_comment_is_ignored():
    event = from_comment(
        make_comment_event("   "),
    )

    assert event is None


def test_gift_becomes_generic_live_event():
    event = from_gift(
        make_gift_event(
            gift_name="Rose",
            quantity=3,
        ),
        session_id="room-123",
    )

    assert event is not None
    assert event.type == EventType.GIFT
    assert event.provider == "tiktok"
    assert event.provider_event_id == "order-123"

    assert event.viewer is not None
    assert event.viewer.username == "@gabriel"

    assert event.payload == {
        "gift_id": 5655,
        "gift_name": "Rose",
        "quantity": 3,
    }


def test_intermediate_streak_event_is_ignored():
    event = from_gift(
        make_gift_event(
            gift_name="Rose",
            quantity=2,
            streakable=True,
            streaking=True,
        )
    )

    assert event is None