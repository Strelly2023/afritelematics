#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
COMMIT="$(git rev-parse HEAD)"
echo "NovaRide traceability validation commit=$COMMIT"
echo "+ python3 -m afritech.ci.novaride_requirements_validator --json"
python3 -m afritech.ci.novaride_requirements_validator --json
echo "+ python3 -m afritech.ci.novaride_mobile_feature_gate"
set +e
python3 -m afritech.ci.novaride_mobile_feature_gate
STATUS=$?
set -e
if [[ "$STATUS" -eq 0 ]]; then
  echo "NOVARIDE_MOBILE_FEATURE_GATE: GO"
else
  echo "NOVARIDE_MOBILE_FEATURE_GATE: NO_GO (expected until every mandatory feature has objective release evidence)"
fi
exit "$STATUS"
