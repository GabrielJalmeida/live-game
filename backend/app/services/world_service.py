from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.world import World


WORLD_CODE = "WORLD_001"
WORLD_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def calculate_world_day(world: World) -> int:
    if world.created_at is None:
        return 1

    created_at = world.created_at

    # O SQLite CURRENT_TIMESTAMP trabalha em UTC.
    # Como ele retorna datetime sem timezone,
    # informamos explicitamente que esse horário é UTC.
    if created_at.tzinfo is None:
        created_at = created_at.replace(
            tzinfo=timezone.utc
        )

    start_date = created_at.astimezone(
        WORLD_TIMEZONE
    ).date()

    today = datetime.now(
        WORLD_TIMEZONE
    ).date()

    days_passed = (
        today - start_date
    ).days

    return max(
        1,
        days_passed + 1
    )


def get_or_create_world(db: Session) -> World:
    statement = select(World).where(
        World.code == WORLD_CODE
    )

    world = db.scalar(statement)

    if world is None:
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

    current_day = calculate_world_day(world)

    if world.day != current_day:
        world.day = current_day

        db.commit()
        db.refresh(world)

    return world