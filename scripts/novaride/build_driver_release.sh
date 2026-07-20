#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
"$ROOT/scripts/novaride/check_signing_readiness.sh"
cd "$ROOT/driver_app/android"
./gradlew clean :app:assembleRelease :app:bundleRelease
"$ROOT/scripts/novaride/verify_mobile_release.sh" driver "$ROOT/driver_app/android/app/build/outputs/apk/release/app-release.apk"
