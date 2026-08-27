# rummy-500

A small engine for the Rummy 500 card game with serialization and a CLI adapter.

**Quick Overview**
- **Card identity:** `Card` auto-generates a persistent `card_id` at construction. `Card.from_dict()` requires a `card_id` in the input and restores it during deserialization. Equality and hashing are based on `card_id`.
- **Serialization keys:** use `card_id` and `player_id` in `to_dict()`/`from_dict()` payloads.
- **Engine / UI separation:** `Game` is UI-agnostic; `GameConsoleAdapter` provides the interactive CLI layer.
- **Validation & errors:** deserializers validate inputs and raise `ValueError` for malformed payloads; code uses exceptions instead of prints.
- **Immutability:** getters return snapshots (tuples) to avoid accidental mutation of internal state.

**Usage notes**
- Create a card: `Card(Suit.HEARTS, Rank.ACE)` — it will receive a generated `card_id`.
- Serialize: call `to_dict()` on `Card`, `Player`, or `Game`.
- Deserialize: call `Card.from_dict(d)` (the dictionary must include a string `card_id`).
 - Serialized game format: `Game.to_dict()` now emits a canonical `plays` list rather than
	 the older `table` mapping. Each play is a dict with `play_id`, `type`, `key`, and `cards`.
	 Example:
	 ```json
	 {
		 "players": [...],
		 "pile_pickup": [...],
		 "pile_discard": [...],
		 "plays": [
			 {"play_id": 1, "type": "R", "key": "HEARTS", "cards": [ ... ]},
			 {"play_id": 2, "type": "W", "key": "THREE", "cards": [ ... ]}
		 ]
	 }
	 ```
 - Note: `Game.from_dict()` now requires `plays` to be present. Legacy `table`-based input
	 is no longer accepted.
Export: `json.dumps(game.to_dict())`
Import: `game = Game.from_dict(json.loads(s))`

**Quick checks**
Run a quick syntax check after edits:
```bash
python3 -m py_compile card.py player.py game.py
```

**Next steps**
- Add unit tests for serialization round-trips and identity preservation.
- Outline server/client (FastAPI/WebSockets) and React frontend scaffold.

## Prioritized Fixes & Design Notes

This project has been analyzed for correctness, security, and maintainability. Below is a prioritized list of issues, explanations, and concrete fixes to guide refactors and future work.

### Important Correctness & Design Issues — Do Soon (P1)
- Table representation is brittle: it encodes play metadata in string keys (e.g., `RH3`). Introduce `Play` (dataclass) and `Table` manager classes, and move table logic (find match, join plays, cleanup) there.
- Break up large methods into smaller helpers to improve readability and testability:
	- `Game.legal_play_spec` → `_is_wreck`, `_is_run`, `_normalize_ace_high`, `_is_run_addon`.
	- `__play_cards`, `__cards_can_be_joined`, `__clean_up_table` → move into `Table` methods.
- Add strict game-state invariants in `Game.from_dict`: no duplicate cards across hands/piles/table, card counts sum to expected deck size, and every `card_id` is unique.
- Add schema validation for external inputs (pydantic/jsonschema) for clearer, faster failure modes on malformed payloads.

### Cleanup & Maintainability — Medium (P2)
- Consider making `Card` immutable after validated creation, or provide explicit mutation methods that enforce invariants.
- Add structured logging for server adapters; keep engine I/O-free.

### Testing and CI
- Add tests for duplicate/overlapping card placements and other invariants (not yet implemented).
- CI currently runs `pytest`, `ruff`, and captures coverage. Consider adding coverage thresholds and codecov integration.
