#!/bin/bash
# deploy.sh — Deploy a new Docker image tag to the Pacman game backend.
# Called by SSM Run Command from GitHub Actions.

set -euo pipefail

export HOME=/home/ec2-user

DEPLOY_TAG="${1:?Usage: deploy.sh <image-tag>}"
ECR_REPO="${2:?Usage: deploy.sh <tag> <ecr-repo-url>}"
HEALTH_URL="${3:-http://localhost:8000/api/health}"
HEALTH_RETRIES=10
HEALTH_INTERVAL=5
LAST_GOOD_PARAM="/pacman/last-good-tag"
CONTAINER_NAME="pacman-backend"

exec > >(tee /var/log/deploy.log) 2>&1
echo "=== Deploy started at $(date -u) ==="
echo "Tag: $DEPLOY_TAG"
echo "ECR Repo: $ECR_REPO"

# --- Fetch SSM config parameters ---
echo "Fetching parameters from SSM Parameter Store..."
PARAMS=$(aws ssm get-parameters \
  --names /pacman/log-level /pacman/domain \
  --query "Parameters[*].[Name,Value]" \
  --output text 2>/dev/null || true)

if [ -n "$PARAMS" ]; then
  echo "$PARAMS" | while IFS=$'\t' read -r name value; do
    param_key=$(echo "$name" | sed 's|/pacman/||')
    echo "${param_key}=${value}" >> /home/ec2-user/Pacman-Game/.env
  done
  echo "Wrote .env file from SSM parameters."
fi

# --- Pull the new image ---
echo "Pulling image: $ECR_REPO:$DEPLOY_TAG"
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin "$ECR_REPO" 2>/dev/null

docker pull "$ECR_REPO:$DEPLOY_TAG"

# --- Stop old containers ---
echo "Stopping old containers..."
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true
docker stop pacman-game-backend-1 2>/dev/null || true
docker rm pacman-game-backend-1 2>/dev/null || true
docker stop pacman-app 2>/dev/null || true
docker rm pacman-app 2>/dev/null || true

# --- Start new container ---
echo "Starting backend with tag $DEPLOY_TAG..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  --network host \
  -e PYTHONUNBUFFERED=1 \
  "$ECR_REPO:$DEPLOY_TAG"

# --- Health check ---
echo "Waiting for backend to become healthy..."
healthy=false
for i in $(seq 1 $HEALTH_RETRIES); do
  sleep $HEALTH_INTERVAL
  echo "Health check attempt $i/$HEALTH_RETRIES..."
  if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    echo "Health check passed."
    healthy=true
    break
  fi
  echo "Health check failed, retrying..."
done

if [ "$healthy" = true ]; then
  echo "Updating last-good-tag SSM parameter to $DEPLOY_TAG..."
  aws ssm put-parameter \
    --name "$LAST_GOOD_PARAM" \
    --value "$DEPLOY_TAG" \
    --type String \
    --overwrite \
    --region us-east-1 2>/dev/null || echo "Warning: Could not update last-good-tag"

  echo "=== Deploy succeeded at $(date -u) ==="
  exit 0
else
  echo "HEALTH CHECK FAILED after $HEALTH_RETRIES attempts."

  echo "Attempting rollback..."
  PREV_TAG=$(aws ssm get-parameter \
    --name "$LAST_GOOD_PARAM" \
    --query "Parameter.Value" \
    --output text 2>/dev/null || echo "")

  if [ -n "$PREV_TAG" ] && [ "$PREV_TAG" != "None" ]; then
    echo "Rolling back to last known good tag: $PREV_TAG"
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    docker run -d \
      --name "$CONTAINER_NAME" \
      --restart unless-stopped \
      --network host \
      -e PYTHONUNBUFFERED=1 \
      "$ECR_REPO:$PREV_TAG"

    sleep $HEALTH_INTERVAL
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
      echo "Rollback succeeded. Backend is healthy with tag $PREV_TAG."
    else
      echo "CRITICAL: Rollback also failed health check. Manual intervention required."
    fi
  else
    echo "No last-good-tag found in SSM. Manual intervention required."
  fi

  echo "=== Deploy FAILED at $(date -u) ==="
  exit 1
fi
