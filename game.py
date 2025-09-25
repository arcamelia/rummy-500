from card import Card, Rank, Suit, CardStatus
from player import Player
from utils import str_list, format_list_of_str
import random
import itertools
from typing import Callable

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
    players: set[Player]            # between 2 - MAX_PLAYERS
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
        self.players = set()
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
        
        while True:
            for p in self.players:
                if len(self.pile_pickup) < 1:
                    # only perform the more cpu intensive check if necessary
                    if not self.can_play_from_discard(p.get_hand()):
                        print("No more cards to pick up")
                        return self.tally_scores()
                    
                self.run_turn_for_player(p)

                if not p.get_hand():
                    print(f"Player {p.get_id()} has gone out!")
                    return self.tally_scores()

    # todo: test 3
    def run_turn_for_player(self, player: Player) -> None:
        """
        Run a complete turn for given player. This consists of pickup, play (optional 
        unless pickup occurs from discard pile), and discard phases. 
        """
        # console-based ui version
        print(f"\n--- Player {player.get_id()}'s Turn ---")

        # Show current hand and discard pile
        hand = player.get_hand()
        print("Your hand:", format_list_of_str(hand))
        print("Discard pile:", format_list_of_str(self.pile_discard))

        force_play_card = self.__run_pickup_phase(player)

        self.__run_play_phase(player, force_play_card)

        self.__run_discard_phase(player)

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
        
        add_to_hand: list[Card] = []

        choice = input("Draw from (p)ickup or (d)iscard pile? [p/d] ").strip().lower()
        if choice == "d":

            choice = input("Choose card index to pick up from (0-indexed): ").strip().lower()
            idx = int(choice)
            add_to_hand = self.pile_discard[idx+1:]
            chosen_card: Card = self.pile_discard[idx]

            # check if chosen_card can be played right away
            if not self.legal_play_possible_with(player.get_hand(), chosen_card):
                print(f"You must be able to use {str(chosen_card)} immediately. Invalid choice.")
                return self.__run_pickup_phase(player)

            # card can be played, proceed with pick up
            self.pile_discard = self.pile_discard[:idx]
            
        elif choice == "p":
            add_to_hand.append(self.pile_pickup.pop())

        else:
            print("Invalid input.")
            return self.__run_pickup_phase(player)

        for c in add_to_hand:
            player.add_to_hand(c)
        print("Your hand after pickup:", format_list_of_str(player.get_hand()))

        return chosen_card  # not None if taken from discard pile

    def __run_play_phase(self, player: Player, reqd_card: Card = None) -> None:
        """
        Given player plays any number of cards from their hand onto the table.
        
        Validation is performed to ensure the chosen cards are legally playable.
        """
        
        if reqd_card is not None:
            print(f"You now need to play the {reqd_card}, in addition to 0 or more other cards from your hand.")
            self.__prompt_and_play(player, reqd_card, allow_skip=False)
        
        else: 
            self.__prompt_and_play(player)

    def __run_discard_phase(self, player: Player) -> None:
        """
        Given player chooses a card from their hand and then discards it (i.e., the 
        chosen card gets placed at the end / the highest index of the discard pile).
        """
        
        print("Your hand:", format_list_of_str(player.get_hand()))
        choice = input("Choose card index to discard (0-indexed): ")
        idx = int(choice)
        discard_card = player.get_hand()[idx]

        player.rmv_from_hand(discard_card, CardStatus.PILE_DISCARD)
        self.pile_discard.append(discard_card)
        
        print(f"You discarded {discard_card}.\n")

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

    # todo: test 2
    def __prompt_and_play(self, player: Player, reqd_card: Card | None = None, allow_skip: bool = True) -> None:
        """
        Prompt given player to choose cards to play, then validate and apply the play if it's legal.

        A normal phase of play is indicated by values of `reqd_card = None` and `allow_skip = True`.
        """
        while True:
            if allow_skip:
                choice = input("Do you want to play any cards? [y/n] ").strip().lower()
                if choice == "n":
                    return
                if choice != "y":
                    print("Invalid input. Try again.")
                    continue

            print("Your hand:", format_list_of_str(player.get_hand()))
            type_of_play = input("Do you want to play a (r)un or a (w)reck? [r/w]").strip().upper()
            if type_of_play != "R" and type_of_play != "W":
                    print("Invalid input. Try again.")
                    continue
            indices_i = input("Choose card indices (0-indexed) from your hand to play (comma-separated): ").strip()
            indices = self.__parse_input_to_list_of_indices(indices_i, len(player.get_hand()))
            if indices is None:
                print("Invalid input. Try again.")
                continue

            chosen_cards = [player.get_hand()[i] for i in indices] + ([] if reqd_card is None else [reqd_card])
            print(f"Chosen cards: {format_list_of_str(chosen_cards)}")

            if self.__try_play(player, chosen_cards, type_of_play):
                reqd_card = None
                allow_skip = True
            else:
                print("Cards were not played successfully. Try again.")

    def __try_play(self, player: Player, cards: list[Card], type_of_play: str) -> bool:
        """
        Return `True` if given cards form a legal play, and are properly added to the table 
        & removed from given player's hand.
        """
        if not self.legal_play_spec(cards, type_of_play):
            print("Invalid play. Try again.")
            return False
        
        print("Valid play.")
        self.__play_cards(player, cards, type_of_play)

        print(f"Updated table: \n{self.stringify_table()}")
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
            cards_played = p.get_table()
            score = 0
            for key, cards in cards_played:
                score += self.__sum_points(cards)
            scores[p.get_id()] = score

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
            # todo: throw error
            print(f"Maximum number of players is {MAX_PLAYERS}")
            return
        
        for p in range(num_players):
            self.players.add(Player(p+1))

    def get_players(self) -> list[Player]:
        """
        Getter for private `players` member.
        """
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
    

