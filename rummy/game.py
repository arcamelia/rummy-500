from .card import Card, Rank, Suit, CardStatus
from .player import Player
from .utils import str_list, format_list_of_str
import random
import itertools
from typing import overload
from .errors.exceptions import DuplicateIDError, GameStateError, IllegalMoveError
from .play import Play, PlayType

MAX_PLAYERS = 7
NUM_CARDS_PER_PLAYER = 7

CARD_POINT_VALUES = {
    Rank.TWO: 5,
    Rank.THREE: 5,
    Rank.FOUR: 5,
    Rank.FIVE: 5,
    Rank.SIX: 5,
    Rank.SEVEN: 5,
    Rank.EIGHT: 5,
    Rank.NINE: 5,
    Rank.TEN: 10,
    Rank.JACK: 10,
    Rank.QUEEN: 10,
    Rank.KING: 10,
    Rank.ACE: 15
}

class Game:
    """
    Represents a game of Rummy 500.
    """
    players: list[Player]
    pile_pickup: list[Card]
    pile_discard: list[Card]
    play_id_counter: int

    def __init__(self, num_players):
        self.players = []
        self.players = self._initialize_players(num_players)
        deck: list[Card] = self._initialize_deck()
        self._deal_cards(deck, self.players)

        self.pile_discard = self._initialize_pile_discard(deck)
        self.pile_pickup = self._initialize_pile_pickup(deck)
        self.play_id_counter = 0 # used for play.key generation
        
        # plays: key = <play.id>, value = <play>
        self.plays: dict[int, Play] = {}
        # card_loc_dict: key = <card.id>, value = (<play.id>, <index in play.cards>)
        self.card_loc_dict: dict[str, tuple[int,int]] = {}

#################### turn phases ####################

    @overload
    def pickup(self, player: Player) -> Card:
        """
        Phase **pickup** (PICKUP PILE) of a player's turn
        """
        if not self.pile_pickup:
            raise IndexError("Pickup pile is empty")
        card = self.pile_pickup.pop()
        player.add_to_hand(card)
        return card

    @overload
    def pickup(self, player: Player, idx: int) -> Card:
        """
        Phase **pickup** (DISCARD PILE) of a player's turn
        """
        if idx < 0 or idx >= len(self.pile_discard):
            raise IndexError("Discard index out of range")
        chosen_card = self.pile_discard[idx]

        if not self.legal_play_with(player.hand, chosen_card):
            raise ValueError(f"Chosen card {chosen_card} cannot be used immediately")

        add_to_hand = self.pile_discard[idx+1:]
        self.pile_discard = self.pile_discard[:idx]
        for c in add_to_hand:
            player.add_to_hand(c)
        return chosen_card

    def play(self, player: Player, indices: list[int], type_of_play: PlayType, reqd_card: Card | None = None) -> bool:
        """
        Phase **play** of a player's turn
        """
        if not indices:
            chosen_cards = []
        else:
            chosen_cards = [player.hand[i] for i in indices]
        if reqd_card is not None:
            chosen_cards.append(reqd_card)

        return self._try_play(player, chosen_cards, type_of_play)

    def discard(self, player: Player, idx: int) -> Card:
        """
        Phase **discard** of a player's turn
        """
        if idx < 0 or idx >= len(player.hand):
            raise IndexError("Hand index out of range")
        card = player.hand[idx]
        player.rmv_from_hand(card, CardStatus.PILE_DISCARD)
        self.pile_discard.append(card)
        return card

