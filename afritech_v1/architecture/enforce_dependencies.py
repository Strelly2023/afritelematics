import ast
import os
import sys
import yaml
import hashlib
import json
from pathlib import Path

# =============================
# ROOT RESOLUTION (ROBUST)
# =============================
SCRIPT_PATH = Path(__file__).resolve()
ARCH_ROOT = SCRIPT_PATH.parent                  # afritech_v1/architecture
REPO_ROOT = SCRIPT_PATH.parents[2]              # ✅ repo root (FIXED)

# =============================
# PATHS
# =============================
RULES_PATH = ARCH_ROOT / "dependency_rules.yaml"
KERNEL_HASH_PATH = REPO_ROOT / "kernel_hash.txt"   # ✅ FIXED (was wrong before)
KERNEL_DIR = REPO_ROOT / "afritech_v1" / "kernel"
SEAL_PATH = ARCH_ROOT / "../kernel/SEAL_MANIFEST.json"
SEAL_PATH = SEAL_PATH.resolve()

# =============================
# LOAD RULES
# =============================
with open(RULES_PATH, "r") as f:
    RULES = yaml.safe_load(f)["layers"]

# =============================
# HASH UTIL
# =============================
def hash_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

# =============================
# KERNEL SNAPSHOT (CANONICAL)
# =============================
def snapshot_kernel():
    entries = []

    if not KERNEL_DIR.exists():
        return entries

    for file_path in sorted(KERNEL_DIR.rglob("*")):
        if not file_path.is_file():
            continue

        if file_path.suffix not in {".py", ".md"}:
            continue

        # ✅ Stable relative path
        rel = file_path.relative_to(REPO_ROOT).as_posix()

        entries.append(f"{hash_file(file_path)}  {rel}")

    return sorted(entries)

# =============================
# KERNEL INTEGRITY CHECK
# =============================
def verify_kernel_integrity():
    if not KERNEL_HASH_PATH.exists():
        print("⚠️ kernel_hash.txt not found — skipping integrity check")
        return

    with open(KERNEL_HASH_PATH) as f:
        expected = sorted(line.strip() for line in f.readlines() if line.strip())

    current = snapshot_kernel()

    if expected != current:
        print("\n🚨 KERNEL TAMPERING DETECTED 🚨\n")

        print("Expected:")
        print("\n".join(expected))

        print("\nCurrent:")
        print("\n".join(current))

        sys.exit(1)

    print("✅ Kernel hash integrity verified")

# =============================
# IMPORT NORMALIZATION
# =============================
def normalize_import(name: str) -> str:
    return name.split(".")[0].strip() if name else ""

# =============================
# IMPORT EXTRACTION
# =============================
def extract_imports(file_path: Path):
    imports = set()

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception:
        return imports

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add(normalize_import(n.name))

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(normalize_import(node.module))

    return imports

# =============================
# DEPENDENCY ENFORCEMENT
# =============================
def run_dependency_check():
    violations = []

    for layer, cfg in RULES.items():
        base_path = (ARCH_ROOT.parent / cfg["path"]).resolve()

        if not base_path.exists():
            continue

        for file_path in base_path.rglob("*.py"):

            imports = extract_imports(file_path)

            for imp in imports:

                # ignore external libs
                if imp not in RULES:
                    continue

                if imp not in cfg["may_import"]:
                    violations.append(
                        f"❌ {layer} -> {imp} | {file_path.relative_to(REPO_ROOT)}"
                    )

    if violations:
        print("\n🚨 AFRITECH ARCHITECTURE VIOLATIONS 🚨\n")
        for v in violations:
            print(v)
        sys.exit(1)

    print("✅ Dependency rules satisfied")

# =============================
# KERNEL SEAL VERIFICATION
# =============================
def verify_kernel_seal():
    if not SEAL_PATH.exists():
        print("⚠️ No kernel seal found — skipping strict verification")
        return

    with open(SEAL_PATH) as f:
        seal = json.load(f)

    expected = seal["files"]
    current = {}

    if not KERNEL_DIR.exists():
        print("⚠️ Kernel directory not found")
        return

    for file_path in KERNEL_DIR.rglob("*"):

        if not file_path.is_file():
            continue

        if file_path.suffix not in {".py", ".md"}:
            continue

        rel = file_path.relative_to(KERNEL_DIR).as_posix()
        current[rel] = hash_file(file_path)

    if expected != current:
        print("\n🚨 KERNEL SEAL VIOLATION 🚨\n")

        print("Expected:")
        print(json.dumps(expected, indent=2))

        print("\nCurrent:")
        print(json.dumps(current, indent=2))

        sys.exit(1)

    print("🔐 Kernel seal verified")

# =============================
# BOOT PIPELINE
# =============================
def main():
    print("🚀 AfriTech v0 Boot Validation Starting...\n")

    verify_kernel_seal()
    verify_kernel_integrity()
    run_dependency_check()

    print("\n✅ AfriTech v0 System Validated Successfully")

# =============================
# ENTRYPOINT
# =============================
if __name__ == "__main__":
    main()