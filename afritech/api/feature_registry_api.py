"""Read-only API surface for the governed NovaTech feature registry."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Literal

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.ecosystem_evolution import (
    build_ecosystem_evolution_certificate,
    build_interoperable_verification_standard,
    publish_live_ecosystem_anchor,
    verify_ecosystem_evolution_certificate,
)
from afritech.features import registry_payload
from afritech.global_verification import (
    build_global_verification_bundle,
    verify_global_verification_bundle,
)
from afritech.tools.feature_registry_verifier import verify_registry_payload
from afritech.trust_badges import build_trust_badge, verify_trust_badge
from afritech.trust_federation import (
    build_federated_trust_certificate,
    verify_federated_trust_certificate,
)


class FeatureRegistryFeatureSchema(BaseModel):
    id: str
    name: str
    technical_status: str
    activation_status: str
    evidence_complete: bool

    class Config:
        extra = "allow"


class FeatureRegistryPayloadSchema(BaseModel):
    classification: Literal["GOVERNED_EVIDENCE_VALIDATED_FEATURE_REGISTRY"]
    status: Literal["FEATURE_REGISTRY_LEVEL_12"]
    generation_mode: Literal["REPLAY_DERIVED_EVIDENCE_PROJECTION"]
    candidate_feature_count: int = Field(ge=0)
    feature_count: int = Field(ge=0)
    complete_feature_count: int = Field(ge=0)
    production_ready_feature_count: int = Field(ge=0)
    live_pilot_authorized: Literal[False]
    production_proven: Literal[False]
    economic_activation_allowed: Literal[False]
    read_only: Literal[True]
    creates_authority: Literal[False]
    feature_hash: str
    evidence_hash: str
    registry_hash: str
    signature: dict[str, object]
    features: list[FeatureRegistryFeatureSchema]

    class Config:
        extra = "allow"


def build_feature_registry_router() -> APIRouter:
    router = APIRouter(tags=["feature-registry"])

    def _payload() -> dict[str, object]:
        return registry_payload()

    @router.get("/api/feature-registry", response_model=FeatureRegistryPayloadSchema)
    def feature_registry(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> FeatureRegistryPayloadSchema:
        return _payload()

    @router.get("/v1/feature-registry", response_model=FeatureRegistryPayloadSchema)
    def feature_registry_v1(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> FeatureRegistryPayloadSchema:
        return _payload()

    @router.get("/public/feature-registry", response_model=FeatureRegistryPayloadSchema)
    def public_feature_registry() -> FeatureRegistryPayloadSchema:
        return _payload()

    @router.get("/public/feature-registry/verify")
    def public_feature_registry_verify() -> dict[str, object]:
        verification = verify_registry_payload(_payload())
        federation = verify_federated_trust_certificate(build_federated_trust_certificate(_payload()))
        return {
            **verification,
            "federated_trust": federation,
        }

    @router.get("/public/trust-badge")
    def public_trust_badge() -> dict[str, object]:
        badge = build_trust_badge()
        return {
            **badge,
            "verification": verify_trust_badge(badge),
        }

    @router.get("/public/trust-badge/{feature_id}")
    def public_feature_trust_badge(feature_id: str) -> dict[str, object]:
        badge = build_trust_badge(feature_id)
        if badge["feature"] is None:
            raise HTTPException(status_code=404, detail="feature not found")
        return {
            **badge,
            "verification": verify_trust_badge(badge),
        }

    @router.get("/public/trust-badge/{feature_id}/html", response_class=HTMLResponse)
    def public_feature_trust_badge_html(feature_id: str) -> str:
        badge = build_trust_badge(feature_id)
        if badge["feature"] is None:
            raise HTTPException(status_code=404, detail="feature not found")
        feature = badge.get("feature") if isinstance(badge.get("feature"), dict) else {}
        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{badge["label"]}</title>
    <style>
      body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #f5f7fb; color: #172033; font-family: Inter, Arial, sans-serif; }}
      main {{ width: min(520px, calc(100vw - 32px)); border: 1px solid #c9d7df; border-radius: 8px; background: #fff; padding: 22px; box-shadow: 0 18px 48px rgba(24, 36, 50, 0.12); }}
      .badge {{ display: inline-flex; align-items: center; gap: 10px; border: 1px solid #8bb9a5; border-radius: 999px; background: #edf8f3; color: #155d42; padding: 8px 12px; font-weight: 900; }}
      .mark {{ width: 18px; height: 18px; border-radius: 999px; display: grid; place-items: center; background: #1f7a55; color: #fff; font-size: 13px; }}
      h1 {{ margin: 18px 0 8px; font-size: 28px; line-height: 1.1; }}
      p {{ color: #526173; line-height: 1.55; }}
      code {{ display: block; margin-top: 12px; background: #edf2f7; border-radius: 6px; padding: 10px; word-break: break-all; }}
      a {{ color: #185b8c; font-weight: 800; text-decoration: none; }}
    </style>
  </head>
  <body>
    <main>
      <div class="badge"><span class="mark">✓</span>{badge["label"]}</div>
      <h1>{feature.get("name", "NovaTech trust proof")}</h1>
      <p>{feature.get("description", "Registry-derived public trust proof.")}</p>
      <p><a href="/public/feature-registry/verify">Verify signed registry</a> · <a href="/public/ecosystem-evolution/verify">Verify system integrity</a></p>
      <code>{badge["registry_hash"]}</code>
    </main>
  </body>
</html>"""

    @router.get("/public/trust-infrastructure")
    def public_trust_infrastructure() -> dict[str, object]:
        certificate = build_federated_trust_certificate(_payload())
        return {
            "classification": "LEVEL_14_FEDERATED_TRUST_NETWORK",
            "registry": _payload(),
            "federated_certificate": certificate.canonical_dict(),
            "verification": verify_federated_trust_certificate(certificate),
            "read_only": True,
            "creates_authority": False,
        }

    @router.get("/public/trust-infrastructure/verify")
    def public_trust_infrastructure_verify() -> dict[str, object]:
        certificate = build_federated_trust_certificate(_payload())
        registry_verification = verify_registry_payload(_payload())
        federation_verification = verify_federated_trust_certificate(certificate)
        return {
            "verified": registry_verification["verified"] and federation_verification["verified"],
            "registry": registry_verification,
            "federation": federation_verification,
            "guarantees": {
                "no_fake_feature_can_exist": registry_verification["no_fake_feature_can_exist"],
                "no_incomplete_feature_can_appear": registry_verification["no_incomplete_feature_can_appear"],
                "no_unverifiable_claim_can_be_exported": registry_verification["no_unverifiable_claim_can_be_exported"],
                "no_production_state_can_be_falsely_implied": registry_verification["no_production_state_can_be_falsely_implied"],
                "no_untrusted_party_can_sign_truth": registry_verification["signer_trusted"],
                "federated_quorum_required": federation_verification["verified"],
            },
        }

    @router.get("/public/global-verification")
    def public_global_verification() -> dict[str, object]:
        bundle = build_global_verification_bundle(_payload())
        return bundle.canonical_dict()

    @router.get("/public/global-verification/verify")
    def public_global_verification_verify() -> dict[str, object]:
        bundle = build_global_verification_bundle(_payload())
        return verify_global_verification_bundle(bundle)

    @router.get("/public/global-verification/portal", response_class=HTMLResponse)
    def public_global_verification_portal() -> str:
        bundle = build_global_verification_bundle(_payload())
        verification = verify_global_verification_bundle(bundle)
        status = "VERIFIED" if verification["verified"] else "REVIEW_REQUIRED"
        cross_network = verification["cross_network"]
        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AfriTech Global Public Verification Layer</title>
    <style>
      body {{ margin: 0; background: #f7f9fc; color: #172033; font-family: Inter, Arial, sans-serif; }}
      main {{ max-width: 1120px; margin: 0 auto; padding: 36px 20px 56px; }}
      h1 {{ margin: 10px 0 8px; font-size: 34px; line-height: 1.05; }}
      p {{ line-height: 1.55; color: #526173; }}
      .status {{ display: inline-flex; border: 1px solid #95c8d8; border-radius: 999px; padding: 6px 12px; color: #15566a; font-weight: 800; background: #eaf7fb; }}
      .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; margin-top: 22px; }}
      .panel {{ border: 1px solid #d1dce5; border-radius: 8px; background: #fff; padding: 16px; }}
      .panel span {{ color: #637287; font-size: 12px; font-weight: 900; text-transform: uppercase; }}
      .panel strong {{ display: block; margin-top: 10px; font-size: 20px; }}
      code {{ background: #edf2f7; border-radius: 4px; padding: 2px 6px; word-break: break-all; }}
      a {{ color: #185b8c; font-weight: 800; text-decoration: none; }}
      ul {{ margin: 8px 0 0 20px; padding: 0; }}
      li {{ margin: 7px 0; }}
    </style>
  </head>
  <body>
    <main>
      <div class="status">{status}</div>
      <h1>AfriTech Global Public Verification Layer</h1>
      <p>Partners and public-sector observers can validate exported truth across independent networks without relying on the originating AfriTech system.</p>
      <section class="grid">
        <article class="panel">
          <span>Classification</span>
          <strong>{verification.get("classification")}</strong>
          <p><code>{verification.get("level")}</code></p>
        </article>
        <article class="panel">
          <span>Global bundle</span>
          <strong>Bundle hash valid: {verification.get("bundle_hash_valid")}</strong>
          <p><code>{verification.get("global_bundle_hash")}</code></p>
        </article>
        <article class="panel">
          <span>Cross-network anchors</span>
          <strong>{cross_network.get("valid_anchor_count")} verified anchors</strong>
          <p>{cross_network.get("network_count")} independent networks, optional on-chain anchoring supported.</p>
        </article>
        <article class="panel">
          <span>Independent truth</span>
          <strong>{verification["guarantees"].get("truth_independent_of_origin_system")}</strong>
          <p>Verification survives export as signed JSON, federated witness data, and public anchor receipts.</p>
        </article>
      </section>
      <section class="grid">
        <article class="panel">
          <span>Global validation links</span>
          <ul>
            <li><a href="/public/global-verification">Global verification bundle</a></li>
            <li><a href="/public/global-verification/verify">Global verification result</a></li>
            <li><a href="/public/trust-infrastructure">Federated trust certificate</a></li>
            <li><a href="/public/feature-registry">Signed registry JSON</a></li>
          </ul>
        </article>
        <article class="panel">
          <span>Authority boundary</span>
          <p>This portal is read-only. It publishes verifiable truth and does not imply live pilot, production, economic, or runtime authority.</p>
        </article>
      </section>
    </main>
  </body>
</html>"""

    @router.get("/public/ecosystem-evolution")
    def public_ecosystem_evolution() -> dict[str, object]:
        certificate = build_ecosystem_evolution_certificate()
        return certificate.canonical_dict()

    @router.get("/public/ecosystem-evolution/verify")
    def public_ecosystem_evolution_verify() -> dict[str, object]:
        certificate = build_ecosystem_evolution_certificate()
        return verify_ecosystem_evolution_certificate(certificate)

    @router.get("/public/ecosystem-evolution/standard")
    def public_ecosystem_evolution_standard() -> dict[str, object]:
        return build_interoperable_verification_standard().canonical_dict()

    @router.post("/api/ecosystem-evolution/anchor/live")
    def publish_ecosystem_live_anchor(
        payload: dict[str, object],
        _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, object]:
        profile_name = str(payload.get("profile", "sepolia"))
        require_live = bool(payload.get("require_live", True))
        receipt = publish_live_ecosystem_anchor(
            profile_name=profile_name,
            require_live=require_live,
        )
        certificate = build_ecosystem_evolution_certificate(live_receipt=receipt)
        return {
            "classification": "LEVEL_16_ECOSYSTEM_TRUST_INFRASTRUCTURE",
            "profile": profile_name,
            "receipt": receipt.canonical_dict(),
            "certificate": certificate.canonical_dict(),
            "verification": verify_ecosystem_evolution_certificate(certificate),
            "read_only": False,
            "creates_runtime_authority": False,
            "authority_boundary": "live_anchor_publishes_public_receipt_without_creating_runtime_or_production_authority",
        }

    @router.get("/public/ecosystem-evolution/portal", response_class=HTMLResponse)
    def public_ecosystem_evolution_portal() -> str:
        certificate = build_ecosystem_evolution_certificate()
        verification = verify_ecosystem_evolution_certificate(certificate)
        status = "VERIFIED" if verification["verified"] else "REVIEW_REQUIRED"
        organizations = verification["organizations"]
        governments = verification["government_adoption"]
        anchor = verification["live_public_ledger_anchoring"]
        standard = verification["interoperable_standard"]
        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AfriTech Ecosystem Trust Infrastructure</title>
    <style>
      body {{ margin: 0; background: #f7f9fc; color: #172033; font-family: Inter, Arial, sans-serif; }}
      main {{ max-width: 1120px; margin: 0 auto; padding: 36px 20px 56px; }}
      h1 {{ margin: 10px 0 8px; font-size: 34px; line-height: 1.05; }}
      p {{ line-height: 1.55; color: #526173; }}
      .status {{ display: inline-flex; border: 1px solid #b8c07c; border-radius: 999px; padding: 6px 12px; color: #59610d; font-weight: 800; background: #fbfbe8; }}
      .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; margin-top: 22px; }}
      .panel {{ border: 1px solid #d1dce5; border-radius: 8px; background: #fff; padding: 16px; }}
      .panel span {{ color: #637287; font-size: 12px; font-weight: 900; text-transform: uppercase; }}
      .panel strong {{ display: block; margin-top: 10px; font-size: 20px; }}
      code {{ background: #edf2f7; border-radius: 4px; padding: 2px 6px; word-break: break-all; }}
      a {{ color: #185b8c; font-weight: 800; text-decoration: none; }}
      ul {{ margin: 8px 0 0 20px; padding: 0; }}
      li {{ margin: 7px 0; }}
    </style>
  </head>
  <body>
    <main>
      <div class="status">{status}</div>
      <h1>AfriTech Ecosystem Trust Infrastructure</h1>
      <p>Level 16 publishes an adoption-ready trust certificate for organizations, government observers, live public-ledger anchoring, and interoperable verification standards.</p>
      <section class="grid">
        <article class="panel">
          <span>Classification</span>
          <strong>{verification.get("classification")}</strong>
          <p><code>{verification.get("level")}</code></p>
        </article>
        <article class="panel">
          <span>Organizations</span>
          <strong>{organizations.get("organization_count")} network profiles</strong>
          <p>Multi-organization trust network verified: {organizations.get("verified")}</p>
        </article>
        <article class="panel">
          <span>Governments</span>
          <strong>{governments.get("government_profile_count")} adoption profiles</strong>
          <p>Cross-government adoption ready: {governments.get("verified")}</p>
        </article>
        <article class="panel">
          <span>Public ledger</span>
          <strong>{anchor.get("status")}</strong>
          <p>Live anchoring supported across {len(anchor.get("supported_profiles", []))} profiles.</p>
        </article>
        <article class="panel">
          <span>Standard</span>
          <strong>{standard.get("standard_id")}</strong>
          <p>Hash valid: {standard.get("standard_hash_valid")}</p>
        </article>
      </section>
      <section class="grid">
        <article class="panel">
          <span>Ecosystem validation links</span>
          <ul>
            <li><a href="/public/ecosystem-evolution">Level 16 ecosystem certificate</a></li>
            <li><a href="/public/ecosystem-evolution/verify">Level 16 verification result</a></li>
            <li><a href="/public/ecosystem-evolution/standard">Interoperable verification standard</a></li>
            <li><a href="/public/global-verification">Level 15 global bundle</a></li>
          </ul>
        </article>
        <article class="panel">
          <span>Authority boundary</span>
          <p>This portal is read-only. It describes adoption and verification infrastructure only; it does not authorize production, live pilot, payment, or runtime execution.</p>
        </article>
      </section>
    </main>
  </body>
</html>"""

    @router.get("/public/feature-registry/portal", response_class=HTMLResponse)
    def public_feature_registry_portal() -> str:
        verification = verify_registry_payload(_payload())
        status = "VERIFIED" if verification["verified"] else "REVIEW_REQUIRED"
        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AfriTech Feature Registry Trust Portal</title>
    <style>
      body {{ margin: 0; background: #f5f7fb; color: #172033; font-family: Inter, Arial, sans-serif; }}
      main {{ max-width: 1120px; margin: 0 auto; padding: 36px 20px 56px; }}
      h1 {{ margin: 10px 0 8px; font-size: 34px; line-height: 1.05; }}
      p {{ line-height: 1.55; color: #526173; }}
      .status {{ display: inline-flex; border: 1px solid #9ccfc0; border-radius: 999px; padding: 6px 12px; color: #146246; font-weight: 800; background: #ecf8f2; }}
      .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; margin-top: 22px; }}
      .panel {{ border: 1px solid #d1dce5; border-radius: 8px; background: #fff; padding: 16px; }}
      .panel span {{ color: #637287; font-size: 12px; font-weight: 900; text-transform: uppercase; }}
      .panel strong {{ display: block; margin-top: 10px; font-size: 20px; }}
      code {{ background: #edf2f7; border-radius: 4px; padding: 2px 6px; }}
      a {{ color: #185b8c; font-weight: 800; text-decoration: none; }}
      ul {{ margin: 8px 0 0 20px; padding: 0; }}
      li {{ margin: 7px 0; }}
    </style>
  </head>
  <body>
    <main>
      <div class="status">{status}</div>
      <h1>AfriTech Feature Registry Trust Portal</h1>
      <p>External partners can validate that exported feature claims are replay-derived, evidence-complete, boundary guarded, signed, and production gated.</p>
      <section class="grid">
        <article class="panel">
          <span>Classification</span>
          <strong>{verification.get("classification")}</strong>
          <p><code>{verification.get("generation_mode")}</code></p>
        </article>
        <article class="panel">
          <span>Registry integrity</span>
          <strong>Signature valid: {verification.get("signature_valid")}</strong>
          <p><code>{verification.get("registry_hash")}</code></p>
        </article>
        <article class="panel">
          <span>Feature safety</span>
          <strong>{verification.get("feature_count")} exported features</strong>
          <p>Production-ready claims: {verification.get("production_ready_feature_count")}</p>
        </article>
        <article class="panel">
          <span>Federated trust</span>
          <strong>Level 14 quorum network</strong>
          <p>Partners and government observers can validate the same signed registry through federated trust witnesses and the Level 15 global public verification layer.</p>
        </article>
        <article class="panel">
          <span>Guarantees</span>
          <ul>
            <li>No fake feature can exist: {verification.get("no_fake_feature_can_exist")}</li>
            <li>No incomplete feature can appear: {verification.get("no_incomplete_feature_can_appear")}</li>
            <li>No unverifiable claim can be exported: {verification.get("no_unverifiable_claim_can_be_exported")}</li>
            <li>No production state can be falsely implied: {verification.get("no_production_state_can_be_falsely_implied")}</li>
          </ul>
        </article>
      </section>
      <section class="grid">
        <article class="panel">
          <span>Partner validation links</span>
          <ul>
            <li><a href="/public/feature-registry">Signed registry JSON</a></li>
            <li><a href="/public/feature-registry/verify">Verification result JSON</a></li>
            <li><a href="/public/trust-infrastructure">Federated trust certificate</a></li>
            <li><a href="/public/trust-infrastructure/verify">Federated trust verification</a></li>
            <li><a href="/public/global-verification">Global verification bundle</a></li>
            <li><a href="/public/global-verification/verify">Global verification result</a></li>
            <li><a href="/public/global-verification/portal">Global public verification portal</a></li>
            <li><a href="/public/ecosystem-evolution">Ecosystem evolution certificate</a></li>
            <li><a href="/public/ecosystem-evolution/verify">Ecosystem evolution verification</a></li>
            <li><a href="/public/ecosystem-evolution/portal">Ecosystem trust portal</a></li>
            <li><a href="/public/trust/dashboard">Public trust dashboard</a></li>
            <li><a href="/public/verify/portal">Public verification portal</a></li>
          </ul>
        </article>
        <article class="panel">
          <span>Authority boundary</span>
          <p>This portal is read-only. It does not create runtime, governance, pilot, economic, or production authority.</p>
        </article>
      </section>
    </main>
  </body>
</html>"""

    return router


__all__ = [
    "FeatureRegistryFeatureSchema",
    "FeatureRegistryPayloadSchema",
    "build_feature_registry_router",
]
