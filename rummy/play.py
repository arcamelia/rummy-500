from enum import Enum
from typing import List
from .card import Card, Rank
from .errors.exceptions import IllegalMoveError

class PlayType(Enum):
    RUN = "R"
    WRECK = "W"

class Play:
    """
    A Play represents a collection of Cards placed on the shared table as a single
    scored play (either a run 'R' or a wreck/set 'W'). Fields:

    The canonical serialized representation used by `Game.to_dict()` is a
    list of plays (each returned by `Play.to_dict()`), e.g.:
        {
          'plays': [
            {'id': 1, 'type': 'R', 'key': 'H', 'cards': [ ... ]},
            {'id': 2, 'type': 'W', 'key': '3', 'cards': [ ... ]}
          ]
        }
    """
    id: int # unique identifier for this Play within the Game
    type: PlayType
    key: str # metadata used to identify what the play groups by (suit for RUN, rank for WRECK)
    cards: List[Card] # the cards that form the play (ordered), must be >= 3 elts

    def __init__(self, id: int, type: 'PlayType', key: str, cards: List[Card], validate: bool = True):
            self._id = id
            self._type = type
            self._key = key
            # `validate` controls whether to enforce the invariant that a newly-created
            # play must contain at least 3 cards. In normal runtime codepaths (e.g.
            # `Game._play_cards`) this should remain `True` so that illegal plays are
            # rejected immediately. However when reconstructing a `Game` from a
            # serialized snapshot we sometimes need to instantiate `Play` objects for
            # intermediate or historical states that may be incomplete (for example,
            # tests or import tools may craft plays with < 3 cards). Passing
            # `validate=False` during deserialization lets the loader rebuild the
            # object graph first and then run holistic validation (see
            # `Game.from_dict` / `Game.validate`) once all pieces are present.
            if validate and len(cards) < 3:
                raise IllegalMoveError("A new play must contain at least 3 cards")
            self._cards = Card.sort_by_suit_and_rank(cards)

    def merge(self, cards: List[Card]) -> None:
        """
        Merge given cards into this play, if it is allowed. Throws IllegalMoveError if cards cannot be added 
        to this play.
        """
        if self.is_legal_merge(cards):
            self.cards = Card.sort_by_suit_and_rank(self.cards + cards)
        else:
            raise IllegalMoveError(f"Cannot add cards {cards} to play {self}")

    def is_legal_merge(self, new_cards: List[Card]) -> bool:
            """
            Return `True` if `new_cards` can be legally merged into this play.
            """
            if len(new_cards) < 1: return True

            if self.type == PlayType.WRECK:
                # there can't be more than 4 of a kind & this play should already contain 3
                return len(self.cards) < 4 and self.key == str(new_cards[0].rank)

            # play is a RUN
            for c in new_cards:
                if str(c.suit) != self.key: return False

            high_ace = Play._high_ace(self._cards) or Play._high_ace(new_cards) or Play._high_ace(self._cards + new_cards)
            amalgamated_cards = Card.sort_by_suit_and_rank(self.cards + new_cards, high_ace)
            counter = amalgamated_cards[0].rank_value

            for c in amalgamated_cards:
                if c.rank_value != counter:
                    if counter == 14 and c.rank == Rank.ACE:
                        continue
                    else:
                        return False
                counter += 1

            return True

    @staticmethod
    def _high_ace(cards: list[Card]) -> bool:
            """
            Return `True` if there is an ace in the list of cards that should be represented 
            as a high card (a rank value of 14 instead of the default 1).
    
            - If the list contains an ace and nothing else, `False` will be returned.
            - If the list contains all 13 cards from the suit, `False` will be returned.
    
            **CONSTRAINT**: This method should only be called on a list of cards of the same 
            suit. The method will not validate this constraint is upheld.
            """
            if len(cards) == 13 or len(cards) == 1:
                return False
            ranks = { c.rank for c in cards }
            return Rank.ACE in ranks and Rank.KING in ranks
      
    @property
    def id(self) -> int:
        return self._id

    @property
    def type(self) -> PlayType:
        return self._type

    @property
    def key(self) -> str:
        return self._key

    @property
    def cards(self) -> List[Card]:
        return self._cards

    def __str__(self) -> str:
        # <type><key><id> e.g. RH1, W32, etc.
        return str(self.type.value) + self.key + str(self.id)

    def to_dict(self) -> dict:
                """
                Serialize this Play to a plain dict suitable for inclusion in `Game.to_dict()`.

                Format:
                    - `play_id`: integer id of the Play (`Play.id`)
                    - `type`: one-character play type (`'R'` or `'W'`)
                    - `key`: play grouping key (suit for runs, rank for wrecks)
                    - `cards`: list of card dicts as produced by `Card.to_dict()`
                """
                return {'play_id': self.id, 'type': self.type.value, 'key': self.key, 'cards': [c.to_dict() for c in self.cards]}
