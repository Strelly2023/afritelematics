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
