from app.events import LiveEvent, OutputEvent
from app.realtime.realtime_manager import RealtimeManager
from app.runtime.experience import InteractiveExperience
from app.runtime.experience_context import ExperienceContext
from app.runtime.experience_loader import ExperienceLoader
from app.runtime.experience_manager import ExperienceManager


class EngineRuntime:
    def __init__(
        self,
        realtime_manager: RealtimeManager | None = None,
        experience_manager: ExperienceManager | None = None,
        experience_loader: ExperienceLoader | None = None,
    ):
        self.realtime_manager = realtime_manager or RealtimeManager()

        self.experience_manager = (
            experience_manager
            or ExperienceManager(
                realtime_manager=self.realtime_manager,
            )
        )

        self.experience_loader = (
            experience_loader
            or ExperienceLoader()
        )

    def register_experience(self, factory) -> None:
        self.experience_loader.register(factory)

    async def start(
        self,
        experience: InteractiveExperience,
        context: ExperienceContext,
    ) -> None:
        await self.experience_manager.start(
            experience,
            context,
        )

    async def start_experience(
        self,
        slug: str,
        context: ExperienceContext,
    ) -> None:
        experience = self.experience_loader.create(slug)

        await self.start(
            experience,
            context,
        )

    async def stop(self) -> None:
        await self.experience_manager.stop()

    async def dispatch(
        self,
        event: LiveEvent,
    ) -> list[OutputEvent]:
        return await self.experience_manager.dispatch(event)

    async def get_state(self) -> dict:
        return await self.experience_manager.get_state()

    async def health(self) -> dict:
        return await self.experience_manager.health()


engine = EngineRuntime()