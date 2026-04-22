terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Replace with your S3 backend details before running terraform init in prod.
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "gatethread/storage/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "GateThread"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}
