import pytest

from pydantic import ValidationError

from app.api.dev_events import RoseEventRequest


def test_valid_rose_event():
    event = RoseEventRequest(
        username="gabriel",
        quantity=1,
        provider="dev"
    )

    assert event.username == "@gabriel"
    assert event.quantity == 1
    assert event.provider == "dev"


def test_username_is_trimmed():
    event = RoseEventRequest(
        username="   gabriel   "
    )

    assert event.username == "@gabriel"


def test_username_cannot_be_empty():
    with pytest.raises(ValidationError):
        RoseEventRequest(
            username="   "
        )


def test_quantity_cannot_be_zero():
    with pytest.raises(ValidationError):
        RoseEventRequest(
            username="@gabriel",
            quantity=0
        )


def test_quantity_cannot_be_negative():
    with pytest.raises(ValidationError):
        RoseEventRequest(
            username="@gabriel",
            quantity=-5
        )


def test_provider_cannot_be_empty():
    with pytest.raises(ValidationError):
        RoseEventRequest(
            username="@gabriel",
            provider="   "
        )


def test_optional_fields_become_none_when_empty():
    event = RoseEventRequest(
        username="@gabriel",
        provider_user_id="   ",
        provider_event_id="   ",
        display_name="   "
    )

    assert event.provider_user_id is None
    assert event.provider_event_id is None
    assert event.display_name is None