#!/usr/bin/env bash
set -euo pipefail

if [ -z "${AFRIRIDE_ANDROID_KEYSTORE_BASE64:-}" ]; then
  echo "missing required Android signing environment variable: AFRIRIDE_ANDROID_KEYSTORE_BASE64" >&2
  exit 1
fi

output_path="${AFRIRIDE_ANDROID_KEYSTORE_PATH:-${1:-}}"
if [ -z "$output_path" ]; then
  echo "usage: materialize_android_keystore.sh [OUTPUT_PATH]" >&2
  exit 1
fi

mkdir -p "$(dirname "$output_path")"
printf '%s' "$AFRIRIDE_ANDROID_KEYSTORE_BASE64" | base64 --decode > "$output_path"
chmod 600 "$output_path"

echo "$output_path"
