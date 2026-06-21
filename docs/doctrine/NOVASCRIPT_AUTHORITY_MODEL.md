# NovaScript Authority Model

NovaScript separates authorities so no single subsystem becomes unchecked proof authority.

```text
Proof              -> truth authority
Policy Registry    -> governance authority
NovaTrust CA        -> certification authority
Trust Exchange      -> federation authority
External Verify API -> audit authority
Reports             -> presentation authority
```

## Rules

- Receipts prove a governed decision occurred.
- Certificates prove issuance lineage.
- Policies prove decision criteria and version.
- Assurance reports prove monitored trust state.
- Trust exchanges prove cross-organization validation.
- Public endpoints expose read-only verification only.

## Canonical Authority Doctrine

```text
Proof defines truth.

Policy defines governance.

Certificates define provenance.

Assurance defines operational confidence.

Federation defines trust relationships.

Audit verifies evidence.

Reports present information.

No layer above may redefine truth.
```

## Non-Override Rule

Presentation, dashboards, public portals, SDK helpers, audit packages, trust graph views, and generated reports may explain or expose evidence. They may not redefine proof truth, mutate runtime state, override policy decisions, or claim production authority.
