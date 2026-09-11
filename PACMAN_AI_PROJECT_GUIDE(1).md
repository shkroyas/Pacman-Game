# Building an AI Pac-Man Agent: A Complete Learning Guide

> A from-scratch guide to understanding and implementing search algorithms (A*) and
> adversarial game-tree search (Alpha-Beta pruning) inside a Pac-Man simulation, then
> packaging the result into a professional, deployable portfolio project.

This guide teaches the **concepts and architecture** in enough depth that you can implement
every component yourself. It intentionally gives pseudocode and design reasoning rather than
copy-paste solution code for any graded coursework — if you're working from a university
assignment spec, write the actual algorithm code yourself using the explanations below, then
treat Sections 8–10 (professional repo, deployment) as fully your own build.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Core Concepts You Need First](#2-core-concepts-you-need-first)
3. [System Architecture](#3-system-architecture)
4. [The GameState Model](#4-the-gamestate-model)
5. [Uninformed & Informed Search — Building Intuition](#5-uninformed--informed-search)
6. [A* Search Deep Dive](#6-a-search-deep-dive)
7. [Adversarial Search: Minimax & Alpha-Beta Deep Dive](#7-adversarial-search-minimax--alpha-beta-deep-dive)
8. [Evaluation Functions — Designing Agent "Judgment"](#8-evaluation-functions)
9. [Testing, Debugging & Benchmarking](#9-testing-debugging--benchmarking)
10. [Professional GitHub Repository Structure](#10-professional-github-repository-structure)
11. [Free-Tier Cloud Deployment (AWS / GCP)](#11-free-tier-cloud-deployment)
12. [Writing Effective Prompts to Work With an AI Assistant](#12-writing-effective-prompts)
13. [Glossary](#13-glossary)

---

## 1. Project Overview

You're building an AI that plays Pac-Man in two fundamentally different modes:

| Mode | Problem Type | Technique | Ghosts? |
|---|---|---|---|
| Navigate to a single dot | Single-agent pathfinding | A* search | No |
| Navigate to one of many dots, minimizing search effort | Single-agent pathfinding | A* with a smarter heuristic | No |
| Eat every dot on the board | Single-agent pathfinding (large state space) | A* or a custom heuristic search / approximation | No |
| Survive and score against real opponents | Adversarial game-tree search | Minimax + Alpha-Beta pruning | Yes (1–4) |

These map onto two entirely different ways of thinking about "search":

- **Single-agent search** — there is one decision-maker and a static world. You're finding a
  path through a graph. This is what A* solves.
- **Adversarial search** — there are multiple decision-makers with opposing goals. You can't
  just find "a path" because the world reacts to you. This is what Minimax/Alpha-Beta solves.

Understanding *why* these need different algorithms is the single most important conceptual
leap in this project.

---

## 2. Core Concepts You Need First

### 2.1 State space
A **state** is a snapshot of everything relevant to decision-making at one moment (e.g.
Pac-Man's position). A **state space** is the set of all reachable states, connected by
**actions** that transform one state into another. Search algorithms explore this space to
find a sequence of actions from a start state to a goal state.

### 2.2 Search problem formalism
Every search problem you build in this project is defined by four things:

1. **Initial state** — where we start
2. **Actions(s)** — what moves are legal from state `s`
3. **Transition model** — `Result(s, a)` → the new state after taking action `a` in state `s`
4. **Goal test** — a function that returns true when a state satisfies the objective
5. *(Optional)* **Path cost function** — assigns a cost to a sequence of actions (in Pac-Man,
   every move costs 1)

This maps directly onto the `getStartState`, `getSuccessors`, and `isGoalState` pattern you'll
implement.

### 2.3 Why we don't just use the full game state as our search state
The full `GameState` object contains walls, all food positions, ghost positions, score, etc.
If you used the *entire* GameState as your search "state" for something like "find a path to
one dot," your state space would be needlessly enormous (because food you're not going to eat
still changes the state's identity). Good state design **abstracts away irrelevant detail** —
for a single-dot search, the state might just be `(pacman_x, pacman_y)`. For "eat all dots,"
you need `(pacman_x, pacman_y, remaining_food)` because which dots are left *does* affect what
counts as a goal.

**Design principle:** include in your state exactly the information needed to (a) determine
legal successors and (b) test the goal — nothing more.

### 2.4 Admissibility and consistency of heuristics
A **heuristic** `h(n)` estimates the cost from state `n` to the nearest goal.

- **Admissible**: `h(n)` never *overestimates* the true cost to the goal. Guarantees A* finds
  the optimal solution.
- **Consistent** (stronger): for every state `n` and successor `n'` reached via action costing
  `c`, `h(n) ≤ c + h(n')`. Consistency guarantees you never need to re-expand a node.

**Manhattan distance** `|x1 - x2| + |y1 - y2|` is admissible for Pac-Man because Pac-Man can
only move in 4 directions at cost 1 per move — so the straight-line grid distance is always a
lower bound on the true path cost (which must additionally go around walls).

### 2.5 Why adversarial search is different
In single-agent search, you control every step. In Pac-Man vs. ghosts, after your move the
ghosts move — and they're trying to *minimize* your outcome, not cooperate. You can't search
for "the path to victory" because the ghosts' choices aren't under your control. Instead you
reason: "assuming the ghosts play to hurt me as much as possible, what's my best move *right
now*?" That's exactly what Minimax formalizes.

---

## 3. System Architecture

```
                         ┌─────────────────────┐
                         │      pacman.py       │  ← game loop, GameState, scoring
                         └──────────┬────────────┘
                                    │
                 ┌──────────────────┼───────────────────┐
                 │                  │                    │
         ┌───────▼───────┐  ┌───────▼────────┐   ┌───────▼────────┐
         │  problems/     │  │   solvers/      │   │   agents/       │
         │  (state models)│  │ (search algos)  │   │ (getAction impl)│
         └───────┬────────┘  └───────┬─────────┘   └───────┬────────┘
                 │                   │                      │
        q1a/b/c_problem.py   q1a/b/c_solver.py         q2Agent.py
        - getStartState()    - A* implementation        - Alpha-Beta
        - isGoalState()      - returns action list       - eval function
        - getSuccessors()

                         ┌─────────────────────┐
                         │     util.py          │  ← Stack, Queue, PriorityQueue
                         └─────────────────────┘
```

**Data flow for Part 1 (search):**
`pacman.py` constructs a `problem` object → passes it to your `solver` function → solver
explores the state space (using `util.PriorityQueue` for A*) → returns a list of `Directions`
actions → `SearchAgent.getAction()` plays them back one at a time each game tick.

**Data flow for Part 2 (adversarial):**
Every single game tick, `pacman.py` calls `Q2_Agent.getAction(gameState)` fresh. There's no
precomputed plan — you re-run Alpha-Beta search from the *current* real game state every turn,
looking ahead some fixed depth, and return just the next move.

---

## 4. The GameState Model

Key methods you'll use constantly (from `pacman.py`):

| Method | Returns | Used for |
|---|---|---|
| `getLegalActions(agentIndex)` | list of `Directions` | generating successors |
| `generateSuccessor(agentIndex, action)` | new `GameState` | applying a move |
| `getPacmanPosition()` | `(x, y)` | heuristics, eval functions |
| `getGhostStates()` | list of `AgentState` | ghost positions, scared timers |
| `getGhostPositions()` | list of `(x, y)` | distance-to-ghost calculations |
| `getFood()` | 2D boolean grid | food-related heuristics |
| `getCapsules()` | list of `(x, y)` | power pellet logic |
| `getScore()` | int | evaluation functions |
| `isWin()` / `isLose()` | bool | terminal test in Alpha-Beta |
| `getNumAgents()` | int | knowing how many ghosts to minimize over |

**Important index convention:** agent index `0` is always Pac-Man. Indices `1..N` are ghosts.
This matters a lot in Alpha-Beta — you need to cycle through *all* agents (Pac-Man once, then
every ghost once) before counting that as one full "depth" of search.

---

## 5. Uninformed & Informed Search

Before A*, it helps to understand the two simpler algorithms it generalizes:

- **BFS (Breadth-First Search)** — expands nodes in order of *distance from start* (using a
  FIFO queue). Finds the shortest path in an unweighted graph, but explores blindly in every
  direction, wasting effort on irrelevant regions of the maze.
- **Uniform-Cost Search (Dijkstra)** — like BFS but generalizes to weighted edges, expanding by
  lowest cumulative cost `g(n)`. Still blind — no notion of "closer to the goal."
- **Greedy Best-First Search** — expands by `h(n)` alone (estimated distance to goal). Fast,
  but not optimal — it can be lured down a path that *looks* close but is actually longer.

**A\* combines both**: it expands nodes by `f(n) = g(n) + h(n)` — actual cost so far *plus*
estimated cost remaining. This gets you the efficiency of "aim toward the goal" (greedy) while
retaining the optimality guarantee of uniform-cost search, *as long as your heuristic is
admissible*.

---

## 6. A* Search Deep Dive

### 6.1 Algorithm structure

```
function A_STAR(problem, heuristic):
    frontier ← PriorityQueue ordered by f(n) = g(n) + h(n)
    frontier.push(problem.getStartState(), priority = heuristic(start))

    g_cost ← dictionary, default ∞
    g_cost[start] ← 0

    came_from ← dictionary  # for path reconstruction

    while frontier is not empty:
        current ← frontier.pop()   # lowest f(n)

        if problem.isGoalState(current):
            return reconstruct_path(came_from, current)

        for (successor, action, step_cost) in problem.getSuccessors(current):
            tentative_g ← g_cost[current] + step_cost

            if tentative_g < g_cost[successor]:
                g_cost[successor] ← tentative_g
                priority ← tentative_g + heuristic(successor)
                frontier.push(successor, priority)
                came_from[successor] ← (current, action)

    return FAILURE   # no path exists
```

### 6.2 Why the `g_cost` dictionary matters
Without tracking the best known cost to reach each state, you'd re-expand the same state
multiple times via different paths, potentially exponentially blowing up runtime. This
dictionary is effectively your "visited/closed set," but smarter — it allows *re-opening* a
state if you find a cheaper way to reach it later (important when heuristics are admissible
but not perfectly consistent).

### 6.3 Path reconstruction
`came_from` stores, for each state, which `(previous_state, action)` produced it. Once you hit
the goal, walk backward through `came_from` to the start, then reverse the collected actions to
get the forward plan.

### 6.4 Designing heuristics for each question

- **Single dot (Q1a):** Manhattan distance from current position to the dot. Admissible
  because it never overestimates grid movement cost, and walls can only make the *true* cost
  higher, never lower.

- **One of many dots (Q1b):** You need a heuristic that stays admissible regardless of *which*
  dot you ultimately pick. Two valid designs:
  - `h(n) = min(Manhattan(n, dot) for dot in remaining_dots)` — safe because it can't overestimate
    the distance to whichever dot turns out to be nearest.
  - Alternatively, decide the target dot *before* search begins (e.g., pick the closest reachable
    one via a cheap BFS distance check first), then run a single-target A* — simpler
    implementation, but requires you to explicitly handle unreachable dots (check reachability
    first, e.g. with a flood-fill/BFS over open squares).

- **All dots (Q1c):** This is the hard one — no simple admissible heuristic is both cheap to
  compute and tight. Two respectable approaches:
  - **Greedy re-planning:** repeatedly run "nearest remaining dot" A* until the board is clear.
    Fast, not globally optimal, but usually very good and simple to reason about in your report.
  - **State-augmented A\*:** state = `(position, frozenset(remaining_food_positions))`, with a
    heuristic like *"Manhattan distance to farthest remaining dot"* (a real, published Pac-Man
    heuristic) or *"cost of a Minimum Spanning Tree over remaining food + distance to nearest
    food"* — both are admissible and dramatically prune the huge combined state space. Given
    the timeout constraint, you likely need to balance completeness against runtime — this
    tradeoff is exactly what your report should analyze empirically (try both, measure time and
    score, discuss the tradeoff).

### 6.5 Common bugs to watch for
- Forgetting to check `isGoalState` on the state you just **popped**, not the one you push
  (checking too early can return a suboptimal path).
- Using a heuristic that's *not* admissible (e.g., Euclidean distance is fine, but anything that
  can overestimate — like adding a penalty term — breaks optimality guarantees).
- Off-by-one errors in walls: `getWalls()`/`hasWall(x, y)` — make sure your successor generation
  never proposes moving into a wall cell.
- Not handling the case where a dot is mathematically unreachable (isolated by walls) — your
  code should detect this and not hang until timeout.

---

## 7. Adversarial Search: Minimax & Alpha-Beta Deep Dive

### 7.1 Minimax — the foundation
Minimax assumes: Pac-Man (MAX) tries to maximize the evaluation score; every ghost (MIN) tries
to minimize it. At a fixed search depth, we can't see all the way to the end of the game, so we
cut off the search and estimate the value of a position with an **evaluation function** (Section 8).

```
function VALUE(state, depth, agentIndex):
    if depth == 0 or state.isWin() or state.isLose():
        return evaluationFunction(state)

    nextAgent ← (agentIndex + 1) mod state.getNumAgents()
    nextDepth ← depth - 1   if nextAgent == 0   else depth
    # depth only decreases once every agent (Pac-Man + all ghosts) has moved —
    # this is what "one ply / one full round" means in a multi-agent game.

    if agentIndex == 0:                     # Pac-Man: MAX
        return max( VALUE(state.generateSuccessor(0, a), nextDepth, nextAgent)
                    for a in state.getLegalActions(0) )
    else:                                    # a ghost: MIN
        return min( VALUE(state.generateSuccessor(agentIndex, a), nextDepth, nextAgent)
                    for a in state.getLegalActions(agentIndex) )
```

`getAction` then calls `VALUE` once per legal Pac-Man action at the root and returns the action
with the highest resulting value.

### 7.2 Why plain Minimax is too slow
Branching factor ≈ 4-5 legal moves per agent, and you may have Pac-Man + up to 4 ghosts = 5
agents per "round." A search depth of `d` rounds explores roughly `b^(agents × d)` nodes —
this explodes very fast. With a 30-second time budget, you need pruning.

### 7.3 Alpha-Beta pruning
Alpha-Beta computes the *exact same result* as Minimax but skips branches that can't possibly
affect the final decision.

- `alpha` = the best value MAX can guarantee so far, along the current path
- `beta` = the best value MIN can guarantee so far, along the current path
- **Prune** whenever `alpha ≥ beta` — this means the current branch can never be chosen by a
  rational opponent above it in the tree, so there's no point continuing to explore it.

```
function ALPHA_BETA(state, depth, agentIndex, alpha, beta):
    if depth == 0 or state.isWin() or state.isLose():
        return evaluationFunction(state)

    nextAgent ← (agentIndex + 1) mod state.getNumAgents()
    nextDepth ← depth - 1   if nextAgent == 0   else depth

    if agentIndex == 0:                       # MAX (Pac-Man)
        value ← -infinity
        for a in state.getLegalActions(0):
            value ← max(value, ALPHA_BETA(state.generateSuccessor(0, a),
                                           nextDepth, nextAgent, alpha, beta))
            alpha ← max(alpha, value)
            if alpha ≥ beta:
                break                          # beta cutoff — MIN parent won't allow this branch
        return value
    else:                                      # MIN (a ghost)
        value ← +infinity
        for a in state.getLegalActions(agentIndex):
            value ← min(value, ALPHA_BETA(state.generateSuccessor(agentIndex, a),
                                           nextDepth, nextAgent, alpha, beta))
            beta ← min(beta, value)
            if alpha ≥ beta:
                break                          # alpha cutoff — MAX parent won't allow this branch
        return value
```

**Critical detail:** `alpha` and `beta` must be **passed down and threaded through siblings**,
not reset for each child — that's what makes the pruning work across the whole subtree.

### 7.4 Practical engineering choices
- **Depth**: measured in full rounds (Pac-Man + every ghost = 1 "ply" in this formulation).
  Start shallow (depth 2) to confirm correctness, then increase while watching the 30-second
  budget.
- **Move ordering**: Alpha-Beta prunes more when good moves are explored first. A cheap trick:
  order successor actions by a quick heuristic estimate (e.g., closer-to-food first for Pac-Man)
  before recursing.
- **Iterative deepening** (optional, more advanced): run Alpha-Beta at depth 1, then 2, then 3…
  until you're close to the time budget, always keeping the best result from the last *completed*
  depth. This protects you from a hard timeout mid-search.
- **Terminal states**: always check `isWin()`/`isLose()` before recursing further — don't burn
  search budget on a subtree that's already decided.

---

## 8. Evaluation Functions

This is the most *creative* and highest-leverage part of Part 2 — Alpha-Beta is a fixed
algorithm, but your evaluation function is where your agent's "personality" and skill come from.

A good evaluation function is a **weighted combination of features**:

```
score(state) = w1 * state.getScore()
             + w2 * (1 / (closest_food_distance + 1))
             + w3 * (closest_ghost_distance)              # further from ghosts = safer
             + w4 * (number_of_remaining_food) * -1        # fewer dots left = better
             + w5 * (bonus if a scared ghost is nearby and chaseable)
             - large_penalty if immediate death is likely
```

**Design process:**
1. Start with just `getScore()` — establishes a working baseline.
2. Add a food-distance term — encourages movement toward food instead of standing still.
3. Add a ghost-distance term — encourages evasion. Be careful: this needs asymmetric handling
   for *scared* ghosts (chase them, don't flee).
4. Tune weights empirically by running games and observing behavior (e.g., agent standing still
   near a wall = food term too weak; agent walking into ghosts = ghost term too weak).
5. Log/print feature values during development to sanity check them before trusting the weighted
   sum.

**Common pitfall:** don't let the "closest food distance" heuristic use Manhattan distance
through walls if it meaningfully misleads the agent (e.g., a wall directly between Pac-Man and
a very close-looking dot). A BFS-based true maze distance is more accurate but more expensive —
this speed/accuracy tradeoff is worth explicitly discussing in your writeup.

---

## 9. Testing, Debugging & Benchmarking

### 9.1 Useful command-line flags
```
-l LAYOUT       # which map to load
-p AGENT_TYPE   # which agent controls Pac-Man
-t              # text-only graphics (keeps full history visible, unlike GUI)
-q              # quiet mode, minimal output
-n NUM_GAMES    # run multiple games back to back
-c              # enable exception/timeout catching (use this while debugging!)
-o              # write a log file to logs/
--timeout=N     # max seconds per agent decision
-z ZOOM         # graphics zoom level
```

### 9.2 A disciplined debugging workflow
1. **Start on the smallest possible layout.** If your A* fails on `tinyMaze`, it will fail
   everywhere — fix it there first.
2. **Print intermediate state.** In your solver, temporarily print `len(frontier)`,
   `g_cost[current]`, and the current position each iteration to confirm the search is
   converging, not looping.
3. **Verify heuristic admissibility manually.** Pick 3–4 states, compute `h(n)` by hand, and
   confirm it's ≤ the actual shortest path length you can count by eye on a small layout.
4. **Use `-t` text mode** for Part 2 debugging — you can scroll back through the whole game,
   which the GUI doesn't allow.
5. **Isolate node-expansion counts** (for Q1b's marking criterion) by incrementing a counter
   each time you pop a node from the frontier — log it at the end of the search.
6. **For Alpha-Beta**, first test *without* pruning (plain Minimax) on a tiny layout with 1
   ghost and a shallow depth, confirm behavior is sane, then add pruning and confirm the chosen
   action doesn't change (only the runtime should improve).

### 9.3 Benchmarking script pattern
Keep a small table (Markdown or CSV) as you iterate:

| Layout | Algorithm/Heuristic | Node Expansions | Solution Cost | Time (s) |
|---|---|---|---|---|
| q1a_tinyMaze | A* + Manhattan | 12 | 8 | 0.01 |
| q1b_tinyCorners | A* + min-dot Manhattan | 45 | 14 | 0.03 |
| ... | ... | ... | ... | ... |

This table becomes the empirical backbone of your report/README, and demonstrates rigor to
anyone reviewing your portfolio.

---

## 10. Professional GitHub Repository Structure

### 10.0 Full combined structure (existing game code + your additions)

This merges the Pac-Man engine's own layout with everything you should add around it. Folders
marked **(engine)** already exist from the base game code; folders marked **(add)** are yours
to create.

```
pacman-ai/
│
├── README.md                     (add)  ← elevator pitch, GIF, architecture, results, how-to-run
├── LICENSE                       (add)  ← MIT recommended for a portfolio project
├── .gitignore                    (add)  ← see contents below
├── requirements.txt              (add)  ← pinned deps: numpy, scipy, pandas, tqdm, tabulate
├── VERSION                       (engine)
├── evaluator.py                  (engine) ← run this to self-score across all layouts
├── pacman.py                     (engine) ← core game loop, GameState class
├── game.py                       (engine) ← Agent base class, AgentState, Directions
├── util.py                       (engine) ← Stack, Queue, PriorityQueue data structures
├── graphicsDisplay.py            (engine)
├── graphicsUtils.py              (engine)
├── textDisplay.py                (engine)
├── layout.py                     (engine)
├── projectParams.py              (engine)
├── testParser.py                 (engine)
│
├── agents/                       (engine, you edit q2Agent.py)
│   ├── directionalGhost.py
│   ├── ghostAgents.py
│   ├── goWestAgent.py
│   ├── greedyAgent.py
│   ├── keyboardAgents.py
│   ├── pacmanAgents.py
│   ├── q2Agent.py                ← YOU implement Alpha-Beta getAction() here
│   ├── randomGhost.py
│   └── searchAgents.py           ← base SearchAgent class (don't modify)
│
├── problems/                     (engine, you fill in all three)
│   ├── q1a_problem.py            ← getStartState / isGoalState / getSuccessors
│   ├── q1b_problem.py
│   └── q1c_problem.py
│
├── solvers/                      (engine, you fill in all three)
│   ├── q1a_solver.py             ← A* implementation
│   ├── q1b_solver.py             ← A* + multi-dot heuristic
│   └── q1c_solver.py             ← full-clear search/approximation
│
├── layouts/                      (engine) ← sample .lay maze files, prefixed q1a_/q1b_/q1c_/q2_
│
├── logs/                         (engine) ← generated by -o flag; gitignored, not committed
│
├── docs/                         (add)
│   ├── architecture.md           ← system diagram + design rationale (Section 3 of guide)
│   ├── algorithms.md             ← your write-up of A* and Alpha-Beta design decisions
│   └── benchmarks.md             ← results tables: node expansions, path cost, runtime
│
├── tests/                        (add)
│   ├── test_q1a_solver.py        ← unit tests on tiny layouts, known-optimal path length
│   ├── test_q1b_solver.py
│   ├── test_q1c_solver.py
│   └── test_q2_agent.py          ← sanity checks: legal actions only, no crashes at depth N
│
├── scripts/                      (add, optional but nice)
│   ├── run_benchmarks.sh         ← loops evaluator.py across configs, saves results to docs/
│   └── generate_report_table.py  ← turns logs/benchmark output into a Markdown table
│
└── .github/
    └── workflows/
        └── ci.yml                (add) ← auto-run tests/evaluator.py on every push
```

### 10.0.1 Separate repo for the deployable demo (Section 11)

Keep this **entirely separate** from the graded/engine repo above — a clean public portfolio
piece with no coupling to restricted course code:

```
pacman-ai-demo/
├── README.md                     ← link to live demo, GIF, tech stack summary
├── LICENSE
├── .gitignore
├── Dockerfile                    ← for Cloud Run / container deployment
├── requirements.txt
├── backend/
│   ├── main.py                   ← FastAPI app, exposes POST /solve, POST /play
│   ├── search.py                 ← your own reimplementation of A* (original, not course code)
│   ├── adversarial.py            ← your own reimplementation of Alpha-Beta
│   └── layouts/                  ← your own original maze files
├── frontend/
│   ├── index.html
│   ├── app.js                    ← canvas rendering of the returned move trace
│   └── style.css
└── .github/
    └── workflows/
        └── deploy.yml            ← auto-deploy to Cloud Run / GitHub Pages on push to main
```

### 10.0.2 Suggested `.gitignore` contents

```
__pycache__/
*.pyc
*.pyo
logs/
.DS_Store
.env
venv/
.vscode/
.idea/
*.egg-info/
```

### 10.1 README essentials
- One-paragraph elevator pitch: what the project does and why it's interesting
- A GIF or screenshot of the agent playing
- Architecture diagram (reuse Section 3)
- "Algorithms implemented" section with a short explanation of A* and Alpha-Beta in your own
  words
- Benchmark results table
- How to run it locally (`conda create`, `pip install -r requirements.txt`, run commands)
- What you'd improve next (shows growth mindset to reviewers)

### 10.2 Git hygiene
- Commit in small, logical chunks: `feat: implement A* for q1a`, `fix: correct heuristic
  admissibility bug`, `docs: add benchmark table` — this commit history *is* part of your
  portfolio; reviewers read it.
- Tag milestone commits (`git tag v0.1-q1a-complete`) so your progression is easy to browse.
- Use a `dev` branch and merge to `main` via pull requests, even solo — it's a habit that reads
  as professional and gives you a place to write PR descriptions summarizing each change.

### 10.3 Example CI workflow (`.github/workflows/ci.yml`)
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/ -v
```

---

## 11. Free-Tier Cloud Deployment

Because the graded repo itself has usage restrictions on how it's shared/hosted, the cleanest
path is to build a **standalone visualizer/demo** in a separate public repo once your learning
is done — e.g., a small web app that lets visitors watch your search agent solve mazes, or your
Alpha-Beta agent play against ghosts, in the browser.

### 11.1 Suggested architecture for the demo
```
Browser (static frontend: HTML/JS canvas or React)
        │  HTTP request (choose layout / algorithm)
        ▼
Backend API (FastAPI or Flask, Python)
        │  runs your search/adversarial agent, returns move sequence or game trace as JSON
        ▼
Frontend renders the trace as an animated grid
```

### 11.2 Google Cloud Run (recommended — generous free tier, simplest for Python)
1. Wrap your agent logic in a small FastAPI app exposing e.g. `POST /solve` returning the move
   sequence and stats (nodes expanded, path cost).
2. Write a `Dockerfile`:
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
   ```
3. `gcloud builds submit --tag gcr.io/YOUR_PROJECT/pacman-demo`
4. `gcloud run deploy pacman-demo --image gcr.io/YOUR_PROJECT/pacman-demo --platform managed --allow-unauthenticated`
5. Cloud Run's free tier (2 million requests/month, generous CPU-seconds) comfortably covers a
   portfolio demo with low traffic.

### 11.3 AWS alternative (Lambda + API Gateway, or a free-tier EC2 t2.micro)
- **Lambda**: package your agent code with the `aws-lambda-python` runtime; API Gateway exposes
  it as HTTP. Free tier: 1M requests/month + 400,000 GB-seconds compute — plenty for a demo.
- **EC2 t2.micro**: 750 hours/month free for 12 months on a new account — simplest if you want a
  persistently running server rather than serverless, but requires you to manage the instance
  (security groups, systemd service, etc.).

### 11.4 Hosting the static frontend
- GitHub Pages (completely free, zero config for a static HTML/JS/React build) is the easiest
  option — point it at your demo repo's `gh-pages` branch or `/docs` folder.
- Have the frontend call your Cloud Run/Lambda backend URL via `fetch()`.

### 11.5 What to put in the portfolio write-up
- Link to the live demo
- Short video/GIF of it running
- A "Lessons learned" section: heuristic design tradeoffs, pruning performance gains you
  measured, evaluation-function tuning process — this narrative is what actually impresses
  reviewers, more than the code itself.

---

## 12. Writing Effective Prompts

When you bring your own code back for review, or want help extending the visualizer/deployment
layer, prompts that get the most useful help share a pattern: **state the goal, show the
relevant code, name the specific symptom or question.**

Good examples:
- *"Here's my `q1a_solver.py` A* implementation [paste code]. On `tinyMaze` it returns a path
  of length 12 but I believe optimal is 8 — can you help me find where the bug is?"*
- *"I've implemented Alpha-Beta in `q2Agent.py` [paste code]. It runs correctly but times out
  at depth 3 with 4 ghosts. What are standard techniques to make this faster without changing
  the algorithm's correctness?"*
- *"Review this evaluation function for style and correctness, not gameplay tuning: [paste
  code]. Am I handling the 'scared ghost' state correctly?"*
- *"Here's my Dockerfile and Cloud Run deploy command — deployment is failing with [error].
  What's likely wrong?"*
- *"Help me write a GitHub Actions workflow that runs my test suite and fails the build if
  evaluator.py reports below X% average score."*

Weak prompts to avoid:
- *"Fix my code"* with no code attached, or no description of expected vs. actual behavior.
- *"Write the solver for me"* — for graded/learning components, ask for explanation +
  debugging help instead, so the understanding stays with you.
- Vague asks like *"make it better"* without specifying which axis (speed? correctness? code
  clarity? memory usage?).

**A reusable template:**
```
Context: [what file / what part of the project]
Goal: [what you're trying to achieve]
Current behavior: [what happens now, with code/output]
Expected behavior: [what should happen]
Specific question: [the narrowest possible version of what's blocking you]
```

---

## 13. Glossary

- **State space** — the set of all configurations reachable from the start via legal actions.
- **Frontier / open set** — the set of discovered-but-not-yet-expanded nodes in a search.
- **Admissible heuristic** — never overestimates true cost to goal; required for A* optimality.
- **Consistent heuristic** — a stronger property than admissibility; guarantees no node needs
  re-expansion.
- **Branching factor** — average number of successors per state; drives exponential blowup.
- **Ply** — one full round of moves by all agents in a multi-agent game.
- **Minimax value** — the game-theoretically optimal value of a state assuming perfect play by
  both MAX and MIN.
- **Alpha-Beta pruning** — an optimization of Minimax that skips provably irrelevant branches
  without changing the result.
- **Evaluation function** — a heuristic estimate of how good a non-terminal state is, used when
  search must be cut off before reaching a true terminal state.
- **Iterative deepening** — repeatedly running search at increasing depth limits, keeping the
  best complete result, to gracefully handle time budgets.

---

*This guide is meant to be read alongside your own code — the pseudocode here should be
translated into your own implementation, in your own words, so that when you're asked to
explain your design (in an interview, or in a written report), the understanding is genuinely
yours.*
