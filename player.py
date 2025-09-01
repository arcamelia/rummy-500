from card import Card, CardStatus
from utils import str_list

class Player:
    def __init__(self, id):
        self.__id: int = id
        self.__hand: list[Card] = []
        self.__played_cards: list[Card]     # for score tallying purposes only, unsorted
        # todo: later self.__played_cards might need to be a dict (FE purposes)
    
    """
    Play given cards from hand. This will remove them from this player's hand and 
    add them to this player's played cards.
    """
    def play_cards(self, cards: list[Card]) -> None:
        # todo: check if cards can be played
        # todo: remove from self.__hand
        # todo: add to self.__played_cards
        return

    """
    Add given card to this player's hand in sorted order.
    """
    def add_to_hand(self, card: Card) -> None:
        card.update(CardStatus.HAND, self.__id)
        self.__hand.append(card)
        self.sort_hand()
    
    """
    Remove given card from this player's hand and mark it as in either PILE_DISCARD 
    or TABLE status.
    """
    def rmv_from_hand(self, card: Card, next_status: CardStatus) -> None:
        if next_status not in (CardStatus.PILE_DISCARD, CardStatus.TABLE):
            # todo: throw error
            print("A card cannot change from a hand to pickup pile or hand")
        card.update(next_status, None)
        self.__hand.remove(card)  # idk if __eq__ needs to be overriden in Card
    
    """
    Sort this player's hand of cards.
    """
    def sort_hand(self) -> None:
        self.__hand = Card.sort_by_suit_and_rank(self.__hand)

    # def move_card_to_index(self, card: Card, idx: int):
    #     pass

    def get_id(self) -> int:
        return self.__id
    
    def get_hand(self) -> list[Card]:
        return self.__hand
    
    def get_played_cards(self) -> list[Card]:
        return self.__played_cards
    
    def __str__(self) -> str:
        return f"player {self.__id}: {', '.join(str_list(self.__hand))}"

