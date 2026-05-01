import os
import hashlib
import json
import sys
from pathlib import Path

# =========================================================
# 🧭 ROOT RESOLUTION (ABSOLUTE + ROBUST)
# =========================================================
ARCH_DIR = Path(__file__).resolve().parent
AFRITECH_ROOT = ARCH_DIR.parent

KERNEL_DIR = AFRITECH_ROOT / "kernel"
SEAL_PATH = KERNEL_DIR / "SEAL_MANIFEST.json"


# =========================================================
# 🔐 HASH FUNCTION (IMMUTABLE FILE DIGEST)
# =========================================================
def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# =========================================================
# 🧭 CANONICAL PATH NORMALIZATION
# =========================================================
def normalize_rel_path(full_path: Path) -> str:
    return full_path.relative_to(KERNEL_DIR).as_posix()


# =========================================================
# 🧱 KERNEL STATE COLLECTION (DETERMINISTIC)
# =========================================================
def collect_kernel_state():
    state = {}

    if not KERNEL_DIR.exists():
        raise RuntimeError(f"Kernel directory missing: {KERNEL_DIR}")

    files = sorted(
        [p for p in KERNEL_DIR.rglob("*") if p.is_file()]
    )

    for file in files:
        if file.suffix not in {".py", ".md"}:
            continue

        rel = normalize_rel_path(file)
        state[rel] = hash_file(file)

    return dict(sorted(state.items()))


# =========================================================
# 📦 ATOMIC SEAL WRITE (CRASH SAFE)
# =========================================================
def atomic_write_json(path: Path, data: dict):
    tmp = path.with_suffix(".tmp")

    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    tmp.replace(path)


# =========================================================
# 📥 LOAD EXISTING SEAL
# =========================================================
def load_existing_seal():
    if not SEAL_PATH.exists():
        return None

    with SEAL_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# 🔍 SEAL DIFF ENGINE
# =========================================================
def diff_seal(old, new):
    old_files = old.get("files", {})
    new_files = new.get("files", {})

    removed = set(old_files) - set(new_files)
    added = set(new_files) - set(old_files)
    changed = {
        k for k in old_files.keys() & new_files.keys()
        if old_files[k] != new_files[k]
    }

    return {
        "removed": sorted(removed),
        "added": sorted(added),
        "changed": sorted(changed),
    }


# =========================================================
# 🔐 SEAL GENERATION
# =========================================================
def generate_seal():
    kernel_state = collect_kernel_state()

    new_seal = {
        "version": "v1",
        "root": "kernel",
        "files": kernel_state,
    }

    old_seal = load_existing_seal()

    atomic_write_json(SEAL_PATH, new_seal)

    print("🔐 Kernel SEAL generated successfully")
    print(f"📦 File: {SEAL_PATH}")
    print(f"📁 Files sealed: {len(kernel_state)}")

    if old_seal:
        changes = diff_seal(old_seal, new_seal)

        if changes["added"] or changes["removed"] or changes["changed"]:
            print("\n⚠️ Seal updated:")
            print(json.dumps(changes, indent=2))


# =========================================================
# 🧪 VALIDATION MODE (CI SAFE)
# =========================================================
def validate_only():
    if not SEAL_PATH.exists():
        print("❌ No seal found")
        sys.exit(1)

    existing = load_existing_seal()
    current = {
        "version": "v1",
        "root": "kernel",
        "files": collect_kernel_state(),
    }

    if existing != current:
        print("🚨 SEAL VALIDATION FAILED")
        sys.exit(1)

    print("✅ Seal is deterministic and valid")


# =========================================================
# 🚀 ENTRYPOINT
# =========================================================
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "generate"

    try:
        if mode == "validate":
            validate_only()
        else:
            generate_seal()

    except Exception as e:
        print("🚨 Kernel seal failure:", str(e))
        sys.exit(1)