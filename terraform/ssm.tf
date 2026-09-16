# SSM Parameter Store entries for application configuration.
# These are non-secret values; secrets should use SSM SecureString or Secrets Manager.

resource "aws_ssm_parameter" "log_level" {
  name        = "/pacman/log-level"
  description = "Application log level (DEBUG, INFO, WARNING, ERROR)"
  type        = "String"
  value       = "INFO"

  tags = {
    Name = "${var.project_name}-log-level"
  }
}

resource "aws_ssm_parameter" "domain" {
  name        = "/pacman/domain"
  description = "Domain name for the application (set once domain is registered)"
  type        = "String"
  value       = "none"

  tags = {
    Name = "${var.project_name}-domain"
  }
}

resource "aws_ssm_parameter" "app_version" {
  name        = "/pacman/app-version"
  description = "Current deployed application version (Git SHA)"
  type        = "String"
  value       = "none"

  tags = {
    Name = "${var.project_name}-app-version"
  }
}

resource "aws_ssm_parameter" "last_good_tag" {
  name        = "/pacman/last-good-tag"
  description = "Last known good Docker image tag (used for rollback)"
  type        = "String"
  value       = "none"

  tags = {
    Name = "${var.project_name}-last-good-tag"
  }
}

resource "aws_ssm_parameter" "feature_flags" {
  name        = "/pacman/feature-flags"
  description = "JSON-encoded feature flags for the application"
  type        = "String"
  value       = "{\"dark_mode\":true,\"ai_demo\":true}"

  tags = {
    Name = "${var.project_name}-feature-flags"
  }
}
