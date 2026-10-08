import argparse
import asyncio
import json

from app.events import OutputEvent
from app.runtime import (
    ExperienceContext,
    ExperienceManager,
    InteractiveExperience,
)
from app.runtime.simulator import EventSimulator


class ConsoleExperience(InteractiveExperience):
    """
    Experience temporária usada exclusivamente
    para validar o pipeline da Engine.
    """

    slug = "console"
    name = "Console Experience"
    version = "0.1.0"

    def __init__(self):
        self.event_count = 0

    async def handle_event(
        self,
        event,
        context,
    ) -> list[OutputEvent]:
        self.event_count += 1

        return [
            OutputEvent(
                type="SIMULATED_EVENT",
                experience=self.slug,
                event_id=event.event_id,
                data={
                    "input_type": event.type.value,
                    "provider": event.provider,
                    "viewer": (
                        event.viewer.username
                        if event.viewer
                        else None
                    ),
                    "payload": event.payload,
                },
            )
        ]

    async def get_state(self) -> dict:
        return {
            "event_count": self.event_count,
        }


async def run(args):
    manager = ExperienceManager()

    experience = ConsoleExperience()

    await manager.start(
        experience,
        ExperienceContext(
            experience_slug=experience.slug
        ),
    )

    simulator = EventSimulator(
        manager,
        provider="dev",
        session_id="dev-session",
    )

    if args.event_type == "comment":
        outputs = await simulator.comment(
            username=args.user,
            text=args.text,
        )

    elif args.event_type == "gift":
        outputs = await simulator.gift(
            username=args.user,
            gift_name=args.gift,
            quantity=args.quantity,
        )

    else:
        raise ValueError(
            f"Tipo de evento desconhecido: "
            f"{args.event_type}"
        )

    for output in outputs:
        print(
            json.dumps(
                output.to_dict(),
                ensure_ascii=False,
                indent=2,
            )
        )

    await manager.stop()


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Interactive Live Engine "
            "development event simulator."
        )
    )

    subparsers = parser.add_subparsers(
        dest="event_type",
        required=True,
    )

    comment_parser = subparsers.add_parser(
        "comment"
    )

    comment_parser.add_argument(
        "--user",
        required=True,
    )

    comment_parser.add_argument(
        "--text",
        required=True,
    )

    gift_parser = subparsers.add_parser(
        "gift"
    )

    gift_parser.add_argument(
        "--user",
        required=True,
    )

    gift_parser.add_argument(
        "--gift",
        required=True,
    )

    gift_parser.add_argument(
        "--quantity",
        type=int,
        default=1,
    )

    return parser


def main():
    parser = build_parser()

    args = parser.parse_args()

    asyncio.run(
        run(args)
    )


if __name__ == "__main__":
    main()