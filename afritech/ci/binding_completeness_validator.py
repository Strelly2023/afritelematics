"""Validate surface-to-implementation binding completion."""

from __future__ import annotations

import sys

from afritech.ci.completion_utils import (
    ROOT,
    fail,
    load_yaml,
    main_result,
    require_non_empty_list,
    validate_entry_state_resolution,
    validate_implemented_entry,
)


BINDING_REGISTRY = ROOT / "afritech/architecture/surface_implementation_binding.yaml"


def validate() -> None:
    validate_entry_state_resolution()
    payload = load_yaml(BINDING_REGISTRY)
    bindings = payload.get("bindings")
    if not isinstance(bindings, dict) or not bindings:
        fail("binding registry must define bindings")

    for name, entry in bindings.items():
        if not isinstance(entry, dict):
            fail(f"binding {name} must be a mapping")
        context = f"{BINDING_REGISTRY.relative_to(ROOT)}::{name}"
        validate_implemented_entry(entry, context)
        if entry.get("implementation_state") == "IMPLEMENTED":
            require_non_empty_list(entry, "authority_scope", context)
            require_non_empty_list(entry, "enforced_by", context)
            if entry.get("runtime_admissible") is not True:
                fail(f"{context} implemented binding must be runtime_admissible")
            if entry.get("replay_participating") is not True:
                fail(f"{context} implemented binding must replay_participate")
            if entry.get("proof_admissible") is not True:
                fail(f"{context} implemented binding must be proof_admissible")

    print(f"✅ Bindings resolved: {len(bindings)}")


def main() -> int:
    return main_result("Binding completeness validation", validate)


if __name__ == "__main__":
    sys.exit(main())
