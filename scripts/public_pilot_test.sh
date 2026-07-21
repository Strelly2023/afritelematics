#!/usr/bin/env bash
set -euo pipefail

echo "Running NovaTech Public Pilot tests..."

python3 -m pytest tests/private_dev -q
python3 -m pytest tests/internal_qa -q
python3 -m pytest tests/controlled_pilot -q
python3 -m pytest tests/public_pilot -q

python3 -m pytest -m "public_pilot or pilot_real_limited or public_pilot_guard or public_pilot_payments or public_pilot_identity or public_pilot_monitoring or public_pilot_incident_response or public_pilot_compliance or public_pilot_release_guard" tests/public_pilot -q

echo "Public Pilot validation complete."
