"""
Layout parser - reads .lay files and creates grid representations.
"""
from game import Directions


class Grid:
    def __init__(self, width, height, initial_value=False):
        self.width = width
        self.height = height
        self.data = [[initial_value for _ in range(height)] for _ in range(width)]

    def is_wall(self, x, y):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return True
        return self.data[int(x)][int(y)]

    def set_wall(self, x, y, value=True):
        self.data[int(x)][int(y)] = value

    def deep_copy(self):
        new_grid = Grid(self.width, self.height)
        for x in range(self.width):
            for y in range(self.height):
                new_grid.data[x][y] = self.data[x][y]
        return new_grid


class FoodGrid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.data = [[False for _ in range(height)] for _ in range(width)]

    def eat_food(self, x, y):
        self.data[int(x)][int(y)] = False

    def has_food(self, x, y):
        return self.data[int(x)][int(y)]

    def deep_copy(self):
        new_grid = FoodGrid(self.width, self.height)
        for x in range(self.width):
            for y in range(self.height):
                new_grid.data[x][y] = self.data[x][y]
        return new_grid


class GameState:
    def __init__(self, layout):
        self.layout = layout
        self.walls = layout.walls.deep_copy()
        self.food = layout.food.deep_copy()
        self.capsules = list(layout.capsules)
        self.num_agents = layout.num_agents
        self.agent_positions = [layout.agent_positions[i] for i in range(self.num_agents)]
        self.agent_directions = [layout.agent_directions[i] for i in range(self.num_agents)]
        self.agent_is_pacman = [layout.agent_is_pacman[i] for i in range(self.num_agents)]
        self.score = 0
        self.num_food = layout.num_food

    def deep_copy(self):
        new_state = GameState.__new__(GameState)
        new_state.layout = self.layout
        new_state.walls = self.walls.deep_copy()
        new_state.food = self.food.deep_copy()
        new_state.capsules = list(self.capsules)
        new_state.num_agents = self.num_agents
        new_state.agent_positions = list(self.agent_positions)
        new_state.agent_directions = list(self.agent_directions)
        new_state.agent_is_pacman = list(self.agent_is_pacman)
        new_state.score = self.score
        new_state.num_food = self.num_food
        return new_state

    def get_agent_position(self, agent_index):
        return self.agent_positions[agent_index]

    def set_agent_position(self, agent_index, position):
        self.agent_positions[agent_index] = position

    def get_agent_direction(self, agent_index):
        return self.agent_directions[agent_index]

    def set_agent_direction(self, agent_index, direction):
        self.agent_directions[agent_index] = direction

    def get_agent_state(self, agent_index):
        from game import AgentState
        return AgentState(
            self.agent_positions[agent_index],
            self.agent_directions[agent_index],
            self.agent_is_pacman[agent_index]
        )

    def get_pacman_position(self):
        return self.agent_positions[0]

    def get_ghost_positions(self):
        return self.agent_positions[1:]

    def get_ghost_states(self):
        return [self.get_agent_state(i) for i in range(1, self.num_agents)]

    def get_walls(self):
        return self.walls

    def get_food(self):
        return self.food

    def get_food_positions(self):
        positions = []
        for x in range(self.food.width):
            for y in range(self.food.height):
                if self.food.has_food(x, y):
                    positions.append((x, y))
        return positions

    def get_capsules(self):
        return self.capsules

    def get_score(self):
        return self.score

    def get_num_agents(self):
        return self.num_agents

    def get_legal_actions(self, agent_index):
        return AgentRules.get_legal_actions(self, agent_index)

    def generate_successor(self, agent_index, action):
        return AgentRules.apply_action(self, action, agent_index)

    def is_win(self):
        return self.num_food == 0

    def is_lose(self):
        return False

    def __str__(self):
        return self.layout.to_str(self.agent_positions)

    def __eq__(self, other):
        if isinstance(other, GameState):
            return (self.agent_positions == other.agent_positions and
                    self.food.data == other.food.data)
        return False

    def __hash__(self):
        return hash((tuple(self.agent_positions), str(self.food.data)))


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
            if not walls.is_wall(next_x, next_y):
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

        if agent_index == 0:
            if new_state.food.has_food(int(new_pos[0]), int(new_pos[1])):
                new_state.food.eat_food(int(new_pos[0]), int(new_pos[1]))
                new_state.score += 10
                new_state.num_food -= 1
            if new_pos in new_state.capsules:
                new_state.capsules.remove(new_pos)
                new_state.score += 50
                for i in range(1, new_state.num_agents):
                    new_state.agent_directions[i] = Directions.STOP

        return new_state


class Layout:
    def __init__(self, layout_text):
        self.layout_text = layout_text
        self.width = 0
        self.height = 0
        self.walls = None
        self.food = None
        self.capsules = []
        self.agent_positions = []
        self.agent_directions = []
        self.agent_is_pacman = []
        self.num_agents = 0
        self.num_food = 0
        self.parse_layout(layout_text)

    def parse_layout(self, layout_text):
        lines = layout_text.strip().split('\n')
        self.height = len(lines)
        self.width = max(len(line) for line in lines)

        self.walls = Grid(self.width, self.height, False)
        self.food = FoodGrid(self.width, self.height)
        self.capsules = []
        self.agent_positions = []
        self.agent_directions = []
        self.agent_is_pacman = []

        for y, line in enumerate(lines):
            for x, ch in enumerate(line):
                if ch == '%':
                    self.walls.set_wall(x, self.height - 1 - y, True)
                elif ch == '.':
                    self.food.data[x][self.height - 1 - y] = True
                    self.num_food += 1
                elif ch == 'o':
                    self.capsules.append((x, self.height - 1 - y))
                elif ch == 'P':
                    self.agent_positions.append((x, self.height - 1 - y))
                    self.agent_directions.append(Directions.STOP)
                    self.agent_is_pacman.append(True)
                    self.num_agents += 1
                elif ch in '12345678':
                    ghost_num = int(ch)
                    while len(self.agent_positions) < ghost_num:
                        self.agent_positions.append((0, 0))
                        self.agent_directions.append(Directions.STOP)
                        self.agent_is_pacman.append(False)
                    self.agent_positions[ghost_num - 1] = (x, self.height - 1 - y)
                    self.agent_directions[ghost_num - 1] = Directions.STOP
                    self.agent_is_pacman[ghost_num - 1] = False
                    if self.num_agents < ghost_num:
                        self.num_agents = ghost_num

    def to_str(self, agent_positions=None):
        chars = []
        for y in range(self.height - 1, -1, -1):
            row = []
            for x in range(self.width):
                if self.walls.is_wall(x, y):
                    row.append('%')
                elif agent_positions and (x, y) in agent_positions:
                    idx = agent_positions.index((x, y))
                    row.append('P' if idx == 0 else str(idx))
                elif self.food.has_food(x, y):
                    row.append('.')
                elif (x, y) in self.capsules:
                    row.append('o')
                else:
                    row.append(' ')
            chars.append(''.join(row))
        return '\n'.join(chars)

    @staticmethod
    def get_layout(name):
        import os
        layout_dir = os.path.join(os.path.dirname(__file__), 'layouts')
        layout_file = os.path.join(layout_dir, name + '.lay')
        if not os.path.exists(layout_file):
            raise ValueError(f"Layout not found: {name}")
        with open(layout_file) as f:
            return Layout(f.read())
