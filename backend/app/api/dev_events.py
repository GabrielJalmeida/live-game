from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.realtime.connection_manager import manager
from app.services.citizen_service import create_citizen
from app.services.world_service import get_or_create_world


router = APIRouter()


class RoseEventRequest(BaseModel):
    username: str


@router.post("/dev/events/rose")
async def simulate_rose(
    payload: RoseEventRequest,
    db: Session = Depends(get_db)
):
    world = get_or_create_world(db)

    citizen = create_citizen(
        db=db,
        world=world,
        name=payload.username
    )

    await manager.broadcast({
        "type": "citizen_spawned",
        "citizen": {
            "id": citizen.id,
            "name": citizen.name,
            "x": citizen.x,
            "y": citizen.y,
            "status": citizen.status
        }
    })

    return {
        "status": "created",
        "citizen": {
            "id": citizen.id,
            "name": citizen.name,
            "x": citizen.x,
            "y": citizen.y,
            "status": citizen.status
        }
    }