"""
Q1b Solver - A* search with multi-dot heuristic.
"""
from util import PriorityQueue


def min_food_heuristic(position, food_positions):
    if not food_positions:
        return 0
    return min(abs(position[0] - f[0]) + abs(position[1] - f[1]) for f in food_positions)


def a_star_multi_solver(problem, heuristic=None):
    if heuristic is None:
        heuristic = min_food_heuristic

    start = problem.get_start_state()
    food_positions = problem.food_positions
    frontier = PriorityQueue()
    frontier.push(start, heuristic(start, food_positions))

    came_from = {}
    cost_so_far = {start: 0}

    while not frontier.is_empty():
        current = frontier.pop()

        if problem.is_goal_state(current):
            return reconstruct_path(came_from, current)

        for next_state, action, cost in problem.get_successors(current):
            new_cost = cost_so_far[current] + cost
            if next_state not in cost_so_far or new_cost < cost_so_far[next_state]:
                cost_so_far[next_state] = new_cost
                priority = new_cost + heuristic(next_state, food_positions)
                frontier.push(next_state, priority)
                came_from[next_state] = (current, action)

    return []


def reconstruct_path(came_from, current):
    total_path = []
    while current in came_from:
        current, action = came_from[current]
        total_path.append(action)
    total_path.reverse()
    return total_path
