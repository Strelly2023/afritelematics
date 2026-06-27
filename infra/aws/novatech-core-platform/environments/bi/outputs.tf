output "api_url" {
  value = module.novatech_core.api_url
}

output "postgres_endpoint" {
  value = module.novatech_core.postgres_endpoint
}

output "novatrust_kms_key_id" {
  value = module.novatech_core.novatrust_kms_key_id
}

output "region_label" {
  value = module.novatech_core.region_label
}

output "rollout_mode" {
  value = module.novatech_core.rollout_mode
}

output "primary_corridor" {
  value = module.novatech_core.primary_corridor
}

output "corridors" {
  value = module.novatech_core.corridors
}

output "settlement_mode" {
  value = module.novatech_core.settlement_mode
}

output "mobile_money_live_enabled" {
  value = module.novatech_core.mobile_money_live_enabled
}

output "compliance_provider" {
  value = module.novatech_core.compliance_provider
}

output "compliance_live_enabled" {
  value = module.novatech_core.compliance_live_enabled
}
