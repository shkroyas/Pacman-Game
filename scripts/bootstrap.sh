#!/bin/bash
# Bootstrap script for EC2 instance — runs once on first boot via user_data.
# Installs Docker, Docker Compose, CloudWatch agent, and registers with SSM.

set -euo pipefail

exec > >(tee /var/log/bootstrap.log) 2>&1
echo "=== Bootstrap started at $(date -u) ==="

# --- System updates ---
dnf update -y

# --- Docker ---
dnf install -y docker
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user

# --- Docker Compose (v2 plugin) ---
dnf install -y docker-compose-plugin

# --- CloudWatch Agent ---
dnf install -y amazon-cloudwatch-agent
cat > /opt/cloudwatch-agent.json <<'CWCONFIG'
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/bootstrap.log",
            "log_group_name": "/pacman-game/bootstrap",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC"
          }
        ]
      }
    }
  },
  "metrics": {
    "namespace": "PacmanGame",
    "metrics_collected": {
      "cpu": {
        "measurement": ["cpu_usage_idle", "cpu_usage_user", "cpu_usage_system"],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": ["used_percent"],
        "metrics_collection_interval": 60,
        "resources": ["*"]
      },
      "mem": {
        "measurement": ["mem_used_percent"],
        "metrics_collection_interval": 60
      }
    }
  }
}
CWCONFIG
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/cloudwatch-agent.json \
  -s

# --- Pull and start application containers ---
ECR_REPO="${ecr_repository_url}"
AWS_REGION="${aws_region}"

if [ -n "$ECR_REPO" ]; then
  echo "Pulling latest image from ECR: $ECR_REPO"
  aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$ECR_REPO"

  # Clone the repo (for docker-compose.yml and nginx config)
  cd /home/ec2-user
  if [ ! -d Pacman-Game ]; then
    git clone https://github.com/shkroyas/Pacman-Game.git
  fi
  cd Pacman-Game
  git pull

  docker compose up -d
  echo "Containers started."
fi

echo "=== Bootstrap completed at $(date -u) ==="
