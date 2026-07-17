#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
version="${NOVARIDE_RELEASE_VERSION:-2026.1.4}"
release_dir="$root/apk-public/novaride/releases/$version"
cert_pem="$release_dir/release_certificate.pem"
cert_sha="$release_dir/release_certificate.sha256"
cert_json="$release_dir/certificate.json"
expected_sha="$("$root/scripts/mobile/release_lineage.py" fingerprint)"

"$root/scripts/mobile/verify_release_signing_credentials.sh"
mkdir -p "$release_dir"

keytool -exportcert -rfc \
  -keystore "$AFRIRIDE_ANDROID_KEYSTORE_PATH" \
  -alias "$AFRIRIDE_ANDROID_KEY_ALIAS" \
  -storepass "$AFRIRIDE_ANDROID_KEYSTORE_PASSWORD" \
  > "$cert_pem"

if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "$cert_pem" > "$cert_sha"
else
  shasum -a 256 "$cert_pem" > "$cert_sha"
fi

python3 - "$cert_json" "$version" "$AFRIRIDE_ANDROID_KEY_ALIAS" "$expected_sha" <<'PY'
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

output = Path(sys.argv[1])
data = {
    "product": "NovaRide",
    "version": sys.argv[2],
    "android_alias": sys.argv[3],
    "certificate_sha256": sys.argv[4],
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "certificate_pem": "release_certificate.pem",
    "certificate_file_sha256": "release_certificate.sha256",
}
output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY

echo "release certificate metadata generated in $release_dir"
