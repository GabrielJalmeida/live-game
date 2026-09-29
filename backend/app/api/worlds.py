from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.world_service import get_or_create_world


router = APIRouter()


@router.get("/world")
def get_world(db: Session = Depends(get_db)):
    world = get_or_create_world(db)

    return {
        "id": world.id,
        "code": world.code,
        "name": world.name,
        "status": world.status,
        "day": world.day,
        "world_time": world.world_time,
        "seed": world.seed
    }