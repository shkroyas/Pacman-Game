"""
Q1b Problem - Multiple dots pathfinding (nearest dot).
"""
from layout import GameState


class Q1bProblem:
    def __init__(self, state):
        self.start_state = state
        self.start_position = state.get_pacman_position()
        self.food_positions = state.get_food_positions()

    def get_start_state(self):
        return self.start_position

    def is_goal_state(self, state):
        if isinstance(state, tuple):
            return state in self.food_positions
        return False

    def get_successors(self, state):
        x, y = int(state[0]), int(state[1])
        successors = []
        walls = self.start_state.get_walls()

        from game import Directions
        for action in Directions:
            if action == Directions.STOP:
                continue
            dx, dy = action.get_vector()
            next_x, next_y = x + dx, y + dy
            if not walls.is_wall(next_x, next_y):
                successors.append(((next_x, next_y), action, 1))

        return successors
