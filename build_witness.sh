#!/usr/bin/env bash
set -euo pipefail

OUT="witness_v1.txt"
: > "$OUT"

find afritech/proof/witness \
  \( \
    -type d \( \
      -name .git -o \
      -name __pycache__ -o \
      -name .mypy_cache -o \
      -name .pytest_cache -o \
      -name .venv -o \
      -name venv -o \
      -name build -o \
      -name dist \
    \) -prune \
  \) -o \
  \( \
    -type f \( \
      -name '*.yaml' -o \
      -name '*.yml' \
    \) -print0 \
  \) 2>/dev/null |
LC_ALL=C sort -z |
while IFS= read -r -d '' file; do
  {
    printf '===== %s =====\n' "$file"
    cat "$file"
    printf '\n\n'
  } >> "$OUT"
done
