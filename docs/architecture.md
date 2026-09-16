# Architecture

## System Overview

```
                    ┌─────────────┐
                    │   User      │
                    │  (Browser)  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Elastic IP │
                    │  (52.x.x.x)│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  EC2        │
                    │  t2.micro   │
                    │             │
                    │  ┌────────┐ │    ┌─────────────────┐
                    │  │ Nginx  │─┼───►│ FastAPI Backend  │
                    │  │ :80/:443│ │    │ (container)      │
                    │  └────────┘ │    │ :8000 (internal) │
                    │  ┌────────┐ │    └─────────────────┘
                    │  │Certbot │ │
                    │  └────────┘ │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼───┐ ┌─────▼─────┐ ┌───▼───────┐
     │  CloudWatch │ │ SSM       │ │ ECR       │
     │  Logs       │ │ Parameter │ │ Container │
     │  Alarms     │ │ Store     │ │ Registry  │
     │  Canary     │ └───────────┘ └───────────┘
     └────────────┘
```

## Components

### EC2 Instance (t2.micro, free tier)
- Amazon Linux 2023
- Docker + Docker Compose v2
- CloudWatch Agent
- Managed via AWS SSM (no inbound SSH needed after bootstrap)

### Nginx (sidecar container)
- Reverse proxy on ports 80/443
- Forwards all requests to `backend:8000` on the Docker network
- Handles gzip compression, WebSocket upgrade headers
- TLS termination (once domain + certificate are configured)
- The FastAPI container's port 8000 is **not** published to the host

### FastAPI Backend (container)
- Python 3.11, FastAPI + Uvicorn
- Serves the web UI and API endpoints
- Only accessible from the Nginx container (no direct internet access)

### Certbot (sidecar container)
- Manages Let's Encrypt TLS certificates
- Renewal runs on a schedule (every 12 hours via container entrypoint)

### CloudWatch
- **Logs**: Application logs shipped via CloudWatch Agent
- **CPU Alarm**: CPUUtilization > 80% for 5 minutes → SNS → email
- **Health Canary**: CloudWatch Synthetics canary hits `/api/health` every 5 minutes
- **Log Metric Filter**: Detects ERROR-level log entries

### SSM Parameter Store
- `/pacman/log-level` — Application log level
- `/pacman/domain` — Domain name (for Nginx config)
- `/pacman/last-good-tag` — Last successful deploy tag (for rollback)
- `/pacman/app-version` — Current deployed version
- `/pacman/feature-flags` — Feature flags (JSON)

### ECR
- Container image registry
- Images tagged with Git SHA for versioning
- Lifecycle policy: untagged images expire after 7 days

### CI/CD Pipeline (GitHub Actions)
```
Push to main → test (pytest) → build & push to ECR → deploy via SSM
```
1. **test**: Runs `pytest` and `flake8` on PRs and pushes
2. **build-and-push**: Builds Docker image, tags with Git SHA, pushes to ECR
3. **deploy**: Sends SSM command to EC2 to pull new image and restart backend

## Design Decisions

### No Application Load Balancer
This is a deliberate cost optimization. An ALB costs ~$16-18/month even at idle.
Instead:
- Nginx runs as a sidecar container for reverse proxying and TLS termination
- CloudWatch Synthetics canary replaces ALB target-group health checks
- Certificate management uses Certbot instead of ACM (ALB listener)

### No SSH Access After Bootstrap
SSM Run Command replaces SSH for all management tasks:
- Deployment via `deploy.sh`
- Configuration via SSM Parameter Store
- Log access via CloudWatch (no need to SSH to read logs)

### Backend Not Exposed to Internet
The FastAPI container uses `expose` (not `ports`), making it only reachable from the
Nginx container on the Docker network. This is tighter security than publishing port 8000.
