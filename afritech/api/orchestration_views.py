from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.response import Response

from afritech.afritpps.observability import (
    build_orchestration_view,
    list_orchestration_views,
)
from afritech.afritpps.persistent import (
    OperatorControlError,
    abort_orchestration,
    pause_orchestration,
    resume_orchestration,
)


@api_view(["GET"])
def orchestration_list_view(request) -> Response:
    return Response({"orchestrations": list_orchestration_views()})


@api_view(["GET"])
def orchestration_detail_view(request, orchestration_id: str) -> Response:
    try:
        view = build_orchestration_view(orchestration_id)
    except Exception:
        return Response({"detail": "orchestration not found"}, status=404)
    return Response(view.canonical_dict())


@api_view(["POST"])
def orchestration_pause_view(request, orchestration_id: str) -> Response:
    return _control_response(
        pause_orchestration,
        request,
        orchestration_id,
    )


@api_view(["POST"])
def orchestration_resume_view(request, orchestration_id: str) -> Response:
    return _control_response(
        resume_orchestration,
        request,
        orchestration_id,
    )


@api_view(["POST"])
def orchestration_abort_view(request, orchestration_id: str) -> Response:
    return _control_response(
        abort_orchestration,
        request,
        orchestration_id,
    )


def _control_response(action, request, orchestration_id: str) -> Response:
    operator_id = str(request.data.get("operator_id") or "operator:unknown")
    reason = str(request.data.get("reason") or "")
    try:
        orchestration = action(
            orchestration_id,
            operator_id=operator_id,
            reason=reason,
        )
    except OperatorControlError as exc:
        return Response({"detail": str(exc)}, status=400)
    except Exception:
        return Response({"detail": "orchestration not found"}, status=404)
    return Response(build_orchestration_view(orchestration.orchestration_id).canonical_dict())
