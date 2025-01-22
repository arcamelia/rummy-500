from enum import Enum

class Card:
    """
    Represents a card during a game of Rummy 500.
    """

    ACE_HIGH = False

    """
    Initialize a new card for a game of Rummy 500. 
    """
    def __init__(self, suit: 'Suit', rank: 'Rank', status: 'CardStatus', player: int = None):
        self.__suit: Suit = suit
        self.__rank: Rank = rank
        self.__status: CardStatus = status
        self.__player: int = player

        if player is None and (status == CardStatus.HAND or status == CardStatus.TABLE):
            # todo: throw an error
            print("player cannot be None when status is HAND or TABLE")

        if player is not None and (status == CardStatus.PICKUP_PILE or status == CardStatus.DISCARD_PILE):
            # todo: throw an error
            print("player must be None when status is PICKUP_PILE or DISCARD_PILE")

    """
    Change the current card status to a new status, if it is allowed.
    """
    def change_status(self, new_status: 'CardStatus') -> None:
        if not CardStatus.is_allowed_status_move(self.__status, new_status):
            # todo: throw error
            print(f"the new status ${new_status} is not an allowed change from current status ${self.__status}")
        else:
            self.__status = new_status

    """
    todo: docstring
    """
    def set_status_and_player(self, new_status: 'CardStatus', new_pid: int = None) -> None:
        self.__status = new_status

        if new_status == CardStatus.PICKUP_PILE or new_status == CardStatus.DISCARD_PILE:
            self.__player = None

        elif new_pid == None:
            # todo: throw error
            print("player cannot be None when status is HAND or TABLE")
    
        else:
            self.__player = new_pid
            # todo: check if player is valid


        # todo: configure defaultly setting the player at the same time

    """
    Key function for sorting cards by suit and then by rank
    """
    @staticmethod
    def __sort_key(card: 'Card', ace_high: bool) -> tuple[int,int]:
        if ace_high and card.get_rank() == Rank.ACE:
            rank_value = 14
        else: rank_value = card.get_rank_value()
        return (card.get_suit_value(), rank_value)
    
    """
    Sort a list of cards by suit and then by rank.
    Order of suits: C, D, S, H.
    Order of ranks: A, 2, 3, ..., J, Q, K (or A high if specified).
    """
    @staticmethod
    def sort_by_suit_and_rank(cards: list['Card'], ace_high=False) -> list['Card']:
        return sorted(cards, key=lambda card: Card.__sort_key(card, ace_high))

    def get_suit(self) -> 'Suit':
        return self.__suit
    
    def get_suit_value(self) -> int:
        return self.__suit.value
    
    def get_rank(self) -> 'Rank':
        return self.__rank
    
    def get_rank_value(self) -> int:
        return self.__rank.value
    
    def get_status(self) -> 'CardStatus':
        return self.__status
    
    def get_player(self) -> int:
        return self.__player
    
    def __str__(self) -> str:
        return str(self.__rank) + str(self.__suit)
    

class Suit(Enum):
    CLUBS = 1
    DIAMONDS = 2
    SPADES = 3
    HEARTS = 4

    def __str__(self) -> str:
        if self == Suit.CLUBS: return "C"
        elif self == Suit.DIAMONDS: return "D"
        elif self == Suit.SPADES: return "S"
        else: return "H"

class Rank(Enum):
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

    def __str__(self) -> str:
        if self == Rank.ACE: return "A"
        elif self == Rank.JACK: return "J"
        elif self == Rank.QUEEN: return "Q"
        elif self == Rank.KING: return "K"
        else: return str(self.value)

class CardStatus(Enum):
    """
    There are 4 possible statuses for a card during game play. Every card must 
    be in exactly one of these statuses. They are as follows:

        PICKUP_PILE: in the pile of pickup cards (position important)
        DISCARD_PILE: in the discard pile (position important)
        HAND: in one of the players' hands (player important)
        TABLE: someone has played the card on the table (player important)

    Cards either start in PICKUP_PILE or HAND status. The possible
    moves between statuses are:

        PICKUP_PILE -> HAND, PICKUP_PILE
        DISCARD_PILE -> HAND, DISCARD_PILE
        HAND -> DISCARD_PILE, TABLE, HAND
        TABLE -> TABLE
    """
    PICKUP_PILE = 1
    DISCARD_PILE = 2
    HAND = 3
    TABLE = 4

    @staticmethod
    def is_allowed_status_move(stat_1: 'CardStatus', stat_2: 'CardStatus') -> bool:
        if stat_1 == CardStatus.PICKUP_PILE:
            return stat_2 == (CardStatus.HAND or CardStatus.PICKUP_PILE)
        elif stat_1 == CardStatus.DISCARD_PILE:
            return stat_2 == (CardStatus.HAND or CardStatus.DISCARD_PILE)
        elif stat_1 == CardStatus.HAND:
            return stat_2 == (CardStatus.DISCARD_PILE or CardStatus.TABLE or CardStatus.HAND)
        else:
            return stat_2 == CardStatus.TABLE

    def __str__(self) -> str:
        return super().__str__()[11:]

