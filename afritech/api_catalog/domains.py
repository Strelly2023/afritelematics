"""Domain API contract definitions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DomainEndpoint:
    method: str
    path: str
    operation_id: str
    summary: str
    audience: tuple[str, ...]
    authority_policy: str
    allowed_roles: tuple[str, ...]
    risk_level: str = "medium"
    idempotency_required: bool = False
    audit_required: bool = True
    replay_required: bool = False
    receipt_required: bool = False
    deprecated: bool = False
    replaced_by: str | None = None
    removal_version: str | None = None
    response_enveloped: bool = True
    error_schema: str = "NovaTechError"


@dataclass(frozen=True, slots=True)
class ApiContract:
    domain: str
    version: str
    maturity: str
    audience: tuple[str, ...]
    owner: str
    authority: str
    replay_required: bool
    evidence_required: bool
    supported_until: str
    description: str
    endpoints: tuple[DomainEndpoint, ...] = field(default_factory=tuple)
    sdk_targets: tuple[str, ...] = field(default_factory=tuple)


def _endpoint(
    method: str,
    path: str,
    operation_id: str,
    summary: str,
    audience: tuple[str, ...],
    roles: tuple[str, ...],
    *,
    authority: str = "NovaPolicy",
    risk: str = "medium",
    idempotency: bool = False,
    replay: bool = False,
    receipt: bool = False,
    deprecated: bool = False,
    replaced_by: str | None = None,
) -> DomainEndpoint:
    return DomainEndpoint(
        method=method,
        path=path,
        operation_id=operation_id,
        summary=summary,
        audience=audience,
        authority_policy=authority,
        allowed_roles=roles,
        risk_level=risk,
        idempotency_required=idempotency,
        replay_required=replay,
        receipt_required=receipt,
        deprecated=deprecated,
        replaced_by=replaced_by,
        removal_version="2027.01.0" if deprecated else None,
    )


def default_api_contracts() -> tuple[ApiContract, ...]:
    return (
        ApiContract(
            domain="platform",
            version="2026.07.0",
            maturity="stable",
            audience=("employee", "operator", "administrator"),
            owner="NovaTech Platform",
            authority="NovaPolicy",
            replay_required=False,
            evidence_required=True,
            supported_until="2027-07-01",
            description="Platform catalog, releases, compatibility, migrations, and API governance.",
            sdk_targets=("platform-sdk-typescript",),
            endpoints=(
                _endpoint("GET", "/v1/platform/api-catalog", "listApiCatalog", "List federated API contracts.", ("employee", "operator", "administrator"), ("DEVELOPER", "OPERATOR", "ADMIN"), replay=False),
                _endpoint("GET", "/v1/platform/releases", "listPlatformApiReleases", "List API release lifecycle records.", ("employee", "operator", "administrator"), ("DEVELOPER", "OPERATOR", "ADMIN")),
                _endpoint("GET", "/v1/platform/compatibility", "platformApiCompatibility", "Show compatibility policy.", ("employee", "operator", "administrator"), ("DEVELOPER", "OPERATOR", "ADMIN")),
            ),
        ),
        ApiContract(
            domain="novaride",
            version="2026.07.0",
            maturity="pilot",
            audience=("customer", "partner", "operator"),
            owner="NovaRide Mobility",
            authority="NovaPolicy",
            replay_required=True,
            evidence_required=True,
            supported_until="2027-07-01",
            description="Ride, driver, passenger, fleet, dispatch, logistics, corporate, and transit APIs.",
            sdk_targets=("novaride-sdk-typescript", "novaride-sdk-kotlin", "novaride-sdk-swift"),
            endpoints=(
                _endpoint("POST", "/v1/rides", "createRide", "Create canonical ride request.", ("customer", "partner"), ("CUSTOMER", "PARTNER"), risk="high", idempotency=True, replay=True),
                _endpoint("GET", "/v1/rides/{ride_id}", "getRide", "Get canonical ride state.", ("customer", "partner", "operator"), ("CUSTOMER", "PARTNER", "OPERATOR"), replay=True),
                _endpoint("POST", "/v1/rides/{ride_id}/accept", "acceptRide", "Driver accepts a ride.", ("partner", "operator"), ("DRIVER", "OPERATOR"), risk="high", idempotency=True, replay=True),
                _endpoint("POST", "/v1/rides/{ride_id}/complete", "completeRide", "Complete a ride.", ("partner", "operator"), ("DRIVER", "OPERATOR"), risk="high", idempotency=True, replay=True, receipt=True),
                _endpoint("GET", "/v1/rides/{ride_id}/replay", "getRideReplay", "Get ride replay package.", ("customer", "partner", "operator"), ("CUSTOMER", "PARTNER", "OPERATOR"), authority="NovaTrust", replay=True),
                _endpoint("GET", "/passenger/status/{ride_id}", "legacyPassengerRideStatus", "Legacy passenger ride status alias.", ("customer",), ("CUSTOMER",), deprecated=True, replaced_by="/v1/rides/{ride_id}"),
            ),
        ),
        ApiContract(
            domain="novapay",
            version="2026.07.0",
            maturity="stable",
            audience=("partner", "operator", "internal-service"),
            owner="NovaPay Core",
            authority="NovaPower",
            replay_required=True,
            evidence_required=True,
            supported_until="2027-07-01",
            description="Wallets, transfers, payments, settlement, and ledger-reference APIs.",
            sdk_targets=("novapay-sdk-python", "novapay-sdk-typescript"),
            endpoints=(
                _endpoint("POST", "/v1/novapay/payment-intents", "createPaymentIntent", "Create payment intent.", ("partner", "internal-service"), ("FINANCE", "OPERATOR"), authority="NovaPower", risk="high", idempotency=True, replay=True, receipt=True),
                _endpoint("GET", "/v1/novapay/wallets/{wallet_id}", "getWallet", "Get wallet summary.", ("partner", "operator"), ("FINANCE", "OPERATOR"), authority="NovaPower", risk="high", replay=True),
            ),
        ),
        ApiContract(
            domain="novaid",
            version="2026.07.0",
            maturity="stable",
            audience=("customer", "partner", "employee", "internal-service"),
            owner="NovaID Identity",
            authority="NovaID",
            replay_required=False,
            evidence_required=True,
            supported_until="2027-07-01",
            description="Identity, devices, credentials, consent, and trust posture APIs.",
            sdk_targets=("novaid-sdk-java",),
            endpoints=(
                _endpoint("POST", "/v1/novaid/sessions", "createNovaIdSession", "Create identity session.", ("customer", "partner", "employee"), ("CUSTOMER", "PARTNER", "EMPLOYEE"), authority="NovaID", risk="high", idempotency=True),
                _endpoint("GET", "/v1/novaid/devices/{device_id}", "getDeviceTrust", "Get device trust posture.", ("partner", "operator", "internal-service"), ("PARTNER", "OPERATOR"), authority="NovaID"),
            ),
        ),
        ApiContract(
            domain="novatrust",
            version="2026.07.0",
            maturity="stable",
            audience=("public", "partner", "operator"),
            owner="NovaTrust Evidence",
            authority="NovaTrust",
            replay_required=True,
            evidence_required=True,
            supported_until="2027-07-01",
            description="Replay, evidence, signatures, and public verification APIs.",
            sdk_targets=("novatrust-sdk-go",),
            endpoints=(
                _endpoint("GET", "/public/trust/proofs/{proof_id}", "getPublicProof", "Get public proof.", ("public",), (), authority="NovaTrust", replay=True),
                _endpoint("GET", "/v1/trust/evidence/{evidence_id}", "getTrustEvidence", "Get evidence record.", ("partner", "operator"), ("PARTNER", "OPERATOR"), authority="NovaTrust", replay=True),
            ),
        ),
        ApiContract(
            domain="novaprogramming",
            version="2026.07.0",
            maturity="pilot",
            audience=("employee", "operator", "administrator"),
            owner="NovaProgramming",
            authority="NovaCodePro",
            replay_required=True,
            evidence_required=True,
            supported_until="2027-07-01",
            description="Workflows, agents, artifacts, and assurance APIs.",
            sdk_targets=("novaprogramming-sdk-typescript",),
            endpoints=(
                _endpoint("POST", "/v1/novaprogramming/workflows", "createWorkflow", "Create governed workflow.", ("employee", "operator"), ("DEVELOPER", "OPERATOR"), authority="NovaCodePro", risk="high", idempotency=True, replay=True),
            ),
        ),
        ApiContract(
            domain="operations",
            version="2026.07.0",
            maturity="stable",
            audience=("operator", "administrator", "internal-service"),
            owner="NovaTech Operations",
            authority="NovaOps",
            replay_required=False,
            evidence_required=True,
            supported_until="2027-07-01",
            description="Health, readiness, metrics, dashboards, and operational controls.",
            endpoints=(
                _endpoint("GET", "/health", "getHealth", "Service health.", ("operator", "internal-service"), ("OPERATOR", "ADMIN"), authority="NovaOps"),
                _endpoint("GET", "/v1/health", "getVersionedHealth", "Versioned health.", ("operator", "internal-service"), ("OPERATOR", "ADMIN"), authority="NovaOps"),
            ),
        ),
        ApiContract(
            domain="public-verification",
            version="2026.07.0",
            maturity="stable",
            audience=("public", "partner"),
            owner="NovaTrust Public Verification",
            authority="NovaTrust",
            replay_required=True,
            evidence_required=True,
            supported_until="2027-07-01",
            description="Trust badges, public proofs, and verification portals.",
            endpoints=(
                _endpoint("GET", "/public/verification/{identifier}", "publicVerify", "Verify public identifier.", ("public",), (), authority="NovaTrust", replay=True),
            ),
        ),
        ApiContract(
            domain="partner",
            version="2026.07.0",
            maturity="pilot",
            audience=("partner", "operator", "administrator"),
            owner="NovaTech Partner Platform",
            authority="NovaPolicy",
            replay_required=True,
            evidence_required=True,
            supported_until="2027-07-01",
            description="API keys, webhooks, onboarding, and certification.",
            endpoints=(
                _endpoint("GET", "/v1/partner/certification/status", "getPartnerCertificationStatus", "Get partner certification status.", ("partner", "operator"), ("PARTNER", "OPERATOR"), replay=True),
                _endpoint("POST", "/v1/partner/certification/run", "runPartnerCertification", "Run partner certification.", ("partner", "operator"), ("PARTNER", "OPERATOR"), risk="high", idempotency=True, replay=True),
                _endpoint("GET", "/v1/partner/certification/evidence", "getPartnerCertificationEvidence", "Get partner certification evidence.", ("partner", "operator"), ("PARTNER", "OPERATOR"), authority="NovaTrust", replay=True),
            ),
        ),
    )