#################### rummy checking logic ####################

    def check_rummy(self, cards: list[Card]) -> bool:
        """
        Return true if the given cards are in the discard pile and are involved in a rummy.
        """
        return {c in self.pile_discard for c in cards} and self.legal_play(cards)

    def legal_play(self, cards: list[Card], type_of_play: PlayType = None) -> bool:
        """
        Return `True` if given list of cards can form a legal play based on the specified type.

        If `type_of_play` does not match the type of play that can be legally formed, the method 
        will return `False` (i.e., responsibility is on the caller to ensure the type of play 
        is classified correctly).
        
        **CONSTRAINT:** Method will only return `True` if all cards in given list encompass a 
        singular play.
        
        For example, if the list of cards looks like `[2H, 2D, 2S, JH, QH, KH]`, the method 
        will return `False`, as these two plays should be made separately (even though the two
        plays are legal on their own).
        """
        # if no type_of_play is specified, check if it's legal as either a run or a wreck
        if not type_of_play: return self.legal_play(cards, PlayType.RUN) or self.legal_play(cards, PlayType.WRECK)

        # type_of_play is specified, proceed as usual
        if len(cards) < 3: return self._legal_play_addon(cards, type_of_play)

        # check WRECK
        ranks = Card.map_to_ranks(cards)
        if all(x == ranks[0] for x in ranks) and type_of_play == PlayType.WRECK: return True

        # check RUN
        if type_of_play != PlayType.RUN: return False
        suits = Card.map_to_suits(cards)
        same_suit = all(x == suits[0] for x in suits)
        consecutive_rank = sorted(ranks) == list(range(min(ranks), max(ranks)+1))

        if Card.contains_ace(cards):
            for i in range(len(ranks)):
                if ranks[i] == 1:
                    ranks[i] = 14
            # check both ace-low and ace-high scenarios
            consecutive_rank_high_ace = sorted(ranks) == list(range(min(ranks), max(ranks)+1))
            consecutive_rank = consecutive_rank or consecutive_rank_high_ace

        return same_suit and consecutive_rank

    def legal_play_with(self, aux: list[Card], required_card: Card) -> bool:
        """
        Return `True` if `required_card` can be legally played in conjunction with 0 or 
        more of the cards contained in `aux` (the auxiliary card list).
        """
        if self.legal_play([required_card]):
            return True
        for num_extra_cards in range(3):
            # TODO: test this
            for subset in itertools.combinations(aux, num_extra_cards):
                candidate_play = [required_card] + list(subset)
                if self.legal_play(candidate_play):
                    return True
        return False

    def _legal_play_addon(self, cards: list[Card], type_of_play: PlayType) -> bool:
        """
        Return true iff all cards in given list can be added on to a singular existing play 
        _and_ is classified under the correct `type_of_play`.
        
        This method should only be called on lists with `len < 3`.
        """
        match len(cards):
            case 1:
                return (
                    self._legal_play_one_card_r(cards[0]) and type_of_play == PlayType.RUN
                ) or (
                    self._legal_play_one_card_w(cards[0]) and type_of_play == PlayType.WRECK
                )
            case 2:
                if type_of_play == PlayType.WRECK: return False
                c1: Card = cards[0]
                c2: Card = cards[1]
                one_card_legal = self._legal_play_one_card_r(c1) or self._legal_play_one_card_r(c2)
                return one_card_legal and Card.same_suit(c1, c2) and Card.consecutive_rank(c1, c2)
            case _:
                return False

    def _legal_play_one_card_r(self, c: Card) -> bool:
        """
        Return true if given card can be played on an existing RUN play.
        """
        for play in self.plays.values():
            if play.type != PlayType.RUN: continue
            if str(c.suit) != play.key: continue

            # found a play of same suit, check if card matches either end of the run
            cards = play.cards
            if not cards: continue
            consecutive_low_no_ace = Card.consecutive_rank(c, cards[0]) and cards[0].rank != Rank.ACE
            consecutive_high_no_ace = Card.consecutive_rank(c, cards[-1]) and cards[-1].rank != Rank.ACE
            if consecutive_low_no_ace or consecutive_high_no_ace: return True

        return False

    def _legal_play_one_card_w(self, card: Card) -> bool:
        """
        Return true if given card can be played on an existing WRECK play.
        """
        for play in self.plays.values():
            if play.type == PlayType.WRECK and play.key == str(card.rank):
                return True
        return False

