# afriride_system/django_app/blockchain/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import publish_proof_to_chain


@api_view(["POST"])
def anchor_proof(request):
    """
    Publish architecture proof to blockchain (Sepolia or fallback).

    Expected payload:
    {
        "proof_hash": "...",
        "mode": "contract"  # optional
    }
    """

    try:
        proof_payload = request.data or {}

        result = publish_proof_to_chain(proof_payload)

        # ✅ Preserve service-level response (no double wrapping)
        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        # ✅ Controlled failure response (never expose stack trace)
        return Response(
            {
                "success": False,
                "mode": "error",
                "error": str(e),
                "anchor": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
