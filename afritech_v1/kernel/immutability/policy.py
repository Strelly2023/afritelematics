import os
from .seal import write_seal
from .verify import verify_kernel


def can_regenerate_kernel(context: str) -> bool:
    """
    Only allow regeneration under explicit controlled contexts.
    """

    allowed = {
        "dev_bootstrap",
        "ci_pipeline",
        "explicit_admin_action"
    }

    return context in allowed


def regenerate_kernel_seal(kernel_dir: str, context: str):
    if not can_regenerate_kernel(context):
        raise PermissionError("Kernel regeneration not allowed")

    verify_kernel(kernel_dir)  # must be clean before re-sealing

    return write_seal(kernel_dir)