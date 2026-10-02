from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path
)
from pydantic import (
    BaseModel,
    Field
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.world_service import (
    get_or_create_world
)
from app.services.world_tree_service import (
    chop_tree,
    get_world_tree_states
)


router = APIRouter()

@router.get("/trees")
def list_world_trees(
    db: Session = Depends(get_db)
):
    world = get_or_create_world(
        db
    )

    trees = get_world_tree_states(
        db=db,
        world=world
    )

    return [
        {
            "tree_key": tree.tree_key,
            "wood_amount": tree.wood_amount,
            "max_wood": tree.max_wood,
            "status": tree.status,
            "regrow_at": (
                tree.regrow_at.isoformat()
                if tree.regrow_at
                else None
            )
        }
        for tree in trees
    ]

class ChopTreeRequest(BaseModel):
    citizen_id: str = Field(
        min_length=1,
        max_length=36
    )


@router.post(
    "/trees/{tree_key}/chop"
)
def chop_world_tree(
    payload: ChopTreeRequest,
    tree_key: str = Path(
        min_length=1,
        max_length=100
    ),
    db: Session = Depends(
        get_db
    )
):
    world = get_or_create_world(
        db
    )

    citizen, tree, status = chop_tree(
        db=db,
        world=world,
        citizen_id=payload.citizen_id,
        tree_key=tree_key
    )

    if status == "CITIZEN_NOT_FOUND":
        raise HTTPException(
            status_code=404,
            detail="Citizen not found."
        )

    if tree is None:
        raise HTTPException(
            status_code=500,
            detail="Tree state unavailable."
        )

    return {
        "status": status.lower(),
        "citizen": {
            "id": citizen.id,
            "name": citizen.name,
            "wood": citizen.wood
        },
        "tree": {
            "tree_key": tree.tree_key,
            "wood_amount": tree.wood_amount,
            "max_wood": tree.max_wood,
            "status": tree.status,
            "regrow_at": (
                tree.regrow_at.isoformat()
                if tree.regrow_at
                else None
            )
        }
    }