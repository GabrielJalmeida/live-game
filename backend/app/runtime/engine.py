from app.realtime.realtime_manager import RealtimeManager
from app.runtime.experience_manager import ExperienceManager


class EngineRuntime:
    def __init__(
        self,
        realtime_manager: RealtimeManager | None = None,
        experience_manager: ExperienceManager | None = None,
    ):
        self.realtime_manager = realtime_manager or RealtimeManager()

        self.experience_manager = (
            experience_manager
            or ExperienceManager(
                realtime_manager=self.realtime_manager,
            )
        )


engine = EngineRuntime()