"""Django REST surfaces for the NovaScript product."""

from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.response import Response

from afritech.novascript import get_novascript_service


SERVICE = get_novascript_service()


@api_view(["GET"])
def novascript_status(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(SERVICE.status(organization_id=organization_id))


@api_view(["GET"])
def novascript_catalog(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(SERVICE.catalog(organization_id=organization_id))


@api_view(["GET"])
def novascript_model_status(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(SERVICE.model_status(organization_id=organization_id))


@api_view(["GET"])
def novascript_prompts(request) -> Response:
    return Response(SERVICE.prompt_catalog())


@api_view(["GET"])
def novascript_context(request, project_id: str) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(SERVICE.project_context(project_id, organization_id=organization_id))


@api_view(["GET"])
def novascript_memory(request, project_id: str) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(SERVICE.memory_snapshot(project_id=project_id, organization_id=organization_id))


@api_view(["POST"])
def novascript_generate(request) -> Response:
    prompt = str(request.data.get("prompt", "")).strip()
    if len(prompt) < 3:
        return Response({"detail": "prompt required"}, status=400)
    return Response(
        SERVICE.generate(
            prompt=prompt,
            project_id=str(request.data.get("project_id", "project-employee-rbac")).strip(),
            language=str(request.data.get("language", "python")).strip() or "python",
            mode=str(request.data.get("mode", "code")).strip() or "code",
            organization_id=str(request.data.get("organization_id", "")).strip() or None,
        )
    )


@api_view(["POST"])
def novascript_explain(request) -> Response:
    code = str(request.data.get("code", "")).strip()
    if not code:
        return Response({"detail": "code required"}, status=400)
    return Response(
        SERVICE.explain(
            code=code,
            context=str(request.data.get("context", "")).strip(),
            organization_id=str(request.data.get("organization_id", "")).strip() or None,
        )
    )


@api_view(["POST"])
def novascript_debug(request) -> Response:
    return Response(
        SERVICE.debug(
            code=str(request.data.get("code", "")),
            error=str(request.data.get("error", "")),
            context=str(request.data.get("context", "")),
            organization_id=str(request.data.get("organization_id", "")).strip() or None,
        )
    )


@api_view(["POST"])
def novascript_architecture(request) -> Response:
    description = str(request.data.get("description", "")).strip()
    if len(description) < 3:
        return Response({"detail": "description required"}, status=400)
    return Response(
        SERVICE.architecture(
            description=description,
            stack=str(request.data.get("stack", "FastAPI + PostgreSQL")).strip() or "FastAPI + PostgreSQL",
            organization_id=str(request.data.get("organization_id", "")).strip() or None,
        )
    )


@api_view(["POST"])
def novascript_tests(request) -> Response:
    target = str(request.data.get("target", "")).strip()
    if not target:
        return Response({"detail": "target required"}, status=400)
    return Response(
        SERVICE.tests(
            target=target,
            framework=str(request.data.get("framework", "pytest")).strip() or "pytest",
            organization_id=str(request.data.get("organization_id", "")).strip() or None,
        )
    )


@api_view(["POST"])
def novascript_docs(request) -> Response:
    topic = str(request.data.get("topic", "")).strip()
    if not topic:
        return Response({"detail": "topic required"}, status=400)
    metadata = request.data.get("metadata", {})
    if not isinstance(metadata, dict):
        return Response({"detail": "metadata must be an object"}, status=400)
    return Response(
        SERVICE.docs(
            topic=topic,
            audience=str(request.data.get("audience", "developer")).strip() or "developer",
            format=str(request.data.get("format", "README")).strip() or "README",
            metadata=metadata,
            organization_id=str(request.data.get("organization_id", "")).strip() or None,
        )
    )


@api_view(["GET"])
def novascript_receipts(request, project_id: str) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(SERVICE.receipt_history(project_id=project_id, organization_id=organization_id))


@api_view(["GET"])
def novascript_repo_intelligence(request, project_id: str) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    focus = str(request.query_params.get("focus", "")).strip()
    return Response(
        SERVICE.repository_intelligence(
            project_id=project_id,
            focus=focus,
            organization_id=organization_id,
        )
    )
