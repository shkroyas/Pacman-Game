# CloudWatch Log Group for application logs
resource "aws_cloudwatch_log_group" "app" {
  name              = "/pacman-game/application"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-logs"
  }
}

# SNS Topic for alarm notifications
resource "aws_sns_topic" "alarm" {
  name = "${var.project_name}-alarms"
}

# SNS Email Subscription (only created if email is provided)
resource "aws_sns_topic_subscription" "alarm_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarm.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CPU Utilization Alarm — triggers when CPU > 80% for 5 minutes
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.project_name}-cpu-high"
  alarm_description   = "CPU utilization exceeded 80% for 5 minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 5
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_actions       = [aws_sns_topic.alarm.arn]
  ok_actions          = [aws_sns_topic.alarm.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    InstanceId = aws_instance.app.id
  }

  tags = {
    Name = "${var.project_name}-cpu-alarm"
  }
}

# CloudWatch Synthetics Canary — monitors /api/health every 5 minutes
resource "aws_synthetics_canary" "health_check" {
  name                 = "${var.project_name}-health-check"
  artifact_s3_location = "s3://${aws_s3_bucket.canary_artifacts.bucket}/canary/"
  execution_role_arn   = aws_iam_role.canary.arn
  handler              = "apiCanaryHealthCheck.handler"
  zip_file             = data.archive_file.canary_lambda.output_path
  runtime_version      = "syn-nodejs-playwright-4.0"
  start_canary         = true

  schedule {
    expression = "rate(5 minutes)"
  }

  success_retention_period = 2
  failure_retention_period = 31

  tags = {
    Name = "${var.project_name}-canary"
  }
}

# S3 bucket for canary artifacts
resource "aws_s3_bucket" "canary_artifacts" {
  bucket = "${var.project_name}-canary-artifacts-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.project_name}-canary-artifacts"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "canary_artifacts" {
  bucket = aws_s3_bucket.canary_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "canary_artifacts" {
  bucket = aws_s3_bucket.canary_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Canary Lambda zip — Node.js Playwright script
data "archive_file" "canary_lambda" {
  type        = "zip"
  output_path = "/tmp/canary_lambda.zip"

  source {
    content  = <<-NODEJS
const { chromium } = require('playwright');

exports.handler = async (event) => {
  const url = "http://${aws_eip.app.public_ip}/api/health";
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const response = await page.goto(url, { timeout: 15000 });
    const body = await response.json();
    if (response.status() === 200 && body.status === 'healthy') {
      return { status: 'pass' };
    }
  } catch (e) {
    console.error('Health check failed:', e.message);
  } finally {
    await browser.close();
  }
  return { status: 'fail' };
};
NODEJS
    filename = "apiCanaryHealthCheck.js"
  }
}

# IAM Role for the canary
resource "aws_iam_role" "canary" {
  name = "${var.project_name}-canary-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "canary_basic" {
  role       = aws_iam_role.canary.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "canary_s3" {
  role       = aws_iam_role.canary.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# VPC network permissions for canary (needed when canary runs in a VPC)
resource "aws_iam_role_policy" "canary_vpc" {
  name = "${var.project_name}-canary-vpc"
  role = aws_iam_role.canary.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:AssignPrivateIpAddresses",
          "ec2:UnassignPrivateIpAddresses"
        ]
        Resource = "*"
      }
    ]
  })
}

# Security group for the canary (needs to reach the EC2 instance)
resource "aws_security_group" "canary" {
  name        = "${var.project_name}-canary-sg"
  description = "Security group for CloudWatch Synthetics canary"
  vpc_id      = data.aws_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-canary-sg"
  }
}

# CloudWatch Metric Filter for health check failures
resource "aws_cloudwatch_log_metric_filter" "health_failures" {
  name           = "${var.project_name}-health-failures"
  log_group_name = aws_cloudwatch_log_group.app.name
  pattern        = "[ERROR]"

  metric_transformation {
    name      = "HealthCheckErrors"
    namespace = "PacmanGame"
    value     = "1"
  }
}

# Alarm on health check errors
resource "aws_cloudwatch_metric_alarm" "health_errors" {
  alarm_name          = "${var.project_name}-health-errors"
  alarm_description   = "Application health check errors detected in logs"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HealthCheckErrors"
  namespace           = "PacmanGame"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_actions       = [aws_sns_topic.alarm.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Name = "${var.project_name}-health-error-alarm"
  }
}
