import sys

from afritech_v1.architecture.enforce_dependencies import (
    verify_kernel_integrity,
    verify_kernel_seal
)

def run_kernel_guard():
    """
    Single gate for ALL kernel immutability rules.
    """

    print("🔐 Running Kernel Immutability Guard...\n")

    # 1. Structural hash verification
    verify_kernel_integrity()

    # 2. Seal verification (authoritative snapshot)
    verify_kernel_seal()

    print("\n✅ Kernel is IMMUTABLE and VALID\n")


if __name__ == "__main__":
    try:
        run_kernel_guard()
    except Exception as e:
        print("🚨 KERNEL IMMUTABILITY FAILURE:", str(e))
        sys.exit(1)