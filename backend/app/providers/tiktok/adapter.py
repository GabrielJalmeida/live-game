from typing import Any

from TikTokLive.events import CommentEvent, GiftEvent

from app.events import EventType, LiveEvent, Viewer


def normalize_username(username: str) -> str:
    username = username.strip()

    if not username:
        raise ValueError(
            "username não pode estar vazio"
        )

    if not username.startswith("@"):
        username = f"@{username}"

    return username


def build_viewer(user: Any) -> Viewer:
    username_value = (
        getattr(user, "unique_id", None)
        or getattr(user, "display_id", None)
    )

    if not username_value:
        raise ValueError(
            "Evento TikTok não possui username."
        )

    username = normalize_username(
        username_value
    )

    provider_user_id = (
        getattr(user, "id", None)
        or getattr(user, "user_id", None)
    )

    return Viewer(
        provider_user_id=(
            str(provider_user_id)
            if provider_user_id is not None
            else None
        ),
        username=username,
        display_name=getattr(
            user,
            "nickname",
            None,
        ),
    )


def extract_provider_event_id(
    event: Any,
) -> str | None:
    value = (
        getattr(event, "order_id", None)
        or getattr(event, "log_id", None)
    )

    if value is None:
        return None

    value = str(value).strip()

    return value or None


def from_comment(
    event: CommentEvent,
    *,
    session_id: str | None = None,
) -> LiveEvent | None:
    user = event.user

    if user is None:
        return None

    comment = event.comment.strip()

    if not comment:
        return None

    return LiveEvent.create(
        type=EventType.COMMENT,
        provider="tiktok",
        provider_event_id=extract_provider_event_id(
            event
        ),
        session_id=session_id,
        viewer=build_viewer(user),
        payload={
            "text": comment,
        },
    )


def from_gift(
    event: GiftEvent,
    *,
    session_id: str | None = None,
) -> LiveEvent | None:
    gift = event.gift
    user = event.user

    if gift is None:
        return None

    if user is None:
        return None

    # Eventos intermediários de streak não representam
    # ainda a quantidade final enviada pelo usuário.
    if gift.streakable and event.streaking:
        return None

    quantity = event.repeat_count or 1

    return LiveEvent.create(
        type=EventType.GIFT,
        provider="tiktok",
        provider_event_id=extract_provider_event_id(
            event
        ),
        session_id=session_id,
        viewer=build_viewer(user),
        payload={
            "gift_id": gift.gift_id
            if hasattr(gift, "gift_id")
            else event.gift_id,
            "gift_name": gift.name,
            "quantity": quantity,
        },
    )