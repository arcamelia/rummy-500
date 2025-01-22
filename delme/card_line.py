from enum import Enum
# from utils.linked_list import LinkedList
from card import Card, Rank

class CardLine:
    """
    Represents a collection of cards that have been played on the table, based on
    their play type (either run or run-wreck).
    """
    
    def __init__(self, type, cards, ace_high=False):
        if cards is None or len(cards) < 3:
            # todo: error throwing / handling ?
            print("a CardLine must be initialized with 3 or more cards")
        
        self.__type: PlayType = type
        self.__ace_high = ace_high
        self.__cards = sorted(cards, key=self.__card_sort_key)
        # note: a linked list wouldn't provide much increase in efficiency because
        #       at most the CardLine would have 13 cards in it to sort through

    def set_ace_high(self):
        self.ace_high = True

    def add_cards(self, cards):
        """
        Add 1 or more cards (contained within a list) to the current line.
        Handles logic of deciding where in the line the cards get added.
        """
        # todo: error checking for if cards can be added

        self.__cards.append(cards)
        self.__sort()

    def __sort(self):
        self.__cards = sorted(self.__cards, key=self.__card_sort_key)

    def __card_sort_key(self, card: Card):
        """
        Key function for sorting cards in the line, respecting Ace's high/low status.
        """
        if self.__ace_high and card.get_rank() == Rank.ACE:
            rank_value = 14
        else: rank_value = card.get_rank_value()

        return (card.get_suit_value(), rank_value)


class PlayType(Enum):
    """
    Represents the type of play for a line of cards.
    """
    RUN = 1     # Sequential cards of the same suit
    WRECK = 2   # Cards of the same rank across different suits

