#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../infra/aws/novatech-core-platform"
terraform init
terraform plan
terraform apply
