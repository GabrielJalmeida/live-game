from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.connection_manager import manager


router = APIRouter()


@router.websocket("/world")
async def world_websocket(websocket: WebSocket):
    await manager.connect(websocket)

    print("🔌 Godot conectado ao WebSocket")

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("🔌 Godot desconectado do WebSocket")