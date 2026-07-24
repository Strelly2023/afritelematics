#!/usr/bin/env bash
set -euo pipefail
ROLE="${1:?role required}"
APK="${2:?APK path required}"
CERTIFICATION="${3:-}"
[[ "$ROLE" == rider || "$ROLE" == driver ]] || { echo "invalid role" >&2; exit 2; }
[[ -f "$APK" ]] || { echo "APK missing" >&2; exit 2; }
command -v apksigner >/dev/null || { echo "apksigner missing" >&2; exit 2; }
apksigner verify --verbose --print-certs "$APK"
shasum -a 256 "$APK"

ARGS=(--tested-binary "$APK" --release-binary "$APK")
if [[ -n "$CERTIFICATION" ]]; then
  ARGS+=(--certification "$CERTIFICATION")
fi
python3 -m afritech.ci.novaride_mobile_feature_gate "${ARGS[@]}"
