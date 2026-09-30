from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db


router = APIRouter()


@router.get("/health")
def health_check(
    db: Session = Depends(get_db)
):
    database_status = "ok"
    overall_status = "ok"

    try:
        db.execute(
            text("SELECT 1")
        )

    except SQLAlchemyError:
        database_status = "error"
        overall_status = "degraded"

    return {
        "status": overall_status,
        "database": database_status,
        "service": "world-001-backend"
    }