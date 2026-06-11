#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${1:-$ROOT_DIR/out/architecture_compliance_export}"

mkdir -p "$OUT_DIR"

DRIFT_REPORT="$OUT_DIR/architecture_drift_report.json"
EXPORT_MD="$OUT_DIR/AFRITECH_ARCHITECTURE_COMPLIANCE_EXPORT.md"
EXPORT_HTML="$OUT_DIR/AFRITECH_ARCHITECTURE_COMPLIANCE_EXPORT.html"

python3 -m afritech.guards.architecture_drift_report > "$DRIFT_REPORT"

cat > "$EXPORT_MD" <<EOF
# AfriTech Architecture Compliance Export

Generated from governed sources.

## Export Pack Definition

EOF

cat "$ROOT_DIR/docs/whitepaper/AFRITECH_ARCHITECTURE_COMPLIANCE_EXPORT_PACK.md" >> "$EXPORT_MD"

cat >> "$EXPORT_MD" <<EOF

---

## Unified Architecture

EOF

cat "$ROOT_DIR/docs/architecture/AFRITECH_UNIFIED_ARCHITECTURE.md" >> "$EXPORT_MD"

cat >> "$EXPORT_MD" <<EOF

---

## AfriCPPT Protocol Spec

EOF

cat "$ROOT_DIR/docs/standards/AFRICPPT_PROTOCOL_SPEC.md" >> "$EXPORT_MD"

cat >> "$EXPORT_MD" <<EOF

---

## Partner One-Pager

EOF

cat "$ROOT_DIR/docs/partners/AFRITECH_PARTNER_ARCHITECTURE_ONE_PAGER.md" >> "$EXPORT_MD"

cat >> "$EXPORT_MD" <<EOF

---

## First Partner Demo Script

EOF

cat "$ROOT_DIR/docs/pitch/AFRITECH_FIRST_PARTNER_DEMO_SCRIPT.md" >> "$EXPORT_MD"

cat >> "$EXPORT_MD" <<EOF

---

## Drift Detection Report

\`\`\`json
EOF

cat "$DRIFT_REPORT" >> "$EXPORT_MD"

cat >> "$EXPORT_MD" <<EOF
\`\`\`
EOF

if command -v pandoc >/dev/null 2>&1; then
  pandoc "$EXPORT_MD" -s -o "$OUT_DIR/AFRITECH_ARCHITECTURE_COMPLIANCE_EXPORT.pdf" || true
fi

cat > "$EXPORT_HTML" <<EOF
<html>
<head><meta charset="utf-8"><title>AfriTech Architecture Compliance Export</title></head>
<body><pre>
EOF

cat "$EXPORT_MD" >> "$EXPORT_HTML"

cat >> "$EXPORT_HTML" <<EOF
</pre></body>
</html>
EOF

echo "ARCHITECTURE_COMPLIANCE_EXPORT_READY: $OUT_DIR"

