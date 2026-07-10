from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_checksum_files_match_when_artifacts_exist() -> None:
    for apk in [
        ROOT / "apk/novaride-rider-v2026.1.2-public-pilot.apk",
        ROOT / "apk/novaride-driver-v2026.1.2-public-pilot.apk",
        ROOT / "apk/novaride-fleet-v2026.1.2-public-pilot.apk",
        ROOT / "apk/novaride-operator-v2026.1.2-public-pilot.apk",
    ]:
        checksum = Path(f"{apk}.sha256")
        if apk.exists() and checksum.exists():
            expected = checksum.read_text(encoding="utf-8").split()[0]
            actual = hashlib.sha256(apk.read_bytes()).hexdigest()
            assert actual == expected