######################## TESTING ########################

game = Game(2)

# all cards in the deck, for convenience
_ac = Card(Suit.CLUBS, Rank.ACE, None)
_2c = Card(Suit.CLUBS, Rank.TWO, None)
_3c = Card(Suit.CLUBS, Rank.THREE, None)
_4c = Card(Suit.CLUBS, Rank.FOUR, None)
_5c = Card(Suit.CLUBS, Rank.FIVE, None)
_6c = Card(Suit.CLUBS, Rank.SIX, None)
_7c = Card(Suit.CLUBS, Rank.SEVEN, None)
_8c = Card(Suit.CLUBS, Rank.EIGHT, None)
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
"""
table = {
    RC1: [5C, 6C, 7C],
    WA2: [AC, AD, AS],
    RH3: [10H, JH, QH, KH],
    RS4: [8S, 9S, 10S],
    RH5: [6H, 7H, 8H],
    W36: [3D, 3S, 3H]
}
"""
# eight_nine_clubs = [ _8c, _9c ]
# jack_to_king_spades = [ _js, _qs, _ks ]
# nine_hearts = [ _9h ]
# three_clubs = [ _3c ]
# king_clubs = [ _kc ]

# TEST legal_play_possible_with
# discard_pile = [ _8c, _4h, _6d, _js, _jh, _kh]
# print(f"0 case should be true: {game.legal_play_possible_with(discard_pile, _4c)}")
# print(f"1 case should be true: {game.legal_play_possible_with(discard_pile, _9c)}")
# print(f"1 case should be true: {game.legal_play_possible_with(discard_pile, _qs)}")
# print(f"2 case should be true: {game.legal_play_possible_with(discard_pile, _qh)}")
# print(f"None case should be false: {game.legal_play_possible_with(discard_pile, _10c)}")

#########################################################

# 2. TEST __prompt_and_play
# 3. TEST run_turn_for_player


# test_cards = [ Card(Suit.HEARTS, Rank.FIVE, None), Card(Suit.HEARTS, Rank.FOUR, None) ]
# print( f"{format_list_of_str(str_list(test_cards))} can be played: {game.legal_play(test_cards)}" )

#########################################################

# game.run_turn_for_player(game.get_players()[0])
