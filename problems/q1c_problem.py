"""
Q1c Problem - Full board clear (eat all dots).
"""
from layout import GameState


class Q1cProblem:
    def __init__(self, state):
        self.start_state = state
        self.start_position = state.get_pacman_position()
        self.all_food = frozenset(state.get_food_positions())

    def get_start_state(self):
        return (self.start_position, frozenset(self.all_food))

    def is_goal_state(self, state):
        if isinstance(state, tuple) and len(state) == 2:
            pos, remaining_food = state
            return len(remaining_food) == 0
        return False

    def get_successors(self, state):
        pos, remaining_food = state
        x, y = int(pos[0]), int(pos[1])
        successors = []
        walls = self.start_state.get_walls()

        from game import Directions
        for action in Directions:
            if action == Directions.STOP:
                continue
            dx, dy = action.get_vector()
            next_x, next_y = x + dx, y + dy
            if not walls.is_wall(next_x, next_y):
                new_food = remaining_food
                if (next_x, next_y) in remaining_food:
                    new_food = remaining_food - {(next_x, next_y)}
                new_state = ((next_x, next_y), new_food)
                successors.append((new_state, action, 1))

        return successors
