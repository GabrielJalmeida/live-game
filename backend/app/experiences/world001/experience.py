from app.events import EventType, LiveEvent, OutputEvent
from app.runtime.experience import InteractiveExperience
from app.runtime.experience_context import ExperienceContext

from app.services.citizen_service import create_or_support_citizen
from app.services.world_service import get_or_create_world

class World001Experience(InteractiveExperience):
    slug = "world001"
    name = "WORLD 001"
    version = "0.1.0"

    async def handle_event(
        self,
        event: LiveEvent,
        context: ExperienceContext,
    ) -> list[OutputEvent]:
        if event.type != EventType.GIFT:
            return []

        gift_name = str(
            event.payload.get("gift_name", "")
        ).strip().casefold()

        if gift_name != "rose":
            return []

        if event.viewer is None:
            raise ValueError(
                "WORLD 001 precisa de Viewer para processar uma Rose."
            )

        if context.session is None:
            raise RuntimeError(
                "WORLD 001 precisa de uma sessão de banco."
            )

        world_service = context.services.get(
            "world_service"
        )
        citizen_service = context.services.get(
            "citizen_service"
        )

        if world_service is None:
            raise RuntimeError(
                "WORLD 001 não recebeu world_service."
            )

        if citizen_service is None:
            raise RuntimeError(
                "WORLD 001 não recebeu citizen_service."
            )

        world = world_service(
            context.session
        )

        quantity = int(
            event.payload.get("quantity", 1)
        )

        if quantity < 1:
            raise ValueError(
                "Quantidade de Rose deve ser maior que zero."
            )

        citizen, created = citizen_service(
            db=context.session,
            world=world,
            name=event.viewer.username,
            quantity=quantity,
            commit=False,
        )

        citizen_data = {
            "id": citizen.id,
            "name": citizen.name,
            "x": citizen.x,
            "y": citizen.y,
            "status": citizen.status,
            "total_roses": citizen.total_roses,
            "wealth": citizen.wealth,
        }

        if created:
            return [
                OutputEvent(
                    type="citizen_spawned",
                    experience=self.slug,
                    data={
                        "citizen": citizen_data,
                    },
                )
            ]

        return [
            OutputEvent(
                type="citizen_supported",
                experience=self.slug,
                data={
                    "citizen": citizen_data,
                    "quantity": quantity,
                },
            )
        ]

    async def get_state(self) -> dict:
        return {
            "slug": self.slug,
        }