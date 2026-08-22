from card import Card, CardStatus
from utils import str_list
from errors.exceptions import DeserializationError

class Player:
    def __init__(self, id):
        self.__id: int = id
        self.__hand: list[Card] = []
        self.__played_cards: list[Card] = []    # for score tallying purposes only, unsorted
        # todo: later self.__played_cards might need to be a dict (FE purposes)

    def add_to_hand(self, card: Card) -> None:
        """
        Add given card to this player's hand in sorted order.
        """
        card.update(CardStatus.HAND, self.__id)
        self.__hand.append(card)
        self.sort_hand()
    
    def rmv_from_hand(self, card: Card, next_status: CardStatus) -> None:
        """
        Remove given card from this player's hand and mark it as in either PILE_DISCARD 
        or TABLE status.
        """
        if next_status == CardStatus.TABLE:
            next_pid = self.__id
            self.__played_cards.append(card)
        elif next_status == CardStatus.PILE_DISCARD:
            next_pid = None
        else:
            raise ValueError("Error removing card from hand: card cannot change from a HAND to PILE_PICKUP or HAND status")
            
        card.update(next_status, next_pid)
        self.__hand.remove(card)  # idk if __eq__ needs to be overriden in Card

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
        
        self.__hand = Card.sort_by_suit_and_rank(self.__hand)

    # def move_card_to_index(self, card: Card, idx: int):
    #     pass

    def get_id(self) -> int:
        """
        Getter for private `__id` member.
        """
        return self.__id
    
    def get_hand(self) -> tuple[Card]:
        """
        Getter for private `__hand` member.
        """
        # return an immutable snapshot to avoid external mutation
        return tuple(self.__hand)
    
    def get_played_cards(self) -> tuple[Card]:
        """
        Getter for private `__played_cards` member.
        """
        return tuple(self.__played_cards)
    
    def __str__(self) -> str:
        """
        Override of `str` method for `Player` class.
        """
        return f"player {self.__id}: {', '.join(str_list(self.__hand))}"

    def to_dict(self) -> dict:
        """Serialize the Player to a dict, including hand and played cards."""
        return {
            'player_id': self.__id,
            'hand': [c.to_dict() for c in self.__hand],
            'played_cards': [c.to_dict() for c in self.__played_cards]
        }

    @staticmethod
    def from_dict(d: dict) -> 'Player':
        """Reconstruct a Player from a dict produced by `to_dict`.

        This will create a new `Player` and populate its hand and played cards.
        """
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
            # assign to player's hand (mutator enforces status/player and sorting)
            p.add_to_hand(card)

        played_list = d.get('played_cards', [])
        if not isinstance(played_list, list):
            raise DeserializationError("Player.from_dict: 'played_cards' must be a list")
        for cd in played_list:
            card = Card.from_dict(cd)
            # normalize status/player to TABLE for played cards
            card.update(CardStatus.TABLE, p.get_id())
            p._Player__played_cards.append(card)

        return p

