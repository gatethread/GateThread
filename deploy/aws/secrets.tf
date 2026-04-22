resource "aws_secretsmanager_secret" "db_password" {
  name        = "gatethread/${var.environment}/db_password"
  description = "GateThread RDS master password"

  tags = {
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}

resource "aws_secretsmanager_secret" "api_key" {
  name        = "gatethread/${var.environment}/api_key"
  description = "GateThread gateway API key"

  tags = {
    Environment = var.environment
  }
}
