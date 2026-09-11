"""
Tests for Q2 Agent - Alpha-Beta pruning.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from layout import Layout, GameState
from agents.q2Agent import Q2Agent


class TestQ2Agent:
    def test_agent_returns_legal_action(self):
        layout = Layout.get_layout('q2Classic')
        state = GameState(layout)
        agent = Q2Agent(depth=1)
        action = agent.get_action(state)
        assert action.value in ['North', 'South', 'East', 'West']

    def test_agent_expands_nodes(self):
        layout = Layout.get_layout('q2Classic')
        state = GameState(layout)
        agent = Q2Agent(depth=1)
        agent.get_action(state)
        assert agent.nodes_expanded > 0

    def test_deeper_search_expands_more(self):
        layout = Layout.get_layout('q2Classic')
        state = GameState(layout)

        agent_shallow = Q2Agent(depth=1)
        agent_shallow.get_action(state)
        nodes_shallow = agent_shallow.nodes_expanded

        agent_deep = Q2Agent(depth=2)
        agent_deep.get_action(state)
        nodes_deep = agent_deep.nodes_expanded

        assert nodes_deep > nodes_shallow

    def test_evaluation_function(self):
        layout = Layout.get_layout('q2Classic')
        state = GameState(layout)
        agent = Q2Agent(depth=1)
        score = agent.default_eval(state)
        assert isinstance(score, float)
