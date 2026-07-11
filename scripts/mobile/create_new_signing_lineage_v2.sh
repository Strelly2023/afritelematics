#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
keystore_path="${NOVARIDE_V2_KEYSTORE_PATH:-$root/.secrets/novaride-release-keystore-v2.jks}"
alias_name="${NOVARIDE_V2_KEY_ALIAS:-novaride-release}"

if [ "${NOVARIDE_CONFIRM_NEW_LINEAGE:-}" != "retire-legacy-and-create-v2" ]; then
  echo "refusing to create a new Android signing lineage without explicit approval" >&2
  echo "set NOVARIDE_CONFIRM_NEW_LINEAGE=retire-legacy-and-create-v2 after formal legacy recovery failure" >&2
  exit 1
fi

for name in NOVARIDE_V2_KEYSTORE_PASSWORD NOVARIDE_V2_KEY_PASSWORD SIGNING_SECRET_PROVIDER; do
  if [ -z "${!name:-}" ]; then
    echo "missing required v2 signing variable: $name" >&2
    exit 1
  fi
done

allowed_secret_providers="$("$root/scripts/mobile/release_lineage.py" secret-providers)"
if ! printf '%s\n' "$allowed_secret_providers" | grep -qx "$SIGNING_SECRET_PROVIDER"; then
  echo "unsupported signing secret provider: $SIGNING_SECRET_PROVIDER" >&2
  exit 1
fi

if [ -e "$keystore_path" ]; then
  echo "refusing to overwrite existing v2 keystore: $keystore_path" >&2
  exit 1
fi

mkdir -p "$(dirname "$keystore_path")"

keytool -genkeypair \
  -keystore "$keystore_path" \
  -storepass "$NOVARIDE_V2_KEYSTORE_PASSWORD" \
  -keypass "$NOVARIDE_V2_KEY_PASSWORD" \
  -alias "$alias_name" \
  -keyalg RSA \
  -keysize 4096 \
  -validity 10000 \
  -dname "CN=NovaRide Release v2, OU=NovaTech, O=NovaTech, L=Melbourne, ST=Victoria, C=AU"

fingerprint="$(
  keytool -list -v \
    -keystore "$keystore_path" \
    -storepass "$NOVARIDE_V2_KEYSTORE_PASSWORD" \
    -alias "$alias_name" |
    awk -F': ' '/SHA256:/{print $2; exit}' |
    tr -d ':[:space:]' |
    tr '[:upper:]' '[:lower:]'
)"

if [ -z "$fingerprint" ]; then
  echo "failed to read v2 signing certificate fingerprint" >&2
  exit 1
fi

echo "NovaRide Android signing lineage v2 generated"
echo "keystore: $keystore_path"
echo "alias: $alias_name"
echo "certificate SHA-256: $fingerprint"
echo
echo "Next steps:"
echo "1. Store NOVARIDE_V2_KEYSTORE_PASSWORD and NOVARIDE_V2_KEY_PASSWORD in the approved secret manager."
echo "2. Back up $keystore_path in encrypted offline storage."
echo "3. Update docs/mobile/release/release_lineage.yaml to retire legacy and activate v2 with this fingerprint."
echo "4. Communicate one-time reinstall migration to pilot users."
