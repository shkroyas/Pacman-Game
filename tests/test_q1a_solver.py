"""
Tests for Q1a solver - A* single dot search.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from layout import Layout, GameState
from problems.q1a_problem import Q1aProblem
from solvers.q1a_solver import a_star_solver, manhattan_heuristic


class TestQ1aSolver:
    def test_tiny_maze_finds_path(self):
        layout = Layout.get_layout('tinyMaze')
        state = GameState(layout)
        problem = Q1aProblem(state)
        actions = a_star_solver(problem, manhattan_heuristic)
        assert len(actions) > 0
        assert all(a.value in ['North', 'South', 'East', 'West'] for a in actions)

    def test_path_reaches_food(self):
        layout = Layout.get_layout('tinyMaze')
        state = GameState(layout)
        problem = Q1aProblem(state)
        actions = a_star_solver(problem, manhattan_heuristic)

        current_state = state
        for action in actions:
            current_state = current_state.generate_successor(0, action)

        assert current_state.get_score() > 0

    def test_heuristic_is_admissible(self):
        pos = (1, 1)
        goal = (5, 5)
        h = manhattan_heuristic(pos, goal)
        assert h == 8
        assert h >= 0

    def test_no_path_returns_empty(self):
        layout_text = "%%%\n%P%\n%%%"
        layout = Layout(layout_text)
        state = GameState(layout)
        problem = Q1aProblem(state)
        actions = a_star_solver(problem, manhattan_heuristic)
        assert actions == []
