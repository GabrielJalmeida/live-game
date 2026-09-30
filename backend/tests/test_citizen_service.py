from unittest.mock import MagicMock

from app.services.citizen_service import (
    create_or_support_citizen,
    ROSE_WEALTH_VALUE,
)


def test_existing_citizen_receives_support():
    db = MagicMock()

    world = MagicMock()
    world.id = "world-test"

    citizen = MagicMock()

    citizen.id = "citizen-001"
    citizen.world_id = world.id
    citizen.name = "@gabriel"
    citizen.total_roses = 3
    citizen.wealth = 30

    db.scalar.return_value = citizen

    result, created = create_or_support_citizen(
        db=db,
        world=world,
        name="@gabriel",
        quantity=2,
        commit=False,
    )

    assert created is False

    assert result.total_roses == 5

    assert result.wealth == (
        30 + 2 * ROSE_WEALTH_VALUE
    )

    db.flush.assert_called_once()


def test_existing_citizen_can_commit():
    db = MagicMock()

    world = MagicMock()
    world.id = "world-test"

    citizen = MagicMock()

    citizen.id = "citizen-001"
    citizen.world_id = world.id
    citizen.name = "@gabriel"
    citizen.total_roses = 1
    citizen.wealth = 10

    db.scalar.return_value = citizen

    result, created = create_or_support_citizen(
        db=db,
        world=world,
        name="@gabriel",
        quantity=1,
        commit=True,
    )

    assert created is False

    assert result.total_roses == 2
    assert result.wealth == 20

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(citizen)


def test_quantity_never_goes_below_one():
    db = MagicMock()

    world = MagicMock()
    world.id = "world-test"

    citizen = MagicMock()

    citizen.id = "citizen-001"
    citizen.world_id = world.id
    citizen.name = "@gabriel"
    citizen.total_roses = 1
    citizen.wealth = 10

    db.scalar.return_value = citizen

    result, created = create_or_support_citizen(
        db=db,
        world=world,
        name="@gabriel",
        quantity=0,
        commit=False,
    )

    assert created is False

    assert result.total_roses == 2
    assert result.wealth == 20