# WORLD 001

**A persistent TikTok LIVE world where viewers become citizens through real-time interactions.**

WORLD 001 is an experimental interactive-live project built with **Godot**, **FastAPI**, **SQLite**, **WebSockets**, and **TikTokLive**. Viewers can trigger the creation of persistent citizens during a TikTok LIVE; each citizen is stored by the backend and reconstructed when the world starts again.

The core idea is simple:

> **🌹 One Rose = you are born into the world.**

## Overview

WORLD 001 explores a live format where the stream is not only something to watch — it is an entry point into a persistent simulation.

During a LIVE, a supported TikTok interaction is received by a Python listener, forwarded to the FastAPI backend, persisted in SQLite, broadcast to Godot over WebSocket, and rendered immediately as a new citizen with the viewer's username.

The world remains persistent between sessions, so citizens created during a LIVE can return when the project is restarted.

## Current MVP

The first end-to-end TikTok LIVE MVP has been validated with a real Rose gift.

Implemented behavior:

- Connect to an active TikTok LIVE.
- Receive real TikTok comments and gift events.
- Detect a Rose gift from a viewer.
- Create a citizen using the viewer's TikTok username.
- Persist citizens in SQLite.
- Broadcast new citizens to Godot in real time through WebSocket.
- Restore persisted citizens when Godot starts.
- Display the current day and population.
- Show a birth message when a new citizen enters the world.
- Keep citizens moving autonomously inside the world.
- Run in a vertical 9:16 layout designed for TikTok LIVE.

## Live Flow

```text
TikTok viewer
    |
    | sends Rose
    v
TikTok LIVE
    |
    v
TikTokLive listener
    |
    | HTTP POST
    v
FastAPI
    |
    +------> SQLite
    |          |
    |          +--> persistent citizen
    |
    | WebSocket
    v
Godot
    |
    v
Citizen appears in the world
```

The backend is the source of truth for persistent world data. Godot acts as the visual client that reconstructs and displays the current state.

## Tech Stack

**Simulation / Client**
- Godot 4.7
- GDScript

**Backend**
- Python
- FastAPI
- SQLAlchemy
- Alembic
- WebSockets

**Persistence**
- SQLite

**TikTok Integration**
- TikTokLive
- httpx

**Broadcast**
- TikTok LIVE Studio

## Architecture

The project is split into two main parts.

### Godot client

Godot is responsible for:

- rendering the world;
- displaying citizens;
- autonomous citizen movement;
- population and day HUD;
- birth feedback;
- receiving real-time WebSocket events;
- loading persisted citizens from the REST API.

### Python backend

FastAPI is responsible for:

- world state;
- citizen creation;
- persistence;
- REST endpoints;
- WebSocket broadcasting;
- development event simulation.

### TikTok listener

The TikTok integration listens to LIVE events separately from the game client.

For a Rose gift:

```text
GiftEvent
→ validate gift
→ extract username and quantity
→ create citizen through backend
→ persist
→ broadcast
```

This keeps the TikTok integration isolated from the simulation itself.

## API

With the backend running, interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Current main endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Backend and database health |
| `GET` | `/api/v1/world` | Current persistent world |
| `GET` | `/api/v1/citizens` | Citizens stored in the world |
| `POST` | `/api/v1/dev/events/rose` | Development Rose event |
| `WS` | `/ws/world` | Real-time world events for Godot |

## Repository Structure

```text
world-001/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/            # REST and WebSocket routes
│   │   ├── db/             # SQLAlchemy session
│   │   ├── integrations/   # TikTok LIVE listener
│   │   ├── models/         # Persistent entities
│   │   ├── realtime/       # WebSocket connection manager
│   │   └── services/       # World and citizen logic
│   └── alembic.ini
│
└── game/
    └── world-001/
        ├── project.godot
        ├── world.tscn
        ├── world.gd
        ├── citizen.tscn
        └── citizen.gd
```

## Getting Started

### Prerequisites

- Python 3.10+
- Godot 4.x
- A TikTok account with access to LIVE for real TikTok testing
- TikTok LIVE Studio for desktop broadcasting

The current development environment has been tested with Python 3.14 and Godot 4.7.

### Backend setup

From the repository root:

```bash
cd backend
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

Install the current backend dependencies:

```bash
python -m pip install fastapi uvicorn sqlalchemy alembic websockets TikTokLive httpx
```

Apply database migrations:

```bash
python -m alembic upgrade head
```

Start the API:

```bash
python -m uvicorn app.main:app --reload
```

### TikTok listener

Set the TikTok LIVE username in:

```text
backend/app/integrations/tiktok_listener.py
```

Then, from `backend/` with the virtual environment active:

```bash
python -m app.integrations.tiktok_listener
```

When the target account is live, the listener connects to the active room and starts receiving supported LIVE events.

### Godot client

Open:

```text
game/world-001/project.godot
```

Run the project with **F5** while the FastAPI backend is active.

On startup, Godot requests the existing citizens from the backend and reconstructs the current population.

## Persistence

WORLD 001 currently stores its persistent state in SQLite.

Alembic manages schema changes, including the current `worlds` and `citizens` tables.

A citizen stores the information required to reconstruct it in the world, including:

- persistent ID;
- world ID;
- username;
- position;
- status;
- creation timestamps.

This means citizens created during a LIVE remain available after restarting the backend and Godot client.

## TikTok Event Handling

The current LIVE integration listens for `GiftEvent` events.

Rose gifts are routed through the same backend flow used by development simulations, so TikTok-specific logic does not directly create visual entities inside Godot.

Gift streaks are processed after the streak finishes to avoid treating intermediate streak updates as separate completed events.

A development comment command is also available in the listener for no-cost event testing before using real gifts.

## Verified Result

The first real TikTok LIVE test successfully completed the full flow:

```text
Real Rose
→ TikTok GiftEvent
→ Python listener
→ FastAPI
→ SQLite
→ WebSocket
→ Godot citizen spawn
→ restart
→ citizen restored
```

The same test also confirmed that real TikTok comments are received by the listener.

## Current Status

**Status: Experimental MVP / In active development**

The core live-interaction loop is functional and has been tested during a real TikTok LIVE.

The current version intentionally keeps the simulation simple: citizens spawn, persist, display their usernames, and move autonomously. Deeper simulation systems such as relationships, jobs, settlements, conflicts, world events, and long-term autonomous behavior are outside the current MVP.

The TikTok connection currently relies on the third-party `TikTokLive` library, so changes to TikTok's internal LIVE protocol may require integration updates.

## Project Direction

WORLD 001 is designed around progressive discovery.

The initial interaction is intentionally easy to understand:

```text
🌹 Rose → a viewer becomes a citizen
```

Future simulation depth can build on top of the same persistent population rather than replacing the core interaction.

The long-term goal is a world that continues to develop through both autonomous simulation and viewer participation.

## Author

**Gabriel Almeida**  
Software Developer

[LinkedIn](https://www.linkedin.com/in/gabriel-almeida-258453364/)
