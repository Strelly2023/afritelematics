import os
import hashlib

KERNEL_DIR = None  # injected by caller


def hash_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def snapshot_kernel(kernel_dir: str):
    entries = {}

    for root, _, files in os.walk(kernel_dir):
        for file in sorted(files):

            if not file.endswith((".py", ".md")):
                continue

            full = os.path.join(root, file)

            # stable identity relative to kernel root
            rel = os.path.relpath(full, kernel_dir)

            entries[rel] = hash_file(full)

    return dict(sorted(entries.items()))