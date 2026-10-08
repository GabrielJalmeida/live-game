from app.events import LiveEvent, OutputEvent
from app.runtime.experience import InteractiveExperience
from app.runtime.experience_context import ExperienceContext


class NoActiveExperienceError(Exception):
    pass


class EventRouter:
    def __init__(self):
        self._experience: InteractiveExperience | None = None
        self._context: ExperienceContext | None = None

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
            context = self._context

            if context is not None:
                await self._experience.stop(context)

        self._experience = None
        self._context = None

    async def route(
        self,
        event: LiveEvent,
        context: ExperienceContext | None = None,
    ) -> list[OutputEvent]:
        if self._experience is None:
            raise NoActiveExperienceError(
                "Nenhuma Experience está ativa."
            )

        active_context = context or self._context

        if active_context is None:
            raise NoActiveExperienceError(
                "Nenhum contexto de Experience está disponível."
            )

        outputs = await self._experience.handle_event(
            event,
            active_context,
        )

        for output in outputs:
            if not isinstance(output, OutputEvent):
                raise TypeError(
                    "Experience deve retornar apenas OutputEvent."
                )

        return outputs