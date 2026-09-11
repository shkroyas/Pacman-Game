"""
Generate demo GIF and video frames for the Pacman AI project.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PIL import Image, ImageDraw, ImageFont
import subprocess
import json
import math
from layout import Layout, GameState
from agents.q2Agent import Q2Agent
from solvers.q1a_solver import a_star_solver, manhattan_heuristic
from solvers.q1b_solver import a_star_multi_solver, min_food_heuristic
from problems.q1a_problem import Q1aProblem
from problems.q1b_problem import Q1bProblem
from agents.ghostAgents import DirectionalGhost
from game import Directions

CELL_SIZE = 24
CELLS_X = 19
CELLS_Y = 15

COLORS = {
    'bg': (22, 33, 62),
    'wall': (26, 26, 46),
    'wall_highlight': (40, 40, 70),
    'floor': (30, 42, 74),
    'food': (233, 69, 96),
    'capsule': (15, 52, 96),
    'pacman': (245, 197, 24),
    'ghost_red': (233, 69, 96),
    'ghost_pink': (255, 105, 180),
    'ghost_cyan': (0, 255, 255),
    'ghost_orange': (255, 165, 0),
    'path': (245, 197, 24, 80),
    'text': (255, 255, 255),
    'accent': (245, 197, 24),
}

GHOST_COLORS = [COLORS['ghost_red'], COLORS['ghost_pink'], COLORS['ghost_cyan'], COLORS['ghost_orange']]


def get_font(size=16):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except:
            return ImageFont.load_default()


def draw_cell(draw, x, y, color, size=CELL_SIZE):
    px, py = x * size, y * size
    draw.rectangle([px, py, px + size - 1, py + size - 1], fill=color)


def draw_pacman(draw, x, y, frame=0, size=CELL_SIZE):
    px, py = x * size + size // 2, y * size + size // 2
    r = size // 2 - 2
    mouth_angle = 0.3 + 0.15 * math.sin(frame * 0.5)
    draw.ellipse([px - r, py - r, px + r, py + r], fill=COLORS['pacman'])
    angle = 0
    x1 = px + int(r * math.cos(angle - mouth_angle))
    y1 = py + int(r * math.sin(angle - mouth_angle))
    x2 = px + int(r * math.cos(angle + mouth_angle))
    y2 = py + int(r * math.sin(angle + mouth_angle))
    draw.polygon([(px, py), (x1, y1), (x2, y2)], fill=COLORS['bg'])


def draw_ghost(draw, x, y, color, frame=0, size=CELL_SIZE):
    px, py = x * size + size // 2, y * size + size // 2
    r = size // 2 - 2
    draw.ellipse([px - r, py - r - 2, px + r, py + r - 2], fill=color)
    wobble = 2 * math.sin(frame * 0.8)
    points = []
    for i in range(8):
        angle = math.pi + (i / 7) * math.pi
        rx = px + int(r * math.cos(angle))
        ry = py + int(r + wobble * (-1 if i % 2 == 0 else 1))
        points.append((rx, ry))
    points.append((px + r, py + r - 2))
    points.append((px - r, py + r - 2))
    draw.polygon(points, fill=color)
    eye_x = px - 3
    draw.ellipse([eye_x - 3, py - r + 2, eye_x + 3, py - r + 8], fill=(255, 255, 255))
    draw.ellipse([eye_x + 4, py - r + 2, eye_x + 10, py - r + 8], fill=(255, 255, 255))
    draw.ellipse([eye_x - 1, py - r + 4, eye_x + 2, py - r + 7], fill=(20, 20, 80))
    draw.ellipse([eye_x + 6, py - r + 4, eye_x + 9, py - r + 7], fill=(20, 20, 80))


def draw_path_highlight(draw, positions, frame=0, size=CELL_SIZE):
    for i, (x, y) in enumerate(positions):
        alpha = max(30, 120 - i * 3)
        color = (245, 197, 24, alpha)
        px, py = x * size + 2, y * size + 2
        draw.rectangle([px, py, px + size - 5, py + size - 5], fill=color[:3])


def render_layout(layout, pacman_pos=None, ghost_positions=None, food_positions=None,
                  path_positions=None, frame=0, width=None, height=None, score=0, status=""):
    if width is None:
        width = layout.width * CELL_SIZE
    if height is None:
        height = layout.height * CELL_SIZE + 50

    img = Image.new('RGB', (width, height), COLORS['bg'])
    draw = ImageDraw.Draw(img)

    for x in range(layout.width):
        for y in range(layout.height):
            drawY = layout.height - 1 - y
            if layout.walls.is_wall(x, y):
                draw_cell(draw, x, drawY, COLORS['wall'])
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < layout.width and 0 <= ny < layout.height:
                        if not layout.walls.is_wall(nx, ny):
                            draw.rectangle(
                                [x * CELL_SIZE + 1, drawY * CELL_SIZE + 1,
                                 (x + 1) * CELL_SIZE - 1, (drawY + 1) * CELL_SIZE - 1],
                                fill=COLORS['wall_highlight']
                            )
            elif layout.food.has_food(x, y):
                draw_cell(draw, x, drawY, COLORS['floor'])
                cx, cy = x * CELL_SIZE + CELL_SIZE // 2, drawY * CELL_SIZE + CELL_SIZE // 2
                draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=COLORS['food'])
            elif (x, y) in layout.capsules:
                draw_cell(draw, x, drawY, COLORS['floor'])
                cx, cy = x * CELL_SIZE + CELL_SIZE // 2, drawY * CELL_SIZE + CELL_SIZE // 2
                draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=COLORS['capsule'])
            else:
                draw_cell(draw, x, drawY, COLORS['floor'])

    if path_positions:
        draw_path_highlight(draw, path_positions, frame)

    if ghost_positions:
        for i, (gx, gy) in enumerate(ghost_positions):
            drawY = layout.height - 1 - gy
            color = GHOST_COLORS[i % len(GHOST_COLORS)]
            draw_ghost(draw, gx, drawY, color, frame)

    if pacman_pos:
        px, py = pacman_pos
        drawY = layout.height - 1 - py
        draw_pacman(draw, px, drawY, frame)

    font = get_font(18)
    title_font = get_font(24)
    y_offset = layout.height * CELL_SIZE + 10

    draw.text((10, y_offset), f"Score: {score}", fill=COLORS['accent'], font=font)
    if status:
        draw.text((width - 200, y_offset), status, fill=COLORS['text'], font=font)

    return img


def generate_astar_frames():
    print("Generating A* search demo frames...")
    layout = Layout.get_layout('mediumMaze')
    state = GameState(layout)
    problem = Q1aProblem(state)
    actions = a_star_solver(problem, manhattan_heuristic)

    frames = []
    positions = [state.get_pacman_position()]

    path_so_far = []
    for i, action in enumerate(actions):
        pos = positions[-1]
        dx, dy = action.get_vector()
        new_pos = (pos[0] + dx, pos[1] + dy)
        positions.append(new_pos)
        path_so_far.append(new_pos)

        img = render_layout(
            layout,
            pacman_pos=new_pos,
            path_positions=path_so_far,
            frame=i,
            score=i * 10,
            status=f"A* Step {i+1}/{len(actions)}"
        )
        frames.append(img)

    for i in range(5):
        img = render_layout(
            layout,
            pacman_pos=positions[-1],
            path_positions=path_so_far,
            frame=len(actions) + i,
            score=len(actions) * 10,
            status="Goal Reached!"
        )
        frames.append(img)

    return frames


def generate_playback_frames():
    print("Generating Alpha-Beta game play frames...")
    layout = Layout.get_layout('q2Classic')
    state = GameState(layout)
    agent = Q2Agent(depth=1)
    ghosts = [DirectionalGhost(i) for i in range(1, layout.num_agents)]

    frames = []
    max_moves = 30

    for move_num in range(max_moves):
        pacman_pos = state.get_pacman_position()
        ghost_pos = state.get_ghost_positions()
        food_pos = state.get_food_positions()

        img = render_layout(
            layout,
            pacman_pos=pacman_pos,
            ghost_positions=ghost_pos,
            food_positions=food_pos,
            frame=move_num,
            score=state.get_score(),
            status=f"Move {move_num+1} | Alpha-Beta Depth=1"
        )
        frames.append(img)

        if state.is_win() or state.is_lose():
            break

        pacman_action = agent.get_action(state)
        state = state.generate_successor(0, pacman_action)

        for ghost in ghosts:
            ghost_action = ghost.get_action(state)
            state = state.generate_successor(ghost.index, ghost_action)

    final_status = "WIN!" if state.is_win() else "Game Over"
    for i in range(8):
        img = render_layout(
            layout,
            pacman_pos=state.get_pacman_position(),
            ghost_positions=state.get_ghost_positions(),
            frame=max_moves + i,
            score=state.get_score(),
            status=final_status
        )
        frames.append(img)

    return frames


def generate_title_frame():
    img = Image.new('RGB', (CELLS_X * CELL_SIZE, CELLS_Y * CELL_SIZE + 50), COLORS['bg'])
    draw = ImageDraw.Draw(img)

    title_font = get_font(36)
    sub_font = get_font(20)
    small_font = get_font(16)

    cx = (CELLS_X * CELL_SIZE) // 2
    cy = (CELLS_Y * CELL_SIZE) // 2

    draw.text((cx - 160, cy - 60), "PACMAN AI", fill=COLORS['pacman'], font=title_font)
    draw.text((cx - 180, cy - 10), "A* Search + Alpha-Beta Pruning", fill=COLORS['text'], font=sub_font)
    draw.text((cx - 100, cy + 30), "Interactive Demo", fill=COLORS['accent'], font=small_font)

    draw_pacman(draw, 2, 2, frame=0)
    draw_ghost(draw, 14, 2, COLORS['ghost_red'], frame=0)
    draw_ghost(draw, 15, 2, COLORS['ghost_pink'], frame=0)

    return img


def generate_algo_comparison_frame():
    img = Image.new('RGB', (CELLS_X * CELL_SIZE, CELLS_Y * CELL_SIZE + 50), COLORS['bg'])
    draw = ImageDraw.Draw(img)

    title_font = get_font(24)
    sub_font = get_font(18)
    small_font = get_font(14)

    left_x = 20
    right_x = CELLS_X * CELL_SIZE // 2 + 20

    draw.text((left_x, 20), "A* Search", fill=COLORS['accent'], font=title_font)
    draw.text((left_x, 55), "- Single agent pathfinding", fill=COLORS['text'], font=small_font)
    draw.text((left_x, 78), "- Manhattan distance heuristic", fill=COLORS['text'], font=small_font)
    draw.text((left_x, 101), "- Optimal path guaranteed", fill=COLORS['text'], font=small_font)
    draw.text((left_x, 124), "- Admissible heuristic", fill=COLORS['text'], font=small_font)

    draw.line([(CELLS_X * CELL_SIZE // 2, 15), (CELLS_X * CELL_SIZE // 2, 160)], fill=COLORS['wall_highlight'], width=2)

    draw.text((right_x, 20), "Alpha-Beta Pruning", fill=COLORS['accent'], font=title_font)
    draw.text((right_x, 55), "- Adversarial game-tree search", fill=COLORS['text'], font=small_font)
    draw.text((right_x, 78), "- Pac-Man vs Ghost opponents", fill=COLORS['text'], font=small_font)
    draw.text((right_x, 101), "- Minimax with pruning", fill=COLORS['text'], font=small_font)
    draw.text((right_x, 124), "- Evaluation function driven", fill=COLORS['text'], font=small_font)

    draw.text((left_x, 180), "Score: f(n) = g(n) + h(n)", fill=COLORS['pacman'], font=sub_font)
    draw.text((left_x, 210), "Heuristic: |x1-x2| + |y1-y2|", fill=COLORS['text'], font=small_font)

    draw.text((right_x, 180), "Score: MAX player maximizes", fill=COLORS['pacman'], font=sub_font)
    draw.text((right_x, 210), "MIN ghosts minimize score", fill=COLORS['text'], font=small_font)

    y = 260
    draw.text((left_x, y), "Best for: Maze navigation", fill=COLORS['food'], font=small_font)
    draw.text((right_x, y), "Best for: Ghost avoidance", fill=COLORS['food'], font=small_font)

    return img


def save_frames(frames, output_dir, prefix="frame"):
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    for i, frame in enumerate(frames):
        path = os.path.join(output_dir, f"{prefix}_{i:04d}.png")
        frame.save(path)
        paths.append(path)
    return paths


def create_gif(frames, output_path, duration=200):
    if not frames:
        return
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=True,
    )
    print(f"GIF saved: {output_path}")


def create_video(frames_dir, output_path, fps=10):
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(fps),
        '-i', os.path.join(frames_dir, 'frame_%04d.png'),
        '-vf', 'scale=480:-1',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '23',
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Video saved: {output_path}")
    else:
        print(f"Video error: {result.stderr[-200:]}")


if __name__ == '__main__':
    output_base = os.path.join(os.path.dirname(__file__), '..', 'docs')

    title = generate_title_frame()
    algo_comp = generate_algo_comparison_frame()
    astar_frames = generate_astar_frames()
    play_frames = generate_playback_frames()

    all_demo_frames = [title, algo_comp] + astar_frames + play_frames

    print(f"\nTotal frames generated: {len(all_demo_frames)}")

    frames_dir = os.path.join(output_base, 'demo_frames')
    save_frames(all_demo_frames, frames_dir, "frame")

    create_gif(astar_frames[:30], os.path.join(output_base, 'pacman_astar_demo.gif'), duration=250)

    create_gif(play_frames[:40], os.path.join(output_base, 'pacman_gameplay_demo.gif'), duration=200)

    create_video(frames_dir, os.path.join(output_base, 'pacman_ai_demo.mp4'), fps=8)

    readme_frames = astar_frames[:15] + play_frames[:15]
    create_gif(readme_frames, os.path.join(output_base, 'pacman_demo.gif'), duration=300)

    print("\nDone! Files saved in docs/")
