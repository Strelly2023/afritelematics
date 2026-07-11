#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "usage: run_with_keychain_android_signing.sh COMMAND [ARGS...]" >&2
  exit 1
fi

read_secret() {
  local env_name="$1"
  shift

  if [ -n "${!env_name:-}" ]; then
    printf '%s' "${!env_name}"
    return 0
  fi

  local candidate
  for candidate in "$@"; do
    if value="$(security find-generic-password -s "$candidate" -w 2>/dev/null)"; then
      if [ -n "$value" ]; then
        printf '%s' "$value"
        return 0
      fi
    fi
  done

  echo "missing required Android signing secret: $env_name" >&2
  exit 1
}

export AFRIRIDE_ANDROID_KEYSTORE_PATH="$(
  read_secret AFRIRIDE_ANDROID_KEYSTORE_PATH \
    AFRIRIDE_ANDROID_KEYSTORE_PATH_V2 \
    AFRIRIDE_ANDROID_KEYSTORE_PATH
)"
export AFRIRIDE_ANDROID_KEYSTORE_PASSWORD="$(
  read_secret AFRIRIDE_ANDROID_KEYSTORE_PASSWORD \
    AFRIRIDE_ANDROID_KEYSTORE_PASSWORD_V2 \
    AFRIRIDE_ANDROID_KEYSTORE_PASSWORD
)"
export AFRIRIDE_ANDROID_KEY_ALIAS="$(
  read_secret AFRIRIDE_ANDROID_KEY_ALIAS \
    AFRIRIDE_ANDROID_KEY_ALIAS_V2 \
    AFRIRIDE_ANDROID_KEY_ALIAS
)"
export AFRIRIDE_ANDROID_KEY_PASSWORD="$(
  read_secret AFRIRIDE_ANDROID_KEY_PASSWORD \
    AFRIRIDE_ANDROID_KEY_PASSWORD_V2 \
    AFRIRIDE_ANDROID_KEY_PASSWORD
)"
export SIGNING_SECRET_PROVIDER="${SIGNING_SECRET_PROVIDER:-macos-keychain}"

exec "$@"
