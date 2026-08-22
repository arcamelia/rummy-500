from card import Card, Rank, Suit, CardStatus
from player import Player
from utils import str_list, format_list_of_str
import random
import itertools
from typing import Callable
from errors.exceptions import DuplicateIDError

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
    players: list[Player]            # between 2 - MAX_PLAYERS (ordered)
    pile_pickup: list[Card]         # begins with many cards, but may become 0 at some point
    pile_discard: list[Card]        # always has > 0 cards in it
    table: dict[str,list[Card]]
    id_counter: int                 # used for generating keys in the table

    """
    Some notes on the table:

    * key formation:
        - prefix character of R (run) or W (wreck)
        - for a R, the second character indicates what suit it is
        - for a W, the second character indicates what rank it is
        - the integer at the end indicates the order of play, and is unique to that sequence (
            determined by `self.id_counter`)

        when a player plays the 5H, it will be added to the front of RH5.
        however, when the 9H is played, it could be placed either at the front of RH3 or the 
        end of RH5. we will resolve this by combining the two lists together as RH3, and 
        removing RH5 from the map (we arbitrarily choose to keep the run that was played first).
    
    * the list values of each entry in the dict MUST BE KEPT IN SORTED ORDER

    * each player will keep track of the cards that they specifically have played, so it's not required
      for the central table to know who played what

    e.g. table = {
        RC1: [3C, 4C, 5C],
        WA2: [AC, AD, AS],
        RH3: [10H, JH, QH, KH, AH],
        RS4: [8S, 9S, 10S],
        RH5: [6H, 7H, 8H],
        W36: [3D, 3S, 3H]
    }

    """

    def __init__(self, num_players):
        self.players = []
        self.__add_players(num_players)
        deck: list[Card] = self.__initialize_deck()
        self.__deal_cards(deck, self.players)

        self.pile_discard = self.__initialize_pile_discard(deck)
        self.pile_pickup = self.__initialize_pile_pickup(deck)
        
        self.table: dict[str,list[Card]] = {}
        self.id_counter = 0
    
    def run(self) -> dict[int,int]:
        """
        Rotate players' turns until it's not possible to continue, then return the game's score.
        """
        
        # Engine loop behavior should be implemented by the caller; this method
        # historically performed console-driven rounds. For server or programmatic
        # use, iterate players and call the action methods exposed on this class.
        raise NotImplementedError("Game.run is UI-specific; use the engine action methods in a loop instead")

    def run_turn_for_player(self, player: Player) -> None:
        """
        Run a complete turn for given player. This consists of pickup, play (optional 
        unless pickup occurs from discard pile), and discard phases. 
        """
        raise NotImplementedError("run_turn_for_player is UI-specific; use GameConsoleAdapter for interactive play")

    def __run_pickup_phase(self, player: Player) -> None | Card:
        """
        Given player chooses a card and then picks it up, either from the pickup or discard pile.

        If the player chooses a card from the pickup pile, the one on top of the deck is added to 
        their hand.

        If the player chooses a card from the discard pile, this method returns the chosen card and 
        adds all other cards with index > the chosen card to the player's hand.

        e.g., if the discard pile currently holds [ 3D, JS, 7C, 10C ] and the player chooses to pick 
        up the JS, this method will return the JS, and add the 7C, 10C to the player's hand.
        (We return the JS because it has to be played straight away.)
        """
        raise NotImplementedError("__run_pickup_phase is UI-specific; use pickup_from_pickup or pickup_from_discard instead")

    def __run_play_phase(self, player: Player, reqd_card: Card = None) -> None:
        """
        Given player plays any number of cards from their hand onto the table.
        
        Validation is performed to ensure the chosen cards are legally playable.
        """
        raise NotImplementedError("__run_play_phase is UI-specific; use play() engine method instead")

    def __run_discard_phase(self, player: Player) -> None:
        """
        Given player chooses a card from their hand and then discards it (i.e., the 
        chosen card gets placed at the end / the highest index of the discard pile).
        """
        raise NotImplementedError("__run_discard_phase is UI-specific; use discard() engine method instead")

    # ------------------ Engine action methods (UI-agnostic) ------------------
    def pickup_from_pickup(self, player: Player) -> Card:
        """Draw the top card from the pickup pile into the player's hand."""
        if not self.pile_pickup:
            raise IndexError("Pickup pile is empty")
        card = self.pile_pickup.pop()
        player.add_to_hand(card)
        return card

    def pickup_from_discard(self, player: Player, idx: int) -> Card:
        """Pick up a card from the discard pile at `idx` and add subsequent cards to hand.

        Returns the chosen card which must be used immediately by the caller (if game rules
        require it). Raises `ValueError` if chosen card cannot be legally used immediately.
        """
        if idx < 0 or idx >= len(self.pile_discard):
            raise IndexError("Discard index out of range")
        chosen_card = self.pile_discard[idx]

        if not self.legal_play_possible_with(player.get_hand(), chosen_card):
            raise ValueError(f"Chosen card {chosen_card} cannot be used immediately")

        # take the chosen card and all cards after it into the player's hand
        add_to_hand = self.pile_discard[idx+1:]
        self.pile_discard = self.pile_discard[:idx]
        for c in add_to_hand:
            player.add_to_hand(c)
        return chosen_card

    def play(self, player: Player, indices: list[int], type_of_play: str, reqd_card: Card | None = None) -> bool:
        """Attempt to play selected indices from player's hand as `type_of_play` ('R' or 'W').

        Returns True if play was successful, False otherwise.
        """
        if not indices:
            chosen_cards = []
        else:
            chosen_cards = [player.get_hand()[i] for i in indices]
        if reqd_card is not None:
            chosen_cards.append(reqd_card)

        return self.__try_play(player, chosen_cards, type_of_play)

    def discard(self, player: Player, idx: int) -> Card:
        """Discard the card at `idx` from player's hand onto the discard pile."""
        if idx < 0 or idx >= len(player.get_hand()):
            raise IndexError("Hand index out of range")
        card = player.get_hand()[idx]
        player.rmv_from_hand(card, CardStatus.PILE_DISCARD)
        self.pile_discard.append(card)
        return card

    def check_rummy(self, cards: list[Card]) -> bool:
        """
        Return true if the given cards are in the discard pile and are involved in a rummy.
        """
        
        return {c in self.pile_discard for c in cards} and self.legal_play_any(cards)

    def legal_play_spec(self, cards: list[Card], type_of_play: str) -> bool:
        """
        Return `True` if given list of cards can form a legal play based on the specified type (could be a 
        *R* [`type_of_play="R"`] or a *W* [`type_of_play="W"`]).

        If the value of `type_of_play` does not match the type of play that can be legally formed, 
        the method will return `False` (i.e., responsibility is on the caller to ensure the type of play 
        is classified correctly).
        
        **CONSTRAINT:** Method will only return `True` if all cards in given list encompass a 
        singular play.
        
        For example, if the list of cards looks like `[2H, 2D, 2S, JH, QH, KH]`, the method 
        will return `False`, as these two plays should be made separately (even though the two
        plays are legal on their own).
        """
        
        if len(cards) < 3: return self.__legal_play_addon(cards, type_of_play) # is it possible to use inheritance here?

        # check W (all same rank)
        ranks = Card.map_to_rank(cards)
        if all(x == ranks[0] for x in ranks) and type_of_play == "W": return True
        
        # check R (all same suit, consecutive ranks)
        suits = Card.map_to_suit(cards)
        same_suit = all(x == suits[0] for x in suits)
        consecutive_rank = sorted(ranks) == list(range(min(ranks), max(ranks)+1))

        # by default, ace has a rank of 1, but it can also be played high (essentially rank of 14)
        if Card.contains_ace(cards):
            for i in range(len(ranks)):
                if ranks[i] == 1:
                    ranks[i] = 14

            consecutive_rank = consecutive_rank or sorted(ranks) == list(range(min(ranks), max(ranks)+1))

        return same_suit and consecutive_rank and type_of_play == "R"

    def legal_play_any(self, cards: list[Card]) -> bool:
        """
        Return true if given cards can be played legally as a run OR a wreck.
        """
        return self.legal_play_spec(cards, "R") or self.legal_play_spec(cards, "W")

    def legal_play_possible_with(self, aux: list[Card], required_card: Card) -> bool:
        """
        Return `True` if `required_card` can be legally played in conjunction with 0 or 
        more of the cards contained in `aux` (the auxiliary card list).
        """

        # 0 case
        if self.legal_play_any([required_card]):
            return True
        
        # 1 or more cards from aux included in the play
        for num_extra_cards in range(4):
            for subset in itertools.combinations(aux, num_extra_cards):
                candidate = [required_card] + list(subset)

                if self.legal_play_any(candidate):
                    return True

        return False

    def __legal_play_addon(self, cards: list[Card], type_of_play: str) -> bool:
        """
        Return true iff all cards in given list can be added on to existing plays on the table AND 
        is classified under the correct type of play (`"R"` or `"W"`).
        
        This method should only be called on lists with `len < 3`.
        """
        
        match len(cards):
            case 1:
                # could be R or W
                return (
                    self.__legal_one_card_play_r(cards[0]) and type_of_play == "R"
                ) or (
                    self.__legal_one_card_play_w(cards[0]) and type_of_play == "W"
                )
            case 2:
                # can only be R
                if type_of_play != "R": return False
                c1: Card = cards[0]
                c2: Card = cards[1]
                one_card_legal = self.__legal_one_card_play_r(c1) or self.__legal_one_card_play_r(c2)
                return one_card_legal and Card.same_suit(c1, c2) and Card.consecutive_rank(c1, c2)
            case _:
                return False

    def __legal_one_card_play_r(self, card: Card) -> bool:
        """
        Return true if given card can be played on an existing *R*.
        """
        
        key_to_find = "R" + str(card.get_suit())
        potentials: dict[str,list[Card]] = {}

        for k, v in self.table.items():
            if k.startswith(key_to_find): potentials[k] = v

        for v in potentials.values():
            # it's illegal to wrap around the end of a run, i.e., no K - A - 2
            consecutive_low_no_ace = Card.consecutive_rank(card, v[0]) and v[0].get_rank() != Rank.ACE
            consecutive_high_no_ace = Card.consecutive_rank(card, v[-1]) and v[-1].get_rank() != Rank.ACE
            if consecutive_low_no_ace or consecutive_high_no_ace: return True

        return False
    
    def __legal_one_card_play_w(self, card: Card) -> bool:
        """
        Return true if given card can be played on an existing *W*.
        """
        
        key_to_find = "W" + str(card.get_rank())
        for k in self.table.keys():
            if k.startswith(key_to_find): return True
        return False

    def __prompt_and_play(self, player: Player, reqd_card: Card | None = None, allow_skip: bool = True) -> None:
        """
        Prompt given player to choose cards to play, then apply the play if it's legal.

        A normal phase of play is indicated by values of `reqd_card = None` and `allow_skip = True`.
        """
        raise NotImplementedError("__prompt_and_play is UI-specific; use play() engine method instead")

    def __try_play(self, player: Player, cards: list[Card], type_of_play: str) -> bool:
        """
        Return `True` if given cards form a legal play, and are properly added to the table 
        & removed from given player's hand.
        """
        if not self.legal_play_spec(cards, type_of_play):
            return False

        self.__play_cards(player, cards, type_of_play)
        return True

    def __play_cards(self, player: Player, cards: list[Card], type_of_play: str) -> None:
        """
        Encompasses all behaviour that occurs when a player moves 1 or more cards 
        from their hand onto the table as points.

        Return `True` if cards are successfully played.

        **CONSTRAINT**: `type_of_play = "R" | "W"`, cards have already been tested for validity
        """
        player.move_cards_to_played(cards)

        play_key = self.__find_play_match(cards, type_of_play)

        if play_key == None:
            # new play on the table
            new_key = self.__create_key(cards, type_of_play)
            self.table[new_key] = cards
        else:
            # add on to an existing play on the table
            old_play_list = self.table[play_key]
            self.table[play_key] = Card.sort_by_suit_and_rank(old_play_list + cards)

        self.__clean_up_table()

    def __parse_input_to_list_of_indices(self, input: str, max: int) -> list[int] | None:
        """
        Parse a comma-separated list of integers (in string format) as input into a `list` of 
        `int` indices. If given input is invalid, return `None`.
        """
        if not input:
            return []
        
        try:
            indices = [int(x) for x in input.split(",")]
        except ValueError:
            return None
        
        if any(i < 0 or i >= max for i in indices):
            return None
        
        return indices

    def __find_play_match(self, cards: list[Card], type_of_play: str) -> str | None:
        """
        Find a list of cards on the table, if one exists, that param cards can be added to. 
        Return the key of matching list if successful, otherwise return `None`.

        Arbitrarily return the first play match found if more than one exists.
        """
        filtered_table = { k: v for k, v in self.table.items() if k.startswith(type_of_play) }
       
        for k, v in filtered_table.items():
            if self.__cards_can_be_joined(v, cards, type_of_play):
                return k 
             
        return None

    def __cards_can_be_joined(self, cards_1: list[Card], cards_2: list[Card], type_of_play: str) -> bool:
        """
        Return `True` if two lists of cards can be joined, based on the `type_of_play`.

        **CONSTRAINT**: neither list can be empty, one of the lists must contain at least 3 cards
        """
        if type_of_play == "W":
            return cards_1[0].get_rank() == cards_2[0].get_rank()
        
        # type_of_play == "R"
        if cards_1[0].get_suit() != cards_2[0].get_suit():
            return False
        
        high_ace = self.__high_ace(cards_1) or self.__high_ace(cards_2) or self.__high_ace(cards_1 + cards_2)
        amalgamated_cards = Card.sort_by_suit_and_rank(cards_1 + cards_2, high_ace)
        counter = amalgamated_cards[0].get_rank_value()     # lowest rank in list
        
        for c in amalgamated_cards:
            if c.get_rank_value() != counter:
                if counter == 14 and c.get_rank() == Rank.ACE:
                    # special handling for a high ace
                    continue
                else:
                    return False
            counter += 1
        
        return True

    def __clean_up_table(self):
        """
        Join any runs together in `self.table` that are connected.
        """
        to_rmv = []

        for k1, v1 in self.table.items():
            for k2, v2 in self.table.items():

                if k1.startswith("R") and k2.startswith("R") and k1 != k2:
                    if self.__cards_can_be_joined(v1, v2, "R"):
                        self.table[k1] = Card.sort_by_suit_and_rank(v1 + v2)
                        to_rmv.append(k2)
        
        for k in to_rmv:
            self.table.pop(k)
    
    def __high_ace(self, cards: list[Card]):
        """
        Return `True` if there is an ace in the list of cards that should be represented 
        as a high card (a rank value of 14 instead of the default 1).

        - If there is only one card in the list and it is an ace, `False` will be returned.
        - If all 13 cards from the suit are in the list, `False` will be returned.

        **CONSTRAINT**: This method should only be called on a list of cards of the same 
        suit. The method will not validate this constraint is upheld.
        """
        if len(cards) == 13 or len(cards) == 1:
            return False
        
        ranks = { c.get_rank() for c in cards }
        return Rank.ACE in ranks and Rank.KING in ranks      

    def __create_key(self, cards: list[Card], type_of_play: str) -> str:
        """
        Return a new, unique key for given list of cards to be played on the table.

        key formation:
        - prefix character of R (run) or W (wreck)
        - for a R, the second character indicates what suit it is
        - for a W, the second character indicates what rank it is
        - the integer at the end indicates the order of play, and is unique to that sequence 
        (note though, that the integers are not necessarily consecutive)
            - e.g., RH8 was started after W35, but there need not be keys XX6, XX7 in between 
            (which could occur if runs were joined)
        """
        self.id_counter += 1
        if type_of_play == "R":
            suit_rank_id = str(cards[0].get_suit())
        else:
            suit_rank_id = str(cards[0].get_rank())
        return type_of_play + suit_rank_id + str(self.id_counter)

    def tally_scores(self) -> dict[int,int]:
        """
        Count up each player's points for the current round and return them in a dict.
        """
        scores = {}
        for p in self.players:
            cards_played = p.get_played_cards()
            score = self.__sum_points(list(cards_played))
            scores[p.get_id()] = score
        return scores

    def __sum_points(self, cards: list[Card]) -> int:
        """
        Return the total point value of all the cards in given list.
        """
        
        score = 0
        for c in cards:
            score += CARD_POINT_VALUES[c.get_rank()]
        return score

    def __initialize_deck(self) -> list[Card]:
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

    def __deal_cards(self, deck: list[Card], players: list[Player]) -> None:
        """
        Deal out `NUM_CARDS_PER_PLAYER` to the given players.
        """
        
        for p in players:
            for _ in range(NUM_CARDS_PER_PLAYER):
                card = deck.pop()
                card.update(CardStatus.HAND, p.get_id())
                p.add_to_hand(card)

    def __initialize_pile_discard(self, deck: list[Card]) -> list[Card]:
        """
        Return a list of cards representing the discard pile.
        """
        
        c = deck.pop()
        c.update(CardStatus.PILE_DISCARD)
        return [ c, deck.pop(), deck.pop() ]

    def __initialize_pile_pickup(self, deck: list[Card]) -> list[Card]:
        """
        Return a list of cards representing the pickup pile.
        """
        
        for card in deck:
            card.update(CardStatus.PILE_PICKUP)
        return deck

    def __add_players(self, num_players: int) -> None:
        """
        Create and add the given number of players to the game (all with unique id).
        """

        if num_players > MAX_PLAYERS:
            raise ValueError(f"Maximum number of players is {MAX_PLAYERS}")

        for p in range(num_players):
            self.players.append(Player(p+1))

    def get_players(self) -> list[Player]:
        """
        Getter for private `players` member.
        """
        # return a shallow copy to avoid external mutation of internal list
        return list(self.players)

    def __str__(self) -> str:
        """
        Override of `str` method for `Game` class.
        """
        players = "\n\t".join(str_list(self.players))
        players = "\t" + players
        return f"players:\n{players}\ndiscard pile: {format_list_of_str(self.pile_discard)}\npickup pile: {format_list_of_str(self.pile_pickup)}"

    def stringify_table(self) -> str:
        """
        Return a string representation of `self.table`.
        """
        
        s = "{\n"
        for key, value in self.table.items():
            s += '\t' + str(key) + ": "
            s += format_list_of_str(str_list(value))
            s += "\n"
        s += "}"
        return s

    def to_dict(self) -> dict:
        """Serialize game state to a JSON-serializable dict.

        - Players are serialized as a list (sorted by id for determinism).
        - Piles and table contain serialized cards.
        """
        players_list = sorted(list(self.players), key=lambda p: p.get_id())
        return {
            'players': [p.to_dict() for p in players_list],
            'pile_pickup': [c.to_dict() for c in self.pile_pickup],
            'pile_discard': [c.to_dict() for c in self.pile_discard],
            'table': {k: [c.to_dict() for c in v] for k, v in self.table.items()},
            'id_counter': self.id_counter
        }

    @staticmethod
    def from_dict(d: dict) -> 'Game':
        """Reconstruct a Game from a dict produced by `to_dict`.

        This bypasses `Game.__init__` and restores internal structures directly.
        """
        if not isinstance(d, dict):
            raise ValueError("Game.from_dict expects a dict")

        g = object.__new__(Game)
        # reconstruct players as ordered list
        g.players = []
        players_list = d.get('players', [])
        if not isinstance(players_list, list):
            raise ValueError("Game.from_dict: 'players' must be a list")
        for pd in players_list:
            p = Player.from_dict(pd)
            g.players.append(p)

        # reconstruct piles
        pile_pickup_list = d.get('pile_pickup', [])
        if not isinstance(pile_pickup_list, list):
            raise ValueError("Game.from_dict: 'pile_pickup' must be a list")
        g.pile_pickup = [Card.from_dict(cd) for cd in pile_pickup_list]

        pile_discard_list = d.get('pile_discard', [])
        if not isinstance(pile_discard_list, list):
            raise ValueError("Game.from_dict: 'pile_discard' must be a list")
        g.pile_discard = [Card.from_dict(cd) for cd in pile_discard_list]

        # reconstruct table
        table_obj = d.get('table', {})
        if not isinstance(table_obj, dict):
            raise ValueError("Game.from_dict: 'table' must be a dict")
        g.table = {k: [Card.from_dict(cd) for cd in v] for k, v in table_obj.items()}

        g.id_counter = d.get('id_counter', 0)

        # Validate no duplicate card IDs across the reconstructed game state
        seen = set()
        def check_and_add(card: Card):
            cid = card.get_id()
            if cid in seen:
                raise DuplicateIDError(f"Duplicate card_id detected during Game.from_dict: {cid}")
            seen.add(cid)

        for p in g.players:
            for c in p.get_hand():
                check_and_add(c)
            for c in p.get_played_cards():
                check_and_add(c)

        for c in g.pile_pickup:
            check_and_add(c)
        for c in g.pile_discard:
            check_and_add(c)

        for k, v in g.table.items():
            for c in v:
                check_and_add(c)

        return g


