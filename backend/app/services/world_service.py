from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.world import World


WORLD_CODE = "WORLD_001"


def get_or_create_world(db: Session) -> World:
    statement = select(World).where(
        World.code == WORLD_CODE
    )

    world = db.scalar(statement)

    if world:
        return world

    world = World(
        code=WORLD_CODE,
        name="WORLD 001",
        seed=1001,
        status="RUNNING",
        world_time=0.0,
        day=1
    )

    db.add(world)
    db.commit()
    db.refresh(world)

    return world