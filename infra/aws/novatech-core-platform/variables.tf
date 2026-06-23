variable "aws_region" {
  type        = string
  description = "AWS region for the core platform deployment."
  default     = "ap-southeast-2"
}

variable "name" {
  type        = string
  description = "Deployment name prefix."
  default     = "novatech-core-platform"
}

variable "container_image" {
  type        = string
  description = "Container image for the NovaTech API."
}

variable "vpc_id" {
  type        = string
  description = "VPC ID."
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs for the load balancer."
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for ECS and RDS."
}

variable "database_password" {
  type        = string
  description = "PostgreSQL password."
  sensitive   = true
}

variable "stripe_api_key_secret_arn" {
  type        = string
  description = "Secrets Manager ARN containing STRIPE_API_KEY."
}
