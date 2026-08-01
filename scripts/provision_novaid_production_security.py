#!/usr/bin/env python3
"""Atomically provision NovaID production security configuration."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import stat
import tempfile
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV = ROOT / "deploy/production/.env.production.trust-node"
MANAGED_KEYS = (
    "NOVAID_JWT_ISSUER",
    "NOVAID_JWT_AUDIENCE",
    "NOVAID_SIGNING_KEYS_JSON",
    "NOVAID_ACTIVE_SIGNING_KEY_ID",
    "NOVAID_TOKEN_PEPPER",
    "NOVAID_REDIS_URL",
)


class ProvisioningError(RuntimeError):
    pass


def _load_lines(path: Path) -> tuple[list[str], dict[str, str]]:
    if not path.is_file() or path.is_symlink():
        raise ProvisioningError(f"protected environment must be a regular file: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    values: dict[str, str] = {}
    for line in lines:
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return lines, values


def provision(path: Path, *, rotate: bool = False) -> Path:
    lines, values = _load_lines(path)
    existing = sorted(key for key in MANAGED_KEYS if values.get(key))
    if existing and not rotate:
        raise ProvisioningError(
            "NovaID security configuration already exists; use --rotate explicitly"
        )
    domain = values.get("AFRITECH_DOMAIN", "").strip()
    if not domain:
        raise ProvisioningError("AFRITECH_DOMAIN is required")

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    previous_id = f"{timestamp}-previous"
    active_id = f"{timestamp}-active"
    generated = {
        "NOVAID_JWT_ISSUER": f"https://{domain}/novaid",
        "NOVAID_JWT_AUDIENCE": "novatech-production",
        "NOVAID_SIGNING_KEYS_JSON": json.dumps(
            {
                previous_id: secrets.token_urlsafe(48),
                active_id: secrets.token_urlsafe(48),
            },
            separators=(",", ":"),
        ),
        "NOVAID_ACTIVE_SIGNING_KEY_ID": active_id,
        "NOVAID_TOKEN_PEPPER": secrets.token_urlsafe(48),
        "NOVAID_REDIS_URL": "redis://redis:6379/0",
    }

    filtered = [
        line
        for line in lines
        if not any(line.startswith(f"{key}=") for key in MANAGED_KEYS)
    ]
    if filtered and filtered[-1]:
        filtered.append("")
    filtered.extend(["# NovaID production security (managed; values must not be logged)."])
    filtered.extend(f"{key}={generated[key]}" for key in MANAGED_KEYS)
    payload = "\n".join(filtered) + "\n"

    backup = path.with_name(f"{path.name}.novaid-{timestamp}.bak")
    backup.write_bytes(path.read_bytes())
    backup.chmod(0o600)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", text=True
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ProvisioningError("protected environment mode is not 0600")
    return backup


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--rotate", action="store_true")
    args = parser.parse_args()
    try:
        backup = provision(args.env_file.resolve(), rotate=args.rotate)
    except ProvisioningError as exc:
        print(f"NovaID production security provisioning FAILED: {exc}")
        return 1
    print("NovaID production security provisioning PASSED")
    print(f"Backup: {backup}")
    print("Secrets disclosed: NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
