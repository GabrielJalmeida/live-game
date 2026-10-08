from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class Viewer:
    provider_user_id: str | None
    username: str
    display_name: str | None = None
    avatar_url: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)