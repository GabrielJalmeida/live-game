# WORLD 001

**A persistent TikTok LIVE world where viewers become citizens through real-time interactions.**

WORLD 001 is an experimental interactive-live project built with **Godot**, **FastAPI**, **SQLite**, **WebSockets**, and **TikTokLive**.

Viewers can enter a persistent virtual world through TikTok LIVE interactions. A Rose can create a new citizen or support an existing one, while the game client immediately moves the broadcast spotlight to that viewer's character.

The core interaction is simple:

> **🌹 One Rose = you are born into the world.**

The long-term idea is larger:

> **The LIVE is the gateway. The world is the product.**

---

## Overview

WORLD 001 explores a livestream format where the audience does not simply watch a simulation — viewers become persistent inhabitants of it.

During a LIVE, supported TikTok events are received by a Python listener, validated by the FastAPI backend, persisted in SQLite, and broadcast to Godot through WebSocket.

A citizen created during one session remains stored in the world and can return when the project starts again.

If the same viewer sends another Rose later, a duplicate citizen is not created. Instead, the existing citizen receives progression and becomes the current broadcast spotlight.

```text
Viewer sends Rose
        ↓
TikTok LIVE
        ↓
TikTokLive listener
        ↓
FastAPI
        ↓
validation + idempotency
        ↓
SQLite persistence
        ↓
WebSocket
        ↓
Godot
        ↓
Citizen created or updated
        ↓
Camera follows that citizen
```

---

## Current Status

**Status: Experimental MVP / v0.2 development checkpoint**

The complete TikTok-to-Godot interaction pipeline has been validated during real TikTok LIVE sessions.

The current build includes:

- real TikTok Rose detection;
- real TikTok comment reception;
- persistent citizens;
- persistent Rose progression;
- duplicate-event protection;
- persistent LIVE event records;
- persistent LIVE user records;
- automatic TikTok reconnection;
- automatic Godot WebSocket reconnection;
- client resynchronization after backend reconnection;
- structured rotating logs;
- backend/database health checks;
- citizen movement boundaries;
- vertical LIVE-oriented HUD;
- automatic citizen spotlight camera;
- automated backend tests.

The simulation itself is intentionally still simple. Autonomous life systems, resources, construction, relationships, settlements, conflicts, catastrophes, and procedural-world expansion belong to later stages.

---

# Core Interaction

## New viewer

When a viewer sends a Rose for the first time:

```text
🌹 Rose
   ↓
LiveEvent registered
   ↓
Citizen created
   ↓
Citizen persisted
   ↓
Godot receives realtime event
   ↓
Citizen appears
   ↓
Camera moves to the citizen
```

The LIVE displays:

```text
🌹 ROSA RECEBIDA

NOVO CIDADÃO
@username
```

---

## Existing viewer

If the viewer already owns a citizen:

```text
🌹 Rose
   ↓
existing Citizen found
   ↓
Rose count increases
   ↓
wealth increases
   ↓
Citizen is updated
   ↓
Camera moves back to that citizen
```

The LIVE displays:

```text
🌹 ROSA RECEBIDA

ACOMPANHANDO
@username
```

The citizen is not duplicated.

---

# Spotlight Camera

WORLD 001 uses a broadcast-oriented camera model.

The camera does **not** attempt to keep every citizen visible simultaneously.

Instead:

> **The most recent viewer who sends a Rose becomes the current protagonist of the LIVE.**

```text
@Maria sends Rose
        ↓
camera follows @Maria

@Joao sends Rose
        ↓
camera moves to @Joao

@Maria sends another Rose later
        ↓
camera finds @Maria again
```

This approach allows the world to expand without forcing the camera to zoom farther and farther away as the population grows.

It also reinforces the persistence concept: returning viewers can see that their previous citizen still exists.

---

# Current MVP Features

## TikTok integration