#################### play phase helpers ####################

    def _try_play(self, player: Player, cards: list[Card], play_type: PlayType) -> bool:
        """
        Return `True` if given cards form a legal play, and are properly added to the table 
        & removed from given player's hand.
        """
        if not self.legal_play(cards, play_type):
            return False
        self._play_cards(player, cards, play_type)
        return True

    def _play_cards(self, player: Player, cards: list[Card], play_type: PlayType) -> None:
        """
        Encompasses all behaviour that occurs when a player moves 1 or more cards 
        from their hand onto the table as points.

        **CONSTRAINT**: cards have already been tested for validity
        """
        key = self._find_play_match(cards, play_type)

        if key is None:
            # start a new play on the table
            p_id = self._generate_play_id()
            p_key = self._generate_play_key(cards, play_type)
            new_play = Play(p_id, play_type, p_key, cards)
            key = self._key_for_plays_dict(new_play)
            self.plays[key] = new_play

        else:
            # update existing play and card_loc_dict
            self.plays[key].cards = Card.sort_by_suit_and_rank(self.plays[key].cards + cards)
        
        # update card_loc_dict
        for idx, c in enumerate(self.plays[key].cards):
            self.card_loc_dict[c.id] = (key, idx)

        self._clean_up_table()
        player.move_cards_to_played(cards)

    def _find_play_match(self, cards: list[Card], type_of_play: PlayType) -> str | None:
        """
        Find a Play in the Game, if one exists, that param cards can be added to. 
        Return the key of matching play if successful, otherwise return `None`.

        Arbitrarily return the first play match found if more than one exists.
        """
        for play in self.plays.values():
            if play.type != type_of_play:
                continue
            if play.is_legal_merge(cards):
                return self._key_for_plays_dict(play)
        return None

    def _clean_up_table(self):
        """
        Merge any runs in `self.plays` that are connected.

        Arbitrarily remove the second play after merging those cards into the first.
        """
        to_remove = []
        play_ids = list(self.plays.keys())
        num_plays = len(play_ids)

        for i in range(num_plays):
            pid1 = play_ids[i]
            p1 = self.plays.get(pid1)
            if not p1 or p1.type == PlayType.WRECK: continue

            for j in range(i+1, num_plays):
                pid2 = play_ids[j]
                p2 = self.plays.get(pid2)
                if not p2 or p2.type == PlayType.WRECK: continue

                if self._try_merge_plays(p1, p2):
                    to_remove.append(pid2)

        for pid in to_remove:
            self.plays.pop(pid, None)

    def _try_merge_plays(self, p1: Play, p2: Play) -> bool:
        """
        Attempt to merge two plays together. Return `True` if they can be / are successfully merged.
        """
        try:
            p1.merge(p2.cards)
        except IllegalMoveError:
            return False

        for idx, card in enumerate(p1.cards):
            self.card_loc_dict[card.id] = (p1.id, idx)
        return True

    def _key_for_plays_dict(self, play: Play) -> str:
        """
        Map a play to its key in `self.plays`.
        """
        return str(play)

    def _generate_play_id(self) -> str:
        """
        Return a unique id for new play to be made.
        """
        self.play_id_counter += 1
        return self.play_id_counter

    def _generate_play_key(self, cards: list[Card], play_type: PlayType) -> str:
            """
            Return the proper key for a play defined by given cards and play type.
            """
            if play_type == PlayType.RUN:
                return str(cards[0].suit)
            else:
                return str(cards[0].rank)

