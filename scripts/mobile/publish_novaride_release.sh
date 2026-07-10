#!/usr/bin/env bash
set -euo pipefail

version="2026.1.3"
channel="public-pilot"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
release_dir="$root/apk-public/novaride/releases/$version"
alias_dir="$root/apk-public/novaride"

mkdir -p "$release_dir" "$alias_dir" "$root/apk"

write_sha256() {
  local path="$1"
  local output="$2"
  local name="${3:-$(basename "$path")}"
  if command -v sha256sum >/dev/null 2>&1; then
    local hash
    hash="$(sha256sum "$path" | awk '{print $1}')"
    printf '%s  %s\n' "$hash" "$name" > "$output"
  else
    local hash
    hash="$(shasum -a 256 "$path" | awk '{print $1}')"
    printf '%s  %s\n' "$hash" "$name" > "$output"
  fi
}

python3 "$root/scripts/mobile/assert_version_increment.py"
python3 "$root/scripts/mobile/assert_no_stale_api_hosts.py"

for app in rider driver; do
  source_apk="$root/apk/novaride-$app-v$version-$channel.apk"
  test -f "$source_apk"
  write_sha256 "$source_apk" "$source_apk.sha256"

  tmp="$release_dir/.$(basename "$source_apk").tmp"
  cp "$source_apk" "$tmp"
  write_sha256 "$tmp" "$tmp.sha256" "$(basename "$source_apk")"
  mv "$tmp" "$release_dir/$(basename "$source_apk")"
  mv "$tmp.sha256" "$release_dir/$(basename "$source_apk").sha256"

  alias_apk="$alias_dir/$app-latest-public-pilot.apk"
  alias_tmp="$alias_apk.tmp"
  cp "$source_apk" "$alias_tmp"
  mv "$alias_tmp" "$alias_apk"
  write_sha256 "$alias_apk" "$alias_apk.sha256"
done

for app in rider driver; do
  source_ipa="$root/apk/novaride-$app-v$version-$channel.ipa"
  if [ -f "$source_ipa" ]; then
    write_sha256 "$source_ipa" "$source_ipa.sha256"
    tmp="$release_dir/.$(basename "$source_ipa").tmp"
    cp "$source_ipa" "$tmp"
    write_sha256 "$tmp" "$tmp.sha256" "$(basename "$source_ipa")"
    mv "$tmp" "$release_dir/$(basename "$source_ipa")"
    mv "$tmp.sha256" "$release_dir/$(basename "$source_ipa").sha256"

    alias_ipa="$alias_dir/$app-latest-public-pilot.ipa"
    alias_tmp="$alias_ipa.tmp"
    cp "$source_ipa" "$alias_tmp"
    mv "$alias_tmp" "$alias_ipa"
    write_sha256 "$alias_ipa" "$alias_ipa.sha256"
  fi
done

cp "$root/docs/mobile/release/novaride_rider_v2026.1.3_manifest.json" "$release_dir/novaride_rider_v2026.1.3_manifest.json"
cp "$root/docs/mobile/release/novaride_driver_v2026.1.3_manifest.json" "$release_dir/novaride_driver_v2026.1.3_manifest.json"
cp "$root/docs/mobile/release/novaride_fleet_v2026.1.3_manifest.json" "$release_dir/novaride_fleet_v2026.1.3_manifest.json"
cp "$root/docs/mobile/release/novaride_operator_v2026.1.3_manifest.json" "$release_dir/novaride_operator_v2026.1.3_manifest.json"
cp "$root/docs/mobile/release/NOVARIDE_V2026_1_3_RELEASE_NOTES.md" "$release_dir/NOVARIDE_V2026_1_3_RELEASE_NOTES.md"

python3 "$root/scripts/mobile/assert_release_provenance.py"
echo "NovaRide $version public pilot artifacts published to $release_dir"
