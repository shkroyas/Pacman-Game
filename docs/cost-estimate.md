# Cost Estimate

## Monthly Cost Breakdown (us-east-1)

| Resource | Free Tier | Monthly Cost | Notes |
|----------|-----------|-------------|-------|
| EC2 t2.micro | 750 hrs/mo | $0 (free tier) | ~$8.50/mo after free tier expires |
| EBS (20GB gp3) | 30GB/mo | $0 (free tier) | ~$1.60/mo after free tier |
| Elastic IP | Free while attached | $0 | ~$3.65/mo if instance is stopped |
| ECR | 500MB storage | $0 | ~$0.10/GB/mo after free tier |
| CloudWatch Logs | 5GB/mo ingestion | $0 (free tier) | ~$0.50/GB/mo after free tier |
| CloudWatch Alarms | 10 free alarms | $0 | ~$0.10/alarm/mo after free tier |
| SNS | 1M publishes | $0 (free tier) | ~$0.50/mo minimal traffic |
| SSM Parameter Store | 10K parameters | $0 | Free tier covers this use case |
| S3 (canary artifacts) | 5GB/mo | $0 (free tier) | Negligible at this scale |
| Route 53 (when domain added) | 1 hosted zone | $0.50/mo | Domain registration ~$12/yr |
| Let's Encrypt Certificate | N/A | $0 | Always free |
| Docker Hub pulls | N/A | $0 | Using ECR instead |

## Total Monthly Cost

### During Free Tier (first 12 months)
**~$0.50/mo** (just Route 53 hosted zone, if domain is registered)

### After Free Tier
**~$12-15/mo** estimate:
- EC2 t2.micro: ~$8.50
- EBS: ~$1.60
- CloudWatch: ~$2-3
- Route 53: ~$0.50
- SNS/SSM/S3: ~$1

## Cost Comparison

| Approach | Monthly Cost |
|----------|-------------|
| **This plan (Nginx sidecar)** | **~$0.50-15/mo** |
| ALB + EC2 | ~$18-25/mo |
| ECS Fargate | ~$15-30/mo |
| AWS App Runner | ~$5-25/mo |

The Nginx sidecar approach saves ~$16-18/mo compared to an ALB, which is the main
reason for this architecture choice. The tradeoff is manual TLS management via Certbot
instead of automatic ACM certificate renewal.

## Free Tier Considerations

- EC2 750 hrs/mo = ~31 days of continuous t2.micro (covers 1 instance 24/7)
- EBS 30GB/mo covers the 20GB root volume
- CloudWatch Logs 5GB/mo ingestion covers application logs at this traffic level
- All other services are within free tier limits for a single low-traffic instance

## Scaling Costs

If traffic grows beyond free tier limits:
- Consider upgrading to t3.small (~$15/mo)
- Add a second AZ for high availability (doubles EC2 cost)
- Move to ALB if you need multi-instance deployment (~$16/mo + target instances)
- At that point, ECS Fargate becomes competitive (~$30-50/mo for small workloads)
