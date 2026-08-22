import json
import pytest

from rummy.card import Card, Suit, Rank, CardStatus
from rummy.player import Player
from rummy.game import Game


def test_card_from_dict_invalid_inputs():
    # non-dict
    with pytest.raises(ValueError):
        Card.from_dict(None)

    # missing card_id
    with pytest.raises(ValueError):
        Card.from_dict({'suit': 'CLUBS', 'rank': 'ACE', 'status': 'HAND', 'player_id': 1})

    # invalid suit name
    bad = {'suit': 'FOO', 'rank': 'ACE', 'status': 'HAND', 'player_id': 1, 'card_id': 'abc'}
    with pytest.raises(ValueError):
        Card.from_dict(bad)


def test_player_from_dict_invalid_inputs():
    with pytest.raises(ValueError):
        Player.from_dict(None)

    # bad player_id type
    with pytest.raises(ValueError):
        Player.from_dict({'player_id': 'one', 'hand': [], 'played_cards': []})

    # hand not a list
    with pytest.raises(ValueError):
        Player.from_dict({'player_id': 1, 'hand': 'notalist', 'played_cards': []})

    # played_cards not a list
    with pytest.raises(ValueError):
        Player.from_dict({'player_id': 1, 'hand': [], 'played_cards': 'nope'})


def test_game_from_dict_invalid_inputs():
    with pytest.raises(ValueError):
        Game.from_dict(None)

    # players not a list
    with pytest.raises(ValueError):
        Game.from_dict({'players': 'nope', 'pile_pickup': [], 'pile_discard': [], 'table': {}})

    # pile_pickup not a list
    with pytest.raises(ValueError):
        Game.from_dict({'players': [], 'pile_pickup': 'bad', 'pile_discard': [], 'table': {}})

    # table not a dict
    with pytest.raises(ValueError):
        Game.from_dict({'players': [], 'pile_pickup': [], 'pile_discard': [], 'table': []})


def test_card_update_enforces_player_when_needed():
    c = Card(Suit.HEARTS, Rank.TWO, CardStatus.PILE_PICKUP, player=None)
    # updating to HAND without providing player id should raise
    with pytest.raises(ValueError):
        c.update(CardStatus.HAND, None)


def test_player_hand_immutable_snapshot():
    p = Player(1)
    c = Card(Suit.SPADES, Rank.THREE, None, player=None)
    p.add_to_hand(c)
    hand = p.get_hand()
    assert isinstance(hand, tuple)
    with pytest.raises(AttributeError):
        hand.append('x')


def test_integration_game_json_roundtrip():
    g = Game(3)
    gd = g.to_dict()
    # must be JSON-serializable
    s = json.dumps(gd)
    parsed = json.loads(s)
    g2 = Game.from_dict(parsed)
    assert len(g.get_players()) == len(g2.get_players())
    # ensure some card ids preserved
    if g.pile_pickup:
        assert [c.get_id() for c in g.pile_pickup] == [c.get_id() for c in g2.pile_pickup]
