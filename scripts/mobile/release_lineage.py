#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LINEAGE = ROOT / "docs/mobile/release/release_lineage.yaml"


def _read() -> str:
    if not LINEAGE.exists():
        raise SystemExit(f"missing release lineage registry: {LINEAGE}")
    return LINEAGE.read_text(encoding="utf-8")


def current_android_fingerprint() -> str:
    text = _read()
    block = _active_android_lineage(text)
    match = re.search(r"^\s*certificate_sha256:\s*([0-9a-fA-F: ]+)\s*$", block, re.M)
    if not match:
        raise SystemExit("missing active android certificate_sha256 in release lineage")
    return re.sub(r"[^0-9a-fA-F]", "", match.group(1)).lower()


def android_alias() -> str:
    text = _read()
    block = _active_android_lineage(text)
    match = re.search(r"^\s*alias:\s*([A-Za-z0-9_.-]+)\s*$", block, re.M)
    if not match:
        raise SystemExit("missing active android alias in release lineage")
    return match.group(1)


def active_android_lineage_id() -> str:
    text = _read()
    block = _active_android_lineage(text)
    match = re.search(r"^\s*-\s*id:\s*([A-Za-z0-9_.-]+)\s*$", block, re.M)
    if not match:
        raise SystemExit("missing active android lineage id")
    return match.group(1)


def _active_android_lineage(text: str) -> str:
    blocks = re.findall(
        r"(?ms)^      - id:.*?(?=^      - id:|^  policy:|\Z)",
        text,
    )
    active_blocks = [
        block
        for block in blocks
        if re.search(r"^\s*active:\s*true\s*$", block, re.M)
    ]
    if len(active_blocks) != 1:
        raise SystemExit(
            f"expected exactly one active android lineage, found {len(active_blocks)}"
        )
    return active_blocks[0]


def android_package_ids() -> dict[str, str]:
    text = _read()
    match = re.search(r"(?ms)^\s*package_ids:\s*$\n(.*?)(?=^\s*lineages:)", text)
    if not match:
        raise SystemExit("missing android package_ids in release lineage")
    package_ids: dict[str, str] = {}
    for line in match.group(1).splitlines():
        item = re.match(r"^\s*([a-z]+):\s*([A-Za-z0-9_.]+)\s*$", line)
        if item:
            package_ids[item.group(1)] = item.group(2)
    if not package_ids:
        raise SystemExit("android package_ids is empty")
    return package_ids


def active_android_lineage_summary() -> str:
    text = _read()
    block = _active_android_lineage(text)
    match = re.search(r"^\s*alias:\s*([A-Za-z0-9_.-]+)\s*$", text, re.M)
    lineage_id = active_android_lineage_id()
    fingerprint = current_android_fingerprint()
    alias = android_alias()
    status = re.search(r"^\s*status:\s*(.+?)\s*$", block, re.M)
    custody = re.search(r"^\s*custody_status:\s*(.+?)\s*$", block, re.M)
    return "\n".join(
        [
            f"id={lineage_id}",
            f"alias={alias}",
            f"certificate_sha256={fingerprint}",
            f"status={status.group(1) if status else 'unknown'}",
            f"custody_status={custody.group(1) if custody else 'unknown'}",
        ]
    )


def allowed_secret_providers() -> list[str]:
    text = _read()
    providers: list[str] = []
    in_section = False
    for line in text.splitlines():
        if re.match(r"^\s*allowed_secret_providers:\s*$", line):
            in_section = True
            continue
        if in_section:
            match = re.match(r"^\s*-\s*([A-Za-z0-9_.-]+)\s*$", line)
            if match:
                providers.append(match.group(1))
                continue
            if line.strip() and not line.startswith(" " * 6):
                break
    if not providers:
        raise SystemExit("missing allowed_secret_providers in release lineage")
    return providers


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "fingerprint":
        print(current_android_fingerprint())
    elif command == "alias":
        print(android_alias())
    elif command == "lineage-id":
        print(active_android_lineage_id())
    elif command == "summary":
        print(active_android_lineage_summary())
    elif command == "secret-providers":
        print("\n".join(allowed_secret_providers()))
    else:
        raise SystemExit(
            "usage: release_lineage.py fingerprint|alias|lineage-id|summary|secret-providers"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
