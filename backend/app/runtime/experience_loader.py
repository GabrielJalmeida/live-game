from collections.abc import Callable

from app.runtime.experience import InteractiveExperience


ExperienceFactory = Callable[[], InteractiveExperience]


class ExperienceLoaderError(Exception):
    pass


class ExperienceAlreadyRegisteredError(ExperienceLoaderError):
    pass


class ExperienceNotFoundError(ExperienceLoaderError):
    pass


class ExperienceLoader:
    def __init__(self):
        self._factories: dict[str, ExperienceFactory] = {}

    def register(self, factory: ExperienceFactory) -> None:
        experience = factory()

        if not experience.slug:
            raise ExperienceLoaderError(
                "A Experience precisa definir um slug."
            )

        if experience.slug in self._factories:
            raise ExperienceAlreadyRegisteredError(
                f"Experience já registrada: {experience.slug}"
            )

        self._factories[experience.slug] = factory

    def create(self, slug: str) -> InteractiveExperience:
        factory = self._factories.get(slug)

        if factory is None:
            raise ExperienceNotFoundError(
                f"Experience não encontrada: {slug}"
            )

        return factory()

    def list_slugs(self) -> list[str]:
        return sorted(self._factories)