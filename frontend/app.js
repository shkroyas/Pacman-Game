const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');

const CELL_SIZE = 20;
const COLORS = {
    wall: '#1a1a2e',
    floor: '#16213e',
    food: '#e94560',
    capsule: '#0f3460',
    pacman: '#f5c518',
    ghost: '#e94560',
    ghostScared: '#533483',
    path: 'rgba(245, 197, 24, 0.3)'
};

let currentLayout = null;
let animationFrame = null;
let moveIndex = 0;
let moves = [];
let gameFrames = [];
let frameIndex = 0;

async function loadLayouts() {
    try {
        const response = await fetch('/api/layouts');
        const data = await response.json();
        const select = document.getElementById('layout-select');
        select.innerHTML = '';
        data.layouts.forEach(layout => {
            const option = document.createElement('option');
            option.value = layout;
            option.textContent = layout;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load layouts:', error);
    }
}

function parseLayout(layoutStr) {
    const lines = layoutStr.split('\n');
    const height = lines.length;
    const width = Math.max(...lines.map(l => l.length));

    const walls = [];
    const food = [];
    const capsules = [];
    let pacman = null;
    const ghosts = [];

    for (let y = 0; y < height; y++) {
        for (let x = 0; x < lines[y].length; x++) {
            const ch = lines[y][x];
            const drawY = height - 1 - y;

            if (ch === '%') {
                walls.push([x, drawY]);
            } else if (ch === '.') {
                food.push([x, drawY]);
            } else if (ch === 'o') {
                capsules.push([x, drawY]);
            } else if (ch === 'P') {
                pacman = [x, drawY];
            } else if (ch >= '1' && ch <= '8') {
                ghosts.push({pos: [x, drawY], index: parseInt(ch)});
            }
        }
    }

    return { walls, food, capsules, pacman, ghosts, width, height };
}

function drawLayout(layout) {
    ctx.fillStyle = COLORS.floor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    layout.walls.forEach(([x, y]) => {
        ctx.fillStyle = COLORS.wall;
        ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
    });

    layout.food.forEach(([x, y]) => {
        ctx.fillStyle = COLORS.food;
        ctx.beginPath();
        ctx.arc(x * CELL_SIZE + CELL_SIZE / 2, y * CELL_SIZE + CELL_SIZE / 2, 3, 0, Math.PI * 2);
        ctx.fill();
    });

    layout.capsules.forEach(([x, y]) => {
        ctx.fillStyle = COLORS.capsule;
        ctx.beginPath();
        ctx.arc(x * CELL_SIZE + CELL_SIZE / 2, y * CELL_SIZE + CELL_SIZE / 2, 6, 0, Math.PI * 2);
        ctx.fill();
    });
}

function drawPacman(x, y) {
    ctx.fillStyle = COLORS.pacman;
    ctx.beginPath();
    ctx.arc(x * CELL_SIZE + CELL_SIZE / 2, y * CELL_SIZE + CELL_SIZE / 2, CELL_SIZE / 2 - 2, 0, Math.PI * 2);
    ctx.fill();
}

function drawGhost(x, y, scared = false) {
    ctx.fillStyle = scared ? COLORS.ghostScared : COLORS.ghost;
    ctx.beginPath();
    ctx.arc(x * CELL_SIZE + CELL_SIZE / 2, y * CELL_SIZE + CELL_SIZE / 2 - 2, CELL_SIZE / 2 - 2, Math.PI, 0);
    ctx.lineTo(x * CELL_SIZE + CELL_SIZE + 2, y * CELL_SIZE + CELL_SIZE + 2);
    ctx.lineTo(x * CELL_SIZE - 2, y * CELL_SIZE + CELL_SIZE + 2);
    ctx.closePath();
    ctx.fill();
}

function drawPath(moves) {
    ctx.fillStyle = COLORS.path;
    moves.forEach(move => {
        ctx.fillRect(move.x * CELL_SIZE + 2, move.y * CELL_SIZE + 2, CELL_SIZE - 4, CELL_SIZE - 4);
    });
}

function drawFrame(frame) {
    ctx.fillStyle = COLORS.floor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    frame.walls.forEach(([x, y]) => {
        ctx.fillStyle = COLORS.wall;
        ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
    });

    frame.food.forEach(([x, y]) => {
        ctx.fillStyle = COLORS.food;
        ctx.beginPath();
        ctx.arc(x * CELL_SIZE + CELL_SIZE / 2, y * CELL_SIZE + CELL_SIZE / 2, 3, 0, Math.PI * 2);
        ctx.fill();
    });

    frame.capsules.forEach(([x, y]) => {
        ctx.fillStyle = COLORS.capsule;
        ctx.beginPath();
        ctx.arc(x * CELL_SIZE + CELL_SIZE / 2, y * CELL_SIZE + CELL_SIZE / 2, 6, 0, Math.PI * 2);
        ctx.fill();
    });

    frame.ghosts.forEach(ghost => {
        drawGhost(ghost[0], ghost[1]);
    });

    drawPacman(frame.pacman[0], frame.pacman[1]);

    document.getElementById('score-value').textContent = frame.score;
}

async function solveMaze() {
    const layoutName = document.getElementById('layout-select').value;
    const algorithm = document.getElementById('algorithm-select').value;
    const depth = parseInt(document.getElementById('depth-input').value);

    document.getElementById('status-value').textContent = 'Solving...';
    document.getElementById('solve-btn').disabled = true;

    try {
        const response = await fetch('/api/solve', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({layout_name: layoutName, algorithm, depth})
        });

        const data = await response.json();

        moves = data.moves;
        currentLayout = parseLayout(data.layout);
        moveIndex = 0;

        document.getElementById('score-value').textContent = data.score;
        document.getElementById('moves-value').textContent = data.path_cost;
        document.getElementById('status-value').textContent = data.win ? 'WIN!' : 'Solved';

        animateSolve();
    } catch (error) {
        document.getElementById('status-value').textContent = 'Error: ' + error.message;
    } finally {
        document.getElementById('solve-btn').disabled = false;
    }
}

function animateSolve() {
    if (moveIndex >= moves.length) return;

    drawLayout(currentLayout);
    drawPath(moves.slice(0, moveIndex + 1));
    drawPacman(moves[moveIndex].x, moves[moveIndex].y);

    moveIndex++;
    animationFrame = setTimeout(animateSolve, 200);
}

async function playGame() {
    const layoutName = document.getElementById('layout-select').value;
    const depth = parseInt(document.getElementById('depth-input').value);

    document.getElementById('status-value').textContent = 'Playing...';
    document.getElementById('play-btn').disabled = true;

    try {
        const response = await fetch('/api/play', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({layout_name: layoutName, depth})
        });

        const data = await response.json();

        gameFrames = data.frames;
        frameIndex = 0;

        document.getElementById('score-value').textContent = data.final_score;
        document.getElementById('moves-value').textContent = data.total_moves;
        document.getElementById('status-value').textContent = data.win ? 'WIN!' : 'Game Over';

        animatePlay();
    } catch (error) {
        document.getElementById('status-value').textContent = 'Error: ' + error.message;
    } finally {
        document.getElementById('play-btn').disabled = false;
    }
}

function animatePlay() {
    if (frameIndex >= gameFrames.length) return;

    drawFrame(gameFrames[frameIndex]);
    frameIndex++;
    animationFrame = setTimeout(animatePlay, 150);
}

function resetCanvas() {
    if (animationFrame) {
        clearTimeout(animationFrame);
        animationFrame = null;
    }
    ctx.fillStyle = COLORS.floor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    document.getElementById('score-value').textContent = '0';
    document.getElementById('moves-value').textContent = '0';
    document.getElementById('status-value').textContent = 'Ready';
}

loadLayouts();
