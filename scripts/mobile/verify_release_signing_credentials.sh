#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
expected_fingerprint="${NOVARIDE_EXPECTED_SIGNING_SHA256:-$("$root/scripts/mobile/release_lineage.py" fingerprint)}"
expected_alias="$("$root/scripts/mobile/release_lineage.py" alias)"
allowed_secret_providers="$("$root/scripts/mobile/release_lineage.py" secret-providers)"

required_vars=(
  AFRIRIDE_ANDROID_KEYSTORE_PATH
  AFRIRIDE_ANDROID_KEYSTORE_PASSWORD
  AFRIRIDE_ANDROID_KEY_ALIAS
  AFRIRIDE_ANDROID_KEY_PASSWORD
)

for name in "${required_vars[@]}"; do
  if [ -z "${!name:-}" ]; then
    echo "missing required Android signing environment variable: $name" >&2
    exit 1
  fi
done

if [ -z "${SIGNING_SECRET_PROVIDER:-}" ]; then
  echo "missing required signing secret provider: SIGNING_SECRET_PROVIDER" >&2
  exit 1
fi

if ! printf '%s\n' "$allowed_secret_providers" | grep -qx "$SIGNING_SECRET_PROVIDER"; then
  echo "unsupported signing secret provider: $SIGNING_SECRET_PROVIDER" >&2
  echo "allowed providers:" >&2
  printf '  %s\n' $allowed_secret_providers >&2
  exit 1
fi

if [ "$AFRIRIDE_ANDROID_KEY_ALIAS" != "$expected_alias" ]; then
  echo "Android signing key alias mismatch" >&2
  echo "expected alias: $expected_alias" >&2
  exit 1
fi

if [ ! -f "$AFRIRIDE_ANDROID_KEYSTORE_PATH" ]; then
  echo "Android signing keystore not found: $AFRIRIDE_ANDROID_KEYSTORE_PATH" >&2
  exit 1
fi

if ! command -v keytool >/dev/null 2>&1; then
  echo "keytool is required to verify Android release signing credentials" >&2
  exit 1
fi

keytool_output="$(
  keytool -list -v \
    -keystore "$AFRIRIDE_ANDROID_KEYSTORE_PATH" \
    -alias "$AFRIRIDE_ANDROID_KEY_ALIAS" \
    -storepass "$AFRIRIDE_ANDROID_KEYSTORE_PASSWORD" 2>&1
)"

normalized_output="$(printf '%s\n' "$keytool_output" | tr '[:upper:]' '[:lower:]' | tr -d ':[:space:]')"
normalized_expected="$(printf '%s' "$expected_fingerprint" | tr '[:upper:]' '[:lower:]' | tr -d ':[:space:]')"

if ! printf '%s' "$normalized_output" | grep -q "$normalized_expected"; then
  echo "Android signing certificate fingerprint mismatch" >&2
  echo "expected SHA-256: $expected_fingerprint" >&2
  exit 1
fi

echo "Android release signing credentials verified"
echo "alias: $AFRIRIDE_ANDROID_KEY_ALIAS"
echo "certificate SHA-256: $expected_fingerprint"
