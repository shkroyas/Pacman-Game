# 🔧 Recovery Runbook — Pacman AI

> Quick reference for incident response and common issues.

---

## 🚨 Emergency Contacts

| Role | Contact |
|------|---------|
| AWS Account | 211125530162 |
| Region | us-east-1 |
| EC2 Instance | i-0e939da1aaf5336f6 |
| Elastic IP | 32.199.240.6 |
| SSH Key | ~/.ssh/pacman-ai-key.pem |

---

## 🔴 Critical Issues

### App Down (Health Check Failing)

**Symptoms:**
- `curl http://32.199.240.6:8000/api/health` fails
- CloudWatch health alarm triggered
- Users can't access the app

**Diagnosis:**

```bash
# 1. Check instance status
aws ec2 describe-instances --instance-ids i-0e939da1aaf5336f6 \
  --query "Reservations[0].Instances[0].State.Name"

# 2. Check Docker containers
ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6 \
  "docker ps -a"

# 3. Check backend logs
ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6 \
  "docker logs pacman-backend --tail 50"
```

**Resolution:**

```bash
# Option 1: Restart container
ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6 \
  "sudo docker restart pacman-backend"

# Option 2: Redeploy last good tag
LAST_GOOD=$(aws ssm get-parameter --name /pacman/last-good-tag --query Parameter.Value --output text)
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=tag:Name,Values=pacman-ai-server" \
  --parameters "commands=['curl -sf https://raw.githubusercontent.com/shkroyas/Pacman-Game/main/scripts/deploy.sh -o /tmp/deploy.sh', 'chmod +x /tmp/deploy.sh', 'sudo /tmp/deploy.sh $LAST_GOOD 211125530162.dkr.ecr.us-east-1.amazonaws.com/pacman-game']" \
  --region us-east-1
```

---

### CI/CD Pipeline Failing

**Symptoms:**
- GitHub Actions showing red/failure
- Pushes to main don't deploy

**Common Causes & Fixes:**

| Error | Cause | Fix |
|-------|-------|-----|
| `Credentials could not be loaded` | Wrong secret name | Check `AWS_KEY_ACCESS_ID` (not `AWS_ACCESS_KEY_ID`) |
| `No module named pytest` | Old workflow running | Ensure `ci.yml` is deleted |
| `unknown shorthand flag: 'd'` | docker-compose issue | Deploy script uses `docker run` now |
| `dubious ownership` | git safe.directory | Deploy script uses curl, not git |

---

### SSM Command Not Executing

**Symptoms:**
- Deploy status shows `null`
- No command invocations found

**Diagnosis:**

```bash
# Check if SSM agent is registered
aws ssm describe-instance-information \
  --query "InstanceInformationList[*].[InstanceId,PingStatus]"

# Check IAM role attachment
aws ec2 describe-iam-instance-profile-associations \
  --filters "Name=instance-id,Values=i-0e939da1aaf5336f6"
```

**Resolution:**

```bash
# 1. Attach IAM role if missing
aws ec2 associate-iam-instance-profile \
  --instance-id i-0e939da1aaf5336f6 \
  --iam-instance-profile Name=pacman-game-instance-profile

# 2. Restart SSM agent
ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6 \
  "sudo systemctl restart amazon-ssm-agent"

# 3. Verify
ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6 \
  "sudo systemctl status amazon-ssm-agent"
```

---

## 🟡 Warning Issues

### High CPU Usage

**Threshold:** >80% for 5 minutes

**Diagnosis:**

```bash
# Check CPU
ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6 \
  "top -bn1 | head -20"

# Check container resource usage
ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6 \
  "docker stats --no-stream"
```

**Resolution:**

```bash
# Restart container
ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6 \
  "sudo docker restart pacman-backend"

# If persistent, consider upgrading to t3.small
```

---

### Disk Space Low

**Diagnosis:**

```bash
ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6 \
  "df -h && docker system df"
```

**Resolution:**

```bash
# Clean Docker resources
ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6 \
  "docker system prune -af --volumes"
```

---

### ECR Image Not Found

**Symptoms:**
- Deploy fails with "image not found"
- Docker pull fails

**Resolution:**

