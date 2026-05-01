import sys
from typing import Dict, Any

from .snapshot import snapshot_kernel
from .seal import load_seal
from .policy import classify_change, ChangeType


# =========================================================
# 🔐 EXCEPTION MODEL
# =========================================================

class KernelTamperError(Exception):
    """
    Raised when kernel integrity is violated beyond policy allowance.
    """
    pass


# =========================================================
# 🔍 KERNEL VERIFICATION ENGINE (v1)
# =========================================================

def verify_kernel(kernel_dir: str, strict: bool = True) -> bool:
    """
    Verifies kernel integrity against SEAL_MANIFEST.

    - compares expected vs current snapshot
    - applies seal policy classification
    - distinguishes evolution vs tampering
    """

    seal = load_seal(kernel_dir)

    if not seal:
        print("⚠️ No kernel seal found — skipping verification")
        return True

    expected: Dict[str, str] = seal.get("files", {})
    current: Dict[str, str] = snapshot_kernel(kernel_dir)

    # =========================================================
    # 🔍 DETECT DIFFERENCES
    # =========================================================

    expected_keys = set(expected.keys())
    current_keys = set(current.keys())

    added = current_keys - expected_keys
    removed = expected_keys - current_keys
    common = expected_keys & current_keys

    changed = {
        k for k in common
        if expected[k] != current[k]
    }

    # =========================================================
    # 🧠 CLASSIFY CHANGES
    # =========================================================

    violations = []
    evolutions = []

    for path in added | removed | changed:

        change_type = classify_change(path)

        if change_type == ChangeType.EVOLUTION:
            evolutions.append(path)

        elif change_type == ChangeType.TAMPERING:
            violations.append(path)

        else:
            violations.append(path)

    # =========================================================
    # 🚨 HANDLE VIOLATIONS
    # =========================================================

    if violations and strict:

        print("\n🚨 KERNEL TAMPERING DETECTED 🚨\n")

        print("❌ Violations:")
        for v in sorted(violations):
            print(f" - {v}")

        print("\n📌 Expected Snapshot:")
        for k, v in expected.items():
            print(f"{v}  {k}")

        print("\n📌 Current Snapshot:")
        for k, v in current.items():
            print(f"{v}  {k}")

        raise KernelTamperError(
            "Kernel integrity violation: unauthorized mutation detected"
        )

    # =========================================================
    # 🧬 EVOLUTION REPORT (NON-FATAL)
    # =========================================================

    if evolutions:
        print("\n🧬 Kernel Evolution Detected (allowed by policy):")
        for e in sorted(evolutions):
            print(f" - {e}")

    # =========================================================
    # ✅ SUCCESS STATE
    # =========================================================

    print("🔐 Kernel integrity verified")
    return True


# =========================================================
# 🧪 CLI ENTRY (optional debug mode)
# =========================================================

if __name__ == "__main__":

    from pathlib import Path

    kernel_path = str(Path(__file__).resolve().parents[2] / "kernel")

    try:
        verify_kernel(kernel_path)
    except KernelTamperError as e:
        print(str(e))
        sys.exit(1)