#!/usr/bin/env bash
set -euo pipefail

release_dir="${1:?usage: publish_static_release.sh RELEASE_DIR VERSION}"
version="${2:?missing release version}"
target="${NOVARIDE_PUBLICATION_TARGET:?NOVARIDE_PUBLICATION_TARGET must be user@host:/absolute/static/root}"

test -d "$release_dir"
test -f "$release_dir/release-manifest.json"
test -f "$release_dir/novaride-rider-v$version-public-pilot.apk"
test -f "$release_dir/novaride-driver-v$version-public-pilot.apk"

case "$target" in
  *:/*) ;;
  *) echo "NOVARIDE_PUBLICATION_TARGET must be an SSH rsync target" >&2; exit 1 ;;
esac

rsync -az --checksum --delay-updates --chmod=F644,D755 \
  "$release_dir/" "$target/novaride/releases/$version/"

echo "published immutable NovaRide release $version"
