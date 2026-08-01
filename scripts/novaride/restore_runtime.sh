#!/usr/bin/env bash
set -euo pipefail

BACKUP_PATH="${1:-}"
TARGET_DSN="${NOVARIDE_RESTORE_TARGET_DSN:-}"
SOURCE_DSN="${NOVARIDE_POSTGRES_DSN:-}"
AGE_IDENTITY="${NOVARIDE_BACKUP_AGE_IDENTITY:-}"

if [[ -z "$BACKUP_PATH" || ! -f "$BACKUP_PATH" ]]; then
  echo "usage: NOVARIDE_RESTORE_TARGET_DSN=... $0 BACKUP_PATH" >&2
  exit 2
fi
if [[ -z "$TARGET_DSN" ]]; then
  echo "NOVARIDE_RESTORE_TARGET_DSN is required for isolated restore" >&2
  exit 2
fi
if [[ -n "$SOURCE_DSN" && "$TARGET_DSN" == "$SOURCE_DSN" ]]; then
  echo "restore target must not equal the source/production DSN" >&2
  exit 2
fi
if [[ "${NOVARIDE_ALLOW_ISOLATED_RESTORE:-}" != "1" ]]; then
  echo "set NOVARIDE_ALLOW_ISOLATED_RESTORE=1 to authorize replacement of the isolated target" >&2
  exit 2
fi
if ! command -v pg_restore >/dev/null 2>&1 || ! command -v psql >/dev/null 2>&1; then
  echo "pg_restore and psql are required" >&2
  exit 2
fi

RESTORE_PATH="$BACKUP_PATH"
TEMP_PATH=""
cleanup() {
  [[ -z "$TEMP_PATH" ]] || rm -f "$TEMP_PATH"
}
trap cleanup EXIT

if [[ "$BACKUP_PATH" == *.age ]]; then
  if [[ -z "$AGE_IDENTITY" || ! -f "$AGE_IDENTITY" ]]; then
    echo "NOVARIDE_BACKUP_AGE_IDENTITY must reference the decryption identity" >&2
    exit 2
  fi
  if ! command -v age >/dev/null 2>&1; then
    echo "age is required for encrypted restore" >&2
    exit 2
  fi
  TEMP_PATH="$(mktemp "${TMPDIR:-/tmp}/novaride-restore.XXXXXX.dump")"
  age --decrypt --identity "$AGE_IDENTITY" --output "$TEMP_PATH" "$BACKUP_PATH"
  RESTORE_PATH="$TEMP_PATH"
fi

pg_restore --list "$RESTORE_PATH" >/dev/null
STARTED="$(date +%s)"
pg_restore \
  --dbname="$TARGET_DSN" \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  --exit-on-error \
  "$RESTORE_PATH"

psql "$TARGET_DSN" -v ON_ERROR_STOP=1 -Atc \
  "SELECT CASE WHEN COUNT(*) > 0 THEN 'restore_integrity_pass' ELSE 'restore_integrity_fail' END FROM pg_catalog.pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema');" \
  | grep -Fxq restore_integrity_pass

FINISHED="$(date +%s)"
printf 'restore_integrity=PASS\nrestore_seconds=%s\n' "$((FINISHED - STARTED))"
