variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "Name of the SSH key pair for EC2"
  type        = string
  default     = "pacman-ai-key"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed SSH access (your IP only). Remove once SSH is no longer needed."
  type        = string
  default     = "0.0.0.0/0"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "pacman-game"
}

variable "alert_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = "shakyaroyas@gmail.com"
}
