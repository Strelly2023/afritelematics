#!/usr/bin/env bash
set -euo pipefail

DSN="${NOVARIDE_POSTGRES_DSN:-}"
BACKUP_DIR="${NOVARIDE_BACKUP_DIR:-artifacts/novaride/production-operations/backups}"
AGE_RECIPIENT="${NOVARIDE_BACKUP_AGE_RECIPIENT:-}"
ENVIRONMENT="${NOVARIDE_ENVIRONMENT:-production}"

if [[ -z "$DSN" ]]; then
  echo "NOVARIDE_POSTGRES_DSN is required for PostgreSQL backup" >&2
  exit 2
fi
if ! command -v pg_dump >/dev/null 2>&1; then
  echo "pg_dump is required" >&2
  exit 2
fi
if [[ "$ENVIRONMENT" == "production" && -z "$AGE_RECIPIENT" ]]; then
  echo "NOVARIDE_BACKUP_AGE_RECIPIENT is required for encrypted production backups" >&2
  exit 2
fi
if [[ -n "$AGE_RECIPIENT" ]] && ! command -v age >/dev/null 2>&1; then
  echo "age is required when NOVARIDE_BACKUP_AGE_RECIPIENT is set" >&2
  exit 2
fi

mkdir -p "$BACKUP_DIR"
umask 077
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PLAIN_PATH="$BACKUP_DIR/novaride-$STAMP.dump"
FINAL_PATH="$PLAIN_PATH"
MANIFEST_PATH="$BACKUP_DIR/novaride-$STAMP.manifest"

cleanup() {
  rm -f "$PLAIN_PATH"
}
trap cleanup EXIT

pg_dump \
  --dbname="$DSN" \
  --format=custom \
  --compress=9 \
  --no-owner \
  --no-privileges \
  --file="$PLAIN_PATH"

pg_restore --list "$PLAIN_PATH" >/dev/null

if [[ -n "$AGE_RECIPIENT" ]]; then
  FINAL_PATH="$PLAIN_PATH.age"
  age --recipient "$AGE_RECIPIENT" --output "$FINAL_PATH" "$PLAIN_PATH"
fi

DIGEST="$(shasum -a 256 "$FINAL_PATH" | awk '{print $1}')"
SIZE="$(wc -c < "$FINAL_PATH" | tr -d ' ')"
{
  printf 'created_at=%s\n' "$STAMP"
  printf 'environment=%s\n' "$ENVIRONMENT"
  printf 'backup_file=%s\n' "$(basename "$FINAL_PATH")"
  printf 'encrypted=%s\n' "$([[ -n "$AGE_RECIPIENT" ]] && printf true || printf false)"
  printf 'sha256=%s\n' "$DIGEST"
  printf 'bytes=%s\n' "$SIZE"
  printf 'pg_dump_version=%s\n' "$(pg_dump --version)"
} > "$MANIFEST_PATH"

trap - EXIT
if [[ "$FINAL_PATH" != "$PLAIN_PATH" ]]; then
  rm -f "$PLAIN_PATH"
fi
printf '%s\n' "$FINAL_PATH"