- Connect to an active TikTok LIVE.
- Receive `GiftEvent`.
- Receive `CommentEvent`.
- Detect Rose gifts.
- Handle gift quantities.
- Normalize usernames.
- Extract external TikTok user identifiers.
- Extract external event identifiers when available.
- Automatically retry when the LIVE is offline.
- Automatically reconnect after connection failures.
- Ignore duplicate external events.

---

## Citizens

Citizens currently contain persistent information including:

- unique ID;
- world ID;
- username;
- world position;
- status;
- total Roses;
- wealth;
- creation timestamps.

A Rose currently contributes:

```text
+1 Rose
+10 wealth
```

per Rose received.

Citizens move autonomously inside the current world boundaries.

---

## Persistence

WORLD 001 currently uses **SQLite** as its persistent database.

The backend is the source of truth.

Godot is a visual client that reconstructs state from the backend.

Current persistent entities include:

```text
World
Citizen
LiveUser
LiveEvent
```

Alembic manages database schema evolution.

---

# Event Idempotency

External LIVE events are treated as untrusted input.

When a reliable external event ID is available, WORLD 001 stores the combination:

```text
provider
+
provider_event_id
```

as a unique event identity.

If the same event reaches the backend twice:

```text
first request
→ processed

same event again
→ duplicate
→ ignored
```

The Citizen receives the effect only once.

This protects the persistent world against duplicated TikTok events and reconnection-related retransmissions.

---

# Event Processing

The current Rose flow is:

```text
external event
      ↓
Pydantic validation
      ↓
LiveUser resolution
      ↓
LiveEvent registered as RECEIVED
      ↓
duplicate check
      ↓
Citizen created or supported
      ↓
LiveEvent becomes PROCESSED
      ↓
transaction commit
      ↓
WebSocket broadcast
```

Citizen changes and the transition to `PROCESSED` are committed together.

If processing fails:

```text
rollback
↓
Citizen change is reverted
↓
LiveEvent remains auditable
↓
event is marked FAILED
```

A WebSocket failure does not undo a successfully persisted Rose.

Godot can recover the current state through REST synchronization.

---

# Realtime Recovery

The Godot client automatically reconnects to the backend WebSocket.

If the backend temporarily stops:

```text
Godot
  ↓
WebSocket disconnects
  ↓
automatic retry
  ↓
backend returns
  ↓
WebSocket reconnects
  ↓
world state resynchronizes
```

Existing citizens are updated instead of duplicated during resynchronization.

The TikTok listener also performs controlled reconnection attempts when the target account is offline or the connection terminates unexpectedly.

---

# Live Flow

```text
TikTok Viewer
     |
     | Rose / Comment
     v
TikTok LIVE
     |
     v
TikTokLive Listener
     |
     | HTTP
     v
FastAPI
     |
     +-------------------+
     |                   |
     v                   v
 Validation           LiveUser
     |                LiveEvent
     |                   |
     +---------+---------+
               |
               v
            SQLite
               |
               v
          World State
               |
               | WebSocket
               v
             Godot
               |
               +--> Citizen spawn/update
               |
               +--> HUD
               |
               +--> Event feed
               |
               +--> Spotlight camera
```

---

# Tech Stack

## Simulation / Visual Client

- Godot 4.x
- GDScript

## Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- WebSockets

## Persistence

- SQLite

## TikTok Integration

- TikTokLive
- httpx

## Testing

- pytest
- unittest.mock

## Broadcast

- TikTok LIVE Studio

The current development environment has been tested with:

```text
Python 3.14.6
Godot 4.7
```

---

# Architecture

WORLD 001 currently consists of three main runtime components.

## Godot Client

Godot is responsible for:

- rendering the world;
- rendering citizens;
- autonomous visual movement;
- citizen spawn feedback;
- Rose progression feedback;
- population and day HUD;
- realtime event feed;
- spotlight camera;
- WebSocket communication;
- restoring state through the REST API.

Godot is **not** the persistent source of truth.

---

## FastAPI Backend

