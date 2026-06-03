"""
Read-only Governance Impact API view.

Endpoint purpose
----------------
Return executions that reference a governance object.

Example:

    GET /api/governance/ADR-0016/impact/

Constitutional Law
------------------
The impact API is read-only.
The impact API is reference-only.
The impact API does not govern.
The impact API does not validate runtime truth.
The impact API does not execute runtime behavior.
The impact API does not mutate receipts.
The impact API does not create governance, replay, proof, CI, or runtime authority.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

try:
    from rest_framework.response import Response
    from rest_framework.views import APIView
except Exception:  # pragma: no cover
    APIView = object  # type: ignore[assignment]

    class Response(dict):  # type: ignore[no-redef]
        """Fallback response for non-DRF environments."""


from afritech.impact.impact_query import query_impact_payload


GOVERNANCE_IMPACT_API_STATUS = "READ_ONLY_GOVERNANCE_IMPACT_API"

REFERENCE_ONLY = True
READ_ONLY = True
DISPLAY_ONLY = True

RUNTIME_AUTHORITY = False
ENFORCEMENT_AUTHORITY = False
VALIDATION_AUTHORITY = False
REPLAY_AUTHORITY = False
PROOF_AUTHORITY = False
CI_AUTHORITY = False
GOVERNANCE_AUTHORITY = False

MUTATION_ALLOWED = False
RECEIPT_MUTATION_ALLOWED = False


def _default_receipt_source() -> tuple[Mapping[str, object], ...]:
    """Return default receipt source.

    This intentionally returns an empty tuple.

    Receipts must be injected by an outer read-only adapter, test, or view
    configuration. This view does not read runtime state, proof state, YAML,
    files, databases, or governance projection directly.
    """

    return ()


def build_governance_impact_response(
    governance_id: str,
    receipts: Iterable[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Build read-only governance impact response.

    This function deliberately avoids dict.update(...) so CI can reject
    mutation-style APIs consistently.
    """

    source = receipts if receipts is not None else _default_receipt_source()

    payload = query_impact_payload(
        governance_id=governance_id,
        receipts=source,
    )

    return {
        **payload,
        "api_status": GOVERNANCE_IMPACT_API_STATUS,
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
    }


class GovernanceImpactView(APIView):
    """Read-only governance impact endpoint."""

    receipt_source: Iterable[Mapping[str, object]] | None = None

    def get(self, request, gov_id: str):  # type: ignore[no-untyped-def]
        """Return executions referencing the governance ID."""

        payload = build_governance_impact_response(
            governance_id=gov_id,
            receipts=self.receipt_source,
        )

        return Response(payload)