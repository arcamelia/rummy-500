import pytest

from card import Card, Suit, Rank, CardStatus
from game import Game
from errors.exceptions import DuplicateIDError


def make_game_with_duplicate_card_in_hand_and_pickup():
    g = Game(2)
    # take an existing card from pickup
    if not g.pile_pickup:
        return g
    card = g.pile_pickup[0]
    # craft a serialized dict and duplicate the card_id into a player's hand
    gd = g.to_dict()
    # inject the same card_id into player 1's hand by copying the first pickup card
    if gd['players'] and gd['pile_pickup']:
        dup_card = dict(gd['pile_pickup'][0])
        gd['players'][0]['hand'].append(dup_card)
    return gd


def test_game_from_dict_raises_on_duplicate_ids():
    gd = make_game_with_duplicate_card_in_hand_and_pickup()
    with pytest.raises(DuplicateIDError):
        Game.from_dict(gd)
