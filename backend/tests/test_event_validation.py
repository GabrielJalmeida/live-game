import pytest

from pydantic import ValidationError

from app.api.dev_engine_events import (
    DevEventRequest,
    DevViewerRequest,
)
from app.events import EventType


def test_valid_generic_gift_event():
    event = DevEventRequest(
        type=EventType.GIFT,
        provider="dev",
        provider_event_id="gift-001",
        viewer=DevViewerRequest(
            username="gabriel",
        ),
        payload={
            "gift_name": "Rose",
            "quantity": 1,
        },
    )

    assert event.type is EventType.GIFT
    assert event.provider == "dev"
    assert event.provider_event_id == "gift-001"
    assert event.viewer is not None
    assert event.viewer.username == "@gabriel"


def test_username_is_trimmed_and_normalized():
    viewer = DevViewerRequest(
        username="   gabriel   ",
    )

    assert viewer.username == "@gabriel"


def test_username_cannot_be_empty():
    with pytest.raises(ValidationError):
        DevViewerRequest(
            username="   ",
        )


def test_provider_cannot_be_empty():
    with pytest.raises(ValidationError):
        DevEventRequest(
            type=EventType.COMMENT,
            provider="   ",
        )


def test_optional_viewer_fields_become_none_when_empty():
    viewer = DevViewerRequest(
        username="@gabriel",
        provider_user_id="   ",
        display_name="   ",
        avatar_url="   ",
    )

    assert viewer.provider_user_id is None
    assert viewer.display_name is None
    assert viewer.avatar_url is None


def test_optional_event_ids_become_none_when_empty():
    event = DevEventRequest(
        type=EventType.COMMENT,
        provider="dev",
        provider_event_id="   ",
        event_id="   ",
        session_id="   ",
    )

    assert event.provider_event_id is None
    assert event.event_id is None
    assert event.session_id is None


def test_payload_defaults_to_empty_dict():
    event = DevEventRequest(
        type=EventType.JOIN,
        provider="dev",
    )

    assert event.payload == {}


def test_invalid_event_type_is_rejected():
    with pytest.raises(ValidationError):
        DevEventRequest(
            type="ROSE",
            provider="dev",
        )