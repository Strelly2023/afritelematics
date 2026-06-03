"""
Read-only execution explanation API.

Constitutional boundaries:

- explains execution
- does not validate execution
- does not authorize execution
- does not mutate receipts
- does not mutate governance
- projection enrichment is optional and display-only
"""

from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from afritech.explainability.execution_explainer import (
    explain_execution_from_store,
)

from afritech.explainability.projection_enrichment import (
    enrich_explanation_payload,
)


@api_view(["GET"])
def explain_execution_view(request, execution_id: str):
    """
    Read-only execution explanation endpoint.

    Returns:
        explanation payload

    Never:
        - validates truth
        - performs runtime decisions
        - modifies receipts
        - modifies governance
        - grants authority
    """

    try:
        explanation_payload = explain_execution_from_store(execution_id)

        # --------------------------------------------------
        # OPTIONAL PROJECTION ENRICHMENT
        #
        # Display-only.
        # If projection data is unavailable,
        # explanation still succeeds.
        # --------------------------------------------------

        projection_index = getattr(
            request,
            "projection_index",
            {},
        )

        if isinstance(projection_index, dict):
            explanation_payload = enrich_explanation_payload(
                explanation_payload,
                projection_index,
            )

        return Response(
            explanation_payload,
            status=status.HTTP_200_OK,
        )

    except FileNotFoundError:
        return Response(
            {
                "error": "execution explanation artifact not found",
                "execution_id": execution_id,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    except ValueError as exc:
        return Response(
            {
                "error": str(exc),
                "execution_id": execution_id,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception:
        # fail closed without leaking internals

        return Response(
            {
                "error": "execution explanation unavailable",
                "execution_id": execution_id,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )