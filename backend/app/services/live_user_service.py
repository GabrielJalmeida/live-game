from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.live_user import LiveUser


def get_or_create_live_user(
    db: Session,
    provider: str,
    provider_user_id: str,
    username: str,
    display_name: str | None = None
) -> LiveUser:

    statement = select(LiveUser).where(
        LiveUser.provider == provider,
        LiveUser.provider_user_id == provider_user_id
    )

    live_user = db.scalar(statement)

    if live_user:
        live_user.username = username
        live_user.display_name = display_name
        live_user.last_seen_at = datetime.utcnow()

        db.commit()
        db.refresh(live_user)

        return live_user

    live_user = LiveUser(
        provider=provider,
        provider_user_id=provider_user_id,
        username=username,
        display_name=display_name
    )

    db.add(live_user)
    db.commit()
    db.refresh(live_user)

    return live_user