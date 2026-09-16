# Pacman-Game — AWS Deployment Upgrade Plan (Nginx Edition)

Repo: `shkroyas/Pacman-Game`
Current state: FastAPI app, Dockerized, `docker-compose up -d` on a manually configured EC2
t2.micro with port 8000 open directly to the internet. GitHub Actions exists but scope unknown
beyond basic CI.

**Architecture decision:** Nginx runs as a reverse-proxy sidecar container on the same EC2
instance, terminating TLS and forwarding to the FastAPI container over the internal Docker
network. No Application Load Balancer. This keeps monthly cost near-zero (no ~$16-18/mo ALB
charge) at the cost of losing the ALB's managed target-group health checks and built-in
listener-based TLS — both of which get rebuilt manually below (Nginx config + Certbot +
a CloudWatch canary).

This plan maps the 10 target improvements onto this exact repo, in dependency order.

---

## Phase-by-phase plan

### Phase 1 — Infrastructure as Code (Terraform)
Replace the manually-clicked EC2 instance, security group, and networking with Terraform.

**Do:**
- `terraform/` module defining: VPC (default VPC is fine to start), an EC2 instance (t2.micro,
  free tier), an Elastic IP (so the public address is stable across instance replacement), a
  security group, and an IAM instance role.
- Security group: inbound 80 and 443 from `0.0.0.0/0` (Nginx handles both — 80 for
  Certbot's HTTP-01 challenge and redirect, 443 for the app). SSH (22) restricted to your IP
  only until Phase 4 removes the need for it entirely.
- Terraform outputs: instance ID, Elastic IP, ECR repository URL (added in Phase 2).
- `terraform import` your *current* instance and security group first, confirm `terraform plan`
  shows no diff, before adding anything new — this proves the IaC matches reality.
- Move to remote state (S3 backend + DynamoDB lock table, both free-tier eligible at this scale)
  once local `apply` works cleanly.

---

### Phase 2 — Push the Docker image to Amazon ECR
Stop deploying from `git pull` on the box; deploy from a versioned, immutable image.

**Do:**
- Terraform: `aws_ecr_repository` with image scanning on push enabled, plus a lifecycle policy
  expiring untagged images after N days.
- Verify manually first: `aws ecr get-login-password | docker login`, `docker build`,
  `docker tag`, `docker push` — confirm the image lands in ECR before touching CI.
- Tag images with the Git SHA (`pacman-ai:<git-sha>`), not just `latest` — this is what makes
  rollback (Phase 9) possible.

---

### Phase 3 — Expand GitHub Actions: test → build → push
**Do:**
- `.github/workflows/deploy.yml` with three jobs:
  1. **test** — `pytest tests/ -v`. Nothing below runs if this fails.
  2. **build-and-push** (needs: test) — build, tag with `${{ github.sha }}` and `latest`,
     authenticate to ECR via `aws-actions/amazon-ecr-login`, push both tags.
  3. **deploy** (needs: build-and-push) — triggers the SSM-based deployment (Phase 4).
- Use **OIDC federation** (`aws-actions/configure-aws-credentials` with `role-to-assume`)
  instead of long-lived AWS access key secrets.

---

### Phase 4 — Deploy automatically to EC2 via AWS Systems Manager
Remove SSH-based deployment entirely; use SSM Run Command instead.

**Do:**
- IAM instance role attaches `AmazonSSMManagedInstanceCore` so the instance registers with SSM
  with no inbound SSH needed.
- GitHub Actions' deploy job calls `aws ssm send-command`, targeting the instance by tag,
  running `scripts/deploy.sh` on the box: pull the new ECR tag, restart the app container via
  `docker compose up -d` (Nginx container stays running/unaffected unless its own config
  changed), then run the Phase 9 health check.
- Nginx's config rarely changes on app deploys, so the deploy script should restart only the
  `backend` service, not the whole Compose stack — keeps TLS/Nginx uptime independent of app
  deploys.

---

### Phase 5 — CloudWatch logs, CPU alarms, application-health alarms
Without an ALB there's no automatic target-group health metric, so health monitoring needs to
be built explicitly.

**Do:**
- CloudWatch agent (installed via `user_data`/bootstrap script) ships both the Nginx access/error
  logs and the app container's logs to a CloudWatch Log Group.
- CPU alarm: CPUUtilization > 80% for 5 minutes → SNS topic → email.
- **Application-health alarm without an ALB:** use a small **CloudWatch Synthetics canary** (or
  a scheduled Lambda on an EventBridge rule) that calls `https://yourdomain/api/health` every
  5 minutes and publishes a custom metric (`HealthCheckSuccess = 0/1`); alarm on that metric.
  This is the direct replacement for what an ALB target group would have given you for free —
  worth noting explicitly in `docs/architecture.md` as a deliberate tradeoff.
- SNS topic + email subscription (free-tier friendly).

---

### Phase 6 — Nginx reverse proxy in front of the app
**Do:**
- Add an `nginx` service to `docker-compose.yml`, on the same Docker network as `backend`,
  proxying `/` → `backend:8000`.
- `nginx/nginx.conf`: reverse proxy config, WebSocket-friendly headers if the frontend ever needs
  them, gzip, and a `server_name` block per domain.
- Security group (Phase 1) now only needs 80/443 open — the FastAPI container's port 8000 is
  **not** published to the host's public interface at all, only reachable inside the Docker
  network from Nginx. This is actually a tighter posture than the ALB approach for a
  single-instance setup, since there's no separate "EC2 SG accepts from ALB SG" hop to configure.

---

### Phase 7 — Enable HTTPS (via Certbot, since there's no ALB/ACM listener to attach a cert to)
**Do:**
- Register or reuse a domain; Route 53 A record pointing directly at the instance's **Elastic
  IP** (from Phase 1) — no ALB alias involved.
- Run **Certbot** (`certbot/certbot` Docker image, or the Nginx Certbot plugin) on the instance
  to obtain a free Let's Encrypt certificate via the HTTP-01 challenge (needs port 80 reachable,
  which Phase 6 already opens).
