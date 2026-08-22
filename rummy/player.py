from .card import Card, CardStatus
from .utils import str_list
from .errors.exceptions import DeserializationError


class Player:
    def __init__(self, id):
        self._id = id
        self._hand = []
        self._played_cards = []

    def add_to_hand(self, card: Card) -> None:
        """
        Add given card to this player's hand in sorted order.
        """
        card.update(CardStatus.HAND, self._id)
        self._hand.append(card)
        self.sort_hand()

    def rmv_from_hand(self, card: Card, next_status: CardStatus) -> None:
        """
        Remove given card from this player's hand and mark it as in either PILE_DISCARD 
        or TABLE status.
        """
        if next_status == CardStatus.TABLE:
            next_pid = self._id
            self._played_cards.append(card)
        elif next_status == CardStatus.PILE_DISCARD:
            next_pid = None
        else:
            raise ValueError("Error removing card from hand: invalid status")
        card.update(next_status, next_pid)
        self._hand.remove(card)

    def move_cards_to_played(self, cards: list[Card]) -> None:
        """
        Play given cards out of this player's hand. Only handles player functionality 
        (doesn't record cards on the table in the `Game`).
        """
        for c in cards:
            self.rmv_from_hand(c, CardStatus.TABLE)

    def sort_hand(self) -> None:
        """
        Sort this player's hand of cards.
        """
        self._hand = Card.sort_by_suit_and_rank(self._hand)

    @property
    def id(self) -> int:
        return self._id

    @property
    def hand(self) -> tuple[Card]:
        return tuple(self._hand)

    @property
    def played_cards(self) -> tuple[Card]:
        return tuple(self._played_cards)

    def __str__(self) -> str:
        return f"player {self._id}: {', '.join(str_list(self._hand))}"

    def to_dict(self) -> dict:
        return {
            'player_id': self._id,
            'hand': [c.to_dict() for c in self._hand],
            'played_cards': [c.to_dict() for c in self._played_cards]
        }

    @staticmethod
    def from_dict(d: dict) -> 'Player':
        if not isinstance(d, dict):
            raise DeserializationError("Player.from_dict expects a dict")
        pid = d.get('player_id')
        if not isinstance(pid, int):
            raise DeserializationError("Player.from_dict: player_id must be an int")
        p = Player(pid)
        hand_list = d.get('hand', [])
        if not isinstance(hand_list, list):
            raise DeserializationError("Player.from_dict: 'hand' must be a list")
        for cd in hand_list:
            card = Card.from_dict(cd)
            p.add_to_hand(card)
        played_list = d.get('played_cards', [])
        if not isinstance(played_list, list):
            raise DeserializationError("Player.from_dict: 'played_cards' must be a list")
        for cd in played_list:
            card = Card.from_dict(cd)
            card.update(CardStatus.TABLE, p.id)
            p._played_cards.append(card)
        return p
