from .card import Card, Rank, Suit, CardStatus
from .player import Player
from .utils import str_list, format_list_of_str
import random
import itertools
from typing import Callable
from .errors.exceptions import DuplicateIDError, GameStateError

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
    table: dict[str,list[Card]]
    id_counter: int

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
        raise NotImplementedError("Game.run is UI-specific; use the engine action methods in a loop instead")

    def run_turn_for_player(self, player: Player) -> None:
        raise NotImplementedError("run_turn_for_player is UI-specific; use GameConsoleAdapter for interactive play")

    #################### Engine action methods (UI-agnostic) ####################
    
    def pickup_from_pickup(self, player: Player) -> Card:
        if not self.pile_pickup:
            raise IndexError("Pickup pile is empty")
        card = self.pile_pickup.pop()
        player.add_to_hand(card)
        return card

    def pickup_from_discard(self, player: Player, idx: int) -> Card:
        if idx < 0 or idx >= len(self.pile_discard):
            raise IndexError("Discard index out of range")
        chosen_card = self.pile_discard[idx]

        if not self.legal_play_possible_with(player.get_hand(), chosen_card):
            raise ValueError(f"Chosen card {chosen_card} cannot be used immediately")

        add_to_hand = self.pile_discard[idx+1:]
        self.pile_discard = self.pile_discard[:idx]
        for c in add_to_hand:
            player.add_to_hand(c)
        return chosen_card

    def play(self, player: Player, indices: list[int], type_of_play: str, reqd_card: Card | None = None) -> bool:
        if not indices:
            chosen_cards = []
        else:
            chosen_cards = [player.get_hand()[i] for i in indices]
        if reqd_card is not None:
            chosen_cards.append(reqd_card)

        return self.__try_play(player, chosen_cards, type_of_play)

    def discard(self, player: Player, idx: int) -> Card:
        if idx < 0 or idx >= len(player.get_hand()):
            raise IndexError("Hand index out of range")
        card = player.get_hand()[idx]
        player.rmv_from_hand(card, CardStatus.PILE_DISCARD)
        self.pile_discard.append(card)
        return card

    def check_rummy(self, cards: list[Card]) -> bool:
        return {c in self.pile_discard for c in cards} and self.legal_play_any(cards)

    def legal_play_spec(self, cards: list[Card], type_of_play: str) -> bool:
        if len(cards) < 3: return self.__legal_play_addon(cards, type_of_play)

        ranks = Card.map_to_rank(cards)
        if all(x == ranks[0] for x in ranks) and type_of_play == "W": return True
        suits = Card.map_to_suit(cards)
        same_suit = all(x == suits[0] for x in suits)
        consecutive_rank = sorted(ranks) == list(range(min(ranks), max(ranks)+1))

        if Card.contains_ace(cards):
            for i in range(len(ranks)):
                if ranks[i] == 1:
                    ranks[i] = 14

            consecutive_rank = consecutive_rank or sorted(ranks) == list(range(min(ranks), max(ranks)+1))

        return same_suit and consecutive_rank and type_of_play == "R"

    def legal_play_any(self, cards: list[Card]) -> bool:
        return self.legal_play_spec(cards, "R") or self.legal_play_spec(cards, "W")

    def legal_play_possible_with(self, aux: list[Card], required_card: Card) -> bool:
        if self.legal_play_any([required_card]):
            return True
        for num_extra_cards in range(4):
            for subset in itertools.combinations(aux, num_extra_cards):
                candidate = [required_card] + list(subset)
                if self.legal_play_any(candidate):
                    return True
        return False

    def __legal_play_addon(self, cards: list[Card], type_of_play: str) -> bool:
        match len(cards):
            case 1:
                return (
                    self.__legal_one_card_play_r(cards[0]) and type_of_play == "R"
                ) or (
                    self.__legal_one_card_play_w(cards[0]) and type_of_play == "W"
                )
            case 2:
                if type_of_play != "R": return False
                c1: Card = cards[0]
                c2: Card = cards[1]
                one_card_legal = self.__legal_one_card_play_r(c1) or self.__legal_one_card_play_r(c2)
                return one_card_legal and Card.same_suit(c1, c2) and Card.consecutive_rank(c1, c2)
            case _:
                return False

    def __legal_one_card_play_r(self, card: Card) -> bool:
        key_to_find = "R" + str(card.get_suit())
        potentials: dict[str,list[Card]] = {}
        for k, v in self.table.items():
            if k.startswith(key_to_find): potentials[k] = v
        for v in potentials.values():
            consecutive_low_no_ace = Card.consecutive_rank(card, v[0]) and v[0].get_rank() != Rank.ACE
            consecutive_high_no_ace = Card.consecutive_rank(card, v[-1]) and v[-1].get_rank() != Rank.ACE
            if consecutive_low_no_ace or consecutive_high_no_ace: return True
        return False

    def __legal_one_card_play_w(self, card: Card) -> bool:
        key_to_find = "W" + str(card.get_rank())
        for k in self.table.keys():
            if k.startswith(key_to_find): return True
        return False

    def __try_play(self, player: Player, cards: list[Card], type_of_play: str) -> bool:
        if not self.legal_play_spec(cards, type_of_play):
            return False
        self.__play_cards(player, cards, type_of_play)
        return True

    def __play_cards(self, player: Player, cards: list[Card], type_of_play: str) -> None:
        player.move_cards_to_played(cards)
        play_key = self.__find_play_match(cards, type_of_play)
        if play_key == None:
            new_key = self.__create_key(cards, type_of_play)
            self.table[new_key] = cards
        else:
            old_play_list = self.table[play_key]
            self.table[play_key] = Card.sort_by_suit_and_rank(old_play_list + cards)
        self.__clean_up_table()

    def __find_play_match(self, cards: list[Card], type_of_play: str) -> str | None:
        filtered_table = { k: v for k, v in self.table.items() if k.startswith(type_of_play) }
        for k, v in filtered_table.items():
            if self.__cards_can_be_joined(v, cards, type_of_play):
                return k
        return None

    def __cards_can_be_joined(self, cards_1: list[Card], cards_2: list[Card], type_of_play: str) -> bool:
        if type_of_play == "W":
            return cards_1[0].get_rank() == cards_2[0].get_rank()
        if cards_1[0].get_suit() != cards_2[0].get_suit():
            return False
        high_ace = self.__high_ace(cards_1) or self.__high_ace(cards_2) or self.__high_ace(cards_1 + cards_2)
        amalgamated_cards = Card.sort_by_suit_and_rank(cards_1 + cards_2, high_ace)
        counter = amalgamated_cards[0].get_rank_value()
        for c in amalgamated_cards:
            if c.get_rank_value() != counter:
                if counter == 14 and c.get_rank() == Rank.ACE:
                    continue
                else:
                    return False
            counter += 1
        return True

    def __clean_up_table(self):
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
        if len(cards) == 13 or len(cards) == 1:
            return False
        ranks = { c.get_rank() for c in cards }
        return Rank.ACE in ranks and Rank.KING in ranks

    def __create_key(self, cards: list[Card], type_of_play: str) -> str:
        self.id_counter += 1
        if type_of_play == "R":
            suit_rank_id = str(cards[0].get_suit())
        else:
            suit_rank_id = str(cards[0].get_rank())
        return type_of_play + suit_rank_id + str(self.id_counter)

    def tally_scores(self) -> dict[int,int]:
        scores = {}
        for p in self.players:
            cards_played = p.get_played_cards()
            score = self.__sum_points(list(cards_played))
            scores[p.get_id()] = score
        return scores

    def __sum_points(self, cards: list[Card]) -> int:
        score = 0
        for c in cards:
            score += CARD_POINT_VALUES[c.get_rank()]
        return score

    def __initialize_deck(self) -> list[Card]:
        deck: list[Card] = []
        for s in Suit:
            for r in Rank:
                card = Card(suit=s, rank=r, status=None, player=None)
                deck.append(card)
        random.shuffle(deck)
        return deck

    def __deal_cards(self, deck: list[Card], players: list[Player]) -> None:
        for p in players:
            for _ in range(NUM_CARDS_PER_PLAYER):
                card = deck.pop()
                card.update(CardStatus.HAND, p.get_id())
                p.add_to_hand(card)

    def __initialize_pile_discard(self, deck: list[Card]) -> list[Card]:
        c = deck.pop()
        c.update(CardStatus.PILE_DISCARD)
        return [ c, deck.pop(), deck.pop() ]

    def __initialize_pile_pickup(self, deck: list[Card]) -> list[Card]:
        for card in deck:
            card.update(CardStatus.PILE_PICKUP)
        return deck

    def __add_players(self, num_players: int) -> None:
        if num_players > MAX_PLAYERS:
            raise ValueError(f"Maximum number of players is {MAX_PLAYERS}")
        for p in range(num_players):
            self.players.append(Player(p+1))

    def get_players(self) -> list[Player]:
        return list(self.players)

    def __str__(self) -> str:
        players = "\n\t".join(str_list(self.players))
        players = "\t" + players
        return f"players:\n{players}\ndiscard pile: {format_list_of_str(self.pile_discard)}\npickup pile: {format_list_of_str(self.pile_pickup)}"

    def stringify_table(self) -> str:
        s = "{\n"
        for key, value in self.table.items():
            s += '\t' + str(key) + ": "
            s += format_list_of_str(str_list(value))
            s += "\n"
        s += "}"
        return s

    def to_dict(self) -> dict:
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
        table_obj = d.get('table', {})
        if not isinstance(table_obj, dict):
            raise ValueError("Game.from_dict: 'table' must be a dict")
        g.table = {k: [Card.from_dict(cd) for cd in v] for k, v in table_obj.items()}
        g.id_counter = d.get('id_counter', 0)
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

    def validate(self) -> None:
        """Validate game invariants in-memory.

        Checks performed:
        - No duplicate `card_id` values across players' hands, played_cards, piles, and table.
        - Card `status` values are consistent with their location (HAND/TABLE/PILE_*).

        Raises `DuplicateIDError` or `GameStateError` on failure.
        """

        seen = set()

        def check_card_location(card: Card, location: str):
            cid = card.get_id()
            if cid in seen:
                raise DuplicateIDError(f"Duplicate card_id detected in game state: {cid}")
            seen.add(cid)

            st = card.get_status()
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
            for c in p.get_hand():
                check_card_location(c, 'hand')
            for c in p.get_played_cards():
                check_card_location(c, 'played')

        for c in self.pile_pickup:
            check_card_location(c, 'pickup')
        for c in self.pile_discard:
            check_card_location(c, 'discard')

        for k, v in self.table.items():
            for c in v:
                check_card_location(c, 'table')


class GameConsoleAdapter:
    def __init__(self, game: Game):
        self.game = game

    def run_turn_for_player(self, player: Player) -> None:
        print(f"\n--- Player {player.get_id()}'s Turn ---")
        print("Your hand:", format_list_of_str(player.get_hand()))
        print("Discard pile:", format_list_of_str(self.game.pile_discard))

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

            more = input("Play more? [y/n] ").strip().lower()
            if more != 'y':
                break

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
