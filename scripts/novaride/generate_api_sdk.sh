#!/usr/bin/env bash
set -euo pipefail
mkdir -p packages/novaride-api-sdk/src/generated
python3 - <<'PY'
from pathlib import Path
import hashlib

root = Path('.')
spec = root / 'reports' / 'novaride' / 'deployment' / 'openapi-placeholder.json'
spec.parent.mkdir(parents=True, exist_ok=True)
spec.write_text('{"source":"/openapi.json","status":"placeholder_requires_live_openapi_export"}\n')
spec_hash = hashlib.sha256(spec.read_bytes()).hexdigest()
generated = root / 'packages' / 'novaride-api-sdk' / 'src' / 'generated'
modules = ['rider','driver','operator','fleet','logistics','corporate','transit','safety','diagnostics','replay','models']
for module in modules:
    (generated / f'{module}.ts').write_text(f'// Generated from /openapi.json placeholder\n// source_spec_hash: sha256:{spec_hash}\nexport const {module}SpecHash = "sha256:{spec_hash}";\n')
PY
