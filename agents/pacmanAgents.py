"""
Simple Pacman agent - moves toward nearest food.
"""
from game import Agent, Directions
from util import Queue


class SimpleAgent(Agent):
    def __init__(self, index=0):
        super().__init__(index)

    def get_action(self, state):
        from layout import AgentRules
        legal_actions = state.get_legal_actions(self.index)
        if not legal_actions:
            return Directions.STOP

        pos = state.get_pacman_position()
        food = state.get_food_positions()

        if not food:
            return legal_actions[0]

        nearest_food = min(food, key=lambda f: abs(f[0] - pos[0]) + abs(f[1] - pos[1]))

        best_action = None
        best_dist = float('inf')
        for action in legal_actions:
            dx, dy = action.get_vector()
            next_pos = (pos[0] + dx, pos[1] + dy)
            dist = abs(next_pos[0] - nearest_food[0]) + abs(next_pos[1] - nearest_food[1])
            if dist < best_dist:
                best_dist = dist
                best_action = action

        return best_action if best_action else legal_actions[0]
