"""Controlled public verification and registry lookup endpoints."""

from __future__ import annotations

from html import escape
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from afritech.architecture.integrity_proof import build_architecture_integrity_proof
from afritech.docs.document_system import load_documentation_compliance_registry
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

    def _documentation_registry_snapshot() -> dict[str, Any]:
        try:
            return load_documentation_compliance_registry() or {}
        except FileNotFoundError:
            return {
                "registry_id": "NOVATECH_DOCUMENTATION_COMPLIANCE_REGISTRY_V1",
                "status": "ACTIVE",
                "standard_protocol": {
                    "name": "AfriCPPT",
                    "expansion": "Global standard protocol for proof, compliance, and trust portability",
                    "publication_surface": "/v1/novatech/documentation/standard",
                },
                "linked_surfaces": {},
            }

    @router.get("/public/verify/health")
    def public_verify_health() -> dict[str, Any]:
        return {
            "status": "ready",
            "classification": "CONTROLLED_PUBLIC_VERIFICATION",
            "authority_boundary": "public_lookup_is_registry_and_packet_read_only",
        }

    @router.get("/public/verify/portal", response_class=HTMLResponse)
    def public_verify_portal(anchor_id: str | None = None) -> str:
        proof = build_architecture_integrity_proof().canonical_dict()
        documentation_registry = _documentation_registry_snapshot()
        standard_protocol = documentation_registry.get("standard_protocol", {})
        public_registry_count = len(list(registry_store.list_entries()))
        partner_entries = [
            entry
            for entry in partner_store.list_entries()
            if entry.public_endpoint_enabled or entry.trust_registry_enabled
        ]
        active_anchor_id = (
            anchor_id
            or proof.get("verification_packet", {}).get("anchor_id")
            or proof.get("anchor_commitment", {}).get("anchor_id")
            or ""
        )
        return f"""<!doctype html>
<html lang='en'>
  <head>
    <meta charset='utf-8' />
    <meta name='viewport' content='width=device-width, initial-scale=1' />
    <meta name='color-scheme' content='light' />
    <title>NovaTrust Public Verification Portal</title>
    <style>
      :root {{
        --bg: #f4f7fb;
        --surface: #ffffff;
        --surface-weak: #f8fbff;
        --ink: #102033;
        --muted: #5c6b7f;
        --line: #d9e3ee;
        --line-strong: #bfd0e2;
        --trust: #184e8b;
        --success: #1e7a4b;
        --radius: 10px;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        font-family: Inter, "Segoe UI", Arial, sans-serif;
        margin: 0;
        background:
          radial-gradient(circle at top right, rgba(24, 78, 139, 0.08), transparent 24%),
          linear-gradient(180deg, #f7f9fc 0%, #eef3f9 100%);
        color: var(--ink);
      }}
      main {{ max-width: 1160px; margin: 0 auto; padding: 28px 20px 56px; }}
      .shell {{ display: grid; gap: 18px; }}
      .hero, .panel, .summary {{
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: var(--radius);
        box-shadow: 0 1px 2px rgba(16,24,40,.04);
      }}
      .hero {{
        padding: 24px;
        display: grid;
        gap: 18px;
      }}
      .hero-top {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        align-items: center;
        justify-content: space-between;
      }}
      .eyebrow {{
        font-size: 12px;
        letter-spacing: .08em;
        text-transform: uppercase;
        color: var(--muted);
      }}
      h1 {{ margin: 0; font-size: clamp(28px, 4vw, 40px); line-height: 1.08; }}
      .lede {{ margin: 0; color: var(--muted); line-height: 1.6; max-width: 78ch; }}
      .status {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 7px 12px;
        border-radius: 999px;
        background: #e8f6ee;
        color: var(--success);
        font-weight: 700;
        white-space: nowrap;
      }}
      .status::before {{
        content: "";
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: currentColor;
      }}
      .trust-bar {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 12px;
      }}
      .summary {{
        padding: 14px 16px;
        background: linear-gradient(180deg, var(--surface), var(--surface-weak));
      }}
      .summary-label {{ font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }}
      .summary-value {{ margin-top: 6px; font-size: 20px; font-weight: 700; }}
      .summary-sub {{ margin-top: 4px; color: var(--muted); font-size: 14px; line-height: 1.45; }}
      .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
      .panel {{ padding: 18px; }}
      .label {{ font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }}
      .panel h2 {{ margin: 0 0 10px; font-size: 18px; }}
      p {{ line-height: 1.6; margin: 0; }}
      a {{ color: var(--trust); text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
      code {{ background: #eef3f7; padding: 2px 6px; border-radius: 4px; }}
      ul {{ margin: 10px 0 0 20px; padding: 0; }}
      li {{ margin: 8px 0; }}
      .link-list {{ display: grid; gap: 8px; margin: 0; padding: 0; list-style: none; }}
      .link-list li {{ margin: 0; }}
      .link-chip {{
        display: inline-flex;
        align-items: center;
        padding: 8px 10px;
        border-radius: 999px;
        border: 1px solid var(--line-strong);
        background: #f8fbff;
        font-size: 14px;
      }}
      .form-row {{
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 10px;
        margin-top: 12px;
      }}
      input[type='text'] {{
        width: 100%;
        border: 1px solid var(--line-strong);
        border-radius: 8px;
        padding: 12px 14px;
        font: inherit;
        background: #fff;
        color: var(--ink);
      }}
      button {{
        border: 0;
        border-radius: 8px;
        padding: 12px 14px;
        background: var(--trust);
        color: #fff;
        font: inherit;
        font-weight: 700;
        cursor: pointer;
      }}
      .muted {{ color: var(--muted); }}
      .callout {{
        border-left: 4px solid var(--trust);
        background: #f6f9fe;
        padding: 14px 16px;
        border-radius: 8px;
      }}
      @media (max-width: 720px) {{
        .hero, .panel {{ padding: 16px; }}
        .form-row {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="shell">
        <header class="hero">
          <div class="hero-top">
            <div class="eyebrow">NovaTrust public verification surface</div>
            <div class="status">Read-only public surface</div>
          </div>
          <h1>Public Trust Verification Portal</h1>
          <p class="lede">
            AfriPay Public Verification Portal for public trust verification. Independent
            parties can verify exported evidence, chain anchors, registry entries, and trust
            dashboards without operator credentials. This portal is evidence-only and does not
            mutate replay, governance, or settlement state.
          </p>
          <div class="trust-bar">
            <div class="summary">
              <div class="summary-label">Active anchor</div>
              <div class="summary-value"><code>{escape(str(active_anchor_id))}</code></div>
              <div class="summary-sub">Deep link to the current public verification packet.</div>
            </div>
            <div class="summary">
              <div class="summary-label">Registry entries</div>
              <div class="summary-value">{public_registry_count}</div>
              <div class="summary-sub">Public trust registry packets visible for lookup.</div>
            </div>
            <div class="summary">
              <div class="summary-label">Partner surfaces</div>
              <div class="summary-value">{len(partner_entries)}</div>
              <div class="summary-sub">Public partner registries and trust-enabled endpoints.</div>
            </div>
          </div>
        </header>

        <section class="grid">
          <div class="panel">
            <div class="label">Verify an anchor</div>
            <h2>Lookup a trust receipt or anchor ID</h2>
            <p class="muted">Enter a public anchor ID to open the canonical verification packet.</p>
            <form class="form-row" id="anchor-lookup">
              <input id="anchor-id" name="anchor_id" type="text" value="{escape(active_anchor_id)}" placeholder="anchor_id or receipt_id" autocomplete="off" spellcheck="false" />
              <button type="submit">Verify</button>
            </form>
            <div class="callout" style="margin-top: 14px;">
              <p>Direct link: <a href="/public/verify/{escape(active_anchor_id)}">/public/verify/{escape(active_anchor_id)}</a></p>
            </div>
          </div>
          <div class="panel">
            <div class="label">Proof exports</div>
            <ul class="link-list">
              <li><a class="link-chip" href='/public/verify/health'>Verification health</a></li>
              <li><a class="link-chip" href='/public/architecture/proof'>Architecture proof</a></li>
              <li><a class="link-chip" href='/public/trust/dashboard'>Public trust dashboard</a></li>
              <li><a class="link-chip" href='/public/architecture/anchors/dashboard'>Anchor dashboard</a></li>
              <li><a class="link-chip" href='/public/architecture/anchors/explorer'>Anchor explorer</a></li>
              <li><a class="link-chip" href='/public/architecture/anchors/verification'>Etherscan verification</a></li>
              <li><a class="link-chip" href='/public/architecture/anchors/reconciliation'>Cross-network reconciliation</a></li>
            </ul>
          </div>
          <div class="panel">
            <div class="label">Documentation compliance</div>
            <ul class="link-list">
              <li><a class="link-chip" href='/public/documentation/portal'>Documentation compliance portal</a></li>
              <li><a class="link-chip" href='/v1/novatech/documentation/standard'>Standard protocol surface</a></li>
            </ul>
            <p style="margin-top: 12px;"><code>{escape(str(standard_protocol.get("name", "AfriCPPT")))}</code></p>
            <p class="muted" style="margin-top: 8px;">
              Public documentation surfaces remain read-only and link out to registry-backed proof.
            </p>
          </div>
          <div class="panel">
            <div class="label">Audit packages</div>
            <ul class="link-list">
              <li><a class="link-chip" href='/api/afripay/proofs/artifacts?download_format=json'>AfriPay proof bundle JSON</a></li>
              <li><a class="link-chip" href='/api/afripay/proofs/artifacts?download_format=pdf'>AfriPay proof bundle PDF</a></li>
            </ul>
          </div>
          <div class="panel">
            <div class="label">Evidence boundary</div>
            <p>This portal is read-only. It does not mutate replay, governance, or settlement state.</p>
            <p style="margin-top: 10px;"><code>public_lookup_is_registry_and_packet_read_only</code></p>
          </div>
        </section>
      </section>
      <script>
        document.getElementById("anchor-lookup")?.addEventListener("submit", function (event) {{
          event.preventDefault();
          var value = document.getElementById("anchor-id")?.value?.trim();
          if (!value) return;
          window.location.href = "/public/verify/" + encodeURIComponent(value);
        }});
      </script>
    </main>
  </body>
</html>"""
    @router.get("/public/registry")
    def public_registry() -> dict[str, Any]:
        proof = build_architecture_integrity_proof().canonical_dict()
        documentation_registry = _documentation_registry_snapshot()
        entries = [entry.canonical_dict() for entry in registry_store.list_entries()]
        entries.append(proof["registry_entry"])
        return {
            "classification": "CONTROLLED_PUBLIC_VERIFICATION",
            "entries": entries,
            "count": len(entries),
            "documentation": {
                "registry_id": documentation_registry.get("registry_id", "NOVATECH_DOCUMENTATION_COMPLIANCE_REGISTRY_V1"),
                "status": documentation_registry.get("status", "ACTIVE"),
                "standard_protocol": documentation_registry.get("standard_protocol", {}),
                "portal": "/public/documentation/portal",
            },
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