#################### pre-amble ####################

    def _initialize_deck(self) -> list[Card]:
        """
        Initialize and return a new deck of shuffled cards.
        """
        deck: list[Card] = []
        for s in Suit:
            for r in Rank:
                card = Card(suit=s, rank=r, status=None, player=None)
                deck.append(card)
        random.shuffle(deck)
        return deck

    def _deal_cards(self, deck: list[Card], players: list[Player]) -> None:
        """
        Deal out `NUM_CARDS_PER_PLAYER` to the given players.
        """
        for p in players:
            for _ in range(NUM_CARDS_PER_PLAYER):
                card = deck.pop()
                card.update(CardStatus.HAND, p.id)
                p.add_to_hand(card)

    def _initialize_pile_discard(self, deck: list[Card]) -> list[Card]:
        """
        Return a list of cards representing the discard pile.
        """
        c = deck.pop()
        c.update(CardStatus.PILE_DISCARD)
        return [ c, deck.pop(), deck.pop() ]

    def _initialize_pile_pickup(self, deck: list[Card]) -> list[Card]:
        """
        Return a list of cards representing the pickup pile.
        """
        for card in deck:
            card.update(CardStatus.PILE_PICKUP)
        return deck

    def _initialize_players(self, num_players: int) -> list[Player]:
        """
        Create and add the given number of players to the game (all with unique id).
        """
        players = []
        if num_players > MAX_PLAYERS:
            raise ValueError(f"Maximum number of players is {MAX_PLAYERS}")
        for p in range(num_players):
            players.append(Player(p+1))
        return players

#################### post-amble ####################

    def tally_scores(self) -> dict[int,int]:
        """
        Count up each player's points for the current round and return them in a dict.
        """
        scores = {}
        for p in self.players:
            cards_played = p.played_cards
            score = self._sum_points(list(cards_played))
            scores[p.id] = score
        return scores

    def _sum_points(self, cards: list[Card]) -> int:
        """
        Return the total point value of all the cards in given list.
        """
        score = 0
        for c in cards:
            score += CARD_POINT_VALUES[c.rank]
        return score