FastAPI is responsible for:

- world state;
- citizen persistence;
- citizen progression;
- LIVE users;
- LIVE events;
- event validation;
- event idempotency;
- transactional event processing;
- REST endpoints;
- health checks;
- WebSocket broadcasting;
- development event simulation;
- structured logging.

---

## TikTok Listener

The TikTok integration is isolated from the simulation domain.

It listens for TikTok events and translates them into requests understood by the backend.

For a Rose:

```text
GiftEvent
   ↓
extract TikTok user
   ↓
extract event identifier
   ↓
normalize payload
   ↓
POST to FastAPI
```

TikTok-specific code does not directly instantiate Godot citizens.

---

# API

With the backend running, interactive FastAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Current main endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Backend and database health |
| `GET` | `/api/v1/world` | Current persistent world |
| `GET` | `/api/v1/citizens` | Persistent citizens |
| `POST` | `/api/v1/dev/events/rose` | Development Rose event |
| `POST` | `/api/v1/dev/events/comment` | Development comment event |
| `WS` | `/ws/world` | Realtime world events |

---

# Health Check

The backend exposes:

```http
GET /api/v1/health
```

Example response:

```json
{
  "status": "ok",
  "database": "ok",
  "service": "world-001-backend"
}
```

The database status is validated with a real database query.

---

# Logging

WORLD 001 uses structured rotating logs.

Current categories include:

```text
world_event
live_integration
error
```

Examples of recorded events include:

```text
rose_received
citizen_rose_applied
rose_processed
rose_duplicate

tiktok_connected
tiktok_disconnected
tiktok_live_offline
tiktok_reconnect_scheduled

rose_processing_failed
rose_broadcast_failed
tiktok_connection_failed
```

Logs are written under:

```text
backend/logs/
```

Runtime logs are excluded from Git.

---

# Repository Structure

```text
world-001/
│
├── backend/
│   ├── alembic/
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── api/
│   │   │   ├── citizens.py
│   │   │   ├── dev_events.py
│   │   │   └── health.py
│   │   │
│   │   ├── db/
│   │   │
│   │   ├── integrations/
│   │   │   └── tiktok_listener.py
│   │   │
│   │   ├── models/
│   │   │   ├── citizen.py
│   │   │   ├── live_event.py
│   │   │   └── live_user.py
│   │   │
│   │   ├── realtime/
│   │   │
│   │   ├── scripts/
│   │   │
│   │   ├── services/
│   │   │   ├── citizen_service.py
│   │   │   ├── live_event_service.py
│   │   │   ├── live_user_service.py
│   │   │   └── world_service.py
│   │   │
│   │   ├── logging_config.py
│   │   └── main.py
│   │
│   ├── tests/
│   │   ├── test_citizen_service.py
│   │   └── test_event_validation.py
│   │
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

---

# Getting Started

## Prerequisites

- Python 3.10+
- Godot 4.x
- TikTok account with LIVE access for real integration testing
- TikTok LIVE Studio for desktop broadcasting

---

## Backend Setup

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
python -m pip install fastapi uvicorn sqlalchemy alembic websockets TikTokLive httpx pytest
```

Apply all database migrations:

```bash
python -m alembic upgrade head
```

Start FastAPI:

```bash
python -m uvicorn app.main:app --reload
```

---

# TikTok Listener

Set the target TikTok username in:

```text
backend/app/integrations/tiktok_listener.py
```

Example:

```python
TIKTOK_USERNAME = "@your_username"
```

Then, from `backend/` with the virtual environment active:

```bash
python -m app.integrations.tiktok_listener
```

If the target account is offline, the listener remains active and retries automatically.

When the account starts a LIVE, supported events can begin flowing into WORLD 001.

---

# Godot Client

Open:

```text
game/world-001/project.godot
```

Start the FastAPI backend first.

Then run the Godot project with:

```text
F5
```

On startup, Godot:

