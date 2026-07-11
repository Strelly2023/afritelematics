#!/usr/bin/env bash
set -euo pipefail

apk_path="${1:?usage: verify_apk_artifact.sh APK_PATH PACKAGE_ID VERSION_NAME VERSION_CODE}"
expected_package="${2:?missing package id}"
expected_version="${3:?missing version name}"
expected_code="${4:?missing version code}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
expected_signing_sha256="${NOVARIDE_EXPECTED_SIGNING_SHA256:-$("$root/scripts/mobile/release_lineage.py" fingerprint)}"

test -f "$apk_path"
file "$apk_path"
unzip -t "$apk_path" >/dev/null

if command -v aapt >/dev/null 2>&1; then
  badging="$(aapt dump badging "$apk_path")"
  echo "$badging" | grep -q "package: name='$expected_package'"
  echo "$badging" | grep -q "versionCode='$expected_code'"
  echo "$badging" | grep -q "versionName='$expected_version'"
else
  echo "warning: aapt not found; package metadata validation skipped" >&2
fi

if command -v apksigner >/dev/null 2>&1; then
  signing_output="$(apksigner verify --verbose --print-certs "$apk_path")"
  printf '%s\n' "$signing_output"
  if printf '%s\n' "$signing_output" | grep -q "CN=Android Debug" && [ "${NOVARIDE_ALLOW_DEBUG_SIGNING:-0}" != "1" ]; then
    echo "debug signing certificate is not allowed for public pilot artifacts" >&2
    exit 1
  fi
  normalized_signing_output="$(printf '%s\n' "$signing_output" | tr '[:upper:]' '[:lower:]' | tr -d ':[:space:]')"
  normalized_expected_sha="$(printf '%s' "$expected_signing_sha256" | tr '[:upper:]' '[:lower:]' | tr -d ':[:space:]')"
  if ! printf '%s' "$normalized_signing_output" | grep -q "$normalized_expected_sha"; then
    echo "APK signing certificate does not match the NovaRide release lineage" >&2
    echo "expected SHA-256: $expected_signing_sha256" >&2
    exit 1
  fi
else
  echo "warning: apksigner not found; signing validation skipped" >&2
fi

if unzip -p "$apk_path" classes.dex 2>/dev/null | strings | grep -Eq 'localhost|127\.0\.0\.1|192\.168\.|10\.[0-9]+\.[0-9]+\.[0-9]+'; then
  echo "stale host found in APK byte strings" >&2
  exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "$apk_path"
else
  shasum -a 256 "$apk_path"
fi
