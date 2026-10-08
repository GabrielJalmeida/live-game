from abc import ABC, abstractmethod

from app.events import LiveEvent, OutputEvent
from app.runtime.experience_context import ExperienceContext


class InteractiveExperience(ABC):
    slug: str = ""
    name: str = ""
    version: str = "0.1.0"

    async def start(
        self,
        context: ExperienceContext,
    ) -> None:
        pass

    async def stop(
        self,
        context: ExperienceContext,
    ) -> None:
        pass

    @abstractmethod
    async def handle_event(
        self,
        event: LiveEvent,
        context: ExperienceContext,
    ) -> list[OutputEvent]:
        raise NotImplementedError

    @abstractmethod
    async def get_state(self) -> dict:
        raise NotImplementedError

    async def health(self) -> dict:
        return {
            "status": "ok",
            "slug": self.slug,
            "version": self.version,
        }