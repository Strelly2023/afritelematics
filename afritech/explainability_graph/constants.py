"""
Constitutional constants for the Explainability Graph.

The Explainability Graph is a read-only visualization and explanation layer.

Constitutional Law
------------------
Graph explains.
Graph visualizes.
Graph does not govern.
Graph does not validate.
Graph does not execute.
Graph does not influence runtime authority.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Constitutional Identity
# ---------------------------------------------------------------------

GRAPH_COMPONENT = "EXPLAINABILITY_GRAPH"

GRAPH_STATUS = "READ_ONLY_EXPLAINABILITY_GRAPH"

GRAPH_VERSION = "1.0"

# ---------------------------------------------------------------------
# Authority Boundaries
# ---------------------------------------------------------------------

RUNTIME_AUTHORITY = False

ENFORCEMENT_AUTHORITY = False

VALIDATION_AUTHORITY = False

REPLAY_AUTHORITY = False

PROOF_AUTHORITY = False

CI_AUTHORITY = False

# ---------------------------------------------------------------------
# Projection Boundaries
# ---------------------------------------------------------------------

PROJECTION_DEPENDENCY = False

PROJECTION_AUTHORITY = False

PROJECTION_DISPLAY_ONLY = True

# ---------------------------------------------------------------------
# Runtime Boundaries
# ---------------------------------------------------------------------

RUNTIME_DEPENDENCY = False

EXECUTION_DEPENDENCY = False

MUTATION_ALLOWED = False

STATE_MODIFICATION_ALLOWED = False

RECEIPT_MUTATION_ALLOWED = False

# ---------------------------------------------------------------------
# Data Classification
# ---------------------------------------------------------------------

GRAPH_DATA_CLASSIFICATION = "REFERENCE_ONLY"

GRAPH_OUTPUT_CLASSIFICATION = "DISPLAY_ONLY"

GRAPH_RELATIONSHIP_CLASSIFICATION = "NON_AUTHORITATIVE"

# ---------------------------------------------------------------------
# Allowed Node Types
# ---------------------------------------------------------------------

ALLOWED_NODE_TYPES = (
    "Execution",
    "ADR",
    "Invariant",
    "Rule",
    "Binding",
    "Receipt",
    "Proof",
)

# ---------------------------------------------------------------------
# Allowed Edge Types
# ---------------------------------------------------------------------

ALLOWED_EDGE_TYPES = (
    "governed_by",
    "explained_by",
    "references",
    "linked_to",
)

# ---------------------------------------------------------------------
# Constitutional Invariants
# ---------------------------------------------------------------------

INVARIANT_GRAPH_IS_READ_ONLY = True

INVARIANT_GRAPH_IS_NON_AUTHORITATIVE = True

INVARIANT_GRAPH_IS_DISPLAY_ONLY = True

INVARIANT_GRAPH_CANNOT_INFLUENCE_RUNTIME = True

INVARIANT_GRAPH_CANNOT_INFLUENCE_REPLAY = True

INVARIANT_GRAPH_CANNOT_INFLUENCE_PROOF = True

# ---------------------------------------------------------------------
# Validator Expectations
# ---------------------------------------------------------------------

EXPECTED_VALIDATOR_NAME = (
    "afritech.ci.explainability_graph_validator"
)

EXPECTED_TEST_MODULE = (
    "afritech.tests.ci.test_explainability_graph_validator"
)

# ---------------------------------------------------------------------
# Constitutional Statement
# ---------------------------------------------------------------------

CONSTITUTIONAL_STATEMENT = (
    "The Explainability Graph is a read-only explanatory surface. "
    "It may visualize relationships between executions, governance "
    "artifacts, receipts, and proofs, but it shall not participate in "
    "runtime execution, replay authority, proof validation, governance "
    "authority, or admissibility decisions."
) 