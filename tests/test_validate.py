import pytest

from rummy.game import Game
from rummy.errors.exceptions import DuplicateIDError, GameStateError


def test_validate_passes_on_new_game():
    g = Game(2)
    # basic validate should pass
    g.validate()


def test_validate_detects_duplicate_in_memory():
    g = Game(2)
    # artificially duplicate a card object reference across structures
    if not g.pile_pickup or not g.players:
        pytest.skip("not enough cards to craft duplicate")
    card = g.pile_pickup[0]
    # append same card object to player's hand (reach into player internals)
    g.players[0]._hand.append(card)
    with pytest.raises((DuplicateIDError, GameStateError)):
        g.validate()


def test_validate_detects_status_mismatch():
    g = Game(2)
    # take a pickup card and put it into pile_discard without updating status
    if not g.pile_pickup:
        pytest.skip("no pickup cards")
    card = g.pile_pickup.pop()
    # leave card.status as PILE_PICKUP but place it in discard
    g.pile_discard.append(card)
    with pytest.raises(GameStateError):
        g.validate()
