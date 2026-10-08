# Interactive Live Engine

**A modular event-driven foundation for building interactive TikTok LIVE games.**

The Interactive Live Engine is a reusable backend foundation for games that react to TikTok LIVE events such as comments, gifts, likes, follows, shares, and joins.

The project originated from the **WORLD 001** prototype and is being refactored so the infrastructure required for TikTok LIVE interaction can be built once and reused across future games.

> **The Engine receives events. The game decides what they mean.**

---

## Overview

Building an interactive TikTok LIVE game usually requires the same infrastructure repeatedly:

* connecting to the LIVE;
* handling reconnections;
* receiving platform events;
* normalizing provider-specific data;
* identifying viewers;
* preventing duplicate processing;
* routing events to gameplay;
* delivering realtime output to a client;
* simulating events locally;
* logging and monitoring the runtime;
* testing the complete event pipeline.

The purpose of this project is to provide that foundation before a new game is built.

A future game should be able to focus primarily on:

```text
GAMEPLAY
+
RULES
+
CLIENT
```

instead of rebuilding the entire TikTok integration and event infrastructure.

---

## Architecture

The core flow is:

```text
TikTok LIVE
     │
     ▼
TikTok Provider
     │
     ▼
TikTok Adapter
     │
     ▼
   LiveEvent
     │
     ▼
Event Ingestion
     │
     ▼
Engine Runtime
     │
     ▼
Interactive Experience
     │
     ▼
 OutputEvent
     │
     ▼
Realtime Manager
     │
     ▼
Game Client
```

The architecture separates platform integration from gameplay.

A TikTok event is first converted into an internal `LiveEvent`. The Engine then delivers that event to the active `InteractiveExperience`, which decides how the game should react and produces an `OutputEvent`.

This means the core does not contain rules such as:

```text
Rose creates a character
Comment "A" means vote
Gift gives energy
Like damages an enemy
```

Those decisions belong to the game being built on top of the Engine.

---

## Core Concepts

### LiveEvent

`LiveEvent` is the internal event contract used by the Engine.

It abstracts provider-specific event objects into a stable structure containing information such as:

```text
event_id
event type
provider
provider event id
session
timestamp
viewer
payload
```

A game should consume `LiveEvent`, not classes from the TikTok provider library.

### Viewer

Represents the viewer associated with an event.

The model can contain:

```text
provider_user_id
username
display_name
avatar_url
```

Stable provider identifiers are preferred when available.

### InteractiveExperience

An `InteractiveExperience` represents the game-specific layer running on the Engine.

It is responsible for interpreting incoming events and producing gameplay outputs.

Conceptually:

```python
class InteractiveExperience:

    async def start(self, context):
        ...

    async def stop(self, context):
        ...

    async def handle_event(self, event, context):
        ...

    async def get_state(self):
        ...

    async def health(self):
        ...
```

The Engine provides the runtime. The Experience provides the game.

### OutputEvent

`OutputEvent` is the result produced by an Experience after processing an event.

The Engine transports the output to connected clients through the realtime layer.

```text
LiveEvent
    ↓
Experience
    ↓
OutputEvent
    ↓
WebSocket
    ↓
Client
```

---

## TikTok Integration

TikTok is isolated inside the provider layer.

```text
TikTokLive
    ↓
Provider Listener
    ↓
TikTok Adapter
    ↓
LiveEvent
```

The provider is responsible for TikTok-specific concerns such as:

* connection;
* reconnection;
* event reception;
* viewer normalization;
* provider event identifiers;
* comment conversion;
* gift conversion;
* streak handling.

Gameplay is intentionally outside this layer.

### Gifts and Roses

A Rose is represented by the Engine simply as a normal:

```text
GIFT
```

The Engine does not assign gameplay meaning to individual gifts.

The game decides what a gift means.

This allows the same infrastructure to support different game designs without modifying the TikTok integration.

---

## Supported Event Types

The initial internal event model includes:

