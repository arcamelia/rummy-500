from enum import Enum

class Card:
    """
    Represents a card during a game of Rummy 500.
    """

    ACE_HIGH = False

    def __init__(self, suit: 'Suit', rank: 'Rank', status: 'CardStatus', player: int = None):
        """
        Initialize a new `Card` for a game of Rummy 500. 
        """

        self.__suit: Suit = suit
        self.__rank: Rank = rank
        self.__status: CardStatus = status
        self.__player: int = player

        if player is None and (status == CardStatus.HAND or status == CardStatus.TABLE):
            raise ValueError("player cannot be None when status is HAND or TABLE")

        if player is not None and (status == CardStatus.PILE_PICKUP or status == CardStatus.PILE_DISCARD):
            raise ValueError("player must be None when status is PILE_PICKUP or PILE_DISCARD")

    def change_status(self, new_status: 'CardStatus') -> None:
        """
        Change the current card status to a new status, if it is allowed.
        """
        
        if not CardStatus.is_allowed_status_move(self.__status, new_status):
            raise ValueError(f"the new status {new_status} is not an allowed change from current status {self.__status}")
        self.__status = new_status

    def update(self, new_status: 'CardStatus', new_pid: int = None) -> None:
        """
        todo: docstring
        """
        
        self.__status = new_status

        if new_status == CardStatus.PILE_PICKUP or new_status == CardStatus.PILE_DISCARD:
            self.__player = None
        elif new_pid is None:
            raise ValueError("player cannot be None when status is HAND or TABLE")
        else:
            self.__player = new_pid
            # todo: check if player is valid


        # todo: configure defaultly setting the player at the same time

    @staticmethod
    def __sort_key(card: 'Card', ace_high: bool) -> tuple[int,int]:
        """
        Key function for sorting cards by suit and then by rank
        """
        if ace_high and card.get_rank() == Rank.ACE:
            rank_value = 14
        else: rank_value = card.get_rank_value()
        return (card.get_suit_value(), rank_value)
    
    @staticmethod
    def sort_by_suit_and_rank(cards: list['Card'], ace_high=False) -> list['Card']:
        """
        Sort a list of cards by suit and then by rank.
        \nOrder of suits: C, D, S, H
        \nOrder of ranks: A, 2, 3, ..., J, Q, K (or A high if specified)
        """
        return sorted(cards, key=lambda card: Card.__sort_key(card, ace_high))

    @staticmethod
    def map_to_rank(cards: list['Card']) -> list[int]:
        """
        Convert a list of cards into a list of those cards' ranks.
        """
        return list(map(Card.get_rank_value, cards))
    
    @staticmethod
    def map_to_suit(cards: list['Card']) -> list[int]:
        """
        Convert a list of cards into a list of those cards' suits.
        """
        return list(map(Card.get_suit_value, cards))

    @staticmethod
    def contains_ace(cards: list['Card']) -> bool:
        """
        Return true if given list of cards contains an ace.
        """
        ranks = Card.map_to_rank(cards)
        return Rank.ACE.value in ranks
    
    @staticmethod
    def same_suit(c1: 'Card', c2: 'Card') -> bool:
        """
        Return true if two cards are the same suit.
        """
        return c1.get_suit() == c2.get_suit()
    
    @staticmethod
    def consecutive_rank(c1: 'Card', c2: 'Card') -> bool:
        """
        Return true if two cards have consecutive rank.
        """
        r1 = c1.get_rank_value()
        r2 = c2.get_rank_value()
        # a king and ace are considered consecutive but have a difference in rank value of 12
        return abs(r1-r2) == 1 or abs(r1-r2) == 12
    
    def get_suit(self) -> 'Suit':
        """
        Getter for private `__suit` member.
        """
        return self.__suit
    
    def get_suit_value(self) -> int:
        """
        Getter for the `int` value of the private `__suit` member.
        """
        return self.__suit.value
    
    def get_rank(self) -> 'Rank':
        """
        Getter for private `__rank` member.
        """
        return self.__rank
    
    def get_rank_value(self) -> int:
        """
        Getter for the `int` value of the private `__rank` member.
        """
        return self.__rank.value
    
    def get_status(self) -> 'CardStatus':
        """
        Getter for private `__status` member.
        """
        return self.__status
    
    def get_player(self) -> int:
        """
        Getter for private `__player` member.
        """
        return self.__player
    
    def __str__(self) -> str:
        """
        Override of `str` method for `Card` class.
        """
        return str(self.__rank) + str(self.__suit)
    
    @staticmethod
    def str_to_card(str: str) -> 'Card':
        """
        Convert the string representation of a card into a `Card` (with no `status`).
        """
        rank = Rank.str_to_rank(str[0])
        suit = Suit.str_to_suit(str[1])
        return Card(suit, rank, None)