- Mount the certificate volume into the Nginx container; Nginx's 443 `server` block references
  `fullchain.pem`/`privkey.pem`.
- Add a **renewal cron job** (Certbot certs expire every 90 days) — either a host crontab entry
  running `docker compose run --rm certbot renew` + `nginx -s reload`, or an SSM Automation
  document on a schedule. This is a genuinely important detail to document, since ACM would have
  handled renewal for you automatically and Certbot does not.

---

### Phase 8 — Externalize configuration
**Do:**
- Move environment-specific values (log level, feature flags, future API keys, the domain name
  itself for Nginx templating) into **SSM Parameter Store**.
- `deploy.sh` fetches parameters via `aws ssm get-parameters` and writes them to a `.env` file
  consumed by `docker compose` at container start, so the same image works across future
  environments without rebuilding.

---

### Phase 9 — Rollback and deployment-verification steps
No ALB target-group health check to lean on, so the deploy script owns this directly.

**Do:**
- After restarting the `backend` container, `deploy.sh` polls `curl -f https://yourdomain/api/health`
  for N retries with a short backoff.
- On failure: re-pull and restart the **previous** ECR tag (SHA-tagged, from Phase 2), verify
  health again, and exit non-zero so the GitHub Actions run shows failed — with a clear log
  line explaining the automatic rollback.
- Track the last known-good tag in an SSM parameter (`/pacman/last-good-tag`), updated only
  after a health check passes, so rollback doesn't depend on parsing Git/GitHub history from the
  instance.

---

### Phase 10 — Document architecture, cost, and recovery
**`docs/architecture.md`:**
- Diagram: GitHub Actions → ECR → SSM → EC2 (Nginx + Certbot + FastAPI containers) → user;
  CloudWatch Synthetics canary watching `/api/health`; CPU alarm; Parameter Store feeding config.
- State explicitly: single instance, no auto scaling, no multi-AZ, Nginx handles TLS
  termination on-box rather than a managed load balancer — accurate scoping over overclaiming.

**`docs/cost-estimate.md`:**
- EC2 t2.micro: free tier 750 hrs/mo, then ~$8.50/mo.
- Elastic IP: free while attached to a running instance.
- Route 53 hosted zone: ~$0.50/mo.
- Let's Encrypt certificate: free.
- CloudWatch Logs + 1 canary + 1-2 alarms: within or very close to free tier at this traffic
  level.
- **No ALB line item** — this is the main cost difference versus the earlier plan, worth calling
  out directly since it's the reason you chose this path.

**`docs/recovery-runbook.md`:**
- Instance terminated unexpectedly: Terraform re-apply recreates it + Elastic IP re-attaches;
  bootstrap script reinstalls Docker/CloudWatch agent/Certbot; SSM redeploys latest ECR tag.
- Certificate expired (renewal cron failed silently): manual
  `docker compose run --rm certbot renew --force-renewal` + `nginx -s reload`; document how to
  check `docker logs certbot` for the last renewal attempt.
- Bad deploy: Phase 9's automatic rollback, plus the manual override command using the
  `/pacman/last-good-tag` SSM parameter.
- Nginx misconfiguration blocking all traffic: `nginx -t` inside the container to validate
  config before reload; keep the previous `nginx.conf` as a committed file so you can revert via
  redeploy rather than hand-editing on the box.

