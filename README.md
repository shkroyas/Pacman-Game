# Pacman AI Demo

A web-based Pacman AI demonstration showcasing **A\* search** and **Alpha-Beta pruning** algorithms.

<div align="center">

![Pacman AI Demo](docs/pacman_demo.gif)

</div>

## Live Demo

[![Deploy](https://img.shields.io/badge/Deploy-AWS%20EC2-blue)](http://32.199.240.6)
[![Live](https://img.shields.io/badge/Live-App-green)](http://32.199.240.6)
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
- **Deployment**: Docker, Nginx, AWS EC2, Terraform
- **CI/CD**: GitHub Actions → ECR → SSM → EC2
- **Monitoring**: CloudWatch Logs, Alarms, Synthetics Canary

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

# Run with docker-compose (includes Nginx reverse proxy)
docker compose up -d

# Or run standalone (dev mode)
docker run -p 8000:8000 pacman-ai
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
├── terraform/                # Infrastructure as Code
│   ├── main.tf               # Provider & backend config
│   ├── ec2.tf                # EC2 instance + Elastic IP
│   ├── ecr.tf                # ECR repository + lifecycle
│   ├── security_groups.tf    # Firewall rules
│   ├── iam.tf                # EC2 instance role (SSM, ECR, CloudWatch)
│   ├── cloudwatch.tf         # Logs, alarms, Synthetics canary
│   ├── ssm.tf                # Parameter Store entries
│   ├── network.tf            # VPC/subnet data sources
│   ├── variables.tf          # Input variables
│   └── outputs.tf            # Exported values
├── nginx/
│   └── nginx.conf            # Reverse proxy config
├── scripts/
│   ├── deploy.sh             # Automated deploy + rollback
│   ├── bootstrap.sh          # EC2 first-boot setup
│   └── renew-cert.sh         # TLS certificate renewal
├── .github/workflows/
│   ├── ci.yml                # Test on PRs
│   └── deploy.yml            # Build → ECR → SSM deploy
├── docs/
│   ├── architecture.md       # System design docs
│   ├── cost-estimate.md      # Monthly cost breakdown
│   ├── recovery-runbook.md   # Incident response
│   └── *.gif/mp4             # Demo media
├── Dockerfile
├── docker-compose.yml        # Nginx + backend + certbot
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

### Prerequisites

- AWS CLI configured with access keys
- Terraform installed locally
- GitHub repository secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

### Initial Setup

```bash
# 1. Create Terraform backend (S3 + DynamoDB for state locking)
aws s3 mb s3://pacman-terraform-state --region us-east-1
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# 2. Import existing EC2 instance (if you have one running)
cd terraform/
terraform init
terraform import aws_instance.app i-XXXXXXXXXXXXXXXXX
terraform import aws_security_group.app sg-XXXXXXXXXXXXXXXXX

# 3. Deploy infrastructure
terraform plan
terraform apply
```

### CI/CD Pipeline

Push to `main` branch triggers:
1. **Test** — pytest + flake8
2. **Build & Push** — Docker image tagged with Git SHA → ECR
3. **Deploy** — SSM Run Command pulls new image and restarts the backend

### Manual Deploy

```bash
# Via SSM from your local machine
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=tag:Name,Values=pacman-game-instance" \
  --parameters "commands=['cd /home/ec2-user/Pacman-Game && sudo ./scripts/deploy.sh <git-sha> <ecr-repo-url>']"
```

### Architecture

See [docs/architecture.md](docs/architecture.md) for full system design.
See [docs/cost-estimate.md](docs/cost-estimate.md) for monthly cost breakdown.
See [docs/recovery-runbook.md](docs/recovery-runbook.md) for incident response.

## Impact of AI in This Project

### Why This Matters

This project demonstrates **fundamental AI concepts** that power real-world systems — from GPS navigation to game-playing engines to autonomous vehicles.

---

### 1. A* Search — Intelligent Pathfinding

**What it does:** Finds the shortest path from point A to point B using heuristics to guide the search.

**Real-World Impact:**
| Application | How A* is Used |
|-------------|----------------|
| **Google Maps / GPS** | Route optimization uses A*-like algorithms to find fastest paths |
| **Robot Navigation** | Robots use A* to navigate warehouses, hospitals, and factories |
| **Video Games** | NPCs (non-player characters) use A* for realistic movement |
| **Logistics** | Delivery companies optimize routes for thousands of packages daily |
| **Network Routing** | Internet packets are routed using shortest-path algorithms |

**Key Insight:** Without A*, computers would brute-force every possible path. A* uses **heuristics** (educated guesses) to search intelligently — cutting millions of calculations to thousands.

```
Traditional: Check ALL paths → O(b^d) operations
A* Search:   Check SMART paths → O(b^(d/2)) operations
```

---

### 2. Alpha-Beta Pruning — Adversarial Decision Making

**What it does:** Makes optimal decisions when an opponent is actively working against you.

**Real-World Impact:**
| Application | How Alpha-Beta is Used |
|-------------|----------------------|
| **Chess Engines** | Deep Blue, Stockfish use Alpha-Beta to defeat grandmasters |
| **Go (AlphaGo)** | Combined with neural networks to beat world champions |
| **Military Strategy** | Game theory applied to defense and security planning |
| **Business Negotiations** | Modeling competitive market strategies |
| **Autonomous Vehicles** | Predicting actions of other drivers in traffic |

**Key Insight:** In a competitive environment, you can't just plan your moves — you must anticipate your opponent's best response. Alpha-Beta **prunes** branches that no rational opponent would choose, making search 10x faster.

```
Minimax:    Explore ALL branches → 1,000,000 nodes
Alpha-Beta: Skip IMPOSSIBLE branches → 100,000 nodes
```

---

### 3. Evaluation Functions — Teaching AI to "Think"

**What it does:** Assigns a numerical score to game states, guiding the AI toward winning positions.

**Real-World Impact:**
| Application | How Evaluation Functions are Used |
|-------------|----------------------------------|
| **Medical Diagnosis** | Scoring patient risk based on multiple health factors |
| **Credit Scoring** | Banks evaluate loanworthiness using weighted features |
| **Quality Control** | Manufacturing robots score product quality |
| **Search Engines** | Google ranks pages using 200+ evaluation signals |
| **Recommendation Systems** | Netflix, Spotify score content relevance |

**Key Insight:** The evaluation function is where **human expertise** meets **machine computation**. We encode what we know (avoid ghosts, eat food) and let the AI optimize from there.

---

### 4. Heuristics — The Art of Good Guesses

**What it does:** Provides fast estimates that guide search without guaranteeing perfection.

**Real-World Impact:**
| Application | How Heuristics are Used |
|-------------|------------------------|
| **GPS Navigation** | "Straight-line distance" as lower bound for travel time |
| **Chess Engines** | Material count + position evaluation as winning estimate |
| **Protein Folding** | Energy-based heuristics predict 3D structures |
| **Scheduling** | Fast estimates help allocate limited resources |
| **Machine Learning** | Feature selection uses heuristic pruning |

**Key Insight:** A good heuristic can reduce search space by **orders of magnitude** while maintaining near-optimal solutions — the same principle powers everything from recommendation engines to self-driving cars.

---

### 5. Multi-Agent Systems — AI in Competition

**What it does:** Multiple AI agents interact, compete, and adapt in real-time.

**Real-World Impact:**
| Application | How Multi-Agent AI is Used |
|-------------|--------------------------|
| **Autonomous Traffic** | Self-driving cars negotiate with each other |
| **Stock Trading** | High-frequency bots compete in markets |
| **Cybersecurity** | AI defends against AI-powered attacks |
| **Smart Grids** | Power distribution optimized across competing demands |
| **Military Drones** | Coordinated swarm behavior |

**Key Insight:** This project's Pac-Man vs. Ghost dynamic mirrors real competitive AI scenarios where agents must predict and counter opponents' strategies.

---

### Summary: From Pac-Man to Production

```
PAC-MAN AI CONCEPT          REAL-WORLD APPLICATION
─────────────────────────────────────────────────────
A* Pathfinding        →     GPS, Robotics, Games
Alpha-Beta Pruning    →     Chess Engines, Strategy AI
Evaluation Functions  →     Medical AI, Credit Scoring
Heuristics            →     Search Engines, ML Features
Multi-Agent Systems   →     Autonomous Vehicles, Trading
State Space Search    →     Planning, Optimization
```

---

### Learning Outcomes

By building this project, you learn:

1. **Algorithm Design** — How to choose the right algorithm for a problem
2. **Heuristic Engineering** — How to encode domain knowledge into AI
3. **Search Optimization** — How to make AI faster with pruning
4. **Adversarial Reasoning** — How AI makes decisions against opponents
5. **System Architecture** — How to deploy AI as a production service
6. **Performance Analysis** — How to measure and optimize AI systems

These are the **exact skills** required for roles in:
- AI/ML Engineering
- Game Development
- Robotics
- Autonomous Systems
- Data Science
- Quantitative Finance

---

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
