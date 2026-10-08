from app.events import (
    EventType,
    LiveEvent,
    Viewer,
)
from app.runtime.experience_manager import ExperienceManager


def normalize_username(username: str) -> str:
    username = username.strip()

    if not username:
        raise ValueError(
            "username não pode ser vazio"
        )

    if not username.startswith("@"):
        username = f"@{username}"

    return username


class EventSimulator:
    """
    Gera LiveEvents artificiais para desenvolvimento local.

    O simulador conhece apenas o contrato da Engine.
    Não conhece TikTok, FastAPI, banco ou gameplay.
    """

    def __init__(
        self,
        manager: ExperienceManager,
        provider: str = "dev",
        session_id: str = "dev-session",
    ):
        self.manager = manager
        self.provider = provider
        self.session_id = session_id

    def build_viewer(
        self,
        *,
        username: str,
        provider_user_id: str | None = None,
        display_name: str | None = None,
    ) -> Viewer:
        normalized_username = normalize_username(
            username
        )

        return Viewer(
            provider_user_id=(
                provider_user_id
                or normalized_username
            ),
            username=normalized_username,
            display_name=display_name,
        )

    def build_comment(
        self,
        *,
        username: str,
        text: str,
        provider_user_id: str | None = None,
        display_name: str | None = None,
    ) -> LiveEvent:
        text = text.strip()

        if not text:
            raise ValueError(
                "comment não pode ser vazio"
            )

        viewer = self.build_viewer(
            username=username,
            provider_user_id=provider_user_id,
            display_name=display_name,
        )

        return LiveEvent.create(
            type=EventType.COMMENT,
            provider=self.provider,
            session_id=self.session_id,
            viewer=viewer,
            payload={
                "text": text,
            },
        )

    def build_gift(
        self,
        *,
        username: str,
        gift_name: str,
        quantity: int = 1,
        gift_id: str | None = None,
        provider_user_id: str | None = None,
        display_name: str | None = None,
    ) -> LiveEvent:
        gift_name = gift_name.strip()

        if not gift_name:
            raise ValueError(
                "gift_name não pode ser vazio"
            )

        if quantity < 1:
            raise ValueError(
                "quantity deve ser maior ou igual a 1"
            )

        viewer = self.build_viewer(
            username=username,
            provider_user_id=provider_user_id,
            display_name=display_name,
        )

        return LiveEvent.create(
            type=EventType.GIFT,
            provider=self.provider,
            session_id=self.session_id,
            viewer=viewer,
            payload={
                "gift_id": gift_id,
                "gift_name": gift_name,
                "quantity": quantity,
            },
        )

    async def dispatch(
        self,
        event: LiveEvent,
    ):
        return await self.manager.dispatch(event)

    async def comment(
        self,
        *,
        username: str,
        text: str,
        provider_user_id: str | None = None,
        display_name: str | None = None,
    ):
        event = self.build_comment(
            username=username,
            text=text,
            provider_user_id=provider_user_id,
            display_name=display_name,
        )

        return await self.dispatch(event)

    async def gift(
        self,
        *,
        username: str,
        gift_name: str,
        quantity: int = 1,
        gift_id: str | None = None,
        provider_user_id: str | None = None,
        display_name: str | None = None,
    ):
        event = self.build_gift(
            username=username,
            gift_name=gift_name,
            quantity=quantity,
            gift_id=gift_id,
            provider_user_id=provider_user_id,
            display_name=display_name,
        )

        return await self.dispatch(event)