import pytest

from app.runtime.experience import InteractiveExperience
from app.runtime.experience_context import ExperienceContext
from app.runtime.experience_loader import (
    ExperienceAlreadyRegisteredError,
    ExperienceLoader,
    ExperienceNotFoundError,
)


class TestExperience(InteractiveExperience):
    slug = "test"
    name = "Test Experience"

    async def start(self, context: ExperienceContext) -> None:
        pass

    async def stop(self, context: ExperienceContext) -> None:
        pass

    async def handle_event(self, event, context):
        return []

    async def get_state(self):
        return {}


def test_loader_registers_and_creates_experience():
    loader = ExperienceLoader()

    loader.register(TestExperience)

    experience = loader.create("test")

    assert isinstance(experience, TestExperience)
    assert loader.list_slugs() == ["test"]


def test_loader_rejects_duplicate_slug():
    loader = ExperienceLoader()

    loader.register(TestExperience)

    with pytest.raises(ExperienceAlreadyRegisteredError):
        loader.register(TestExperience)


def test_loader_rejects_unknown_experience():
    loader = ExperienceLoader()

    with pytest.raises(ExperienceNotFoundError):
        loader.create("does-not-exist")