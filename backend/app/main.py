from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.worlds import router as worlds_router
from app.api.citizens import router as citizens_router
from app.api.dev_engine_events import router as dev_engine_events_router
from app.api.websocket import router as websocket_router
from app.api.world_trees import router as world_trees_router

from app.runtime.engine import engine
from app.runtime.experience_context import ExperienceContext


@asynccontextmanager
async def lifespan(app: FastAPI):
    experience = engine.experience_loader.create("world001")

    await engine.start(
        experience,
        ExperienceContext(
            experience_slug="world001"
        ),
    )

    yield

    await engine.stop()


app = FastAPI(
    title="WORLD 001 API",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(
    health_router,
    prefix="/api/v1"
)

app.include_router(
    worlds_router,
    prefix="/api/v1"
)

app.include_router(
    citizens_router,
    prefix="/api/v1"
)

app.include_router(
    dev_engine_events_router,
    prefix="/api/v1"
)

app.include_router(
    world_trees_router,
    prefix="/api/v1"
)

app.include_router(
    websocket_router,
    prefix="/ws"
)


@app.get("/")
def root():
    return {
        "project": "WORLD 001",
        "version": "0.1.0",
        "status": "running"
    }