```text
COMMENT
GIFT
LIKE
FOLLOW
SHARE
JOIN
CONNECT
DISCONNECT
```

Provider availability may vary.

The Engine's responsibility is to normalize supported events into a common internal contract.

---

## Event Processing

Incoming events follow the central ingestion pipeline:

```text
Provider Event
     ↓
Adapter
     ↓
LiveEvent
     ↓
Viewer Resolution
     ↓
Event Persistence
     ↓
Deduplication
     ↓
Engine Dispatch
     ↓
Experience
     ↓
OutputEvent
     ↓
Realtime
```

Event persistence currently tracks processing states such as:

```text
RECEIVED
PROCESSED
FAILED
```

Provider event identifiers are used when available to prevent duplicate processing.

---

## Development Simulator

The project includes a development event simulator so the Engine can be exercised without opening a real TikTok LIVE.

Example:

```bash
python scripts/simulate_event.py comment --user gabriel --text "test"
```

Gift simulation:

```bash
python scripts/simulate_event.py gift --user gabriel --gift Rose --quantity 1
```

The simulator generates generic events rather than hard-coding gameplay rules.

This makes it possible to develop and test the event pipeline independently from TikTok.

---

## Development API

Development builds expose a generic event endpoint:

```http
POST /api/v1/dev/events
```

Example payload:

```json
{
  "type": "GIFT",
  "provider": "dev",
  "provider_event_id": "dev-event-001",
  "viewer": {
    "provider_user_id": "dev-001",
    "username": "gabriel"
  },
  "payload": {
    "gift_name": "Rose",
    "quantity": 1
  }
}
```

The endpoint is intentionally generic and does not contain game-specific routes.

---

## Realtime

Experiences communicate through `OutputEvent`.

The realtime layer converts those outputs into WebSocket messages for connected clients.

```text
Experience
    ↓
OutputEvent
    ↓
Realtime Manager
    ↓
WebSocket
    ↓
Client
```

This allows different games to use different clients without rebuilding the event transport layer.

Possible clients include:

```text
Godot
Web / OBS
External game clients
```

---

## Technology Stack

### Backend

* Python
* FastAPI
* SQLAlchemy
* Alembic
* WebSockets
* TikTokLive

### Testing

* pytest
* pytest-asyncio

### Client Integration

* Godot for game clients originating from the current prototype
* WebSocket-based clients for realtime communication

### Persistence

The current backend includes relational persistence and Alembic migrations. Persistence is intended to be used when a game requires durable state rather than being mandatory for every possible game.

---

## Project Structure

The repository is being reorganized around the Engine boundary.

The current backend is structured around these main areas:

```text
backend/
├── app/
│   ├── api/
│   ├── db/
│   ├── events/
│   ├── experiences/
│   ├── models/
│   ├── providers/
│   │   └── tiktok/
│   ├── realtime/
│   ├── runtime/
│   └── services/
│
├── scripts/
└── tests/
```

The architectural direction is to keep the Engine infrastructure separate from game-specific code and clients.

---

## Running Locally

The backend is currently developed from the `backend/` directory.

### Start the API

```bash
cd backend
.venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

Once running, the FastAPI application provides its development documentation through:

```text
/docs
```

### Health Check

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

The service name reflects the project's origin in WORLD 001 and will be updated as the Engine replaces the remaining legacy identity.

---

## Testing

The backend uses `pytest` for automated testing.

From the `backend/` directory:

```bash
.venv\Scripts\python.exe -m pytest -q
```

Current verified checkpoint:

```text
62 passed
0 failures
```

The test suite covers the event contracts, runtime, realtime communication, event ingestion, TikTok adapter, listeners, and integration flows.

---

## Current Status

**Status: Active development — Engine refactor**

The core event pipeline is functional and the project has already established the main architectural boundaries between:

```text
Provider
    ↓
LiveEvent
    ↓
Engine
    ↓
Experience
    ↓
OutputEvent
    ↓