class GameConsoleAdapter:
    """Thin console adapter that uses `Game` engine methods for interactive play.

    This adapter keeps all `input()` / `print()` calls out of the engine itself so the
    engine can be used in servers, tests, or other adapters (web UI). Use this class
    only for local interactive sessions.
    """
    def __init__(self, game: Game):
        self.game = game

    def run_turn_for_player(self, player: Player) -> None:
        print(f"\n--- Player {player.get_id()}'s Turn ---")
        print("Your hand:", format_list_of_str(player.get_hand()))
        print("Discard pile:", format_list_of_str(self.game.pile_discard))

        # Pickup phase
        while True:
            choice = input("Draw from (p)ickup or (d)iscard pile? [p/d] ").strip().lower()
            if choice == 'd':
                try:
                    idx = int(input("Choose card index to pick up from (0-indexed): ").strip())
                    reqd_card = self.game.pickup_from_discard(player, idx)
                    break
                except Exception as e:
                    print("Invalid pickup from discard:", e)
                    continue
            elif choice == 'p':
                try:
                    reqd_card = None
                    self.game.pickup_from_pickup(player)
                    break
                except Exception as e:
                    print("Invalid pickup from pickup pile:", e)
                    continue
            else:
                print("Invalid input.")

        # Play phase
        while True:
            if reqd_card is None:
                choice = input("Do you want to play any cards? [y/n] ").strip().lower()
                if choice == 'n':
                    break
                if choice != 'y':
                    print("Invalid input. Try again.")
                    continue

            print("Your hand:", format_list_of_str(player.get_hand()))
            type_of_play = input("Do you want to play a (r)un or a (w)reck? [r/w] ").strip().upper()
            if type_of_play not in ('R', 'W'):
                print("Invalid input. Try again.")
                continue

            indices_i = input("Choose card indices (0-indexed) from your hand to play (comma-separated): ").strip()
            indices = self.game._Game__parse_input_to_list_of_indices(indices_i, len(player.get_hand()))
            if indices is None:
                print("Invalid input. Try again.")
                continue

            success = self.game.play(player, indices, type_of_play, reqd_card)
            if success:
                reqd_card = None
                print("Play successful.")
                print("Updated table:\n", self.game.stringify_table())
            else:
                print("Invalid play. Try again.")
                continue

            # allow multiple plays per turn
            more = input("Play more? [y/n] ").strip().lower()
            if more != 'y':
                break

        # Discard phase
        while True:
            try:
                print("Your hand:", format_list_of_str(player.get_hand()))
                idx = int(input("Choose card index to discard (0-indexed): ").strip())
                card = self.game.discard(player, idx)
                print(f"You discarded {card}.\n")
                break
            except Exception as e:
                print("Invalid discard:", e)
                continue
    

