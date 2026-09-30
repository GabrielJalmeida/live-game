import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.citizen import Citizen
from app.models.world import World


ROSE_WEALTH_VALUE = 10


def create_or_support_citizen(
    db: Session,
    world: World,
    name: str,
    quantity: int = 1,
    commit: bool = True
) -> tuple[Citizen, bool]:

    quantity = max(
        1,
        quantity
    )

    statement = (
        select(Citizen)
        .where(
            Citizen.world_id == world.id,
            Citizen.name == name
        )
        .order_by(
            Citizen.created_at
        )
        .limit(1)
    )

    citizen = db.scalar(
        statement
    )

    if citizen:
        citizen.total_roses += quantity

        citizen.wealth += (
            quantity
            * ROSE_WEALTH_VALUE
        )

        if commit:
            db.commit()
            db.refresh(citizen)

        else:
            db.flush()

        return citizen, False

    citizen = Citizen(
        world_id=world.id,
        name=name,
        x=random.uniform(
            1100,
            1900
        ),
        y=random.uniform(
            1100,
            1900
        ),
        status="ACTIVE",
        total_roses=quantity,
        wealth=(
            quantity
            * ROSE_WEALTH_VALUE
        )
    )

    db.add(citizen)

    if commit:
        db.commit()
        db.refresh(citizen)

    else:
        db.flush()

    return citizen, True


def get_world_citizens(
    db: Session,
    world: World
) -> list[Citizen]:

    statement = (
        select(Citizen)
        .where(Citizen.world_id == world.id)
        .order_by(Citizen.created_at)
    )

    return list(db.scalars(statement).all())