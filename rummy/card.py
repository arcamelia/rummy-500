from enum import Enum
import uuid
from .errors.exceptions import DeserializationError

class Card:
    """
    Represents a card during a game of Rummy 500.
    """
    ACE_HIGH = False

    def __init__(self, suit: 'Suit', rank: 'Rank', status: 'CardStatus', player: int = None):
        self._suit = suit
        self._rank = rank
        self._status = status
        self._player = player
        self._id = uuid.uuid4().hex

        if player is None and (status == CardStatus.HAND or status == CardStatus.TABLE):
            raise ValueError("player cannot be None when status is HAND or TABLE")

        if player is not None and (status == CardStatus.PILE_PICKUP or status == CardStatus.PILE_DISCARD):
            raise ValueError("player must be None when status is PILE_PICKUP or PILE_DISCARD")

    # TODO: review change_status and update methods - when are they are needed?
    def change_status(self, new_status: 'CardStatus') -> None:
        """
        Change the current card status to a new status, if it is allowed.
        """
        if not CardStatus.is_allowed_status_move(self._status, new_status):
            raise ValueError("invalid status transition")
        self._status = new_status

    def update(self, new_status: 'CardStatus', new_pid: int = None) -> None:
        """
        TODO: `update` docstring
        """
        self._status = new_status
        if new_status == CardStatus.PILE_PICKUP or new_status == CardStatus.PILE_DISCARD:
            self._player = None
        elif new_pid is None:
            raise ValueError("player cannot be None when status is HAND or TABLE")
        else:
            self._player = new_pid

    @staticmethod
    def _sort_key(card: 'Card', ace_high: bool) -> tuple[int,int]:
        """
        Key function for sorting cards by suit and then by rank
        """
        if ace_high and card.rank == Rank.ACE:
            rank_value = 14
        else:
            rank_value = card.rank_value
        return (card.suit_value, rank_value)

    @staticmethod
    def sort_by_suit_and_rank(cards: list['Card'], ace_high=False) -> list['Card']:
        """
        Sort a list of cards by suit and then by rank.
        \nOrder of suits: C, D, S, H
        \nOrder of ranks: A, 2, 3, ..., J, Q, K (or A high if specified)
        """
        return sorted(cards, key=lambda card: Card._sort_key(card, ace_high))

    @staticmethod
    def map_to_ranks(cards: list['Card']) -> list[int]:
        """
        Convert a list of cards into a list of those cards' ranks.
        """
        return list(map(Card.get_rank_value, cards))

    @staticmethod
    def map_to_suits(cards: list['Card']) -> list[int]:
        """
        Convert a list of cards into a list of those cards' suits.
        """
        return list(map(Card.get_suit_value, cards))

    @staticmethod
    def contains_ace(cards: list['Card']) -> bool:
        """
        Return true if given list of cards contains an ace.
        """
        ranks = Card.map_to_ranks(cards)
        return Rank.ACE.value in ranks

    @staticmethod
    def same_suit(c1: 'Card', c2: 'Card') -> bool:
        """
        Return true if two cards are the same suit.
        """
        return c1.suit == c2.suit

    @staticmethod
    def consecutive_rank(c1: 'Card', c2: 'Card') -> bool:
        """
        Return true if two cards have consecutive rank.
        """
        r1 = c1.rank_value
        r2 = c2.rank_value
        return abs(r1-r2) == 1 or abs(r1-r2) == 12

    @property
    def suit(self) -> 'Suit':
        return self._suit

    @property
    def suit_value(self) -> int:
        return self._suit.value

    @property
    def rank(self) -> 'Rank':
        return self._rank

    @property
    def rank_value(self) -> int:
        return self._rank.value

    @property
    def status(self) -> 'CardStatus':
        return self._status

    @property
    def player(self) -> int:
        return self._player

    @property
    def id(self) -> str:
        return self._id

    def __str__(self) -> str:
        return str(self.rank) + str(self.suit)

    def __repr__(self) -> str:
        return f"Card({self.suit},{self.rank},{self.status},{self.player},{self.id})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def to_dict(self) -> dict:
        return {
            'suit': self.suit.name if self.suit is not None else None,
            'rank': self.rank.name if self.rank is not None else None,
            'status': self.status.name if self.status is not None else None,
            'player_id': self.player,
            'card_id': self.id
        }

    @staticmethod
    def from_dict(d: dict) -> 'Card':
        if not isinstance(d, dict):
            raise DeserializationError("Card.from_dict expects a dict")

        suit_name = d.get('suit')
        rank_name = d.get('rank')
        status_name = d.get('status')
        player = d.get('player_id')
        cid = d.get('card_id')

        try:
            suit = Suit[suit_name] if suit_name is not None else None
        except Exception:
            raise DeserializationError(f"Invalid suit value in Card.from_dict: {suit_name}")

        try:
            rank = Rank[rank_name] if rank_name is not None else None
        except Exception:
            raise DeserializationError(f"Invalid rank value in Card.from_dict: {rank_name}")

        try:
            status = CardStatus[status_name] if status_name is not None else None
        except Exception:
            raise DeserializationError(f"Invalid status value in Card.from_dict: {status_name}")

        if player is not None and not isinstance(player, int):
            raise DeserializationError("Card.from_dict: player_id must be an int or None")

        if cid is None or not isinstance(cid, str):
            raise DeserializationError("Card.from_dict: card_id is required and must be a string")

        card = Card(suit=suit, rank=rank, status=status, player=player)
        card._set_id_for_deserialization(cid)
        return card

    def _set_id_for_deserialization(self, cid: str) -> None:
        if cid is None or not isinstance(cid, str):
            raise DeserializationError("card id must be a non-empty string for deserialization")
        self._id = cid


class Suit(Enum):
    CLUBS = 1
    DIAMONDS = 2
    SPADES = 3
    HEARTS = 4

    def __str__(self) -> str:
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
        if stat_1 == CardStatus.PILE_PICKUP:
            return stat_2 in {CardStatus.HAND, CardStatus.PILE_PICKUP}
        elif stat_1 == CardStatus.PILE_DISCARD:
            return stat_2 in {CardStatus.HAND, CardStatus.PILE_DISCARD}
        elif stat_1 == CardStatus.HAND:
            return stat_2 in {CardStatus.PILE_DISCARD, CardStatus.TABLE, CardStatus.HAND}
        else:
            return stat_2 == CardStatus.TABLE

    def __str__(self) -> str:
        return super().__str__()[11:]
