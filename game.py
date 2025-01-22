from card import Card, Rank, Suit, CardStatus
from player import Player
from utils import str_list, format_list_of_str
import random

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

    def __init__(self, players: set[Player]):
        if len(players) > MAX_PLAYERS:
            # todo: throw error
            print(f"Maximum number of players is {MAX_PLAYERS}")
            return
        self.players: set[Player] = players
        deck = self.initialize_deck()
        self.deal_cards(deck)
        self.table: dict[str,list[Card]] = {}

    """
    e.g. table = {
        RC1: [3C, 4C, 5C],
        WA2: [AC, AD, AS],
        RH3: [10H, JH, QH, KH, AH],
        RS4: [8S, 9S, 10S],
        RH5: [6H, 7H, 8H],
        WJ6: [3D, 3S, 3H]
    }
    key formation:
      * prefix character of R (run) or W (wreck)
      * for a R, the second character indicates what suit it is
      * for a W, the second character indicates what rank it is
      * the integer at the end indicates the order of play, and is unique to that sequence

    when a player plays the 5H, it will be added to the front of RH5.
    however, when the 9H is played, it could be placed either at the front of RH3 or the 
    end of RH5. we will resolve this by combining the two lists together as RH3, and 
    removing RH5 from the map (we arbitrarily choose to keep the run that was played first).
    
    (Note we also keep track of which cards a specific player has played via a dict in the 
    table variable in the Player class.)
    """


    """
    Run a game of Rummy 500, then return the players' scores in a dict.
    """
    def run(self) -> dict[int,int]:
        while True:
            for p in self.players:
                p.run_turn()
                if not p.get_hand():
                    print("A player has gotten rid of all their cards")
                    return self.tally_scores()

    """
    Return true if there is a rummy currently on the table.
    """
    def check_rummy(self) -> bool:
        """
        table = {
            RC1: [3C, 4C, 5C],
            WA2: [AC, AD, AS],
            RH3: [10H, JH, QH, KH, AH],
            RS4: [8S, 9S, 10S],
            RH5: [6H, 7H, 8H],
            WJ6: [3D, 3S, 3H]
        }
        player 1 = {
            RC: [3C, 4C, 5C],
            RH: [10H, AH],
            W3: [3D, 3S, 3H],
            WA: [AC, AD, AS]
        }
        player 2 = {
            RH: [JH, QH, KH],
            RS: [8S, 9S, 10S],
            RH: [6H, 7H, 8H]
        }
        """
        # todo
        # self.__check_pile_rummy()
        # self.__check_table_pile_rummy()
        return
    
    
    """
    Count up each player's points for the current round and return them via a dict.
    """
    def tally_scores(self) -> dict[int,int]:
        scores = {}
        for p in self.players:
            cards_played = p.get_table()
            score = 0
            for key, cards in cards_played:
                score += self.tally_cards(cards)
            scores[p.get_id()] = score

    """
    Return the total point value of all the cards in given list.
    """
    def tally_cards(self, cards: list[Card]) -> int:
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
    Deal out cards for a new game of Rummy 500.
    After this method returns, every player should have 7 cards in their hand, the 
    pickup pile should have 1 card, and the discard pile should have all the rest.
    """
    def deal_cards(self, deck: list[Card]) -> None:
        self.__deal_to_players(deck)
        self.__deal_pickup_discard(deck)

    def __deal_pickup_discard(self, deck: list[Card]) -> None:
        self.pickup_pile = []
        self.pickup_pile.append(deck.pop().set_status_and_player(CardStatus.PICKUP_PILE, None))
        for card in deck:
            card.set_status_and_player(CardStatus.DISCARD_PILE, None)
        self.discard_pile = deck

    def __deal_to_players(self, deck: list[Card]) -> None:
        for p in self.players:
            for _ in range(NUM_CARDS_PER_PLAYER):
                card = deck.pop()
                card.set_status_and_player(CardStatus.HAND, p.get_id())
                p.add_to_hand(card)

    def __str__(self) -> str:
        players = "\n\t".join(str_list(self.players))
        players = "\t" + players
        return f"players:\n{players}\ndiscard pile: {format_list_of_str(self.discard_pile)}\npickup pile: {format_list_of_str(self.pickup_pile)}"


# trial game run
players = set([Player(1), Player(2)])
game = Game(players)
# print(game)

# ace = Card(Suit.CLUBS, Rank.ACE, CardStatus.TABLE)
# jack = Card(Suit.CLUBS, Rank.JACK, CardStatus.TABLE)
# two = Card(Suit.CLUBS, Rank.TWO, CardStatus.TABLE)
# game.tally_cards([two, jack, ace])

