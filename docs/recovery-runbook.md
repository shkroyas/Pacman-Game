# Recovery Runbook

## Scenario 1: EC2 Instance Terminated

**Symptoms**: App unreachable, SSM commands fail

**Recovery steps**:
```bash
# From local machine with Terraform installed:
cd terraform/
terraform apply -auto-approve
```

Terraform will:
1. Recreate the EC2 instance with the same configuration
2. Reattach the Elastic IP automatically
3. Run the bootstrap script (installs Docker, pulls latest image, starts containers)

**Verification**:
```bash
# Check the instance is running
aws ec2 describe-instances --filters "Name=tag:Name,Values=pacman-game-instance" \
  --query "Reservations[0].Instances[0].State.Name" --output text

# Check the app is healthy
curl -f http://<elastic-ip>/api/health
```

**Time to recovery**: ~5-10 minutes (instance boot + Docker setup + container start)

---

## Scenario 2: Certificate Expired (Renewal Failed)

**Symptoms**: Browser shows TLS error, Nginx serving HTTP only

**Recovery steps**:
```bash
# SSH into the instance (or use SSM)
ssh -i key.pem ec2-user@<elastic-ip>

# Check certbot logs
docker compose logs certbot

# Force renewal
cd /home/ec2-user/Pacman-Game
docker compose run --rm certbot renew --force-renewal --webroot -w /var/www/certbot

# Reload Nginx
docker compose exec nginx nginx -s reload
```

**If renewal fails completely**:
```bash
# Remove old certificate and get a new one
docker compose run --rm certbot certonly --webroot -w /var/www/certbot \
  --email your@email.com --agree-tos -d yourdomain.com

# Reload Nginx
docker compose exec nginx nginx -s reload
```

**Prevention**: Check renewal cron is working:
```bash
# View cron logs
grep certbot /var/log/cron

# Test renewal without actually renewing
docker compose run --rm certbot renew --dry-run
```

---

## Scenario 3: Bad Deploy (Health Check Failed)

**Symptoms**: Deploy script reports health check failure, rollback was attempted

**Automatic rollback**:
The `deploy.sh` script automatically rolls back to the last known good tag if the
health check fails. Check the deploy log:
```bash
# Via SSM or SSH
cat /var/log/deploy.log
```

**Manual rollback** (if automatic rollback also failed):
```bash
# Get the last known good tag from SSM
LAST_GOOD=$(aws ssm get-parameter --name /pacman/last-good-tag \
  --query "Parameter.Value" --output text)

# Pull and restart with that tag
cd /home/ec2-user/Pacman-Game
export IMAGE_TAG="$LAST_GOOD"
export ECR_REPO_URL="<your-ecr-repo-url>"
docker compose up -d --force-recreate --no-deps backend

# Verify health
curl -f http://localhost:8000/api/health
```

**Force a specific tag**:
```bash
export IMAGE_TAG="<git-sha-of-known-good-commit>"
export ECR_REPO_URL="<your-ecr-repo-url>"
docker compose up -d --force-recreate --no-deps backend
```

---

## Scenario 4: Nginx Misconfiguration Blocking Traffic

**Symptoms**: All requests return 502, 500, or connection refused

**Recovery steps**:
```bash
# Test Nginx configuration
docker compose exec nginx nginx -t

# If config test fails, revert to the last working nginx.conf
# The config file is committed to git, so:
cd /home/ec2-user/Pacman-Game
git checkout main -- nginx/nginx.conf

# Reload with the fixed config
docker compose exec nginx nginx -s reload
```

**If Nginx container won't start**:
```bash
# Check Nginx logs
docker compose logs nginx

# Restart the container
docker compose restart nginx

# Or rebuild from scratch
docker compose up -d --force-recreate nginx
```

---

## Scenario 5: EC2 Instance Unreachable (Network Issue)

**Symptoms**: Can't SSH, can't reach app, SSM shows instance as "online" but unresponsive

**Recovery steps**:
1. Check instance status in AWS Console
2. Check system status checks (hardware issues — AWS handles these)
3. If instance status check failed:
   ```bash
   # Stop and start (not reboot) the instance to migrate to new hardware
   aws ec2 stop-instances --instance-ids <instance-id>
   aws ec2 wait instance-stopped --instance-ids <instance-id>
   aws ec2 start-instances --instance-ids <instance-id>
   ```
4. Elastic IP automatically reattaches to the restarted instance
5. Bootstrap script runs on first boot, so Docker and containers restart automatically

---

## Scenario 6: SSM Agent Not Responding

**Symptoms**: SSM commands time out, instance shows as "offline" in SSM

**Recovery steps**:
```bash
# Via SSH (temporarily enable port 22 in security group)
ssh -i key.pem ec2-user@<elastic-ip>

# Check SSM agent status
sudo systemctl status amazon-ssm-agent

# Restart SSM agent
sudo systemctl restart amazon-ssm-agent

# If SSM agent is missing or corrupted
sudo yum install -y amazon-ssm-agent
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
```

---

## Scenario 7: Disk Full

**Symptoms**: Deploy fails, containers can't start, health checks fail

**Recovery steps**:
```bash
# Check disk usage
df -h

# Clean up Docker resources
docker system prune -af --volumes

# Remove old logs
sudo journalctl --vacuum-size=100M

# Check CloudWatch agent logs aren't consuming too much space
sudo du -sh /opt/aws/amazon-cloudwatch-agent/
```

**Prevention**: The ECR lifecycle policy automatically expires untagged images after 7 days.

---

## Emergency Contacts

- **AWS Console**: https://console.aws.amazon.com/
- **GitHub Repo**: https://github.com/shkroyas/Pacman-Game
- **Terraform State**: S3 bucket `pacman-terraform-state` in us-east-1

## Quick Reference Commands

| Action | Command |
|--------|---------|
| Check app health | `curl -f http://<ip>/api/health` |
| View deploy log | `cat /var/log/deploy.log` |
| View bootstrap log | `cat /var/log/bootstrap.log` |
| Restart backend | `docker compose restart backend` |
| Restart Nginx | `docker compose exec nginx nginx -s reload` |
| Check Nginx config | `docker compose exec nginx nginx -t` |
| View all containers | `docker compose ps` |
| View backend logs | `docker compose logs backend` |
| Force rollback | `export IMAGE_TAG=<tag> && docker compose up -d --force-recreate --no-deps backend` |