#################### utils ####################

    def to_dict(self) -> dict:
        """
        Serialize the full `Game` state to a dict suitable for persistence or
        transport.

        Returned structure:
          - `players`: list of player dicts (each from `Player.to_dict()`)
          - `pile_pickup`: list of pickup pile card dicts
          - `pile_discard`: list of discard pile card dicts
          - `plays`: canonical list of plays (each from `Play.to_dict()`)
          - `id_counter`: integer play id counter for future play generation

        Note: In-memory `self.plays` uses observable keys of `str(play)` for
        human-friendly debugging and display; the serialized form is a plain
        list of play dicts so that callers need not rely on in-memory dict keys.
        """
        players_list = sorted(self.players, key=lambda p: p.id)
        return {
            'players': [p.to_dict() for p in players_list],
            'pile_pickup': [c.to_dict() for c in self.pile_pickup],
            'pile_discard': [c.to_dict() for c in self.pile_discard],
            'plays': [pl.to_dict() for pl in sorted(self.plays.values(), key=lambda x: x.id)],
            'id_counter': self.play_id_counter
        }

    @staticmethod
    def from_dict(d: dict) -> 'Game':
        """
        Reconstruct a `Game` from a dict previously produced by `to_dict()`.

        This method validates the outer schema and rebuilds players, piles, and
        plays from the serialized payload. The in-memory `self.plays` mapping uses
        keys equal to `str(play)` for observability, while each `Play.id` remains
        the numeric identifier used in the game.
        """
        if not isinstance(d, dict):
            raise ValueError("Game.from_dict expects a dict")
        g = object.__new__(Game)
        g.players = []
        players_list = d.get('players', [])
        if not isinstance(players_list, list):
            raise ValueError("Game.from_dict: 'players' must be a list")
        for pd in players_list:
            p = Player.from_dict(pd)
            g.players.append(p)
        pile_pickup_list = d.get('pile_pickup', [])
        if not isinstance(pile_pickup_list, list):
            raise ValueError("Game.from_dict: 'pile_pickup' must be a list")
        g.pile_pickup = [Card.from_dict(cd) for cd in pile_pickup_list]
        pile_discard_list = d.get('pile_discard', [])
        if not isinstance(pile_discard_list, list):
            raise ValueError("Game.from_dict: 'pile_discard' must be a list")
        g.pile_discard = [Card.from_dict(cd) for cd in pile_discard_list]
        # Expect serialized `plays` list (canonical). Legacy 'table' support removed.
        plays_obj = d.get('plays')
        if plays_obj is None:
            raise ValueError("Game.from_dict: 'plays' must be provided as a list")
        if not isinstance(plays_obj, list):
            raise ValueError("Game.from_dict: 'plays' must be a list")
        g.plays = {}
        g.card_loc_dict = {}
        for pd in plays_obj:
            if not isinstance(pd, dict):
                raise ValueError("each play must be a dict in 'plays'")
            pid = pd.get('play_id')
            typ_val = pd.get('type')
            # accept either PlayType value ('R'/'W') or PlayType member
            if isinstance(typ_val, str):
                try:
                    typ = PlayType(typ_val)
                except Exception:
                    raise ValueError(f"invalid play type: {typ_val}")
            elif isinstance(typ_val, PlayType):
                typ = typ_val
            else:
                raise ValueError("play 'type' must be a string or PlayType")

            key_field = pd.get('key')
            cards_list = [Card.from_dict(cd) for cd in pd.get('cards', [])]
            play = Play(id=pid, type=typ, key=key_field, cards=list(cards_list))
            key = g._key_for_plays_dict(play)
            g.plays[key] = play
            for idx, c in enumerate(cards_list):
                # card_loc_dict maps to (play.id, index_in_play)
                g.card_loc_dict[c.id] = (play.id, idx)
        g.play_id_counter = d.get('id_counter', 0)
        seen = set()
        def check_and_add(card: Card):
            cid = card.id
            if cid in seen:
                raise DuplicateIDError(f"Duplicate card_id detected during Game.from_dict: {cid}")
            seen.add(cid)
        for p in g.players:
            for c in p.hand:
                check_and_add(c)
            for c in p.played_cards:
                check_and_add(c)
        for c in g.pile_pickup:
            check_and_add(c)
        for c in g.pile_discard:
            check_and_add(c)
        for play in g.plays.values():
            for c in play.cards:
                check_and_add(c)
        return g

    def validate(self) -> None:
        """Validate game invariants in-memory.

        Checks performed:
        - No duplicate `card_id` values across players' hands, played_cards, piles, and table.
        - Card `status` values are consistent with their location (HAND/TABLE/PILE_*).

        Raises `DuplicateIDError` or `GameStateError` on failure.
        """

        seen = set()

        def check_card_location(card: Card, location: str):
            cid = card.id
            if cid in seen:
                raise DuplicateIDError(f"Duplicate card_id detected in game state: {cid}")
            seen.add(cid)

            st = card.status
            if st is not None:
                if location == 'hand' and st != CardStatus.HAND:
                    raise GameStateError(f"Card {cid} in hand but status is {st}")
                if location == 'played' and st != CardStatus.TABLE:
                    raise GameStateError(f"Card {cid} in played_cards but status is {st}")
                if location == 'pickup' and st != CardStatus.PILE_PICKUP:
                    raise GameStateError(f"Card {cid} in pile_pickup but status is {st}")
                if location == 'discard' and st != CardStatus.PILE_DISCARD:
                    raise GameStateError(f"Card {cid} in pile_discard but status is {st}")
                if location == 'table' and st != CardStatus.TABLE:
                    raise GameStateError(f"Card {cid} on table but status is {st}")

        for p in self.players:
            for c in p.hand:
                check_card_location(c, 'hand')
            for c in p.played_cards:
                check_card_location(c, 'played')

        for c in self.pile_pickup:
            check_card_location(c, 'pickup')
        for c in self.pile_discard:
            check_card_location(c, 'discard')
        # validate table/play cards
        for play in self.plays.values():
            for c in play.cards:
                check_card_location(c, 'table')

    def __str__(self) -> str:
        players = "\n\t".join(str_list(self.players))
        players = "\t" + players
        return f"players:\n{players}\ndiscard pile: {format_list_of_str(self.pile_discard)}\npickup pile: {format_list_of_str(self.pile_pickup)}"

    def stringify_plays(self) -> str:
        """
        Return a string representation of `self.plays`.
        """
        s = "{\n"
        for play in self.plays.values():
            s += '\t' + str(play) + ": "
            s += format_list_of_str(str_list(play.cards))
            s += "\n"
        s += "}"
        return s

