#!/usr/bin/env bash
set -euo pipefail

python3 -m pytest -m 'private_dev or local_only or simulated_payment or no_live_charge' tests/private_dev -q

