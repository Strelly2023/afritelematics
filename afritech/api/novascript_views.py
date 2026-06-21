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
def novascript_trust_analytics(request, project_id: str) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(SERVICE.trust_analytics(project_id=project_id, organization_id=organization_id))


@api_view(["POST"])
def novascript_receipt_verify(request) -> Response:
    if not isinstance(request.data, dict):
        return Response({"detail": "receipt payload must be an object"}, status=400)
    return Response(SERVICE.verify_receipt(dict(request.data)))


@api_view(["POST"])
def novascript_audit_verify(request) -> Response:
    if not isinstance(request.data, dict):
        return Response({"detail": "audit package must be an object"}, status=400)
    return Response(SERVICE.verify_audit_package(dict(request.data)))


@api_view(["POST"])
def novascript_validate_artifact(request) -> Response:
    if not isinstance(request.data, dict):
        return Response({"detail": "validation payload must be an object"}, status=400)
    return Response(SERVICE.validate_artifact(dict(request.data)))


@api_view(["POST"])
def novascript_policy_register(request) -> Response:
    source = str(request.data.get("source", "")).strip()
    if not source:
        return Response({"detail": "source required"}, status=400)
    try:
        return Response(SERVICE.register_policy(source))
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=400)


@api_view(["POST"])
def novascript_policy_transition(request, policy_id: str) -> Response:
    status = str(request.data.get("status", "")).strip()
    try:
        return Response(SERVICE.transition_policy(policy_id=policy_id, status=status))
    except (KeyError, ValueError) as exc:
        return Response({"detail": str(exc)}, status=400)


@api_view(["GET"])
def novascript_federation_status(request) -> Response:
    return Response(SERVICE.federation_status())


@api_view(["GET"])
def novascript_global_trust_status(request) -> Response:
    return Response(SERVICE.global_trust_status())


@api_view(["GET"])
def novascript_trust_graph(request) -> Response:
    return Response(SERVICE.trust_graph())


@api_view(["GET"])
def novascript_risk_dashboard(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(SERVICE.organization_risk_dashboard(organization_id=organization_id))


@api_view(["GET"])
def novascript_standard_profile(request) -> Response:
    return Response(SERVICE.standard_profile_status())


@api_view(["GET"])
def novascript_platform_integrations(request) -> Response:
    organization_id = str(request.query_params.get("organization_id", "")).strip() or None
    return Response(SERVICE.platform_integrations(organization_id=organization_id))


@api_view(["POST"])
def novascript_platform_integration_register(request) -> Response:
    scopes = request.data.get("scopes", [])
    if not isinstance(scopes, list):
        return Response({"detail": "scopes must be a list"}, status=400)
    integration_name = str(request.data.get("integration_name", "")).strip()
    integration_type = str(request.data.get("integration_type", "")).strip()
    if not integration_name or not integration_type:
        return Response({"detail": "integration_name and integration_type required"}, status=400)
    return Response(
        SERVICE.register_platform_integration(
            organization_id=str(request.data.get("organization_id", "")).strip() or None,
            integration_name=integration_name,
            integration_type=integration_type,
            scopes=[str(scope) for scope in scopes],
        )
    )


@api_view(["GET"])
def novascript_field_adoption_status(request) -> Response:
    return Response(SERVICE.field_adoption_status())


@api_view(["POST"])
def novascript_organization_onboard(request) -> Response:
    organization_id = str(request.data.get("organization_id", "")).strip()
    legal_name = str(request.data.get("legal_name", "")).strip()
    sector = str(request.data.get("sector", "")).strip()
    trust_domain = str(request.data.get("trust_domain", "")).strip()
    if not all([organization_id, legal_name, sector, trust_domain]):
        return Response(
            {"detail": "organization_id, legal_name, sector, and trust_domain required"},
            status=400,
        )
    return Response(
        SERVICE.onboard_organization(
            organization_id=organization_id,
            legal_name=legal_name,
            sector=sector,
            trust_domain=trust_domain,
        )
    )


@api_view(["POST"])
def novascript_federation_trust_exchange(request) -> Response:
    try:
        trust_score = int(request.data.get("trust_score", 0))
    except (TypeError, ValueError):
        return Response({"detail": "trust_score must be an integer"}, status=400)
    return Response(
        SERVICE.trust_exchange(
            issuer_org=str(request.data.get("issuer_org", "org-nova")),
            subject_org=str(request.data.get("subject_org", "external-auditor")),
            receipt_hash=str(request.data.get("receipt_hash", "")),
            trust_score=trust_score,
        )
    )


@api_view(["POST"])
def novascript_deployment_feedback(request, project_id: str) -> Response:
    evidence = request.data.get("evidence", {})
    if not isinstance(evidence, dict):
        return Response({"detail": "evidence must be an object"}, status=400)
    try:
        validation_score = int(request.data.get("validation_score", 100))
    except (TypeError, ValueError):
        return Response({"detail": "validation_score must be an integer"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    return Response(
        SERVICE.record_deployment_feedback(
            project_id=project_id,
            environment=str(request.data.get("environment", "staging")),
            status=str(request.data.get("status", "validated")),
            validation_score=validation_score,
            evidence=evidence,
            organization_id=organization_id,
        )
    )


@api_view(["POST"])
def novascript_production_evidence(request, project_id: str) -> Response:
    validation_status = str(request.data.get("validation_status", "")).strip()
    if not validation_status:
        return Response({"detail": "validation_status required"}, status=400)
    organization_id = str(request.data.get("organization_id", "")).strip() or None
    evidence_hash = request.data.get("evidence_hash")
    return Response(
        SERVICE.record_production_evidence(
            organization_id=organization_id,
            project_id=project_id,
            environment=str(request.data.get("environment", "production")).strip() or "production",
            evidence_type=str(request.data.get("evidence_type", "deployment_validation")).strip()
            or "deployment_validation",
            validation_status=validation_status,
            evidence_hash=str(evidence_hash) if evidence_hash is not None else None,
        )
    )


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


@api_view(["GET"])
def novascript_public_trust_receipt(request, receipt_id: str) -> Response:
    result = SERVICE.public_receipt(receipt_id)
    if result is None:
        return Response({"detail": "receipt not found"}, status=404)
    return Response(result)


@api_view(["GET"])
def novascript_public_certificate(request, certificate_id: str) -> Response:
    result = SERVICE.public_certificate(certificate_id)
    if result is None:
        return Response({"detail": "certificate not found"}, status=404)
    return Response(result)


@api_view(["GET"])
def novascript_public_assurance(request, report_id: str) -> Response:
    result = SERVICE.public_assurance_report(report_id)
    if result is None:
        return Response({"detail": "assurance report not found"}, status=404)
    return Response(result)


@api_view(["GET"])
def novascript_public_verification_package(request, receipt_id: str) -> Response:
    result = SERVICE.portable_verification_package(receipt_id)
    if result is None:
        return Response({"detail": "verification package not found"}, status=404)
    return Response(result)
