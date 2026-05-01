import sys

from afritech_v1.architecture.generate_kernel_seal import (
    validate_only as validate_seal
)

from afritech_v1.architecture.enforce_dependencies import (
    run_dependency_check
)

from afritech_v1.kernel.immutability.guard import (
    run_kernel_guard
)

from afritech_v1.kernel.bootstrap import boot


# =========================================================
# 🚀 BOOT SEQUENCE CONTRACT (STRICT ORDER)
# =========================================================

BOOT_STEPS = [
    ("Kernel Immutability Guard", run_kernel_guard),
    ("Kernel Seal Validation", validate_seal),
    ("Dependency Rules Check", run_dependency_check),
]


def run_boot_contract():
    print("\n🚀 AFRITECH v1 BOOT CONTRACT STARTING\n")

    for name, step in BOOT_STEPS:
        print(f"🔹 {name}...")

        try:
            step()
        except Exception as e:
            print(f"\n🚨 BOOT FAILURE at: {name}")
            print(str(e))
            sys.exit(1)

        print(f"✅ {name} PASSED\n")

    print("🚀 All system invariants validated\n")

    # ONLY NOW system is allowed to boot
    boot()

    print("\n🟢 AfriTech v1 RUNNING (STATE: STABLE)\n")


# =========================================================
# ENTRYPOINT
# =========================================================
if __name__ == "__main__":
    run_boot_contract()