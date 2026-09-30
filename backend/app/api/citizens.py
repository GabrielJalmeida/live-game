from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.citizen_service import get_world_citizens
from app.services.world_service import get_or_create_world


router = APIRouter()


@router.get("/citizens")
def list_citizens(db: Session = Depends(get_db)):
    world = get_or_create_world(db)

    citizens = get_world_citizens(
        db=db,
        world=world
    )

    return [
    {
        "id": citizen.id,
        "name": citizen.name,
        "x": citizen.x,
        "y": citizen.y,
        "status": citizen.status,
        "total_roses": citizen.total_roses,
        "wealth": citizen.wealth
    }
    for citizen in citizens
]