Realtime
```

The TikTok provider is currently isolated from WORLD 001 gameplay, and the development event API is generic.

The next architectural stage is the separation between **domain events and persistence models**, followed by further extraction of the remaining WORLD 001-specific implementation from the Engine infrastructure.

The Engine is not yet considered a finished reusable distribution.

---

## From WORLD 001 to a Reusable Engine

WORLD 001 was the original implementation that demonstrated the concept.

The current repository extracts the infrastructure that can be reused by future games.

The intended evolution is:

```text
WORLD 001 prototype
        ↓
extract infrastructure
        ↓
Interactive Live Engine
        ↓
new game
        ↓
new gameplay
```

WORLD 001 is therefore part of the project's history and migration path, not the definition of the Engine itself.

---

## Creating a New Game

Once the Engine foundation is complete, a new game should be created as an Experience on top of the existing infrastructure.

The intended development flow is:

```text
Game idea
    ↓
Define gameplay
    ↓
Create Experience
    ↓
Choose relevant LIVE events
    ↓
Implement game rules
    ↓
Define OutputEvents
    ↓
Connect client
    ↓
Simulate locally
    ↓
Test
    ↓
Run end-to-end
    ↓
TikTok LIVE
```

The new game should not need to recreate:

```text
TikTok connection
reconnection
event normalization
viewer handling
event ingestion
deduplication
WebSocket transport
simulator
basic health
logging
test infrastructure
```

---

## Design Principles

### Event-driven

External interactions are represented as events and passed through a predictable processing pipeline.

### Provider-independent gameplay

TikTok-specific objects must not become gameplay contracts.

### Experience-based gameplay

The game decides how incoming events affect its world, rules, state, and mechanics.

### Reusable realtime

WebSocket infrastructure belongs to the Engine rather than individual games.

### Local-first development

Developers should be able to simulate and test interactions without depending on a live audience.

### Evidence over assumptions

The Engine is validated through automated tests, local simulation, integration tests, and real provider integration rather than by embedding multiple demonstration games into the repository.

### Simplicity before scale

The initial architecture favors a modular application over premature microservices or unnecessary infrastructure.

---

## Security

The system treats viewer-generated content as untrusted input.

Comments and other LIVE data must not become arbitrary:

```text
shell commands
SQL
eval / exec
system input
```

without an explicit parser, validation, and allowlist.

Provider credentials and secrets are configuration concerns and are not part of the event payload or client-facing realtime messages.

---

## Roadmap

The roadmap focuses on completing the Engine before building games on top of it.

### Engine Core

* [x] Generic `LiveEvent`
* [x] `Viewer`
* [x] Event type system
* [x] Event Router
* [x] Experience contract
* [x] Experience Context
* [x] Experience Loader
* [x] Engine Runtime
* [x] Output events
* [x] Realtime manager
* [x] WebSocket event transport

### Provider

* [x] TikTok adapter
* [x] Comment normalization
* [x] Gift normalization
* [x] Rose represented as a generic gift
* [x] Provider event IDs
* [x] Gift streak handling
* [x] Basic reconnect strategy

### Development

* [x] Generic development event API
* [x] Local event simulator
* [x] Automated tests
* [x] Integration pipeline tests

### Next

* [ ] Separate domain events from persistence models
* [ ] Complete WORLD 001 gameplay isolation
* [ ] Establish reusable client foundations
* [ ] Improve local developer tooling
* [ ] Add session/replay infrastructure where justified
* [ ] Complete Engine hardening and end-to-end validation
* [ ] Prepare the base for new game development

---

## Repository Philosophy

The purpose of this repository is not to contain every game that can be built with it.

It exists to make building those games significantly easier.

```text
ONE ENGINE
    +
MANY FUTURE GAMES
```

The infrastructure should be solved once.

The gameplay should be created separately.

---

## Author

**Gabriel Almeida**

Software Developer

GitHub: [Gabriel Almeida](https://github.com/GabrielJalmeida)