---

## File structure additions

```
Pacman-Game/
├── backend/                          (existing)
├── frontend/                         (existing)
├── agents/  problems/  solvers/  layouts/  tests/   (existing)
│
├── terraform/                        ← NEW (Phase 1, 2, 5, 7)
│   ├── main.tf                       # provider config, backend config
│   ├── variables.tf                  # region, instance_type, domain_name, etc.
│   ├── outputs.tf                    # instance_id, elastic_ip, ecr_repository_url
│   ├── network.tf                    # VPC/subnet data sources (default VPC)
│   ├── security_groups.tf            # single SG: 80/443 public, 22 restricted (temp)
│   ├── iam.tf                        # EC2 instance role: SSM, ECR pull, CloudWatch, SNS
│   ├── ec2.tf                        # instance resource, Elastic IP, user_data bootstrap
│   ├── ecr.tf                        # repository + lifecycle policy
│   ├── route53.tf                    # hosted zone A record → Elastic IP
│   ├── cloudwatch.tf                 # log group, CPU alarm, Synthetics canary, SNS topic
│   └── ssm.tf                        # Parameter Store entries (non-secret config)
│
├── nginx/                            ← NEW (Phase 6, 7)
│   ├── nginx.conf                    # reverse proxy config, 80→443 redirect, TLS block
│   └── certbot/                      # webroot / cert volume mount point (gitignored contents)
│
├── scripts/
│   ├── deploy.sh                     ← NEW (Phase 4, 9) — pull image, restart backend only,
│   │                                     health-check via curl, rollback on failure
│   ├── bootstrap.sh                  ← NEW — EC2 user_data: installs Docker, Docker Compose,
│   │                                     CloudWatch agent, registers with SSM
│   └── renew-cert.sh                 ← NEW (Phase 7) — certbot renew + nginx reload, run via cron
│
├── .github/workflows/
│   ├── ci.yml                        (existing — keep for pytest on PRs)
│   └── deploy.yml                    ← NEW (Phase 3, 4) — test → build/push to ECR →
│                                          trigger SSM deploy
│
├── docs/
│   ├── architecture.md               ← NEW (Phase 10)
│   ├── cost-estimate.md              ← NEW (Phase 10)
│   ├── recovery-runbook.md           ← NEW (Phase 10)
│   ├── pacman_demo.gif               (existing)
│   ├── pacman_astar_demo.gif         (existing)
│   ├── pacman_gameplay_demo.gif      (existing)
│   └── pacman_ai_demo.mp4            (existing)
│
├── docker-compose.yml                (existing — add nginx + certbot services)
├── docker-compose.prod.yml           ← NEW, optional — prod-specific overrides/secrets wiring
├── Dockerfile                        (existing, for the backend service)
├── requirements.txt                  (existing)
└── README.md                         (existing — update Live Demo link from raw IP:8000 to
                                          the HTTPS domain once Phase 7 is done)
```

---

## `docker-compose.yml` shape (reference, not final code)

```yaml
services:
  backend:
    build: .
    expose:
      - "8000"          # NOT published to host — only reachable by nginx on the compose network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certbot/conf:/etc/letsencrypt
      - ./nginx/certbot/www:/var/www/certbot
    depends_on:
      - backend
    restart: unless-stopped

  certbot:
    image: certbot/certbot
    volumes:
      - ./nginx/certbot/conf:/etc/letsencrypt
      - ./nginx/certbot/www:/var/www/certbot
    entrypoint: "certbot certonly --webroot -w /var/www/certbot"
```

---

## Suggested execution order

1. **Terraform-import the current setup** — describe today's EC2 + SG in Terraform, confirm
   `terraform plan` shows no diff, before changing anything.
2. **ECR + manual push** — confirm the instance can pull manually before wiring CI.
3. **Nginx + Certbot locally verified** — get `docker compose up` running Nginx + backend with a
   real cert on the box, tested by hand, before automating deploys around it.
4. **SSM deploy script, run manually once** — verify `deploy.sh` works via a manual
   `aws ssm send-command` call before wiring it into GitHub Actions; remove SSH inbound once
   confirmed.
5. **GitHub Actions pipeline** — test → build/push → SSM deploy, using the verified script.
6. **CloudWatch canary + CPU alarm** — add once there's a stable, redeployable, HTTPS-reachable
   service to actually alarm on.
7. **Certbot renewal cron** — set up and test with `--dry-run` before trusting it unattended.
8. **Parameter Store + rollback logic** — layer in last, once the happy path is proven.
9. **Docs** — write last, once they describe something real.

Keep the live demo link working at each step; avoid long stretches where multiple phases are
half-finished simultaneously.
