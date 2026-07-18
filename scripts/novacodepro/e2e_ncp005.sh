#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

cd novacodepro_portal
npm run test:e2e
