from card import Card, Rank, Suit, CardStatus
from player import Player
from utils import str_list, format_list_of_str
import random
import copy
import pprint

MAX_PLAYERS = 7
NUM_CARDS_PER_PLAYER = 7
CARD_VALUES = {
    Rank.TWO: 5,
    Rank.THREE: 5,
    Rank.FOUR: 5,
    Rank.FIVE: 5,
    Rank.SIX: 5,
    Rank.SEVEN: 5,
    Rank.EIGHT: 5,
    Rank.NINE: 5,
    Rank.TEN: 10,
    Rank.JACK: 10,
    Rank.QUEEN: 10,
    Rank.KING: 10,
    Rank.ACE: 15
}

class Game:
    """
    Represents a game of Rummy 500.
    """
    players: set[Player]
    pile_pickup: list[Card]
    pile_discard: list[Card]
    table: dict[str,list[Card]]

    """
    Some notes on the table:

    * key formation:
        - prefix character of R (run) or W (wreck)
        - for a R, the second character indicates what suit it is
        - for a W, the second character indicates what rank it is
        - the integer at the end indicates the order of play, and is unique to that sequence

        when a player plays the 5H, it will be added to the front of RH5.
        however, when the 9H is played, it could be placed either at the front of RH3 or the 
        end of RH5. we will resolve this by combining the two lists together as RH3, and 
        removing RH5 from the map (we arbitrarily choose to keep the run that was played first).
    
    * the list values of each entry in the dict MUST BE KEPT IN SORTED ORDER

    * each player will keep track of the cards that they specifically have played, so it's not required
      for the central table to know who played what

    e.g. table = {
        RC1: [3C, 4C, 5C],
        WA2: [AC, AD, AS],
        RH3: [10H, JH, QH, KH, AH],
        RS4: [8S, 9S, 10S],
        RH5: [6H, 7H, 8H],
        W36: [3D, 3S, 3H]
    }

    """

    def __init__(self, num_players):
        self.players = set()
        self.add_players(num_players)
        deck: list[Card] = self.initialize_deck()
        self.deal_cards(deck, self.players)

        self.pile_discard = self.initialize_pile_discard(deck)
        self.pile_pickup = self.initialize_pile_pickup(deck)
        
        self.table: dict[str,list[Card]] = {}

    """
    Create and add the given number of players to the game (all with unique id).
    """
    def add_players(self, num_players: int) -> None:
        if num_players > MAX_PLAYERS:
            # todo: throw error
            print(f"Maximum number of players is {MAX_PLAYERS}")
            return
        
        for p in range(num_players):
            self.players.add(Player(p+1))

    """
    Rotate players' turns until it's not possible to continue, then return the game's score.
    """
    def run(self) -> dict[int,int]:
        while True:
            for p in self.players:
                if not p.can_pick_up():
                    print("No more cards to pick up")
                    return self.tally_scores()
                p.run_turn()
                if not p.get_hand():
                    print("A player has gotten rid of all their cards")
                    return self.tally_scores()

    """
    Return true if given list of cards can form a legal play (could be a R or a W).
    Constraint: will only return true if all cards in given list encompass a singular play
                For example, if the list of cards looks like [2H, 2D, 2S, JH, QH, KH], the method 
                will return false, as these two plays should be made separately (even though the 
                two plays are legal on their own).
    """
    def legal_play(self, cards: list[Card]) -> bool:
        if len(cards) < 3: return self.legal_play_addon(cards) # is it possible to use inheritance here?

        # check W (all same rank)
        ranks = Card.map_to_rank(cards)
        if all(x == ranks[0] for x in ranks): return True
        
        # check R (all same suit, consecutive ranks)
        suits = Card.map_to_suit(cards)
        same_suit = all(x == suits[0] for x in suits)
        consecutive_rank = sorted(ranks) == list(range(min(ranks), max(ranks)+1))

        # by default, ace has a rank of 1, but it can also be played high (essentially rank of 14)
        if Card.contains_ace(cards):
            for i in range(len(ranks)):
                if ranks[i] == 1:
                    ranks[i] = 14

            consecutive_rank = consecutive_rank or sorted(ranks) == list(range(min(ranks), max(ranks)+1))

        return same_suit and consecutive_rank

    """
    Return true iff all cards in given list can be added on to existing plays on the table.
    This method should only be called on lists with len < 3.
    """
    def legal_play_addon(self, cards: list[Card]) -> bool:
        match len(cards):
            case 1:
                # could be R or W
                return self.legal_one_card_play_r(cards[0]) or self.legal_one_card_play_w(cards[0])
            case 2:
                # can only be R
                c1: Card = cards[0]
                c2: Card = cards[1]
                one_card_legal = self.legal_one_card_play_r(c1) or self.legal_one_card_play_r(c2)
                return one_card_legal and Card.same_suit(c1, c2) and Card.consecutive_rank(c1, c2)
            case _:
                return False

    """
    Return true if given card can be played on an existing R.
    """
    def legal_one_card_play_r(self, card: Card) -> bool:
        key_to_find = "R" + str(card.get_suit())
        potentials: dict[str,list[Card]] = {}

        for k, v in self.table.items():
            if k.startswith(key_to_find): potentials[k] = v

        for v in potentials.values():
            # it's illegal to wrap around the end of a run, i.e., no K - A - 2
            consecutive_low_no_ace = Card.consecutive_rank(card, v[0]) and v[0].get_rank() != Rank.ACE
            consecutive_high_no_ace = Card.consecutive_rank(card, v[-1]) and v[-1].get_rank() != Rank.ACE
            if consecutive_low_no_ace or consecutive_high_no_ace: return True

        return False
    
    """
    Return true if given card can be played on an existing W.
    """
    def legal_one_card_play_w(self, card: Card) -> bool:
        key_to_find = "W" + str(card.get_rank())
        for k in self.table.keys():
            if k.startswith(key_to_find): return True
        return False

    """
    Return true if the given cards are in the discard pile and are involved in a rummy.

    definitions
    "pile rummy" : 3 or more cards in the discard pile can be played together
    "table rummy" : >= 1 card in the discard pile can be played somewhere on the table
                    AND the rummy is called after a player discards
                    (typically the card involved is the top card in the discard pile)
    "pickup rummy" : >= 1 card in the discard pile can be played somewhere on the table
                    AND the rummy is called after a player picks up
                    (typically the card involved is NOT the top card in the discard pile)

    for the purposes of writing the function, these semantics don't necessarily matter
    we need to develop an efficient algorithm for checking whether any one card can be
    played in conjunction with a potential mixture of discard and table cards

    there are 3 cases:
    - any 1 card in the discard pile can be attached to any of the table lists
    - any 2 cards in the discard pile can be attached to any of the table lists
    - any 3 or more cards in the discard pile can be played together
    (plus the case that 0 cards in the discard pile can be played, i.e., no rummy)

    """
    def check_rummy(self, cards: list[Card]) -> bool:
        # todo: check that the cards are in the discard pile
        return self.legal_play(cards)
            
    
    """
    Count up each player's points for the current round and return them in a dict.
    """
    def tally_scores(self) -> dict[int,int]:
        scores = {}
        for p in self.players:
            cards_played = p.get_table()
            score = 0
            for key, cards in cards_played:
                score += self.sum_points(cards)
            scores[p.get_id()] = score

    """
    Return the total point value of all the cards in given list.
    """
    def sum_points(self, cards: list[Card]) -> int:
        score = 0
        for c in cards:
            score += CARD_VALUES[c.get_rank()]
        return score

    """
    Initialize and return a new deck of shuffled cards.
    """
    def initialize_deck(self) -> list[Card]:
        deck: list[Card] = []
        for s in Suit:
            for r in Rank:
                card = Card(suit=s, rank=r, status=None, player=None)
                deck.append(card)
        random.shuffle(deck)
        return deck

    """
    Deal out NUM_CARDS_PER_PLAYER to the given players.
    """
    def deal_cards(self, deck: list[Card], players: list[Player]) -> None:
        for p in players:
            for _ in range(NUM_CARDS_PER_PLAYER):
                card = deck.pop()
                card.update(CardStatus.HAND, p.get_id())
                p.add_to_hand(card)

    """
    Return a list of cards representing the discard pile.
    """
    def initialize_pile_discard(self, deck: list[Card]) -> list[Card]:
        discard = []
        c = deck.pop().update(CardStatus.PILE_DISCARD)
        discard.append(c)
        return discard

    """
    Return a list of cards representing the pickup pile.
    """
    def initialize_pile_pickup(self, deck: list[Card]) -> list[Card]:
        for card in deck:
            card.update(CardStatus.PILE_PICKUP)
        return deck


    def __str__(self) -> str:
        players = "\n\t".join(str_list(self.players))
        players = "\t" + players
        return f"players:\n{players}\ndiscard pile: {format_list_of_str(self.pile_discard)}\npickup pile: {format_list_of_str(self.pile_pickup)}"

    """
    Return a string representation of the table.
    """
    def stringify_table(self) -> str:
            s = "{\n"
            num_items = 0
            for key, value in self.table.items():
                num_items += 1
                s += '\t' + str(key) + ": "
                s += format_list_of_str(str_list(value))
                s += "\n"
            s += "}"
            return s
    

