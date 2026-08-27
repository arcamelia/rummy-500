# rummy-500

A small Python engine for Rummy 500. The rules live in the game model, while the CLI is just a thin adapter on top.

## What this project is

The codebase models the core of a Rummy 500 game:

- cards have stable identity and status
- players own hands and played cards
- table plays are represented as structured `Play` objects
- game state is validated and serialized as dict payloads
- snapshot validation catches duplicate IDs and malformed state

## Files

- `rummy/card.py` — card identity, suit/rank enums, status transitions
- `rummy/player.py` — hand ownership and player seat state
- `rummy/play.py` — structured play object for runs and wrecks
- `rummy/game.py` — legal move logic, table behavior, state validation, serialization
- `rummy/validators.py` — validation of dict/JSON/file snapshots
- `rummy/game_console_adaptor.py` — CLI adapter for interactive play

## Core model

### Card

A `Card` is the atomic unit of the game. It carries:

- `suit`
- `rank`
- `status`
- `player_id`
- generated `card_id`

Important points:

- `card_id` is the stable identity used for equality and hashing
- `Card.to_dict()` includes `card_id` so the object can be reconstructed reliably
- `Card.from_dict()` restores the same identity instead of generating a new one
- status transitions happen through `update()` and must remain consistent with ownership

### Player

A `Player` owns:

- `id`
- `hand`
- `played_cards`

The player layer is intentionally small: it manages hand updates, discard transitions, and played-card tracking, but does not own rule logic for legality.

### Play

A `Play` represents one table entry, rather than a brittle string key encoding metadata.

A play contains:

- `id`
- `type` (`RUN` or `WRECK`)
- `key` (suit for runs, rank for wrecks)
- `cards`

This is a cleaner model than earlier table representations that encoded play metadata in strings.

### Game

`Game` is the center of the engine. It owns:

- players
- pickup pile
- discard pile
- active plays
- card location lookup
- play id counter

It is responsible for:

- dealing cards
- validating move legality
- adding to or merging plays on the table
- cleaning up play state after merges
- checking duplicate IDs and state consistency
- serializing/deserializing the round state

## Game flow

A turn follows a simple loop:

1. pickup from pickup pile or discard pile
2. optionally play cards onto the table
3. discard one card
4. pass to next player

## Serialization

The canonical serialized format is a dict with a `plays` list.

Example:

```json
{
  "players": [
    {
      "player_id": 1,
      "hand": [
        {"suit": "HEARTS", "rank": "TEN", "status": "HAND", "player_id": 1, "card_id": "..."}
      ],
      "played_cards": []
    }
  ],
  "pile_pickup": [
    {"suit": "CLUBS", "rank": "ACE", "status": "PILE_PICKUP", "player_id": null, "card_id": "..."}
  ],
  "pile_discard": [
    {"suit": "DIAMONDS", "rank": "KING", "status": "PILE_DISCARD", "player_id": null, "card_id": "..."}
  ],
  "plays": [
    {
      "play_id": 1,
      "type": "R",
      "key": "HEARTS",
      "cards": [
        {"suit": "HEARTS", "rank": "NINE", "status": "TABLE", "player_id": 1, "card_id": "..."},
        {"suit": "HEARTS", "rank": "TEN", "status": "TABLE", "player_id": 1, "card_id": "..."},
        {"suit": "HEARTS", "rank": "JACK", "status": "TABLE", "player_id": 1, "card_id": "..."}
      ]
    }
  ],
  "id_counter": 1
}
```

Important details:

- `Game.to_dict()` emits the serialized state
- `Game.from_dict()` reconstructs the game from that payload
- `plays` is the canonical serialized form; legacy `table`-style encodings are not used
- the in-memory `Game.plays` dict may still use readable `str(play)` keys, but the persisted format is a list

## Validation

Validation is split into two layers:

### In-memory validation

`Game.validate()` checks that:

- no card appears in more than one location
- statuses match their location (hand/table/pile)

### Snapshot validation

`validate_snapshot()` checks dict/JSON/file snapshots before they are accepted as game state. It also rejects duplicate `card_id`s.

This is the main safeguard for external input and persistence paths.

## Current project status

