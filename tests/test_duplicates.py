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


def test_duplicate_between_player_hand_and_table():
    g = Game(2)
    gd = g.to_dict()
    # ensure there is at least one player hand and one table entry to manipulate
    if not gd['players']:
        pytest.skip("no players to test with")
    if not gd['table']:
        # create a table entry by moving a card from a player's hand into the table
        # but for serialized manipulation, we'll instead duplicate a pickup card into table
        if not gd['pile_pickup']:
            pytest.skip("no cards to craft table entry")
        gd['table'] = {'T1': [dict(gd['pile_pickup'][0])]}

    # pick a card from player 0's hand (or pickup if empty)
    source_list = gd['players'][0]['hand'] if gd['players'][0]['hand'] else gd['pile_pickup']
    if not source_list:
        pytest.skip("no cards available to duplicate")

    dup_card = dict(source_list[0])
    # append the same card to the first table entry
    first_table_key = next(iter(gd['table'].keys()))
    gd['table'][first_table_key].append(dup_card)

    with pytest.raises(DuplicateIDError):
        Game.from_dict(gd)


def test_duplicate_across_table_entries():
    g = Game(2)
    gd = g.to_dict()
    # ensure at least two table entries exist; if not, craft them from pickup cards
    keys = list(gd.get('table', {}).keys())
    if len(keys) < 2:
        # create two keys using pickup cards
        if len(gd.get('pile_pickup', [])) < 2:
            pytest.skip("not enough cards to craft table entries")
        gd['table'] = {
            'T1': [dict(gd['pile_pickup'][0])],
            'T2': [dict(gd['pile_pickup'][1])]
        }
        keys = ['T1', 'T2']

    # duplicate a card from the first table entry into the second
    first_key = keys[0]
    second_key = keys[1]
    if not gd['table'][first_key]:
        pytest.skip("first table entry empty")
    dup_card = dict(gd['table'][first_key][0])
    gd['table'][second_key].append(dup_card)

    with pytest.raises(DuplicateIDError):
        Game.from_dict(gd)
