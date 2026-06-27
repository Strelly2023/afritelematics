terraform {
  required_version = ">= 1.6.0"
}

locals {
  config = jsondecode(file("${path.module}/terraform.tfvars.json"))
}

module "novatech_core" {
  source = "../.."

  aws_region                         = local.config.aws_region
  name                               = local.config.name
  container_image                    = local.config.container_image
  vpc_id                             = local.config.vpc_id
  public_subnet_ids                  = local.config.public_subnet_ids
  private_subnet_ids                 = local.config.private_subnet_ids
  database_password                  = local.config.database_password
  stripe_api_key_secret_arn          = local.config.stripe_api_key_secret_arn
  event_bus_backend                  = local.config.event_bus_backend
  event_bus_kafka_brokers            = local.config.event_bus_kafka_brokers
  novapay_region                     = local.config.novapay_region
  novatrust_signing_provider         = local.config.novatrust_signing_provider
  novatrust_kms_signing_enabled      = local.config.novatrust_kms_signing_enabled
  novatrust_kms_signing_algorithm    = local.config.novatrust_kms_signing_algorithm
  novapay_cbdc_live_enabled          = local.config.novapay_cbdc_live_enabled
  novapay_cbdc_network               = local.config.novapay_cbdc_network
  novapay_rollout_mode               = local.config.novapay_rollout_mode
  novapay_primary_corridor           = local.config.novapay_primary_corridor
  novapay_corridors                  = local.config.novapay_corridors
  novapay_settlement_mode            = local.config.novapay_settlement_mode
  novapay_mobile_money_live_enabled  = local.config.novapay_mobile_money_live_enabled
  novapay_compliance_provider        = local.config.novapay_compliance_provider
  novapay_compliance_live_enabled    = local.config.novapay_compliance_live_enabled
  novapay_env_vars                   = local.config.novapay_env_vars
  novapay_secret_arns                = local.config.novapay_secret_arns
}
