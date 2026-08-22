import json
import pytest

from game import Game
from errors.exceptions import DuplicateIDError, GameStateError
from validators import validate_snapshot


def test_validate_snapshot_passes_on_serialized_game():
    g = Game(2)
    gd = g.to_dict()
    validate_snapshot(gd)


def test_validate_snapshot_detects_duplicate_card_id():
    g = Game(2)
    gd = g.to_dict()
    # duplicate first pickup card into player 0 hand
    if not gd['pile_pickup']:
        pytest.skip("no pickup cards")
    dup = dict(gd['pile_pickup'][0])
    # mark the duplicated card as if it were in a hand so duplicate-ID
    # detection is triggered rather than a status/location mismatch
    dup['status'] = 'HAND'
    gd['players'][0]['hand'].append(dup)
    with pytest.raises(DuplicateIDError):
        validate_snapshot(gd)


def test_validate_snapshot_status_mismatch():
    g = Game(2)
    gd = g.to_dict()
    # place a pickup card into discard list without changing status
    if not gd['pile_pickup']:
        pytest.skip("no pickup cards")
    c = gd['pile_pickup'].pop()
    gd['pile_discard'].append(c)
    with pytest.raises(GameStateError):
        validate_snapshot(gd)


def test_validate_snapshot_accepts_json_string():
    g = Game(2)
    gd = g.to_dict()
    s = json.dumps(gd)
    validate_snapshot(s)


def test_validate_snapshot_accepts_file_path(tmp_path):
    g = Game(2)
    gd = g.to_dict()
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(gd))
    # accept path string
    validate_snapshot(str(p))
    # accept Path
    validate_snapshot(p)
