from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.citizen import Citizen
from app.models.world import World
from app.models.world_tree import WorldTree


TREE_MAX_WOOD = 10
TREE_REGROW_SECONDS = 30


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    )


def get_or_create_tree(
    db: Session,
    world: World,
    tree_key: str
) -> WorldTree:

    statement = (
        select(WorldTree)
        .where(
            WorldTree.world_id == world.id,
            WorldTree.tree_key == tree_key
        )
    )

    tree = db.scalar(
        statement
    )

    if tree is not None:
        return tree

    tree = WorldTree(
        world_id=world.id,
        tree_key=tree_key,
        wood_amount=TREE_MAX_WOOD,
        max_wood=TREE_MAX_WOOD,
        status="GROWN",
        regrow_at=None
    )

    db.add(tree)
    db.flush()

    return tree


def refresh_tree_regrowth(
    tree: WorldTree
) -> bool:

    if tree.status != "STUMP":
        return False

    if tree.regrow_at is None:
        return False

    if tree.regrow_at > utc_now():
        return False

    tree.status = "GROWN"
    tree.wood_amount = tree.max_wood
    tree.regrow_at = None

    return True


def chop_tree(
    db: Session,
    world: World,
    citizen_id: str,
    tree_key: str
) -> tuple[
    Citizen | None,
    WorldTree | None,
    str
]:

    citizen_statement = (
        select(Citizen)
        .where(
            Citizen.id == citizen_id,
            Citizen.world_id == world.id
        )
    )

    citizen = db.scalar(
        citizen_statement
    )

    if citizen is None:
        return (
            None,
            None,
            "CITIZEN_NOT_FOUND"
        )

    tree = get_or_create_tree(
        db=db,
        world=world,
        tree_key=tree_key
    )

    refresh_tree_regrowth(
        tree
    )

    if (
        tree.status != "GROWN"
        or tree.wood_amount <= 0
    ):
        db.commit()
        db.refresh(tree)
        db.refresh(citizen)

        return (
            citizen,
            tree,
            "TREE_UNAVAILABLE"
        )

    # =====================================================
    # ATOMIC RESOURCE CHANGE
    # =====================================================

    tree.wood_amount -= 1
    citizen.wood += 1

    # Última unidade.
    if tree.wood_amount <= 0:
        tree.wood_amount = 0
        tree.status = "STUMP"

        tree.regrow_at = (
            utc_now()
            + timedelta(
                seconds=TREE_REGROW_SECONDS
            )
        )

    # Citizen + Tree são persistidos juntos.
    db.commit()

    db.refresh(citizen)
    db.refresh(tree)

    return (
        citizen,
        tree,
        "COLLECTED"
    )

def get_world_tree_states(
    db: Session,
    world: World
) -> list[WorldTree]:

    statement = (
        select(WorldTree)
        .where(
            WorldTree.world_id == world.id
        )
        .order_by(
            WorldTree.tree_key
        )
    )

    trees = list(
        db.scalars(statement).all()
    )

    changed = False

    for tree in trees:
        if refresh_tree_regrowth(tree):
            changed = True

    if changed:
        db.commit()

        for tree in trees:
            db.refresh(tree)

    return trees