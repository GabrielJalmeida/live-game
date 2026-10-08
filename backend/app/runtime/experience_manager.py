from app.events import LiveEvent, OutputEvent
from app.runtime.event_router import EventRouter
from app.runtime.experience import InteractiveExperience
from app.runtime.experience_context import ExperienceContext


class ExperienceManager:
    def __init__(self):
        self.router = EventRouter()

    @property
    def active_experience(
        self,
    ) -> InteractiveExperience | None:
        return self.router.experience

    async def start(
        self,
        experience: InteractiveExperience,
        context: ExperienceContext,
    ) -> None:
        await self.stop()

        await self.router.set_experience(
            experience,
            context,
        )

    async def stop(self) -> None:
        await self.router.clear_experience()

    async def dispatch(
        self,
        event: LiveEvent,
    ) -> list[OutputEvent]:
        return await self.router.route(event)

    async def get_state(self) -> dict:
        experience = self.active_experience

        if experience is None:
            return {}

        return await experience.get_state()

    async def health(self) -> dict:
        experience = self.active_experience

        if experience is None:
            return {
                "status": "no_experience",
            }

        return await experience.health()