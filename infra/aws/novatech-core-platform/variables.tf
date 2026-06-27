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

variable "event_bus_backend" {
  type        = string
  description = "NovaPay event bus backend."
  default     = "in_memory"
}

variable "event_bus_kafka_brokers" {
  type        = string
  description = "Comma-separated Kafka bootstrap brokers."
  default     = ""
}

variable "novapay_region" {
  type        = string
  description = "NovaPay region label used for event annotation."
  default     = "AU"
}

variable "novatrust_signing_provider" {
  type        = string
  description = "NovaTrust signing backend."
  default     = "ed25519"
}

variable "novatrust_kms_signing_enabled" {
  type        = bool
  description = "Enable KMS-backed signing."
  default     = false
}

variable "novatrust_kms_signing_algorithm" {
  type        = string
  description = "AWS KMS signing algorithm."
  default     = "ECDSA_SHA_256"
}

variable "novapay_cbdc_live_enabled" {
  type        = bool
  description = "Enable live CBDC provider mode."
  default     = false
}

variable "novapay_cbdc_network" {
  type        = string
  description = "CBDC network label."
  default     = "pilot-ledger"
}

variable "novapay_rollout_mode" {
  type        = string
  description = "Rollout mode for the NovaPay deployment."
  default     = "canary"
}

variable "novapay_primary_corridor" {
  type        = string
  description = "Primary live corridor label."
  default     = "AU->KE"
}

variable "novapay_corridors" {
  type        = list(string)
  description = "Approved corridor labels for this deployment."
  default     = ["AU->KE", "AU->BI", "AU->CD", "USA->KE"]
}

variable "novapay_settlement_mode" {
  type        = string
  description = "Settlement strategy for the corridor."
  default     = "pre_funded"
}

variable "novapay_mobile_money_live_enabled" {
  type        = bool
  description = "Enable live mobile money execution."
  default     = false
}

variable "novapay_compliance_provider" {
  type        = string
  description = "Compliance provider label."
  default     = "sumsub"
}

variable "novapay_compliance_live_enabled" {
  type        = bool
  description = "Enable live compliance provider checks."
  default     = false
}
