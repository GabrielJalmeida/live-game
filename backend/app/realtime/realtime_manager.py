from uuid import uuid4

from app.events import OutputEvent
from app.realtime.connection_manager import ConnectionManager


class RealtimeManager:
    """
    Converte OutputEvents em mensagens de transporte
    e publica para os clientes conectados.

    Não conhece gameplay específico.
    """

    def __init__(
        self,
        connection_manager: ConnectionManager | None = None,
    ):
        self.connections = (
            connection_manager
            or ConnectionManager()
        )

    @staticmethod
    def build_message(
        output: OutputEvent,
    ) -> dict:
        return {
            "message_id": f"msg_{uuid4()}",
            "type": "EXPERIENCE_EVENT",
            "experience": output.experience,
            "data": {
                "event": output.type,
                **output.data,
            },
        }

    async def publish(
        self,
        output: OutputEvent,
    ) -> dict:
        message = self.build_message(output)

        await self.connections.broadcast(
            message
        )

        return message