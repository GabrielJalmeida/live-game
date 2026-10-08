from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExperienceContext:
    experience_slug: str
    session: Any | None = None
    services: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)