"""
AfriTech Registry Sovereignty Binder

Establishes cryptographic constitutional closure by sealing
registry authority against explicitly declared constitutional surfaces.

Registry defines identity.
Filesystem only instantiates it.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import yaml


# ---------------------------------------------------------------------
# Constitutional failure
# ---------------------------------------------------------------------

def constitutional_halt(message: str) -> None:
    raise SystemExit(f"\n❌ CONSTITUTIONAL VIOLATION\n{message}\n")


# ---------------------------------------------------------------------
# Deterministic manifest-based hashing
# ---------------------------------------------------------------------

def sha256_manifest(root: Path, files: list[str]) -> str:
    """
    Deterministic constitutional hash.

    Only files explicitly declared by the registry are hashed.
    Hash domain = (relative path + file contents), order-stable.

    Any undeclared filesystem content is constitutionally irrelevant.
    """
    hasher = hashlib.sha256()

    for rel_path in sorted(files):
        path = root / rel_path

        if not path.exists():
            constitutional_halt(
                f"Declared constitutional file missing: {rel_path}"
            )

        hasher.update(rel_path.encode())
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")

    return hasher.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------
# Registry sealing
# ---------------------------------------------------------------------

def seal_registry() -> None:
    base = Path(__file__).resolve().parents[1]
    registry_path = base / "registry" / "registry.yaml"

    if not registry_path.exists():
        constitutional_halt("registry.yaml missing")

    with open(registry_path, "r") as f:
        registry = yaml.safe_load(f)

    attestation = registry.setdefault("attestation", {})

    # ------------------------------------------------------------
    # Seal state validation
    # ------------------------------------------------------------

    if attestation.get("seal_status") == "SEALED":
        constitutional_halt("Registry already sealed")

    kernel_hashes = attestation.get("kernel_hashes")

    if not kernel_hashes:
        constitutional_halt(
            "Registry must declare kernel_hashes before sealing"
        )

    # ------------------------------------------------------------
    # Compute constitutional hashes from declared manifests
    # ------------------------------------------------------------

    computed_hashes: dict[str, dict[str, object]] = {}

    for scope, data in kernel_hashes.items():

        declared_files = data.get("files")

        if not declared_files:
            constitutional_halt(
                f"No constitutional file manifest for scope: {scope}"
            )

        computed_hashes[scope] = {
            "files": declared_files,
            "hash": sha256_manifest(base, declared_files),
        }

    # ------------------------------------------------------------
    # Registry pre-seal snapshot hash
    # ------------------------------------------------------------

    registry_bytes = yaml.safe_dump(
        registry,
        sort_keys=False
    ).encode()

    registry_hash = sha256_bytes(registry_bytes)

    # ------------------------------------------------------------
    # Apply seal atomically
    # ------------------------------------------------------------

    attestation.update({
        "registry_hash": registry_hash,
        "kernel_hashes": computed_hashes,
        "seal_status": "SEALED",
    })

    with open(registry_path, "w") as f:
        yaml.safe_dump(registry, f, sort_keys=False)

    # ------------------------------------------------------------
    # Seal report
    # ------------------------------------------------------------

    print("🔏 REGISTRY SOVEREIGNTY SEALED")
    print(f"registry_hash: {registry_hash}")

    for scope, data in computed_hashes.items():
        print(f"{scope}: {data['hash']}")


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------

if __name__ == "__main__":
    seal_registry()