from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.connection_manager import manager
from app.runtime.engine import engine


router = APIRouter()


@router.websocket("/world")
async def world_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    print("🔌 Godot conectado ao WebSocket WORLD 001")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("🔌 Godot desconectado do WebSocket WORLD 001")


@router.websocket("/events")
async def events_websocket(websocket: WebSocket):
    connections = engine.realtime_manager.connections

    await connections.connect(websocket)
    print("🔌 Cliente conectado ao WebSocket da Engine")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections.disconnect(websocket)
        print("🔌 Cliente desconectado do WebSocket da Engine")