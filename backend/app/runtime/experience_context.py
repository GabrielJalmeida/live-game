from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExperienceContext:
    experience_slug: str
    config: dict[str, Any] = field(default_factory=dict)