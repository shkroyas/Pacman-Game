# 🚀 Deployment Guide — Pacman AI on AWS

> Complete step-by-step guide to deploy the Pacman AI application on AWS with CI/CD.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Infrastructure Setup](#phase-1-infrastructure-setup)
4. [Phase 2: ECR Repository](#phase-2-ecr-repository)
5. [Phase 3: Docker Image](#phase-3-docker-image)
6. [Phase 4: GitHub Actions CI/CD](#phase-4-github-actions-cicd)
7. [Phase 5: EC2 Deployment](#phase-5-ec2-deployment)
8. [Phase 6: Monitoring](#phase-6-monitoring)
9. [Verification](#verification)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
Developer → GitHub Push → GitHub Actions → ECR → SSM → EC2 → Live App
                          ┌──────────────────────────────────────┐
                          │  CI/CD Pipeline                      │
                          │  1. Test (pytest + flake8)            │
                          │  2. Build Docker image                │
                          │  3. Push to ECR                       │
                          │  4. Deploy via SSM                    │
                          │  5. Health check + rollback           │
                          └──────────────────────────────────────┘
```

---

## Prerequisites

### Required Tools

| Tool | Install | Verify |
|------|---------|--------|
| AWS CLI | [Install](https://aws.amazon.com/cli/) | `aws --version` |
| Terraform | [Install](https://terraform.io) | `terraform version` |
| Docker | [Install](https://docker.com) | `docker --version` |
| Git | [Install](https://git-scm.com) | `git --version` |

### AWS Account Setup

```bash
# Configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output (json)

# Verify identity
aws sts get-caller-identity
```

### Required IAM Permissions

Your IAM user needs these policies:
- `AdministratorAccess` (for full setup) OR
- Custom policy with: EC2, ECR, SSM, CloudWatch, IAM, S3, SNS permissions

---

## Phase 1: Infrastructure Setup

### Step 1.1: Create Terraform Backend

```bash
# Create S3 bucket for Terraform state
aws s3 mb s3://pacman-tf-state-211125530162 --region us-east-1

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### Step 1.2: Initialize Terraform

```bash
cd terraform/
terraform init
```

Expected output:
```
Terraform has been successfully initialized!
```

### Step 1.3: Import Existing Resources (if applicable)

If you already have an EC2 instance running:

```bash
# Import existing EC2 instance
terraform import aws_instance.app i-0e939da1aaf5336f6

# Import existing security group
terraform import aws_security_group.app sg-09b658ff81bd3214c
```

### Step 1.4: Deploy Infrastructure

```bash
# Preview changes
terraform plan

# Apply changes
terraform apply
```

Type `yes` when prompted. This creates:
- ✅ EC2 instance (t3.micro)
- ✅ Elastic IP (32.199.240.6)
- ✅ ECR repository
- ✅ IAM role (SSM, ECR, CloudWatch)
- ✅ Security group (ports 80, 443, 8000, 22)
- ✅ CloudWatch log group + alarms
- ✅ Synthetics canary (health check)
- ✅ SSM parameters

### Step 1.5: Verify Infrastructure

```bash
# Check outputs
terraform output

# Expected:
# elastic_ip = "32.199.240.6"
# ecr_repository_url = "211125530162.dkr.ecr.us-east-1.amazonaws.com/pacman-game"
# instance_id = "i-0e939da1aaf5336f6"
```

---

## Phase 2: ECR Repository

### Step 2.1: Login to ECR

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 211125530162.dkr.ecr.us-east-1.amazonaws.com
```

Expected: `Login Succeeded`

---

## Phase 3: Docker Image

### Step 3.1: Build Docker Image

```bash
# From project root
docker build -t pacman-game:latest .
```

### Step 3.2: Test Locally

```bash
# Run container
docker run -d --name test -p 8000:8000 pacman-game:latest

# Verify health
curl http://localhost:8000/api/health
# Expected: {"status":"healthy","version":"1.0.0"}

# Stop test container
docker stop test && docker rm test
```

### Step 3.3: Push to ECR

```bash
# Tag for ECR
docker tag pacman-game:latest 211125530162.dkr.ecr.us-east-1.amazonaws.com/pacman-game:latest
docker tag pacman-game:latest 211125530162.dkr.ecr.us-east-1.amazonaws.com/pacman-game:initial

# Push to ECR
docker push 211125530162.dkr.ecr.us-east-1.amazonaws.com/pacman-game:latest
docker push 211125530162.dkr.ecr.us-east-1.amazonaws.com/pacman-game:initial
```

### Step 3.4: Deploy to EC2 (Manual)

```bash
# SSH into EC2 (one-time setup)
ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6

# Or use SSM (no SSH needed)
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=tag:Name,Values=pacman-ai-server" \
  --parameters "commands=['docker pull 211125530162.dkr.ecr.us-east-1.amazonaws.com/pacman-game:latest', 'docker stop pacman-backend 2>/dev/null || true', 'docker rm pacman-backend 2>/dev/null || true', 'docker run -d --name pacman-backend --restart unless-stopped --network host -e PYTHONUNBUFFERED=1 211125530162.dkr.ecr.us-east-1.amazonaws.com/pacman-game:latest']" \
  --region us-east-1
```

---

## Phase 4: GitHub Actions CI/CD

### Step 4.1: Create GitHub Secrets

Go to: `https://github.com/shkroyas/Pacman-Game/settings/secrets/actions`

Click **New repository secret** for each:

| Name | Value |
|------|-------|
| `AWS_KEY_ACCESS_ID` | Your IAM access key ID |
| `AWS_SECRET_ACCESS_KEY` | Your IAM secret access key |

### Step 4.2: Verify Workflow File

Ensure `.github/workflows/deploy.yml` exists with:

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install and run tests
        run: |
          python -m venv .venv
          .venv/bin/pip install pytest flake8 -r requirements.txt
          .venv/bin/pytest tests/ -v
      - name: Run linter
        run: .venv/bin/flake8 ...

  build-and-push:
    needs: test
    if: always()
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_KEY_ACCESS_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - uses: aws-actions/amazon-ecr-login@v2
      - run: docker build -t $ECR_REPOSITORY:${{ github.sha }} .
      - run: docker push ...

  deploy:
    needs: build-and-push
    steps:
      - run: aws ssm send-command ... (deploy script)
```

### Step 4.3: Push to Trigger Pipeline

```bash
git add .
git commit -m "feat: initial deployment"
git push origin main
```

### Step 4.4: Monitor Pipeline

1. Go to: `https://github.com/shkroyas/Pacman-Game/actions`
2. Click on the running workflow
3. Watch each step:
   - 🧪 Test (pytest + flake8)
   - 🐳 Build & Push to ECR
   - 🚀 Deploy to EC2

---

## Phase 5: EC2 Deployment

### Automatic Deployment (via CI/CD)

When you push to `main`, the pipeline automatically:

1. **Downloads deploy.sh** from GitHub
2. **Pulls the new Docker image** from ECR
3. **Stops old container** and starts new one
4. **Runs health checks** (10 attempts, 5s interval)
5. **On success**: Updates SSM parameter `last-good-tag`
6. **On failure**: Rolls back to last known good tag

### Manual Deployment

```bash
# Deploy specific tag
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=tag:Name,Values=pacman-ai-server" \
  --parameters "commands=['curl -sf https://raw.githubusercontent.com/shkroyas/Pacman-Game/main/scripts/deploy.sh -o /tmp/deploy.sh', 'chmod +x /tmp/deploy.sh', 'sudo /tmp/deploy.sh <git-sha> 211125530162.dkr.ecr.us-east-1.amazonaws.com/pacman-game']" \
  --region us-east-1
```

### Rollback

```bash
# Get last good tag
aws ssm get-parameter --name /pacman/last-good-tag --query Parameter.Value --output text

# Deploy rollback
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=tag:Name,Values=pacman-ai-server" \
  --parameters "commands=['curl -sf https://raw.githubusercontent.com/shkroyas/Pacman-Game/main/scripts/deploy.sh -o /tmp/deploy.sh', 'chmod +x /tmp/deploy.sh', 'sudo /tmp/deploy.sh <last-good-tag> 211125530162.dkr.ecr.us-east-1.amazonaws.com/pacman-game']" \
  --region us-east-1
```

---

## Phase 6: Monitoring

### CloudWatch Logs

```bash
# View application logs
aws logs tail /pacman-game/application --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /pacman-game/application \
  --filter-pattern "ERROR"
```

### Health Check

```bash
# Manual health check
curl http://32.199.240.6:8000/api/health

# Expected: {"status":"healthy","version":"1.0.0"}
```

### CloudWatch Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| CPU High | >80% for 5 min | Email notification |
| Health Failures | >5 errors in 5 min | Email notification |

### Synthetics Canary

- Runs every 5 minutes
- Hits `/api/health` endpoint
- CloudWatch Dashboard for visibility

---

## Verification

### Checklist

- [ ] EC2 instance is running
- [ ] Elastic IP is associated (32.199.240.6)
- [ ] Security group allows ports 80, 443, 8000, 22
- [ ] IAM role is attached to instance
- [ ] SSM agent is running on instance
- [ ] Docker is installed and running
- [ ] App responds to health check
- [ ] GitHub Actions secrets are configured
- [ ] CI/CD pipeline passes all steps
- [ ] CloudWatch logs are being received
- [ ] SNS email subscription is confirmed

### Quick Verification Commands

```bash
# Check app health
curl http://32.199.240.6:8000/api/health

# Check ECR images
aws ecr describe-images --repository-name pacman-game --region us-east-1

# Check SSM command history
aws ssm list-commands --region us-east-1 --max-results 5

# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /pacman-game

# Check instance status
aws ec2 describe-instances --instance-ids i-0e939da1aaf5336f6
```

---

## Troubleshooting

### Issue: pytest not found in CI

**Symptom**: `No module named pytest`

**Solution**: The workflow uses a virtual environment:
```yaml
- name: Install and run tests
  run: |
    python -m venv .venv
    .venv/bin/pip install pytest flake8 -r requirements.txt
    .venv/bin/pytest tests/ -v
```

### Issue: Deploy fails with "dubious ownership"

**Symptom**: `fatal: detected dubious ownership in repository`

**Solution**: The deploy script now downloads via curl instead of git pull:
```bash
curl -sf https://raw.githubusercontent.com/.../deploy.sh -o /tmp/deploy.sh
```

### Issue: docker-compose not found

**Symptom**: `unknown shorthand flag: 'd' in -d`

**Solution**: Deploy script uses direct `docker run` commands instead of docker-compose.

### Issue: SSM command fails

**Symptom**: Deploy status shows `null`

**Solution**: Check IAM role is attached:
```bash
aws ec2 describe-iam-instance-profile-associations \
  --filters "Name=instance-id,Values=i-0e939da1aaf5336f6"
```

If empty, attach:
```bash
aws ec2 associate-iam-instance-profile \
  --instance-id i-0e939da1aaf5336f6 \
  --iam-instance-profile Name=pacman-game-instance-profile
```

Then restart SSM agent:
```bash
ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6 \
  "sudo systemctl restart amazon-ssm-agent"
```

### Issue: GitHub secrets not loading

**Symptom**: `Credentials could not be loaded`

**Solution**: Verify secret names match exactly:
- `AWS_KEY_ACCESS_ID` (not `AWS_ACCESS_KEY_ID`)
- `AWS_SECRET_ACCESS_KEY`

---

## 🔄 Deployment Flow Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Developer  │     │    GitHub     │     │     AWS      │
│              │     │              │     │              │
│  git push ───┼────►│  Actions     │     │              │
│              │     │     │        │     │              │
│              │     │     ▼        │     │              │
│              │     │  ┌──────┐   │     │              │
│              │     │  │ Test │   │     │              │
│              │     │  └──┬───┘   │     │              │
│              │     │     ▼        │     │              │
│              │     │  ┌──────┐   │     │  ┌──────┐   │
│              │     │  │Build │───┼────►│  │ ECR  │   │
│              │     │  └──┬───┘   │     │  └──┬───┘   │
│              │     │     ▼        │     │     │        │
│              │     │  ┌──────┐   │     │  ┌──▼───┐   │
│              │     │  │Deploy│───┼────►│  │ SSM  │   │
│              │     │  └──────┘   │     │  └──┬───┘   │
│              │     │              │     │     │        │
│              │     │              │     │  ┌──▼───┐   │
│              │     │              │     │  │ EC2  │   │
│              │     │              │     │  └──┬───┘   │
│              │     │              │     │     │        │
│              │     │              │     │  ┌──▼───┐   │
│  ◄───────────┼─────┼──────────────┼─────┤  │Live  │   │
│   Browser    │     │              │     │  │ App  │   │
└──────────────┘     └──────────────┘     │  └──────┘   │
                                          └──────────────┘
```

---

## 📊 Resource Summary

| Resource | ID/ARN | Status |
|----------|--------|--------|
| EC2 Instance | `i-0e939da1aaf5336f6` | ✅ Running |
| Elastic IP | `32.199.240.6` | ✅ Associated |
| ECR Repository | `pacman-game` | ✅ Active |
| IAM Role | `pacman-game-ec2-role` | ✅ Attached |
| Security Group | `sg-09b658ff81bd3214c` | ✅ Configured |
| CloudWatch Log Group | `/pacman-game/application` | ✅ Active |
| SSM Parameters | 5 parameters | ✅ Created |
| Synthetics Canary | `pacman-game-health-check` | ✅ Running |

---

*Last updated: September 2026*
