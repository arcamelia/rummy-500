from .player import Player
from .game import Game
from .utils import format_list_of_str

class GameConsoleAdapter:
    def __init__(self, game: Game):
        self.game = game
    
    def run(self) -> dict[int,int]:
        """
        Rotate players' turns until it's not possible to continue, then return the game's score.
        """
        while True:
            for p in self.game.players:
                if len(self.game.pile_pickup) < 1:
                    # only perform the more cpu intensive check if necessary
                    if not self.can_play_from_discard(p.get_hand()):
                        print("No more cards to pick up")
                        return self.tally_scores()
                    
                self.run_turn_for_player(p)

                if not p.get_hand():
                    print(f"Player {p.get_id()} has gone out!")
                    return self.tally_scores()

    def run_turn_for_player(self, player: Player) -> None:
        """
        Run a complete turn for given player. This consists of pickup, play (optional 
        unless pickup occurs from discard pile), and discard phases. 
        """
        print(f"\n--- Player {player.id}'s Turn ---")
        print("Your hand:", format_list_of_str(player.hand))
        print("Discard pile:", format_list_of_str(self.game.pile_discard))

        while True:
            choice = input("Draw from (p)ickup or (d)iscard pile? [p/d] ").strip().lower()
            if choice == 'd':
                try:
                    idx = int(input("Choose card index to pick up from (0-indexed): ").strip())
                    reqd_card = self.game.pickup(player, idx)
                    break
                except Exception as e:
                    print("Invalid pickup from discard:", e)
                    continue
            elif choice == 'p':
                try:
                    reqd_card = None
                    self.game.pickup(player)
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

            print("Your hand:", format_list_of_str(player.hand))
            type_of_play = input("Do you want to play a (r)un or a (w)reck? [r/w] ").strip().upper()
            if type_of_play not in ('R', 'W'):
                print("Invalid input. Try again.")
                continue

            indices_i = input("Choose card indices (0-indexed) from your hand to play (comma-separated): ").strip()
            indices = self.game._Game__parse_input_to_list_of_indices(indices_i, len(player.hand))
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
                print("Your hand:", format_list_of_str(player.hand))
                idx = int(input("Choose card index to discard (0-indexed): ").strip())
                card = self.game.discard(player, idx)
                print(f"You discarded {card}.\n")
                break
            except Exception as e:
                print("Invalid discard:", e)
                continue
