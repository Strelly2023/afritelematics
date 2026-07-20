#!/usr/bin/env bash
set -euo pipefail
ROLE="${1:?role required}"
APK="${2:?APK path required}"
[[ "$ROLE" == rider || "$ROLE" == driver ]] || { echo "invalid role" >&2; exit 2; }
[[ -f "$APK" ]] || { echo "APK missing" >&2; exit 2; }
command -v apksigner >/dev/null || { echo "apksigner missing" >&2; exit 2; }
apksigner verify --verbose --print-certs "$APK"
shasum -a 256 "$APK"
