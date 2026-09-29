from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import engine


router = APIRouter()


@router.get("/health")
def health():
    database_status = "ok"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    except Exception:
        database_status = "error"

    return {
        "status": "ok",
        "database": database_status,
        "simulation": "not_started",
        "live_provider": "not_connected"
    }