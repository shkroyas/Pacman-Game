"""
Q2 Agent - Alpha-Beta pruning with evaluation function.
"""
from game import Agent, Directions


class Q2Agent(Agent):
    def __init__(self, depth=2, eval_fn=None):
        super().__init__(0)
        self.depth = depth
        self.eval_fn = eval_fn or self.default_eval
        self.nodes_expanded = 0

    def get_action(self, state):
        self.nodes_expanded = 0
        best_score = float('-inf')
        best_action = None
        alpha = float('-inf')
        beta = float('inf')

        for action in state.get_legal_actions(0):
            successor = state.generate_successor(0, action)
            score = self.alpha_beta(successor, self.depth, 1, alpha, beta)
            if score > best_score:
                best_score = score
                best_action = action
            alpha = max(alpha, score)

        return best_action if best_action else Directions.STOP

    def alpha_beta(self, state, depth, agent_index, alpha, beta):
        self.nodes_expanded += 1

        if depth == 0 or state.is_win() or state.is_lose():
            return self.eval_fn(state)

        next_agent = (agent_index + 1) % state.get_num_agents()
        next_depth = depth - 1 if next_agent == 0 else depth

        if agent_index == 0:
            return self.max_value(state, next_depth, next_agent, alpha, beta)
        else:
            return self.min_value(state, next_depth, next_agent, alpha, beta)

    def max_value(self, state, depth, agent_index, alpha, beta):
        value = float('-inf')
        for action in state.get_legal_actions(agent_index):
            successor = state.generate_successor(agent_index, action)
            value = max(value, self.alpha_beta(successor, depth, agent_index, alpha, beta))
            if value > beta:
                return value
            alpha = max(alpha, value)
        return value

    def min_value(self, state, depth, agent_index, alpha, beta):
        value = float('inf')
        for action in state.get_legal_actions(agent_index):
            successor = state.generate_successor(agent_index, action)
            next_agent = (agent_index + 1) % state.get_num_agents()
            next_depth = depth - 1 if next_agent == 0 else depth
            value = min(value, self.alpha_beta(successor, next_depth, next_agent, alpha, beta))
            if value < alpha:
                return value
            beta = min(beta, value)
        return value

    def default_eval(self, state):
        score = state.get_score() * 1.0

        food_positions = state.get_food_positions()
        pacman_pos = state.get_pacman_position()

        if food_positions:
            min_food_dist = min(abs(pacman_pos[0] - f[0]) + abs(pacman_pos[1] - f[1])
                              for f in food_positions)
            score += 10.0 / (min_food_dist + 1)

        for i, ghost_pos in enumerate(state.get_ghost_positions()):
            ghost_state = state.get_agent_state(i + 1)
            dist = abs(pacman_pos[0] - ghost_pos[0]) + abs(pacman_pos[1] - ghost_pos[1])
            if ghost_state.scared_timer > 0:
                score += 20.0 / (dist + 1)
            else:
                if dist < 3:
                    score -= 100.0 / (dist + 1)
                else:
                    score -= 1.0 / (dist + 1)

        score -= len(food_positions) * 2

        return score
