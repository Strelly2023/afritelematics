output "api_url" {
  value = "http://${aws_lb.api.dns_name}"
}

output "postgres_endpoint" {
  value = aws_db_instance.postgres.address
}

output "novatrust_kms_key_id" {
  value = aws_kms_key.novatrust_signing.key_id
}

output "region_label" {
  value = var.novapay_region
}

output "rollout_mode" {
  value = var.novapay_rollout_mode
}

output "primary_corridor" {
  value = var.novapay_primary_corridor
}

output "corridors" {
  value = var.novapay_corridors
}

output "settlement_mode" {
  value = var.novapay_settlement_mode
}

output "mobile_money_live_enabled" {
  value = var.novapay_mobile_money_live_enabled
}

output "compliance_provider" {
  value = var.novapay_compliance_provider
}

output "compliance_live_enabled" {
  value = var.novapay_compliance_live_enabled
}
