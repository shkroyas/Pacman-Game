"""
FastAPI backend for Pacman AI demo.
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from layout import Layout, GameState
from agents.q2Agent import Q2Agent
from solvers.q1a_solver import a_star_solver, manhattan_heuristic
from solvers.q1b_solver import a_star_multi_solver, min_food_heuristic
from solvers.q1c_solver import a_star_full_solver
from problems.q1a_problem import Q1aProblem
from problems.q1b_problem import Q1bProblem
from problems.q1c_problem import Q1cProblem
from game import Directions

app = FastAPI(title="Pacman AI Demo", version="1.0.0")

frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


class SolveRequest(BaseModel):
    layout_name: str = "tinyMaze"
    algorithm: str = "astar"
    depth: int = 2


class Move(BaseModel):
    x: int
    y: int
    direction: str


class SolveResponse(BaseModel):
    moves: List[Move]
    score: int
    nodes_expanded: int
    path_cost: int
    win: bool
    layout: str
    iterations: int


class PlayRequest(BaseModel):
    layout_name: str = "q2Classic"
    depth: int = 2
    max_moves: int = 200


class PlayResponse(BaseModel):
    frames: List[dict]
    final_score: int
    win: bool
    total_moves: int


@app.get("/")
async def root():
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/api/layouts")
async def get_layouts():
    layout_dir = os.path.join(os.path.dirname(__file__), '..', 'layouts')
    layouts = []
    for f in os.listdir(layout_dir):
        if f.endswith('.lay'):
            name = f[:-4]
            layouts.append(name)
    return {"layouts": sorted(layouts)}


@app.post("/api/solve", response_model=SolveResponse)
async def solve(request: SolveRequest):
    try:
        layout = Layout.get_layout(request.layout_name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Layout '{request.layout_name}' not found")

    state = GameState(layout)

    algorithm = request.algorithm

    def _run_solve_sync():
        if algorithm == "astar":
            problem = Q1aProblem(state)
            return a_star_solver(problem, manhattan_heuristic)
        elif algorithm == "astar_multi":
            problem = Q1bProblem(state)
            return a_star_multi_solver(problem, min_food_heuristic)
        elif algorithm == "astar_full":
            problem = Q1cProblem(state)
            return a_star_full_solver(problem)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    try:
        actions = await asyncio.wait_for(
            asyncio.to_thread(_run_solve_sync),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Solver timed out (10s limit)")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    moves = []
    current_state = state
    for action in actions:
        pos = current_state.get_pacman_position()
        dx, dy = action.get_vector()
        moves.append(Move(
            x=int(pos[0]),
            y=int(pos[1]),
            direction=action.value
        ))
        current_state = current_state.generate_successor(0, action)

    return SolveResponse(
        moves=moves,
        score=current_state.get_score(),
        nodes_expanded=0,
        path_cost=len(actions),
        win=current_state.is_win(),
        layout=layout.to_str(),
        iterations=len(actions)
    )


@app.post("/api/play", response_model=PlayResponse)
async def play(request: PlayRequest):
    try:
        layout = Layout.get_layout(request.layout_name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Layout '{request.layout_name}' not found")

    state = GameState(layout)
    agent = Q2Agent(depth=request.depth)

    from agents.ghostAgents import DirectionalGhost
    ghosts = [DirectionalGhost(i) for i in range(1, layout.num_agents)]

    frames = []
    max_moves = request.max_moves
    walls_sent = False

    for move_num in range(max_moves):
        current_state_dict = {
            "pacman": list(state.get_pacman_position()),
            "ghosts": [list(g) for g in state.get_ghost_positions()],
            "food": [list(f) for f in state.get_food_positions()],
            "capsules": [list(c) for c in state.get_capsules()],
            "score": state.get_score(),
        }
        if not walls_sent:
            current_state_dict["walls"] = [
                [x, y]
                for x in range(state.get_walls().width)
                for y in range(state.get_walls().height)
                if state.get_walls().is_wall(x, y)
            ]
            walls_sent = True
        frames.append(current_state_dict)

        if state.is_win() or state.is_lose():
            break

        pacman_action = agent.get_action(state)
        state = state.generate_successor(0, pacman_action)

        for ghost in ghosts:
            ghost_action = ghost.get_action(state)
            state = state.generate_successor(ghost.index, ghost_action)

    return PlayResponse(
        frames=frames,
        final_score=state.get_score(),
        win=state.is_win(),
        total_moves=len(frames)
    )


@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
