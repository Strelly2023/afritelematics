#!/usr/bin/env bash
set -euo pipefail
for name in AFRIRIDE_ANDROID_KEYSTORE_PATH AFRIRIDE_ANDROID_KEYSTORE_PASSWORD AFRIRIDE_ANDROID_KEY_ALIAS AFRIRIDE_ANDROID_KEY_PASSWORD; do
  if [[ -z "${!name:-}" ]]; then
    echo "signing readiness: BLOCKED ($name is not set)" >&2
    exit 2
  fi
done
[[ -f "$AFRIRIDE_ANDROID_KEYSTORE_PATH" ]] || { echo "signing readiness: BLOCKED (keystore missing)" >&2; exit 2; }
keytool -list -keystore "$AFRIRIDE_ANDROID_KEYSTORE_PATH" -alias "$AFRIRIDE_ANDROID_KEY_ALIAS" -storepass:env AFRIRIDE_ANDROID_KEYSTORE_PASSWORD >/dev/null
echo "signing readiness: PASS"
