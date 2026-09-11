"""
Text-based display for Pacman game.
"""


class TextDisplay:
    def __init__(self, quiet=False):
        self.quiet = quiet
        self.move_count = 0

    def display(self, state):
        if self.quiet:
            return
        self.move_count += 1
        if self.move_count % 50 == 0:
            print(f"Move {self.move_count}: Score {state.get_score()}")
            print(str(state))
            print()

    def display_game_result(self, state, result):
        print("\n" + "=" * 40)
        if state.is_win():
            print("YOU WIN!")
        else:
            print("GAME OVER")
        print(f"Final Score: {result['score']}")
        print(f"Moves: {self.move_count}")
        if 'nodes_expanded' in result:
            print(f"Nodes Expanded: {result['nodes_expanded']}")
        if 'search_time' in result:
            print(f"Search Time: {result['search_time']:.3f}s")
        print("=" * 40)
