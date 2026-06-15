"""Controlled public verification and registry lookup endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from afritech.architecture.integrity_proof import build_architecture_integrity_proof
from afritech.partner_registry import PartnerRegistryStore
from afritech.partner_verification import PartnerVerificationStore
from afritech.trust_network import TrustRegistryStore


def build_public_verification_router(
    *,
    verification_store: PartnerVerificationStore,
    registry_store: TrustRegistryStore,
    partner_store: PartnerRegistryStore,
) -> APIRouter:
    router = APIRouter(tags=["public-verification"])

    @router.get("/public/verify/health")
    def public_verify_health() -> dict[str, Any]:
        return {
            "status": "ready",
            "classification": "CONTROLLED_PUBLIC_VERIFICATION",
            "authority_boundary": "public_lookup_is_registry_and_packet_read_only",
        }

    @router.get("/public/verify/portal", response_class=HTMLResponse)
    def public_verify_portal() -> str:
        proof = build_architecture_integrity_proof().canonical_dict()
        anchor_id = proof.get("verification_packet", {}).get("anchor_id", "unknown")
        return f"""<!doctype html>
<html lang='en'>
  <head>
    <meta charset='utf-8' />
    <meta name='viewport' content='width=device-width, initial-scale=1' />
    <title>AfriPay Public Verification Portal</title>
    <style>
      :root {{ color-scheme: light; }}
      body {{ font-family: Inter, Arial, sans-serif; margin: 0; background: #f5f7fa; color: #122033; }}
      main {{ max-width: 1080px; margin: 0 auto; padding: 32px 20px 56px; }}
      header {{ padding: 24px 0 12px; }}
      h1 {{ margin: 0 0 8px; font-size: 28px; }}
      p {{ line-height: 1.5; }}
      .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
      .panel {{ background: #fff; border: 1px solid #d9e2ec; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(16,24,40,.04); }}
      .label {{ font-size: 12px; letter-spacing: .02em; text-transform: uppercase; color: #5b7087; margin-bottom: 8px; }}
      code {{ background: #eef3f7; padding: 2px 6px; border-radius: 4px; }}
      a {{ color: #184e8b; text-decoration: none; }}
      ul {{ margin: 8px 0 0 20px; }}
      .status {{ display: inline-block; padding: 4px 10px; border-radius: 999px; background: #e9f6ec; color: #15653c; font-weight: 600; }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <div class='status'>Read-only public surface</div>
        <h1>AfriPay Public Verification Portal</h1>
        <p>Independent parties can verify exported evidence, chain anchors, and trust dashboards without operator credentials.</p>
      </header>
      <section class='grid'>
        <div class='panel'>
          <div class='label'>Proof exports</div>
          <ul>
            <li><a href='/public/architecture/proof'>Architecture proof</a></li>
            <li><a href='/public/verify/{anchor_id}'>Public verification packet</a></li>
            <li><a href='/public/trust/dashboard'>Public trust dashboard</a></li>
            <li><a href='/public/architecture/anchors/dashboard'>Anchor dashboard</a></li>
            <li><a href='/public/architecture/anchors/explorer'>Anchor explorer</a></li>
            <li><a href='/public/architecture/anchors/verification'>Etherscan verification</a></li>
            <li><a href='/public/architecture/anchors/reconciliation'>Cross-network reconciliation</a></li>
          </ul>
        </div>
        <div class='panel'>
          <div class='label'>Audit packages</div>
          <ul>
            <li><a href='/api/afripay/proofs/artifacts?download_format=json'>AfriPay proof bundle JSON</a></li>
            <li><a href='/api/afripay/proofs/artifacts?download_format=pdf'>AfriPay proof bundle PDF</a></li>
          </ul>
        </div>
        <div class='panel'>
          <div class='label'>Evidence boundary</div>
          <p>This portal is read-only. It does not mutate replay, governance, or settlement state.</p>
          <p><code>{proof.get('authority_boundary')}</code></p>
        </div>
      </section>
    </main>
  </body>
</html>"""
    @router.get("/public/registry")
    def public_registry() -> dict[str, Any]:
        proof = build_architecture_integrity_proof().canonical_dict()
        entries = [entry.canonical_dict() for entry in registry_store.list_entries()]
        entries.append(proof["registry_entry"])
        return {
            "classification": "CONTROLLED_PUBLIC_VERIFICATION",
            "entries": entries,
            "count": len(entries),
            "authority_boundary": "public_lookup_is_registry_and_packet_read_only",
        }

    @router.get("/public/verify/{anchor_id}")
    def public_verify(anchor_id: str) -> dict[str, Any]:
        proof = build_architecture_integrity_proof().canonical_dict()
        if proof["verification_packet"]["anchor_id"] == anchor_id:
            return {
                "classification": "CONTROLLED_PUBLIC_VERIFICATION",
                "authority_boundary": "trace_and_replay_remain_truth_public_surface_reads_exports_only",
                "packet": proof["verification_packet"],
                "registry_entry": proof["registry_entry"],
            }
        try:
            packet = verification_store.load(anchor_id)
            registry_entry = registry_store.load(anchor_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="anchor not found") from exc
        return {
            "classification": "CONTROLLED_PUBLIC_VERIFICATION",
            "authority_boundary": "trace_and_replay_remain_truth_public_surface_reads_exports_only",
            "packet": packet.canonical_dict(),
            "registry_entry": registry_entry.canonical_dict(),
        }

    @router.get("/public/partners/registry")
    def public_partner_registry() -> dict[str, Any]:
        partners = [
            entry.canonical_dict()
            for entry in partner_store.list_entries()
            if entry.public_endpoint_enabled or entry.trust_registry_enabled
        ]
        return {
            "classification": "CONTROLLED_PUBLIC_PARTNER_REGISTRY",
            "partners": partners,
            "count": len(partners),
            "authority_boundary": "partner_registry_indexes_adoption_only",
        }

    return router


__all__ = ["build_public_verification_router"]
