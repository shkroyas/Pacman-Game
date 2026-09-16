"""
Q1a Solver - A* search for single dot.
"""
from util import PriorityQueue


def manhattan_heuristic(position, goal):
    return abs(position[0] - goal[0]) + abs(position[1] - goal[1])


def a_star_solver(problem, heuristic=None):
    if heuristic is None:
        heuristic = manhattan_heuristic

    start = problem.get_start_state()

    if problem.goal_position is None:
        return []

    frontier = PriorityQueue()
    frontier.push(start, heuristic(start, problem.goal_position))

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
                priority = new_cost + heuristic(next_state, problem.goal_position)
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