class Suit(Enum):
    CLUBS = 1
    DIAMONDS = 2
    SPADES = 3
    HEARTS = 4

    def __str__(self) -> str:
        """
        Override of `str` method for `Suit` class.
        """

        match self:
            case Suit.CLUBS:
                return "C"
            case Suit.DIAMONDS:
                return "D"
            case Suit.SPADES:
                return "S"
            case _:
                return "H"

    @staticmethod
    def str_to_suit(str: str) -> 'Suit':
        """
        Convert the string representation of a suit into a `Suit`.
        """

        match str:
            case "C":
                return Suit.CLUBS
            case "D":
                return Suit.DIAMONDS
            case "S":
                return Suit.SPADES
            case "H":
                return Suit.HEARTS
            case _:
                raise ValueError(f"Given string '{str}' is not a valid Suit")

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
        """
        Override of `str` method for `Rank` class.
        """

        match self:
            case Rank.ACE:
                return "A"
            case Rank.JACK:
                return "J"
            case Rank.QUEEN:
                return "Q"
            case Rank.KING:
                return "K"
            case _:
                return str(self.value)

    @staticmethod
    def str_to_rank(str: str) -> 'Rank':
        """
        Convert the string representation of a rank into a `Rank`.
        """
        
        match str:
            case "A":
                return Rank.ACE
            case "J":
                return Rank.JACK
            case "Q":
                return Rank.QUEEN
            case "K":
                return Rank.KING
            case _:
                return Rank(int(str))

class CardStatus(Enum):
    """
    There are 4 possible statuses for a card during game play. Every card must 
    be in exactly one of these statuses. They are as follows:

        PILE_PICKUP: in the pile of pickup cards (position important)
        PILE_DISCARD: in the discard pile (position important)
        HAND: in one of the players' hands (player important)
        TABLE: someone has played the card on the table (player important)

    Cards either start in PILE_PICKUP or HAND status. The possible
    moves between statuses are:

        PILE_PICKUP -> HAND, PILE_PICKUP
        PILE_DISCARD -> HAND, PILE_DISCARD
        HAND -> PILE_DISCARD, TABLE, HAND
        TABLE -> TABLE
    """
    PILE_PICKUP = 1
    PILE_DISCARD = 2
    HAND = 3
    TABLE = 4

    @staticmethod
    def is_allowed_status_move(stat_1: 'CardStatus', stat_2: 'CardStatus') -> bool:
        """
        todo: docstring
        """
        if stat_1 == CardStatus.PILE_PICKUP:
            return stat_2 in {CardStatus.HAND, CardStatus.PILE_PICKUP}
        elif stat_1 == CardStatus.PILE_DISCARD:
            return stat_2 in {CardStatus.HAND, CardStatus.PILE_DISCARD}
        elif stat_1 == CardStatus.HAND:
            return stat_2 in {CardStatus.PILE_DISCARD, CardStatus.TABLE, CardStatus.HAND}
        else:
            return stat_2 == CardStatus.TABLE

    def __str__(self) -> str:
        """
        Convert the string representation of a card status into a `CardStatus`.
        """
        return super().__str__()[11:]
