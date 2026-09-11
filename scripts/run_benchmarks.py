#!/usr/bin/env python3
"""
Benchmarking script for Pacman AI algorithms.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import time
from layout import Layout, GameState
from problems.q1a_problem import Q1aProblem
from problems.q1b_problem import Q1bProblem
from solvers.q1a_solver import a_star_solver, manhattan_heuristic
from solvers.q1b_solver import a_star_multi_solver, min_food_heuristic
from agents.q2Agent import Q2Agent


def benchmark_search(layout_name, problem_class, solver, heuristic=None):
    layout = Layout.get_layout(layout_name)
    state = GameState(layout)
    problem = problem_class(state)

    start_time = time.time()
    actions = solver(problem, heuristic)
    elapsed = time.time() - start_time

    return {
        'layout': layout_name,
        'algorithm': solver.__name__,
        'path_cost': len(actions),
        'time': elapsed,
        'score': state.get_score()
    }


def benchmark_alphabeta(layout_name, depth):
    layout = Layout.get_layout(layout_name)
    state = GameState(layout)
    agent = Q2Agent(depth=depth)

    start_time = time.time()
    action = agent.get_action(state)
    elapsed = time.time() - start_time

    return {
        'layout': layout_name,
        'algorithm': f'AlphaBeta(depth={depth})',
        'nodes_expanded': agent.nodes_expanded,
        'time': elapsed,
        'action': action.value
    }


def run_benchmarks():
    results = []

    print("Benchmarking A* Search...")
    results.append(benchmark_search('tinyMaze', Q1aProblem, a_star_solver, manhattan_heuristic))
    results.append(benchmark_search('q1a_tinyMaze', Q1aProblem, a_star_solver, manhattan_heuristic))
    results.append(benchmark_search('q1b_mediumCorners', Q1bProblem, a_star_multi_solver, min_food_heuristic))

    print("Benchmarking Alpha-Beta...")
    results.append(benchmark_alphabeta('q2Classic', 1))
    results.append(benchmark_alphabeta('q2Classic', 2))

    print("\n" + "=" * 70)
    print(f"{'Layout':<25} {'Algorithm':<30} {'Result':<15} {'Time (s)':<10}")
    print("=" * 70)

    for r in results:
        if 'path_cost' in r:
            result_str = f"Cost: {r['path_cost']}"
        else:
            result_str = f"Nodes: {r['nodes_expanded']}"
        print(f"{r['layout']:<25} {r['algorithm']:<30} {result_str:<15} {r['time']:.4f}")

    print("=" * 70)


if __name__ == '__main__':
    run_benchmarks()
