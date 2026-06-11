#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-ubuntu@16.176.215.89:~/afritelematics/}"
SOURCE="${2:-/Users/ostrinov/afritelematics/}"
SSH_KEY_PATH="${AFRITECH_EC2_SSH_KEY:-$HOME/.ssh/afritech-key.pem}"
REMOTE_SSH="ssh -i ${SSH_KEY_PATH}"
SYNC_PATHS=(
  "pyproject.toml"
  "README.md"
  "requirements.txt"
  ".dockerignore"
  "deploy"
  "dashboard"
  "ecosystems"
  "scripts"
  "afritech"
  "afriride_system/__init__.py"
  "afriride_system/api"
  "afriride_system/backend"
  "afriride_system/django_app"
  "afriride_system/services"
)

if [[ ! -f "${SSH_KEY_PATH}" ]]; then
  echo "SSH key not found: ${SSH_KEY_PATH}" >&2
  echo "Set AFRITECH_EC2_SSH_KEY=/path/to/key.pem and retry." >&2
  exit 1
fi

echo "Syncing ${SOURCE} -> ${TARGET}"
echo "Using SSH key ${SSH_KEY_PATH}"

${REMOTE_SSH} "${TARGET%%:*}" "mkdir -p ~/afritelematics"

for rel_path in "${SYNC_PATHS[@]}"; do
  local_source="${SOURCE%/}/${rel_path}"
  if [[ ! -e "${local_source}" ]]; then
    continue
  fi

  remote_dir="${TARGET%/}"
  if [[ "${rel_path}" == */* ]]; then
    remote_dir="${remote_dir}/${rel_path%/*}/"
  else
    remote_dir="${remote_dir}/"
  fi

  echo "-> ${rel_path}"
  rsync -avz \
    -e "${REMOTE_SSH}" \
    --delete \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude '.mypy_cache' \
    --exclude '.ruff_cache' \
    --exclude '.idea' \
    --exclude '.vscode' \
    --exclude '.DS_Store' \
    --exclude 'node_modules' \
    --exclude 'dist' \
    --exclude 'build' \
    --exclude 'out' \
    --exclude '.expo' \
    --exclude '.dart_tool' \
    --exclude '.gradle' \
    --exclude 'Pods' \
    --exclude '*.apk' \
    --exclude '*.aab' \
    --exclude '*.ipa' \
    --exclude '*.dmg' \
    --exclude '*.sqlite3' \
    --exclude 'db.sqlite3' \
    --exclude 'htmlcov' \
    --exclude 'coverage.xml' \
    --exclude '.coverage' \
    --exclude '.env' \
    --exclude '.env.*' \
    --exclude 'afritech/ci' \
    --exclude 'afritech/tests' \
    --exclude 'afritech.egg-info' \
    "${local_source}" "${remote_dir}"
done

echo "Sync complete."
