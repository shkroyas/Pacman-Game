#!/bin/bash
# AWS EC2 Deployment Script for Pacman AI
# Run this on your EC2 instance after SSH-ing in

set -e

echo "=== Pacman AI Deployment ==="

# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
cd /home/ec2-user
git clone https://github.com/shkroyas/Pacman-Game.git
cd Pacman-Game

# Build and run
docker-compose up -d

echo ""
echo "=== Deployment Complete ==="
echo "Access the app at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To restart: docker-compose restart"
echo "To stop: docker-compose down"
