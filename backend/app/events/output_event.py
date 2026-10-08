from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class OutputEvent:
    type: str
    data: dict = field(default_factory=dict)
    experience: str | None = None
    event_id: str = field(
        default_factory=lambda: f"out_{uuid4()}"
    )

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "type": self.type,
            "experience": self.experience,
            "data": self.data.copy(),
        }