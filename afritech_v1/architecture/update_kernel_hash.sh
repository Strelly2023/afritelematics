#!/bin/bash
#afritech_v1/architecture/update_kernel_hash.sh

echo "⚠️ Updating kernel hash — requires intentional action"

find afritech_v1/kernel -type f \( -name "*.py" -o -name "*.md" \) \
  -exec sh -c 'sha256sum "$1" | sed "s|$PWD/||"' _ {} \; \
  | sort > afritech_v1/architecture/kernel_hash.txt

echo "✅ Kernel hash updated"