variable "environment" {
  description = "Deployment environment (e.g. prod, staging)"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

# ---------------------------------------------------------------------------
# Networking — supplied by the VPC module (separate issue)
# ---------------------------------------------------------------------------

variable "vpc_id" {
  description = "ID of the VPC to deploy into. Provided by the VPC/networking module."
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for RDS and ElastiCache. At least two for multi-AZ."
  type        = list(string)
}

variable "app_security_group_id" {
  description = "Security group attached to the GateThread app server. Storage SGs allow ingress from this."
  type        = string
}

# ---------------------------------------------------------------------------
# PostgreSQL (RDS)
# ---------------------------------------------------------------------------

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage_gb" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "GateThread"
}

variable "db_password" {
  description = "Master password for the RDS instance. Supply via TF_VAR_db_password or Secrets Manager."
  type        = string
  sensitive   = true
}

# ---------------------------------------------------------------------------
# Redis (ElastiCache)
# ---------------------------------------------------------------------------

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}
