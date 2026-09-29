import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.citizen import Citizen
from app.models.world import World


def create_citizen(
    db: Session,
    world: World,
    name: str
) -> Citizen:

    citizen = Citizen(
        world_id=world.id,
        name=name,
        x=random.uniform(1100, 1900),
        y=random.uniform(1100, 1900),
        status="ACTIVE"
    )

    db.add(citizen)
    db.commit()
    db.refresh(citizen)

    return citizen


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