```text
loads world state
+
loads persistent citizens
+
connects WebSocket
+
reconstructs the current population
```

If the WebSocket connection later drops, the client automatically retries and resynchronizes after reconnection.

---

# Development Rose Simulation

WORLD 001 can be tested without spending TikTok gifts.

Inside the Godot client:

```text
R
```

triggers a simulated development Rose.

The backend also includes development scripts under:

```text
backend/app/scripts/
```

including TikTok-style Rose simulation used to test external event IDs and duplicate protection.

---

# Tests

Run the complete backend test suite from:

```text
backend/
```

with the virtual environment active:

```bash
python -m pytest tests -v
```

Current checkpoint:

```text
10 passed
```

The automated tests currently cover:

- valid Rose events;
- username normalization;
- empty username rejection;
- zero quantity rejection;
- negative quantity rejection;
- empty provider rejection;
- optional-field normalization;
- support of existing citizens;
- Rose/wealth progression;
- transactional and committed citizen updates.

Additional integration behavior has also been manually validated, including:

- duplicate external event rejection;
- WebSocket reconnection;
- state resynchronization;
- TikTok offline retry;
- persistent citizen restoration;
- spotlight switching.

---

# Database Migrations

Alembic currently manages migrations for:

- worlds;
- citizens;
- citizen progression;
- citizen uniqueness;
- LIVE users;
- LIVE events;
- external-event uniqueness.

Apply the latest schema with:

```bash
python -m alembic upgrade head
```

---

# Git Safety

Runtime and local development data are excluded from the repository.

Examples include:

```text
.venv/
__pycache__/
.pytest_cache/
logs/
*.log
*.db
```

The SQLite databases therefore remain local and are not part of the Git history.

---

# Verified Live Result

The real TikTok LIVE pipeline has successfully completed:

```text
Real Rose
→ TikTok GiftEvent
→ Python listener
→ FastAPI
→ validation
→ SQLite
→ WebSocket
→ Godot citizen spawn/update
→ persistence
→ restart
→ citizen restored
```

Real TikTok comments have also successfully reached the Godot event feed.

---

# Current World

The current visual world is still a prototype.

It currently contains:

- a bounded 2D world;
- stylized terrain;
- roads;
- central plaza;
- decorative vegetation;
- flowers;
- autonomous moving citizens;
- Rose-based visual progression;
- realtime HUD;
- event feed;
- persistent day counter;
- spotlight camera.

The current visual assets and procedural decorations are intentionally provisional.

They exist to validate the experience before the final visual direction is built.

---

# Project Direction

WORLD 001 is designed around **progressive discovery**.

The viewer should understand the first interaction almost immediately:

```text
🌹 Rose
↓
you enter the world
```

Complexity should emerge later from the simulation itself.

Planned evolution includes concepts such as:

```text
persistent citizen
       ↓
needs
       ↓
resources
       ↓
work
       ↓
construction
       ↓
relationships
       ↓
families
       ↓
villages
       ↓
cities
       ↓
conflicts
       ↓
world events
```

The project is being developed through small vertical versions rather than attempting to build the final simulation at once.

---

# Next Development Stage

The current backend/live-interaction foundation is being hardened before deeper simulation systems are added.

The next development direction is expected to focus on:

- stronger procedural world generation;
- improved provisional visual identity;
- valid navigable regions and spawn areas;
- resources;
- hunger and energy;
- simple autonomous decision-making;
- the first persistent life loop.

The final visual style is intentionally deferred until the simulation loop has been validated.

---

# Design Principle

WORLD 001 is not intended to become a screen full of buttons and instructions.

The desired experience is:

```text
simple to enter
↓
easy to understand
↓
interesting to watch
↓
increasingly complex underneath
```

The LIVE should expose moments from a world that feels alive rather than requiring viewers to understand every system immediately.

---

# Author

**Gabriel Almeida**  
Software Developer

[LinkedIn](https://www.linkedin.com/in/gabriel-almeida-258453364/)