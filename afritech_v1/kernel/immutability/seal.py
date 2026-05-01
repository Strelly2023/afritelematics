import os
import json
from .snapshot import snapshot_kernel

SEAL_FILE = "SEAL_MANIFEST.json"


def load_seal(kernel_dir: str):
    path = os.path.join(kernel_dir, SEAL_FILE)

    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        return json.load(f)


def write_seal(kernel_dir: str):
    path = os.path.join(kernel_dir, SEAL_FILE)

    seal = {
        "version": "v1",
        "files": snapshot_kernel(kernel_dir),
    }

    with open(path, "w") as f:
        json.dump(seal, f, indent=2, sort_keys=True)

    return seal