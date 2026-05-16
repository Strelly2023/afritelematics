import yaml
from pathlib import Path
from typing import Dict, Any

# ============================================================
# ROOT RESOLUTION (ROBUST + HOOK-SAFE)
# ============================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "afritech" / "registry" / "registry.yaml"

# ============================================================
# INTERNAL CACHE
# ============================================================

_registry_cache: Dict[str, Any] | None = None


def _load_registry() -> Dict[str, Any]:
    """
    Load full registry (root object, not nested).

    Cached to ensure performance and determinism.
    """
    global _registry_cache

    if _registry_cache is None:

        if not REGISTRY_PATH.exists():
            raise FileNotFoundError(
                f"Registry file not found: {REGISTRY_PATH}"
            )

        data = yaml.safe_load(REGISTRY_PATH.read_text())

        if not isinstance(data, dict):
            raise ValueError("Invalid registry format: root must be a dict")

        if "epoch" not in data:
            raise ValueError("Invalid registry: missing 'epoch' section")

        _registry_cache = data

    return _registry_cache


# ============================================================
# CURRENT EPOCH (AUTHORITATIVE)
# ============================================================

def get_current_epoch() -> int:
    """
    Return the canonical current epoch.

    Source of truth:
        registry["epoch"]["current"]
    """
    data = _load_registry()

    epoch_section = data.get("epoch")

    if not isinstance(epoch_section, dict):
        raise ValueError("Invalid registry: 'epoch' must be a dict")

    if "current" not in epoch_section:
        raise ValueError("Registry epoch missing 'current' field")

    return epoch_section["current"]


# ============================================================
# MODULE → EPOCH RESOLUTION
# ============================================================

def get_module_epoch(module_name: str) -> int:
    """
    Resolve module epoch using registry topology.

    If module is not explicitly listed:
        → defaults to current epoch (safe fallback)
    """
    data = _load_registry()

    # modules are OPTIONAL in your schema
    modules = data.get("registry", {}).get("modules", {})

    current_epoch = get_current_epoch()

    # ✅ Exact match
    if module_name in modules:
        return modules[module_name].get("epoch", current_epoch)

    # ✅ Prefix match (critical for nested modules)
    for registered_module, meta in modules.items():
        if module_name.startswith(registered_module):
            return meta.get("epoch", current_epoch)

    # ✅ Default: current epoch (safe)
    return current_epoch


# ============================================================
# DEBUG HELPERS
# ============================================================

def debug_registry():
    data = _load_registry()
    print("\n[DEBUG] Registry loaded successfully")
    print("[DEBUG] Current epoch:", get_current_epoch())
    print("[DEBUG] Epoch section:", data.get("epoch"))


def debug_module_epoch(module_name: str):
    epoch = get_module_epoch(module_name)
    current = get_current_epoch()

    print(
        f"[DEBUG] Module: {module_name} | "
        f"Module Epoch: {epoch} | Current Epoch: {current}"
    )