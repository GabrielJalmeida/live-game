from app.events import LiveEvent, OutputEvent
from app.runtime.experience import InteractiveExperience
from app.runtime.experience_context import ExperienceContext


class NoActiveExperienceError(RuntimeError):
    pass


class EventRouter:
    def __init__(self):
        self._experience: InteractiveExperience | None = None
        self._context: ExperienceContext | None = None

    @property
    def experience(self) -> InteractiveExperience | None:
        return self._experience

    async def set_experience(
        self,
        experience: InteractiveExperience,
        context: ExperienceContext,
    ) -> None:
        self._experience = experience
        self._context = context

        await experience.start(context)

    async def clear_experience(self) -> None:
        if self._experience is not None:
            await self._experience.stop(
                self._context
            )

        self._experience = None
        self._context = None

    async def route(
        self,
        event: LiveEvent,
    ) -> list[OutputEvent]:
        if (
            self._experience is None
            or self._context is None
        ):
            raise NoActiveExperienceError(
                "Nenhuma Experience está ativa."
            )

        outputs = await self._experience.handle_event(
            event,
            self._context,
        )

        for output in outputs:
            if not isinstance(
                output,
                OutputEvent,
            ):
                raise TypeError(
                    "Experience retornou um objeto "
                    "que não é OutputEvent."
                )

        return outputs