- the core model is stable
- serialization is consistent
- duplicate detection works
- the test suite passes
- the project is ready for a thin UI or server layer on top

## Follow-up work worth doing next

cleanup and refactoring opportunities:

- split large game-rule methods into smaller helpers
- move table merge logic into a more explicit table abstraction
- strengthen snapshot validation beyond the current duplicate/status checks
- add more rule-focused tests for edge cases and ace handling

## Web UI migration plan

The engine is already structured well for a web transition because the game rules and state model are centralised in Python. The safest migration path is to keep the engine as the source of truth and add a thin server/UI layer around it rather than rewriting rules logic into a browser frontend.

### 1. Keep the engine authoritative

The Python game object should remain the canonical rules engine for all gameplay decisions.

- `Game` owns legal move checks and state transitions
- `Card`, `Player`, and `Play` define the domain model
- `validate_snapshot()` remains the guardrail for incoming state payloads
- the UI should not reimplement move legality or card ownership logic

This preserves the current separation between core logic and presentation.

### 2. Add a persistent API boundary

The next step is to expose the engine through a small HTTP or WebSocket layer.

Recommended responsibilities:

- create or restore game sessions
- return a canonical game snapshot using `Game.to_dict()`
- accept player actions as structured payloads
- validate incoming data before mutation
- apply engine rules and return the updated state

A good contract is:

- server receives a player action or move request
- server reconstructs state from snapshot or persisted game record
- server runs the rule engine
- server emits a new validated snapshot back to the client

This pattern keeps the UI stateless and ensures every game action passes through the same logic path.

### 3. Use the current snapshot format as the transport contract

The current `plays`-based snapshot format is already a strong foundation for network use.

For a web UI, each client can store and render the latest snapshot returned by the server, and only the server is allowed to mutate game state.

The transport payload should contain:

- players and their hand state
- pickup/discard piles
- active `plays`
- identity metadata such as `card_id` and `play_id`

This makes it easy to:

- render the state in a browser
- persist game sessions
- replay or restore a game
- validate before accepting any incoming payload

### 4. Split responsibilities between server and client

A clean split is:

- server: game logic, validation, persistence, turn ordering, player actions
- client: rendering, input capture, animation, user interaction, optimistic UI only for presentation

The client should never be treated as the authority on legal play. It may show buttons or drag-and-drop affordances, but the final check must happen server-side.

This matters for multiplayer because each device is only a view into the authoritative world state.

### 5. Define the multiplayer flow

For multi-player devices, the server should own the session lifecycle.

Suggested model:

- one game session per table
- each player has a seat and a client connection
- the server tracks whose turn it is
- moves are authorized by player identity and current turn state
- messages are broadcast as full snapshots or targeted diffs

This keeps players synchronised without letting clients manipulate hidden game state.

### 6. Introduce UI-specific adapters, not new rules code

The browser app should focus on:

- rendering cards and plays
- handling drag/drop or button selection
- showing turn state and game status
- sending player actions to the server

The UI should adapt the canonical engine model rather than reproduce it. Any logic that checks “is this move valid?” must route back through the server or the Python engine.

### 7. Add validation at the network boundary

Before any mutable server action is accepted, the request should be validated as a proper game action payload.

The current validation strategy already points in the right direction:

- `Game.validate()` guards live state
- `validate_snapshot()` guards serialized input
- the server should reject malformed actions and malformed snapshots before mutation

This is especially important once multiple devices send actions concurrently.

### 8. Recommended rollout plan

A practical transition sequence is:

1. keep the existing CLI and engine as-is
2. expose a minimal API around `Game.to_dict()` and `Game.from_dict()`
3. add a server-side `create_game`, `apply_action`, and `get_snapshot` layer
4. build a browser client that renders the returned snapshot
5. add websocket or polling updates for real-time multiplayer sync
6. move persistence, session management, and reconnect handling into the server layer

### 9. Design goal

The target architecture should feel like this:

- engine = rules and state
- server = session authority and validation
- frontend = view and user interaction
- snapshots = durable, portable game state contract

That keeps the project easy to test, easy to extend, and consistent with the design already present in the codebase.

In other words, the web UI transition is not a rewrite of the game logic. It is a controlled expansion of the existing engine boundary into a client/server model while preserving the core rules as the single source of truth.
