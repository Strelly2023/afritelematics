#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROVENANCE = ROOT / "reports/mobile/releases/2026.1.4/novaride-release-provenance.json"
PLACEHOLDER = re.compile(r"^(pending|pending-release-build|unknown)$", re.I)


def require_real(value: object, label: str) -> None:
    if value is None or value == "" or PLACEHOLDER.fullmatch(str(value).strip()):
        raise SystemExit(f"missing or placeholder provenance value: {label}")


def main() -> int:
    if not PROVENANCE.exists():
        raise SystemExit(f"missing provenance {PROVENANCE}")
    data = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    for key in ("generated_at", "builder", "branch", "commit", "workflow_run"):
        require_real(data.get(key), key)
    if data.get("publicationVerified") is not False:
        raise SystemExit("unpublished release provenance must keep publicationVerified=false")
    for app in ("rider", "driver"):
        entry = data.get(app)
        if not isinstance(entry, dict):
            raise SystemExit(f"missing {app} provenance")
        for key in (
            "version", "versionCode", "packageId", "apiHost", "apkSha256", "apkByteSize",
            "signingCertificateSha256", "signingVerificationStatus", "publicationUrl",
        ):
            require_real(entry.get(key), f"{app}.{key}")
    print("release provenance verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