######################## TESTING ########################

if __name__ == '__main__':
    game = Game(2)

    # all cards in the deck, for convenience
    _ac = Card(Suit.CLUBS, Rank.ACE, None)
    _2c = Card(Suit.CLUBS, Rank.TWO, None)
    _3c = Card(Suit.CLUBS, Rank.THREE, None)
    _4c = Card(Suit.CLUBS, Rank.FOUR, None)
    _5c = Card(Suit.CLUBS, Rank.FIVE, None)
    _6c = Card(Suit.CLUBS, Rank.SIX, None)
    _7c = Card(Suit.CLUBS, Rank.SEVEN, None)
    _8c = Card(Suit.CLUBS, Rank.EIGHT, 0)
    _9c = Card(Suit.CLUBS, Rank.NINE, None)
    _10c = Card(Suit.CLUBS, Rank.TEN, None)
    _jc = Card(Suit.CLUBS, Rank.JACK, None)
    _qc = Card(Suit.CLUBS, Rank.QUEEN, None)
    _kc = Card(Suit.CLUBS, Rank.KING, None)

    _ad = Card(Suit.DIAMONDS, Rank.ACE, None)
    _2d = Card(Suit.DIAMONDS, Rank.TWO, None)
    _3d = Card(Suit.DIAMONDS, Rank.THREE, None)
    _4d = Card(Suit.DIAMONDS, Rank.FOUR, None)
    _5d = Card(Suit.DIAMONDS, Rank.FIVE, None)
    _6d = Card(Suit.DIAMONDS, Rank.SIX, None)
    _7d = Card(Suit.DIAMONDS, Rank.SEVEN, None)
    _8d = Card(Suit.DIAMONDS, Rank.EIGHT, None)
    _9d = Card(Suit.DIAMONDS, Rank.NINE, None)
    _10d = Card(Suit.DIAMONDS, Rank.TEN, None)
    _jd = Card(Suit.DIAMONDS, Rank.JACK, None)
    _qd = Card(Suit.DIAMONDS, Rank.QUEEN, None)
    _kd = Card(Suit.DIAMONDS, Rank.KING, None)

    _as = Card(Suit.SPADES, Rank.ACE, None)
    _2s = Card(Suit.SPADES, Rank.TWO, None)
    _3s = Card(Suit.SPADES, Rank.THREE, None)
    _4s = Card(Suit.SPADES, Rank.FOUR, None)
    _5s = Card(Suit.SPADES, Rank.FIVE, None)
    _6s = Card(Suit.SPADES, Rank.SIX, None)
    _7s = Card(Suit.SPADES, Rank.SEVEN, None)
    _8s = Card(Suit.SPADES, Rank.EIGHT, None)
    _9s = Card(Suit.SPADES, Rank.NINE, None)
    _10s = Card(Suit.SPADES, Rank.TEN, None)
    _js = Card(Suit.SPADES, Rank.JACK, None)
    _qs = Card(Suit.SPADES, Rank.QUEEN, None)
    _ks = Card(Suit.SPADES, Rank.KING, None)

    _ah = Card(Suit.HEARTS, Rank.ACE, None)
    _2h = Card(Suit.HEARTS, Rank.TWO, None)
    _3h = Card(Suit.HEARTS, Rank.THREE, None)
    _4h = Card(Suit.HEARTS, Rank.FOUR, None)
    _5h = Card(Suit.HEARTS, Rank.FIVE, None)
    _6h = Card(Suit.HEARTS, Rank.SIX, None)
    _7h = Card(Suit.HEARTS, Rank.SEVEN, None)
    _8h = Card(Suit.HEARTS, Rank.EIGHT, None)
    _9h = Card(Suit.HEARTS, Rank.NINE, None)
    _10h = Card(Suit.HEARTS, Rank.TEN, None)
    _jh = Card(Suit.HEARTS, Rank.JACK, None)
    _qh = Card(Suit.HEARTS, Rank.QUEEN, None)
    _kh = Card(Suit.HEARTS, Rank.KING, None)

    ############### initialize a table midgame ###############

    rc1 = [ _5c, _6c, _7c ]
    wa2 = [ _ac, _ad, _as ]
    rh3 = [ _10h, _jh, _qh, _kh ]
    rs4 = [ _8s, _9s, _10s ]
    rh5 = [ _6h, _7h, _8h ]
    w36 = [ _3d, _3s, _3h ]

    game.table = { "RC1": rc1, "WA2": wa2, "RH3": rh3, "RS4": rs4, "RH5": rh5, "W36": w36 }
    print("table = " + game.stringify_table())

    game.get_players()[0].add_to_hand(_8c)
    adapter = GameConsoleAdapter(game)
    adapter.run_turn_for_player(game.get_players()[0])
