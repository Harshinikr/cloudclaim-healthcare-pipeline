variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "cloudclaim"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "bucket_name" {
  description = "S3 bucket name for claim ingestion"
  type        = string
  default     = "cloudclaim-harsh-dev-2026"
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for claims storage"
  type        = string
  default     = "cloudclaim-claims"
}

variable "alert_email" {
  description = "Email address for rejection alerts"
  type        = string
  default     = "harshini2602@gmail.com"
}