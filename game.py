"""
Game engine - Agent base class, Directions, and AgentState.
"""
import time
from enum import Enum


class Directions(Enum):
    NORTH = 'North'
    SOUTH = 'South'
    EAST = 'East'
    WEST = 'West'
    STOP = 'Stop'

    def get_vector(self):
        return {
            Directions.NORTH: (0, 1),
            Directions.SOUTH: (0, -1),
            Directions.EAST: (1, 0),
            Directions.WEST: (-1, 0),
            Directions.STOP: (0, 0),
        }[self]

    def __str__(self):
        return self.value


class AgentState:
    def __init__(self, position=(), direction=Directions.STOP, is_pacman=False):
        self.position = position
        self.direction = direction
        self.is_pacman = is_pacman
        self.scared_timer = 0

    def copy(self):
        state = AgentState(self.position, self.direction, self.is_pacman)
        state.scared_timer = self.scared_timer
        return state

    def __str__(self):
        if self.is_pacman:
            return "Pacman: %s %s" % (str(self.position), str(self.direction))
        else:
            return "Ghost: %s %s" % (str(self.position), str(self.direction))

    def __eq__(self, other):
        if isinstance(other, AgentState):
            return (self.position == other.position and
                    self.direction == other.direction and
                    self.is_pacman == other.is_pacman)
        return False

    def __hash__(self):
        return hash((self.position, self.direction, self.is_pacman))


class Agent:
    def __init__(self, index=0):
        self.index = index

    def get_action(self, state):
        raise NotImplementedError


class AgentRules:
    PACMAN_SPEED = 1
    GHOST_SPEED = 1
    SCARED_TIME = 40

    @staticmethod
    def get_legal_actions(state, agent_index):
        pos = state.get_agent_position(agent_index)
        x, y = int(pos[0]), int(pos[1])
        walls = state.get_walls()
        legal = []
        for action in Directions:
            dx, dy = action.get_vector()
            next_x, next_y = x + dx, y + dy
            if not walls[next_x][next_y]:
                legal.append(action)
        return legal

    @staticmethod
    def apply_action(state, action, agent_index):
        new_state = state.deep_copy()
        pos = new_state.get_agent_position(agent_index)
        x, y = int(pos[0]), int(pos[1])
        dx, dy = action.get_vector()
        new_pos = (x + dx, y + dy)
        new_state.set_agent_position(agent_index, new_pos)
        new_state.set_agent_direction(agent_index, action)
        return new_state


class Game:
    def __init__(self, agents, state, display=None, quiet=False):
        self.agents = agents
        self.state = state
        self.display = display
        self.quiet = quiet
        self.num_agents = len(agents)
        self.game_over = False
        self.move_history = []

    def run(self):
        self.game_over = False
        agent_index = 0
        num_agents = len(self.agents)
        num_iterations = 0
        max_iterations = 10000

        while not self.game_over and num_iterations < max_iterations:
            agent_state = self.state.get_agent_state(agent_index)
            if agent_state.is_pacman:
                action = self.agents[agent_index].get_action(self.state)
            else:
                action = self.agents[agent_index].get_action(self.state)

            self.move_history.append((agent_index, action))
            self.state = AgentRules.apply_action(self.state, action, agent_index)

            if not self.quiet:
                self.display.display(self.state)

            agent_index = (agent_index + 1) % num_agents
            num_iterations += 1

            if self.state.is_win() or self.state.is_lose():
                self.game_over = True

        return self.state
