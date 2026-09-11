"""
Pacman main game loop - orchestrates agents, layout, and game execution.
"""
import sys
import time
from layout import Layout, GameState
from game import Agent, Directions, AgentRules
from textDisplay import TextDisplay


def read_layout(layout_name):
    return Layout.get_layout(layout_name)


class SearchAgent(Agent):
    def __init__(self, problem_class, solver, heuristic=None):
        super().__init__(0)
        self.problem_class = problem_class
        self.solver = solver
        self.heuristic = heuristic
        self.actions = None
        self.action_index = 0
        self.search_time = 0
        self.nodes_expanded = 0

    def register_problem(self, state):
        problem = self.problem_class(state)
        start_time = time.time()
        self.actions = self.solver(problem, self.heuristic)
        self.search_time = time.time() - start_time
        self.action_index = 0

    def get_action(self, state):
        if self.actions is None:
            self.register_problem(state)
        if self.action_index < len(self.actions):
            action = self.actions[self.action_index]
            self.action_index += 1
            return action
        return Directions.STOP

    def get_path_cost(self):
        return len(self.actions) if self.actions else 0

    def get_nodes_expanded(self):
        return self.nodes_expanded


class AlphaBetaAgent(Agent):
    def __init__(self, depth=2, eval_fn=None):
        super().__init__(0)
        self.depth = depth
        self.eval_fn = eval_fn
        self.nodes_expanded = 0
        self.search_time = 0

    def get_action(self, state):
        start_time = time.time()
        best_score = float('-inf')
        best_action = None
        legal_actions = state.get_legal_actions(0)

        for action in legal_actions:
            successor = state.generate_successor(0, action)
            score = self.alpha_beta(successor, self.depth - 1, 1,
                                    float('-inf'), float('inf'))
            if score > best_score:
                best_score = score
                best_action = action

        self.search_time = time.time() - start_time
        return best_action

    def alpha_beta(self, state, depth, agent_index, alpha, beta):
        self.nodes_expanded += 1

        if depth == 0 or state.is_win() or state.is_lose():
            return self.evaluate(state)

        next_agent = (agent_index + 1) % state.get_num_agents()
        next_depth = depth - 1 if next_agent == 0 else depth

        if agent_index == 0:
            return self.max_value(state, next_depth, next_agent, alpha, beta)
        else:
            return self.min_value(state, next_agent, alpha, beta)

    def max_value(self, state, depth, agent_index, alpha, beta):
        value = float('-inf')
        for action in state.get_legal_actions(0):
            successor = state.generate_successor(0, action)
            value = max(value, self.alpha_beta(successor, depth, agent_index, alpha, beta))
            if value > beta:
                return value
            alpha = max(alpha, value)
        return value

    def min_value(self, state, agent_index, alpha, beta):
        value = float('inf')
        for action in state.get_legal_actions(agent_index):
            successor = state.generate_successor(agent_index, action)
            next_agent = (agent_index + 1) % state.get_num_agents()
            next_depth = self.depth - 1 if next_agent == 0 else self.depth
            value = min(value, self.alpha_beta(successor, next_depth, next_agent, alpha, beta))
            if value < alpha:
                return value
            beta = min(beta, value)
        return value

    def evaluate(self, state):
        if self.eval_fn:
            return self.eval_fn(state)
        return state.get_score()


def run_game(layout_name, agent_type='search', depth=2, num_games=1, quiet=False):
    layout = read_layout(layout_name)
    display = TextDisplay(quiet=quiet)
    results = []

    for i in range(num_games):
        state = GameState(layout)

        if agent_type == 'search':
            from problems.q1a_problem import Q1aProblem
            from solvers.q1a_solver import a_star_solver
            agent = SearchAgent(Q1aProblem, a_star_solver)
        elif agent_type == 'alpha_beta':
            agent = AlphaBetaAgent(depth=depth)
        else:
            from agents.pacmanAgents import SimpleAgent
            agent = SimpleAgent(0)

        ghost_agents = []
        for j in range(1, layout.num_agents):
            from agents.ghostAgents import DirectionalGhost
            ghost_agents.append(DirectionalGhost(j))

        all_agents = [agent] + ghost_agents

        game = Game(all_agents, state, display, quiet)
        final_state = game.run()

        results.append({
            'score': final_state.get_score(),
            'win': final_state.is_win(),
            'nodes_expanded': agent.nodes_expanded if hasattr(agent, 'nodes_expanded') else 0,
            'search_time': agent.search_time if hasattr(agent, 'search_time') else 0,
        })

        if not quiet:
            display.display_game_result(final_state, results[-1])

    return results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Pacman AI')
    parser.add_argument('-l', '--layout', default='tinyMaze', help='Layout name')
    parser.add_argument('-p', '--agent', default='search', help='Agent type')
    parser.add_argument('-d', '--depth', type=int, default=2, help='Search depth')
    parser.add_argument('-n', '--num-games', type=int, default=1, help='Number of games')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
    args = parser.parse_args()

    results = run_game(args.layout, args.agent, args.depth, args.num_games, args.quiet)

    print(f"\nResults across {len(results)} game(s):")
    avg_score = sum(r['score'] for r in results) / len(results)
    win_rate = sum(1 for r in results if r['win']) / len(results)
    print(f"Average Score: {avg_score:.1f}")
    print(f"Win Rate: {win_rate:.0%}")
