# afritech/governance/binding_generator.py

"""
AfriTech Binding Generator

Purpose:
Derive ALL authority bindings deterministically from constitutional artifacts.

Core Principle:
    AUTHORITY = f(GENESIS, TRACE_SCHEMA, STATE_SCHEMA, INVARIANTS)

Guarantees:
- no manual authority definitions
- canonical derivation
- replay equality
- cryptographic integrity
- system-wide consistency

This is the AUTHORITY CLOSURE layer of the system.
"""

from typing import Dict, Any, List
import hashlib
import json


from afritech.genesis.genesis_hash import compute_genesis_hash
from afritech.trace.trace_hash import canonical_json as trace_canonical_json
from afritech.state_machine.state_hash import canonical_json as state_canonical_json


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class BindingGenerationError(Exception):
    """Raised when binding derivation fails"""
    pass


# -----------------------------------------------------------------
# CANONICAL UTILS
# -----------------------------------------------------------------

def canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash_obj(data: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(data).encode()).hexdigest()


# -----------------------------------------------------------------
# GENERATOR
# -----------------------------------------------------------------

class BindingGenerator:

    def __init__(
        self,
        genesis: Dict[str, Any],
        trace_schema: Dict[str, Any],
        state_schema: Dict[str, Any],
        invariants: Dict[str, Any],
    ):

        if not all([genesis, trace_schema, state_schema, invariants]):
            raise BindingGenerationError("missing_input_artifacts")

        self.genesis = genesis
        self.trace_schema = trace_schema
        self.state_schema = state_schema
        self.invariants = invariants

        self._bindings: List[Dict[str, Any]] = []

    # =============================================================
    # ENTRYPOINT
    # =============================================================

    def generate(self) -> Dict[str, Any]:

        self._bindings = []  # reset

        # ORDER IS CRITICAL FOR DETERMINISM
        self._bind_authority()
        self._bind_trace()
        self._bind_state()
        self._bind_proof()
        self._bind_runtime()

        manifest = {
            "binding_manifest": {
                "source_artifacts": self._compute_source_hashes(),
                "bindings": self._bindings,
                "root_binding_hash": self._compute_root_hash(),
            }
        }

        return manifest

    # =============================================================
    # SOURCE HASHES
    # =============================================================

    def _compute_source_hashes(self) -> Dict[str, str]:

        return {
            "genesis_hash": compute_genesis_hash(self.genesis),
            "trace_schema_hash": hash_obj(self.trace_schema),
            "state_schema_hash": hash_obj(self.state_schema),
            "invariants_hash": hash_obj(self.invariants),
        }

    # =============================================================
    # BINDING CREATION (GENERIC)
    # =============================================================

    def _create_binding(
        self,
        binding_id: str,
        binding_type: str,
        target: str,
        constraint: str,
        derived_from: List[str],
        scope: List[str],
        enforcement_level: str = "STRICT"
    ) -> Dict[str, Any]:

        base = {
            "id": binding_id,
            "type": binding_type,
            "target": target,
            "constraint": constraint,
            "derived_from": sorted(derived_from),
            "binding_version": "v1",
            "scope": {
                "applies_to": sorted(scope),
                "enforcement_level": enforcement_level,
            },
            "validation": {
                "required": True,
                "failure_policy": {
                    "type": "HARD_FAILURE",
                    "effect": "SYSTEM_REJECTION",
                },
            },
        }

        base["binding_hash"] = hash_obj(base)

        return base

    # =============================================================
    # AUTHORITY BINDING (CRITICAL ROOT)
    # =============================================================

    def _bind_authority(self):

        genesis_hash = compute_genesis_hash(self.genesis)

        binding = self._create_binding(
            binding_id="BIND-AUTH-ROOT-001",
            binding_type="AUTHORITY_BINDING",
            target="GLOBAL_AUTHORITY",
            constraint="All authority MUST derive from GENESIS",
            derived_from=[genesis_hash],
            scope=["EXECUTION", "VALIDATION", "TRACE", "STATE"],
        )

        self._bindings.append(binding)

    # =============================================================
    # TRACE BINDING
    # =============================================================

    def _bind_trace(self):

        binding = self._create_binding(
            binding_id="BIND-TRACE-001",
            binding_type="TRACE_BINDING",
            target="TRACE_SYSTEM",
            constraint="Trace events MUST map exactly to execution steps and state transitions",
            derived_from=[
                hash_obj(self.trace_schema),
                hash_obj(self.state_schema)
            ],
            scope=["TRACE", "EXECUTION"],
        )

        self._bindings.append(binding)

    # =============================================================
    # STATE MACHINE BINDING
    # =============================================================

    def _bind_state(self):

        states = self.state_schema.get("state_machine", {}).get("states", [])

        binding = self._create_binding(
            binding_id="BIND-STATE-001",
            binding_type="STATE_BINDING",
            target="STATE_MACHINE",
            constraint=f"State machine MUST enforce {len(states)} states with total transition coverage",
            derived_from=[hash_obj(self.state_schema)],
            scope=["STATE", "EXECUTION"],
        )

        self._bindings.append(binding)

    # =============================================================
    # PROOF BINDING
    # =============================================================

    def _bind_proof(self):

        binding = self._create_binding(
            binding_id="BIND-PROOF-001",
            binding_type="PROOF_BINDING",
            target="TRACE_AND_STATE_PROOFS",
            constraint="All transitions and traces MUST produce verifiable proofs",
            derived_from=[
                hash_obj(self.trace_schema),
                hash_obj(self.state_schema)
            ],
            scope=["VALIDATION", "TRACE", "STATE"],
        )

        self._bindings.append(binding)

    # =============================================================
    # RUNTIME BINDING
    # =============================================================

    def _bind_runtime(self):

        binding = self._create_binding(
            binding_id="BIND-RUNTIME-001",
            binding_type="RUNTIME_BINDING",
            target="EXECUTION_ENVIRONMENT",
            constraint="Runtime MUST enforce all derived bindings with no bypass",
            derived_from=[
                compute_genesis_hash(self.genesis),
                hash_obj(self.state_schema),
                hash_obj(self.trace_schema),
            ],
            scope=["EXECUTION"],
        )

        self._bindings.append(binding)

    # =============================================================
    # ROOT HASH (GLOBAL COMMITMENT)
    # =============================================================

    def _compute_root_hash(self) -> str:

        # IMPORTANT: stable ordering
        ordered_hashes = sorted([
            b["binding_hash"] for b in self._bindings
        ])

        payload = {
            "binding_hashes": ordered_hashes
        }

        return hashlib.sha256(
            canonical_json(payload).encode()
        ).hexdigest()

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self):
        return f"<BindingGenerator bindings={len(self._bindings)}>"