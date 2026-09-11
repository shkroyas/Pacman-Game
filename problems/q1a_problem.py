"""
Q1a Problem - Single dot pathfinding.
"""
from layout import GameState


class Q1aProblem:
    def __init__(self, state):
        self.start_state = state
        self.start_position = state.get_pacman_position()
        self.goal_position = None
        food_positions = state.get_food_positions()
        if food_positions:
            self.goal_position = food_positions[0]

    def get_start_state(self):
        return self.start_position

    def is_goal_state(self, state):
        if isinstance(state, tuple):
            return state == self.goal_position
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