######################## TESTING ########################

game = Game(2)

rc1 = [ Card(Suit.CLUBS, Rank.FIVE, None), Card(Suit.CLUBS, Rank.SIX, None), Card(Suit.CLUBS, Rank.SEVEN, None) ]
wa2 = [ Card(Suit.CLUBS, Rank.ACE, None), Card(Suit.DIAMONDS, Rank.ACE, None), Card(Suit.SPADES, Rank.ACE, None) ]
rh3 = [ Card(Suit.HEARTS, Rank.TEN, None), Card(Suit.HEARTS, Rank.JACK, None), Card(Suit.HEARTS, Rank.QUEEN, None), Card(Suit.HEARTS, Rank.KING, None), Card(Suit.HEARTS, Rank.ACE, None) ]
rs4 = [ Card(Suit.SPADES, Rank.EIGHT, None), Card(Suit.SPADES, Rank.NINE, None), Card(Suit.SPADES, Rank.TEN, None) ]
rh5 = [ Card(Suit.HEARTS, Rank.SIX, None), Card(Suit.HEARTS, Rank.SEVEN, None), Card(Suit.HEARTS, Rank.EIGHT, None) ]
w36 = [ Card(Suit.DIAMONDS, Rank.THREE, None), Card(Suit.SPADES, Rank.THREE, None), Card(Suit.HEARTS, Rank.THREE, None) ]

table = { "RC1": rc1, "WA2": wa2, "RH3": rh3, "RS4": rs4, "RH5": rh5, "W36": w36 }
game.table = table
print("table = " + game.stringify_table())
"""
table = {
    RC1: [5C, 6C, 7C],
    WA2: [AC, AD, AS],
    RH3: [10H, JH, QH, KH, AH],
    RS4: [8S, 9S, 10S],
    RH5: [6H, 7H, 8H],
    W36: [3D, 3S, 3H]
}
"""

test_cards = [ Card(Suit.HEARTS, Rank.FIVE, None), Card(Suit.HEARTS, Rank.FOUR, None) ]
print( f"{format_list_of_str(str_list(test_cards))} can be played: {game.legal_play(test_cards)}" )

