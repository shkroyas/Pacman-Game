"""
Ghost agents - various ghost behaviors.
"""
from game import Agent, Directions
import random


class RandomGhost(Agent):
    def __init__(self, index):
        super().__init__(index)

    def get_action(self, state):
        legal_actions = state.get_legal_actions(self.index)
        if not legal_actions:
            return Directions.STOP
        return random.choice(legal_actions)


class DirectionalGhost(Agent):
    def __init__(self, index, prob_attack=0.8, prob_scared_flee=0.8):
        super().__init__(index)
        self.prob_attack = prob_attack
        self.prob_scared_flee = prob_scared_flee

    def get_action(self, state):
        legal_actions = state.get_legal_actions(self.index)
        if not legal_actions:
            return Directions.STOP

        pos = state.get_agent_position(self.index)
        pacman_pos = state.get_pacman_position()

        is_scared = state.get_agent_state(self.index).scared_timer > 0

        best_action = None
        best_dist = float('inf')
        for action in legal_actions:
            dx, dy = action.get_vector()
            next_pos = (pos[0] + dx, pos[1] + dy)
            dist = abs(next_pos[0] - pacman_pos[0]) + abs(next_pos[1] - pacman_pos[1])
            if dist < best_dist:
                best_dist = dist
                best_action = action

        if is_scared:
            if random.random() < self.prob_scared_flee:
                return best_action
            return random.choice(legal_actions)
        else:
            if random.random() < self.prob_attack:
                return best_action
            return random.choice(legal_actions)
