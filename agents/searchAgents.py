"""
Search agents - base classes for search-based Pacman.
"""
from game import Agent, Directions


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
        import time
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
