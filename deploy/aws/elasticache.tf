# ---------------------------------------------------------------------------
# Security group — only the app server can reach Redis
# ---------------------------------------------------------------------------

resource "aws_security_group" "redis" {
  name        = "gatethread-redis-${var.environment}"
  description = "Allow Redis access from the GateThread app server only"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Redis from app server"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "gatethread-redis-${var.environment}"
    Environment = var.environment
  }
}

# ---------------------------------------------------------------------------
# Subnet group — ElastiCache must span at least two subnets
# ---------------------------------------------------------------------------

resource "aws_elasticache_subnet_group" "redis" {
  name       = "gatethread-redis-${var.environment}"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "gatethread-redis-${var.environment}"
    Environment = var.environment
  }
}

# ---------------------------------------------------------------------------
# ElastiCache cluster (single-node Redis 7)
#
# No persistence: matches docker-compose.yml config (--save "" --appendonly no).
# Transcript buffers and redaction maps are ephemeral by design — losing them
# on a node restart is acceptable and expected.
# ---------------------------------------------------------------------------

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "gatethread-${var.environment}"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]

  # No persistence — mirrors docker-compose.yml intentionally
  snapshot_retention_limit = 0

  tags = {
    Name        = "gatethread-redis-${var.environment}"
    Environment = var.environment
  }
}
