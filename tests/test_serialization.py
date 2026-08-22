from card import Card, Suit, Rank, CardStatus
from player import Player
from game import Game


def test_card_roundtrip_preserves_id_and_equality():
    c = Card(Suit.CLUBS, Rank.ACE, CardStatus.PILE_PICKUP, player=None)
    d = c.to_dict()
    c2 = Card.from_dict(d)
    assert c.get_id() == c2.get_id()
    assert c == c2
    assert hash(c) == hash(c2)


def test_player_roundtrip_preserves_cards_and_ids():
    p = Player(1)
    # add a card via Player.add_to_hand which enforces status/player
    card = Card(Suit.HEARTS, Rank.KING, None, player=None)
    p.add_to_hand(card)

    pd = p.to_dict()
    p2 = Player.from_dict(pd)

    assert p.get_id() == p2.get_id()
    # hands should have same length and same card ids
    hand_ids = [c.get_id() for c in p.get_hand()]
    hand2_ids = [c.get_id() for c in p2.get_hand()]
    assert hand_ids == hand2_ids


def test_game_roundtrip_preserves_structure_and_card_ids():
    g = Game(2)
    gd = g.to_dict()
    g2 = Game.from_dict(gd)

    # same number of players
    assert len(g.get_players()) == len(g2.get_players())

    # compare pile pickup card ids
    pickup_ids = [c.get_id() for c in g.pile_pickup]
    pickup2_ids = [c.get_id() for c in g2.pile_pickup]
    assert pickup_ids == pickup2_ids

    discard_ids = [c.get_id() for c in g.pile_discard]
    discard2_ids = [c.get_id() for c in g2.pile_discard]
    assert discard_ids == discard2_ids
