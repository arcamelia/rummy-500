import pytest

from rummy.card import Card, Suit, Rank, CardStatus
from rummy.game import Game
from rummy.errors.exceptions import DuplicateIDError


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


def test_duplicate_between_player_hand_and_table():
    g = Game(2)
    gd = g.to_dict()
    # ensure there is at least one player hand and one table entry to manipulate
    if not gd['players']:
        pytest.skip("no players to test with")
    if not gd.get('plays'):
        # create a play entry by duplicating a pickup card into plays
        if not gd['pile_pickup']:
            pytest.skip("no cards to craft play entry")
        gd['plays'] = [{'play_id': 1, 'type': 'R', 'key': 'X', 'cards': [dict(gd['pile_pickup'][0])]}]

    # pick a card from player 0's hand (or pickup if empty)
    source_list = gd['players'][0]['hand'] if gd['players'][0]['hand'] else gd['pile_pickup']
    if not source_list:
        pytest.skip("no cards available to duplicate")

    dup_card = dict(source_list[0])
    # append the same card to the first table entry
    first_play = gd['plays'][0]
    first_play['cards'].append(dup_card)

    with pytest.raises(DuplicateIDError):
        Game.from_dict(gd)


def test_duplicate_across_table_entries():
    g = Game(2)
    gd = g.to_dict()
    # ensure at least two table entries exist; if not, craft them from pickup cards
    plays = gd.get('plays', [])
    if len(plays) < 2:
        if len(gd.get('pile_pickup', [])) < 2:
            pytest.skip("not enough cards to craft play entries")
        gd['plays'] = [
            {'play_id': 1, 'type': 'R', 'key': 'X', 'cards': [dict(gd['pile_pickup'][0])]},
            {'play_id': 2, 'type': 'R', 'key': 'Y', 'cards': [dict(gd['pile_pickup'][1])]}
        ]
        plays = gd['plays']

    # duplicate a card from the first play into the second
    if not plays[0]['cards']:
        pytest.skip("first play entry empty")
    dup_card = dict(plays[0]['cards'][0])
    plays[1]['cards'].append(dup_card)

    with pytest.raises(DuplicateIDError):
        Game.from_dict(gd)
