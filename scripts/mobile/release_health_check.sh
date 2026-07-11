#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
version="${NOVARIDE_RELEASE_VERSION:-2026.1.3}"
release_dir="$root/apk-public/novaride/releases/$version"

echo "NovaRide release health check: $version"

command -v keytool >/dev/null 2>&1 || {
  echo "missing required tool: keytool" >&2
  exit 1
}

android_sdk="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}}"

if command -v apksigner >/dev/null 2>&1; then
  echo "apksigner: available"
elif [ -d "$android_sdk/build-tools" ] && find "$android_sdk/build-tools" -name apksigner -type f -print -quit 2>/dev/null | grep -q .; then
  echo "apksigner: available under $android_sdk"
else
  echo "missing required tool: apksigner" >&2
  exit 1
fi

test -d "$release_dir" || {
  echo "missing release output directory: $release_dir" >&2
  exit 1
}

test -f "$root/docs/mobile/release/release_lineage.yaml" || {
  echo "missing release lineage registry" >&2
  exit 1
}

test -f "$root/apk-public/novaride/releases/$version/release-manifest.json" || {
  echo "missing release manifest for $version" >&2
  exit 1
}

"$root/scripts/mobile/verify_release_signing_credentials.sh"
python3 "$root/scripts/mobile/verify_release_manifest.py"
python3 "$root/scripts/mobile/assert_release_provenance.py"

echo "NovaRide release health check passed"
