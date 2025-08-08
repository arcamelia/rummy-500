from card import Card, CardStatus
from utils import str_list

class Player:
    def __init__(self, id):
        self.__id: int = id
        self.__hand: list[Card] = []
        self.__table: dict[Card] = {}

    """
    Execute a turn for this player. Involves pickup, play, and discard phases.
    """
    def run_turn(self) -> None:
        # todo
        # 1. pickup from either pickup or discard pile
        # 2. play any cards from hand
        # 3. discard a card from hand
        return
    
    """
    Return true if this player can pick up a card from either the discard or pickup piles.
    """
    def can_pick_up(self) -> bool:
        # todo
        return False

    """
    Play given cards from hand. This will remove them from this player's hand and 
    add them to this player's table.
    """
    def play_cards(self, cards: list[Card]) -> None:
        # todo: check if cards can be played
        # todo: remove from self.__hand
        # todo: add to self.__table
        return

    def discard(self, card: Card) -> None:
        # todo
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
    
    def get_table(self) -> dict[Card]:
        return self.__table
    
    def __str__(self) -> str:
        return f"player {self.__id}: {', '.join(str_list(self.__hand))}"

