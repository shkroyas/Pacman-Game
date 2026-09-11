# Pacman AI Demo

A web-based Pacman AI demonstration showcasing **A\* search** and **Alpha-Beta pruning** algorithms.

<div align="center">

![Pacman AI Demo](docs/pacman_demo.gif)

</div>

## Live Demo

[![Deploy](https://img.shields.io/badge/Deploy-AWS%20EC2-blue)](http://52.91.111.241:8000)
[![Live](https://img.shields.io/badge/Live-App-green)](http://52.91.111.241:8000)
[![Video](https://img.shields.io/badge/Video-Watch-red)](docs/pacman_ai_demo.mp4)

## Algorithms Implemented

### A* Search
- Single-dot pathfinding with Manhattan distance heuristic
- Multi-dot search with minimum food distance heuristic
- Full board clear with food-count heuristic

<div align="center">

![A* Search Demo](docs/pacman_astar_demo.gif)

</div>

### Alpha-Beta Pruning
- Adversarial game-tree search against ghost opponents
- Configurable search depth
- Evaluation function combining score, food distance, and ghost proximity

<div align="center">

![Gameplay Demo](docs/pacman_gameplay_demo.gif)

</div>

## Tech Stack

- **Backend**: Python, FastAPI
- **Frontend**: HTML5 Canvas, JavaScript
- **Deployment**: Docker, AWS EC2

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Open browser
open http://localhost:8000
```

### Docker

```bash
# Build image
docker build -t pacman-ai .

# Run container
docker run -p 8000:8000 pacman-ai

# Or use docker-compose
docker-compose up
```

## Project Structure

```
pacman-game/
├── backend/
│   └── main.py              # FastAPI application
├── frontend/
│   ├── index.html            # Main HTML page
│   ├── app.js                # Canvas rendering & API calls
│   └── style.css             # Styling
├── agents/
│   ├── pacmanAgents.py       # Simple agent
│   ├── ghostAgents.py        # Ghost behaviors
│   ├── q2Agent.py            # Alpha-Beta agent
│   └── searchAgents.py       # Search agent base
├── problems/
│   ├── q1a_problem.py        # Single dot problem
│   ├── q1b_problem.py        # Multi-dot problem
│   └── q1c_problem.py        # Full clear problem
├── solvers/
│   ├── q1a_solver.py         # A* solver
│   ├── q1b_solver.py         # Multi-dot solver
│   └── q1c_solver.py         # Full clear solver
├── layouts/                  # Maze layout files
├── tests/                    # Unit tests
├── docs/
│   ├── pacman_demo.gif       # Main demo GIF
│   ├── pacman_astar_demo.gif # A* search demo
│   ├── pacman_gameplay_demo.gif # Gameplay demo
│   └── pacman_ai_demo.mp4    # Full demo video
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main page |
| `/api/layouts` | GET | List available layouts |
| `/api/solve` | POST | Solve a maze with specified algorithm |
| `/api/play` | POST | Play a full game with Alpha-Beta agent |
| `/api/health` | GET | Health check |

## Features

- **Interactive Web Interface**: Watch AI agents solve mazes in real-time
- **Multiple Algorithms**: Choose between A* search and Alpha-Beta pruning
- **Configurable Depth**: Adjust search depth for Alpha-Beta agent
- **Multiple Layouts**: Test on different maze configurations
- **Real-time Visualization**: Canvas-based rendering with smooth animations

## AWS Deployment

### EC2 Setup

1. Launch EC2 instance (t2.micro, Amazon Linux 2)
2. Install Docker:
   ```bash
   sudo yum update -y
   sudo yum install docker -y
   sudo service docker start
   sudo usermod -a -G docker ec2-user
   ```

3. Clone and deploy:
   ```bash
   git clone https://github.com/shkroyas/Pacman-Game.git
   cd Pacman-Game
   docker-compose up -d
   ```

4. Open port 8000 in security group

## Running Tests

```bash
python -m pytest tests/ -v
```

## Benchmarks

Run benchmarking script:

```bash
python scripts/run_benchmarks.py
```

## License

MIT License - see [LICENSE](LICENSE)
