from app.events import LiveEvent, OutputEvent
from app.realtime.realtime_manager import RealtimeManager
from app.runtime.event_router import EventRouter
from app.runtime.experience import InteractiveExperience
from app.runtime.experience_context import ExperienceContext


class ExperienceManager:
    def __init__(
        self,
        router: EventRouter | None = None,
        realtime_manager: RealtimeManager | None = None,
    ):
        self.router = router or EventRouter()
        self.realtime_manager = realtime_manager or RealtimeManager()

    async def start(
        self,
        experience: InteractiveExperience,
        context: ExperienceContext,
    ) -> None:
        await self.router.set_experience(experience, context)


    async def stop(self) -> None:
        await self.router.clear_experience()

    async def dispatch(
        self,
        event: LiveEvent,
        context: ExperienceContext | None = None,
        publish: bool = True,
    ) -> list[OutputEvent]:
        outputs = await self.router.route(
            event,
            context,
        )

        if publish:
            await self.publish(outputs)

        return outputs

    async def publish(
        self,
        outputs: list[OutputEvent],
    ) -> None:
        for output in outputs:
            await self.realtime_manager.publish(output)

    async def get_state(self) -> dict:
        experience = self.router._experience

        if experience is None:
            return {}

        return await experience.get_state()

    async def health(self) -> dict:
        experience = self.router._experience

        if experience is None:
            return {"status": "no_active_experience"}

        return await experience.health()