"""
Game engine - Agent base class, Directions, and AgentState.
"""
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
    def __init__(self, position=(), direction=Directions.STOP, is_pacman=False, scared_timer=0):
        self.position = position
        self.direction = direction
        self.is_pacman = is_pacman
        self.scared_timer = scared_timer

    def copy(self):
        state = AgentState(self.position, self.direction, self.is_pacman, self.scared_timer)
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
                    self.is_pacman == other.is_pacman and
                    self.scared_timer == other.scared_timer)
        return False

    def __hash__(self):
        return hash((self.position, self.direction, self.is_pacman, self.scared_timer))


class Agent:
    def __init__(self, index=0):
        self.index = index

    def get_action(self, state):
        raise NotImplementedError


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
        from layout import AgentRules
        self.game_over = False
        agent_index = 0
        num_agents = len(self.agents)
        num_iterations = 0
        max_iterations = 10000

        while not self.game_over and num_iterations < max_iterations:
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
