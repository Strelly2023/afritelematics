"""
AfriTech Registry Sovereignty Binder

This module establishes cryptographic constitutional closure by
binding the registry document to the kernel constitutional surface.

It operates ABOVE semantic registry binding.
"""

from pathlib import Path
import hashlib
import yaml


def constitutional_halt(message: str):
    raise SystemExit(f"\n❌ CONSTITUTIONAL VIOLATION\n{message}\n")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    hasher.update(path.read_bytes())
    return hasher.hexdigest()


def sha256_tree(root: Path) -> str:
    hasher = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


def seal_registry():
    base = Path(__file__).parents[1]

    registry_path = base / "registry" / "registry.yaml"
    kernel_root = base / "kernel"

    if not registry_path.exists():
        constitutional_halt("registry.yaml missing")

    if not kernel_root.exists():
        constitutional_halt("kernel directory missing")

    with open(registry_path, "r") as f:
        registry = yaml.safe_load(f)

    attestation = registry.setdefault("attestation", {})

    if attestation.get("seal_status") == "SEALED":
        constitutional_halt("Registry already sealed")

    registry_hash = sha256_file(registry_path)
    kernel_hash = sha256_tree(kernel_root)

    attestation.update({
        "registry_hash": registry_hash,
        "kernel_hash": kernel_hash,
        "seal_status": "SEALED",
    })

    with open(registry_path, "w") as f:
        yaml.safe_dump(registry, f, sort_keys=False)

    print("🔏 Registry sovereignty sealed")
    print(f"   registry_hash: {registry_hash}")
    print(f"   kernel_hash:   {kernel_hash}")

if __name__ == "__main__":
    seal_registry()
