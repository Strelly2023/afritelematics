#!/usr/bin/env bash
set -euo pipefail
python3 scripts/novaride/verify_runtime_migrations.py
python3 scripts/novaride/verify_event_schema_compatibility.py
python3 scripts/novaride/verify_live_runtime.py
python3 scripts/novaride/verify_backup_restore.py
echo "Release-candidate deployment verification scripts completed. Live external services remain required for certification."
