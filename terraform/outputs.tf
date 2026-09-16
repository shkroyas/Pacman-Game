output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.app.id
}

output "instance_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.app.public_ip
}

output "elastic_ip" {
  description = "Elastic IP address (stable across instance replacement)"
  value       = aws_eip.app.public_ip
}

output "ecr_repository_url" {
  description = "URL of the ECR repository for pushing Docker images"
  value       = aws_ecr_repository.app.repository_url
}

output "ecr_repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.app.arn
}

output "security_group_id" {
  description = "ID of the application security group"
  value       = aws_security_group.app.id
}
