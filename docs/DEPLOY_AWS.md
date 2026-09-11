# AWS EC2 Deployment Guide

## Prerequisites
- AWS account with EC2 access
- SSH key pair created in AWS
- Security group allowing ports 22 (SSH), 8000 (app)

## Step 1: Launch EC2 Instance

1. Go to AWS EC2 Console
2. Click "Launch Instance"
3. Choose **Amazon Linux 2023** (free tier eligible)
4. Select **t2.micro** instance type
5. Create/select a key pair
6. Configure security group:
   - Allow SSH (port 22) from your IP
   - Allow HTTP (port 8000) from anywhere (0.0.0.0/0)
7. Launch instance

## Step 2: Connect to Instance

```bash
ssh -i your-key.pem ec2-user@YOUR_EC2_PUBLIC_IP
```

## Step 3: Deploy the App

Run these commands on the EC2 instance:

```bash
# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone and deploy
cd /home/ec2-user
git clone https://github.com/shkroyas/Pacman-Game.git
cd Pacman-Game
docker-compose up -d
```

## Step 4: Verify Deployment

```bash
curl http://localhost:8000/api/health
# Should return: {"status":"healthy","version":"1.0.0"}
```

## Step 5: Access the App

Open browser: `http://YOUR_EC2_PUBLIC_IP:8000`

## Useful Commands

```bash
# View logs
docker-compose logs -f

# Restart app
docker-compose restart

# Stop app
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

## Troubleshooting

1. **Port 8000 not accessible**: Check security group allows inbound on port 8000
2. **Docker permission denied**: Log out and back in after `usermod -a -G docker`
3. **Container won't start**: Check logs with `docker-compose logs`
