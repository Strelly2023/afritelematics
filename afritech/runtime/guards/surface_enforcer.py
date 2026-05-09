# afritech/runtime/guards/surface_enforcer.py

"""
AfriTech Runtime Surface Enforcer

Purpose:
Enforce that ONLY declared surfaces are allowed
to execute during runtime.

This enforces:
- surface existence validation
- executable permission validation
- authority scope compatibility

Failure → runtime invalidation
"""

import os
import yaml
from typing import Dict, Any


SURFACE_REGISTRY_PATH = "afritech/governance/surface_registry.yaml"


class SurfaceViolationError(Exception):
    """Raised when a surface violates runtime rules"""
    pass


class SurfaceEnforcer:

    def __init__(self):
        self.registry = self._load_registry()

    # -----------------------------------------------------------------
    # LOAD REGISTRY
    # -----------------------------------------------------------------

    def _load_registry(self) -> Dict[str, Any]:
        if not os.path.exists(SURFACE_REGISTRY_PATH):
            raise SurfaceViolationError("missing_surface_registry")

        with open(SURFACE_REGISTRY_PATH, "r") as f:
            data = yaml.safe_load(f)

        return data.get("surface_registry", {}).get("surfaces", {})

    # -----------------------------------------------------------------
    # VALIDATE SURFACE
    # -----------------------------------------------------------------

    def validate_surface(self, path: str):
        """
        Validate a runtime surface before execution
        """

        surface = self._find_surface(path)

        if not surface:
            raise SurfaceViolationError(f"undeclared_surface: {path}")

        if not surface.get("executable", False):
            raise SurfaceViolationError(f"non_executable_surface: {path}")

        return True

    # -----------------------------------------------------------------
    # AUTHORITY VALIDATION
    # -----------------------------------------------------------------

    def validate_authority_scope(self, path: str, authority: str):
        """
        Ensure authority is allowed to execute this surface
        """

        surface = self._find_surface(path)

        scope = surface.get("authority_scope")

        if scope == "GLOBAL":
            return True

        if scope == "GUARDED":
            return True  # enforced elsewhere (guards layer)

        if scope == "AUTHORITY_BOUND":
            if not authority:
                raise SurfaceViolationError("missing_authority_context")

        if scope == "NONE":
            raise SurfaceViolationError("forbidden_surface_execution")

    # -----------------------------------------------------------------
    # INTERNAL HELPERS
    # -----------------------------------------------------------------

    def _find_surface(self, path: str):
        """
        Match path to declared surface
        """
        for name, surface in self.registry.items():
            registered_path = surface.get("path")

            if path.startswith(registered_path):
                return surface

        return None