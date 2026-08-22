import json
import os
from pathlib import Path
from typing import Union

from errors.exceptions import DuplicateIDError, GameStateError


def _check_card_dict(cd: dict, location: str, seen: set):
    if not isinstance(cd, dict):
        raise GameStateError("card entry must be a dict")
    cid = cd.get('card_id')
    if cid is None or not isinstance(cid, str):
        raise GameStateError("card_id missing or invalid in snapshot")
    if cid in seen:
        raise DuplicateIDError(f"Duplicate card_id in snapshot: {cid}")
    seen.add(cid)

    st = cd.get('status')
    # only validate when status is present
    if st is not None:
        if location == 'hand' and st != 'HAND':
            raise GameStateError(f"Card {cid} in hand but status is {st}")
        if location == 'played' and st != 'TABLE':
            raise GameStateError(f"Card {cid} in played_cards but status is {st}")
        if location == 'pickup' and st != 'PILE_PICKUP':
            raise GameStateError(f"Card {cid} in pile_pickup but status is {st}")
        if location == 'discard' and st != 'PILE_DISCARD':
            raise GameStateError(f"Card {cid} in pile_discard but status is {st}")
        if location == 'table' and st != 'TABLE':
            raise GameStateError(f"Card {cid} on table but status is {st}")


def validate_snapshot(obj: Union[dict, str, Path]) -> None:
    """Validate a serialized game snapshot without constructing a Game.

    Accepts either a dict, a JSON string, or a file path to a JSON file.

    Raises `DuplicateIDError` or `GameStateError` on failure.
    """
    if isinstance(obj, dict):
        d = obj
        # fall through
    elif isinstance(obj, (str, Path)):
        # Try parsing as JSON string first (handles both compact and pretty JSON).
        try:
            d = json.loads(str(obj))
        except Exception:
            # If parsing failed, try treating as a file path and read its contents.
            p = Path(obj)
            if p.exists() and p.is_file():
                try:
                    d = json.loads(p.read_text())
                except Exception as e:
                    raise GameStateError(f"failed to parse JSON file: {e}")
            else:
                raise GameStateError("failed to parse JSON string and path does not exist")
    else:
        raise GameStateError("validate_snapshot expects a dict, JSON string, or file path")

    if not isinstance(d, dict):
        raise GameStateError("snapshot root must be a dict")

    seen = set()

    # players
    players_list = d.get('players', [])
    if not isinstance(players_list, list):
        raise GameStateError("'players' must be a list in snapshot")
    for pd in players_list:
        if not isinstance(pd, dict):
            raise GameStateError("player entry must be a dict")
        hand = pd.get('hand', [])
        if not isinstance(hand, list):
            raise GameStateError("'hand' must be a list in player snapshot")
        for cd in hand:
            _check_card_dict(cd, 'hand', seen)
        played = pd.get('played_cards', [])
        if not isinstance(played, list):
            raise GameStateError("'played_cards' must be a list in player snapshot")
        for cd in played:
            _check_card_dict(cd, 'played', seen)

    # piles
    pile_pickup_list = d.get('pile_pickup', [])
    if not isinstance(pile_pickup_list, list):
        raise GameStateError("'pile_pickup' must be a list in snapshot")
    for cd in pile_pickup_list:
        _check_card_dict(cd, 'pickup', seen)

    pile_discard_list = d.get('pile_discard', [])
    if not isinstance(pile_discard_list, list):
        raise GameStateError("'pile_discard' must be a list in snapshot")
    for cd in pile_discard_list:
        _check_card_dict(cd, 'discard', seen)

    # table
    table_obj = d.get('table', {})
    if not isinstance(table_obj, dict):
        raise GameStateError("'table' must be a dict in snapshot")
    for k, v in table_obj.items():
        if not isinstance(v, list):
            raise GameStateError("table entry must be a list of card dicts")
        for cd in v:
            _check_card_dict(cd, 'table', seen)