```bash
# Check ECR images
aws ecr describe-images \
  --repository-name pacman-game \
  --region us-east-1 \
  --query "imageDetails[*].[imageTags,imagePushedAt]" \
  --output table

# Rebuild and push
docker build -t pacman-game:latest .
docker tag pacman-game:latest 211125530162.dkr.ecr.us-east-1.amazonaws.com/pacman-game:latest
docker push 211125530162.dkr.ecr.us-east-1.amazonaws.com/pacman-game:latest
```

---

## 🟢 Routine Tasks

### Deploy New Version

```bash
# 1. Push to main (triggers CI/CD)
git push origin main

# 2. Monitor pipeline
# https://github.com/shkroyas/Pacman-Game/actions

# 3. Verify health
curl http://32.199.240.6:8000/api/health
```

### Manual Rollback

```bash
# Get last known good tag
LAST_GOOD=$(aws ssm get-parameter \
  --name /pacman/last-good-tag \
  --query Parameter.Value \
  --output text)

# Deploy it
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=tag:Name,Values=pacman-ai-server" \
  --parameters "commands=['curl -sf https://raw.githubusercontent.com/shkroyas/Pacman-Game/main/scripts/deploy.sh -o /tmp/deploy.sh', 'chmod +x /tmp/deploy.sh', 'sudo /tmp/deploy.sh $LAST_GOOD 211125530162.dkr.ecr.us-east-1.amazonaws.com/pacman-game']" \
  --region us-east-1
```

### View Logs

```bash
# CloudWatch (preferred)
aws logs tail /pacman-game/application --follow

# Direct from container
ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6 \
  "docker logs -f pacman-backend"
```

### Update SSM Parameters

```bash
# Update log level
aws ssm put-parameter --name /pacman/log-level --value DEBUG --type String --overwrite

# Update feature flags
aws ssm put-parameter --name /pacman/feature-flags --value '{"new_ui":true}' --type String --overwrite
```

---

## 📊 Monitoring Commands

### Health Dashboard

```bash
# Quick status check
echo "=== App Health ===" && curl -sf http://32.199.240.6:8000/api/health
echo -e "\n=== EC2 Status ===" && aws ec2 describe-instances --instance-ids i-0e939da1aaf5336f6 --query "Reservations[0].Instances[0].[State.Name,PublicIpAddress]"
echo -e "\n=== Docker Status ===" && ssh -i ~/.ssh/pacman-ai-key.pem ec2-user@32.199.240.6 "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
echo -e "\n=== Latest Deploy ===" && aws ssm get-parameter --name /pacman/last-good-tag --query Parameter.Value --output text
```

### CloudWatch Queries

```bash
# Recent errors
aws logs filter-log-events \
  --log-group-name /pacman-game/application \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s000) \
  --query "events[*].[timestamp,message]" \
  --output table

# Request count
aws logs filter-log-events \
  --log-group-name /pacman-game/application \
  --filter-pattern "GET /api/" \
  --start-time $(date -d '1 hour ago' +%s000) \
  --query "events | length(@)"
```

---

## 🔐 Security Incidents

### Suspected Unauthorized Access

```bash
# Check CloudTrail for API calls
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=ConsoleLogin \
  --max-results 10

# Check security group changes
aws ec2 describe-security-group-attributes \
  --group-id sg-09b658ff81bd3214c
```

### Rotate Access Keys

```bash
# Create new key
aws iam create-access-key --user-name royas-admin

# Delete old key
aws iam delete-access-key --user-name royas-admin --access-key-id OLD_KEY_ID

# Update GitHub secrets
# Go to: https://github.com/shkroyas/Pacman-Game/settings/secrets/actions
```

---

## 📋 Post-Incident Checklist

After any incident:

- [ ] Root cause identified
- [ ] Fix applied and tested
- [ ] Monitoring verified
- [ ] Documentation updated
- [ ] SNS notification received
- [ ] Rollback plan documented
- [ ] Prevention measures implemented

---

## 🔗 Useful Links

| Resource | URL |
|----------|-----|
| GitHub Actions | https://github.com/shkroyas/Pacman-Game/actions |
| Live App | http://32.199.240.6:8000 |
| Health Check | http://32.199.240.6:8000/api/health |
| Terraform State | s3://pacman-tf-state-211125530162 |
| CloudWatch Logs | /pacman-game/application |

---

*Last updated: September 2026*
