from card import Card, CardStatus
from utils import str_list

class Player:
    def __init__(self, id):
        self.__id: int = id
        self.__hand: list[Card] = []
        self.__played_cards: list[Card]     # for score tallying purposes only, unsorted
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
        if next_status not in (CardStatus.PILE_DISCARD, CardStatus.TABLE):
            # todo: throw error
            print("A card cannot change from a hand to pickup pile or hand")
        card.update(next_status, None)
        self.__hand.remove(card)  # idk if __eq__ needs to be overriden in Card

    def play_cards(self, cards: list[Card]) -> None:
        """
        Play given cards out of this player's hand. Only handles player functionality 
        (doesn't record cards on the table in the `Game`).
        """
        for c in cards:
            c.update(CardStatus.TABLE)
            self.__played_cards.append(c)
    
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
    
    def get_hand(self) -> list[Card]:
        """
        Getter for private `__hand` member.
        """
        return self.__hand
    
    def get_played_cards(self) -> list[Card]:
        """
        Getter for private `__played_cards` member.
        """
        return self.__played_cards
    
    def __str__(self) -> str:
        """
        Override of `str` method for `Player` class.
        """
        return f"player {self.__id}: {', '.join(str_list(self.__hand))}"

