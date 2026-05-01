import ast
import os
import sys
import yaml
import hashlib
import json

# =============================
# ROOT RESOLUTION (STABLE)
# =============================
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.join(ROOT, ".."))

RULES_PATH = os.path.join(ROOT, "architecture/dependency_rules.yaml")
KERNEL_HASH_PATH = os.path.join(ROOT, "architecture/kernel_hash.txt")

# =============================
# LOAD RULES
# =============================
with open(RULES_PATH) as f:
    RULES = yaml.safe_load(f)["layers"]

# =============================
# HASH UTIL
# =============================
def hash_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

# =============================
# KERNEL SNAPSHOT (CANONICAL)
# =============================
def snapshot_kernel():
    entries = []

    kernel_root = os.path.join(PROJECT_ROOT, "afritech_v1", "kernel")

    for root, _, files in os.walk(kernel_root):
        for file in sorted(files):

            if not file.endswith((".py", ".md")):
                continue

            full = os.path.join(root, file)

            # canonical relative path
            rel = os.path.relpath(full, PROJECT_ROOT).replace("\\", "/")

            entries.append(f"{hash_file(full)}  {rel}")

    return sorted(entries)

# =============================
# KERNEL INTEGRITY CHECK
# =============================
def verify_kernel_integrity():
    if not os.path.exists(KERNEL_HASH_PATH):
        print("⚠️ kernel_hash.txt not found — skipping integrity check")
        return

    with open(KERNEL_HASH_PATH) as f:
        expected = sorted([line.strip() for line in f.readlines()])

    current = snapshot_kernel()

    if expected != current:
        print("\n🚨 KERNEL TAMPERING DETECTED 🚨\n")

        print("Expected:")
        print("\n".join(expected))

        print("\nCurrent:")
        print("\n".join(current))

        sys.exit(1)

    print("🔐 Kernel integrity verified")

# =============================
# IMPORT NORMALIZATION
# =============================
def normalize_import(name: str) -> str:
    return name.split(".")[0].strip() if name else ""

# =============================
# IMPORT EXTRACTION
# =============================
def extract_imports(file_path):
    imports = set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
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
        base_path = os.path.join(ROOT, cfg["path"])

        if not os.path.exists(base_path):
            continue

        for root, _, files in os.walk(base_path):
            for file in files:

                if not file.endswith(".py"):
                    continue

                full_path = os.path.join(root, file)
                imports = extract_imports(full_path)

                for imp in imports:

                    # ignore external libs / stdlib
                    if imp not in RULES:
                        continue

                    # enforce dependency rule
                    if imp not in cfg["may_import"]:
                        violations.append(
                            f"❌ {layer} -> {imp} | {full_path}"
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
    seal_path = os.path.join(ROOT, "kernel/SEAL_MANIFEST.json")

    if not os.path.exists(seal_path):
        print("⚠️ No kernel seal found — skipping strict verification")
        return

    with open(seal_path) as f:
        seal = json.load(f)

    expected = seal["files"]
    current = {}

    kernel_root = os.path.join(PROJECT_ROOT, "afritech_v1", "kernel")

    for root, _, files in os.walk(kernel_root):
        for file in files:

            if not file.endswith((".py", ".md")):
                continue

            full = os.path.join(root, file)
            rel = os.path.relpath(full, kernel_root).replace("\\", "/")

            current[rel] = hash_file(full)

    if expected != current:
        print("\n🚨 KERNEL SEAL VIOLATION 🚨\n")
        print("Expected:")
        print(json.dumps(expected, indent=2))

        print("\nCurrent:")
        print(json.dumps(current, indent=2))

        sys.exit(1)

    print("🔐 Kernel seal verified")

# =============================
# BOOT PIPELINE (SINGLE ENTRYPOINT)
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