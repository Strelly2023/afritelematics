#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Iterable
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs/governance/NOVATECH_PLATFORM_ADMINISTRATOR_AND_STAFF_MANUAL_V2.md"


def block(text: str) -> str:
    return dedent(text).strip("\n")


@dataclass(frozen=True)
class AppendixDoc:
    title: str
    path: Path
    note: str


CORE_SECTIONS: list[str] = [
    block(
        """
        # NOVATECH PLATFORM ADMINISTRATOR & STAFF MANUAL

        ## Version 2.0

        **Status:** Official internal reference

        **Audience:** Administrators, operations staff, trust staff, finance staff, developers, product operators, and designated contractors

        **Scope:** Internal platform operations, governance, proof, trust, intelligence, economy, SaaS, marketplace, and organization control surfaces

        **Authority boundary:** This manual explains the platform. It does not replace constitutional truth, legal review, government approval, production incident authority, or service-specific runbooks.

        ## Document Control

        | Field | Value |
        |---|---|
        | Document ID | NOVATECH-ADMIN-STAFF-MANUAL-V2 |
        | Version | 2.0 |
        | Classification | Official Internal Document |
        | Owner | NovaTech Platform Operations |
        | Review Cycle | Monthly for active controls, quarterly for policy surfaces |
        | Replacement | Expands and supersedes the original v1 handbook material |

        ## How to Use This Manual

        1. Read the scope and authority boundary first.
        2. Use the role section that matches your access level.
        3. Follow the operating sections that correspond to your daily work.
        4. Use the incident and escalation sections when a system is degraded, uncertain, or under review.
        5. Use the appendices for source-of-truth references, detailed playbooks, and operational pack material.

        ## Platform Summary

        NovaTech is a proof-governed digital infrastructure platform. It unifies governance, execution, proof, trust, intelligence, economy, and organization surfaces into a single operating environment.

        The manual treats the platform as an integrated stack:

        - Constitution and governance define what is allowed.
        - Execution services carry out bounded operational work.
        - Proof and replay preserve truth and traceability.
        - Trust services expose verifiable evidence to operators and external stakeholders.
        - Intelligence services interpret live and historical signals.
        - Economy services manage tenants, billing, and commercial surfaces.
        - Product services provide the business-facing applications.
        - Organization OS surfaces connect intranet, extranet, knowledge, workflow, and communication into one operating model.
        - Outcome intelligence, federated trust, and marketplace services let the platform learn, exchange proofs, and scale across organizations.

        ## Operating Principles

        - Truth before claims.
        - Governance before execution.
        - Proof before trust.
        - Verification before publication.
        - Security before scale.
        - Readability before cleverness.
        - Stability before automation.
        - Human accountability before autonomous action.
        - Evidence before opinion.
        - Replay before belief.

        ## Documentation Governance

        NovaTech documentation is treated as governed platform infrastructure.

        - The canonical source set lives in governed repository documents.
        - The registry records what is published, who owns it, and how it was generated.
        - The lineage manifest records which source documents were used.
        - The certificate records the document hash, source count, and validator version.
        - Role-specific manuals are generated from the same controlled source set.
        - The full reference manual remains the most complete operational knowledge archive.

        Documentation control artifacts live under:

        - `docs/registry/DOCUMENT_REGISTRY.yaml`
        - `docs/registry/lineage/`
        - `docs/registry/certificates/`

        ## Document Lineage

        The full reference manual is generated from governed repository sources. Its detailed lineage manifest and certificate are published in the documentation registry.

        - Source manifest: `docs/registry/lineage/NOVATECH-FULL-REFERENCE-V2.sources.json`
        - Certificate: `docs/registry/certificates/NOVATECH-FULL-REFERENCE-V2.json`
        """
    ),
    block(
        """
        ## 1. Platform Architecture

        NovaTech is organized as a layered control system:

        1. Constitution
        2. Governance
        3. Runtime
        4. Proof
        5. Trust
        6. Intelligence
        7. Economy
        8. Organization OS
        9. Products
        10. Marketplace and Trust Network

        The operating rule is simple: lower layers define legitimacy; higher layers explain, coordinate, and improve.

        | Layer | Responsibility | Typical Owner |
        |---|---|---|
        | Constitution | Invariants, admissibility, identity, replay authority | Governance and constitution maintainers |
        | Governance | Policies, bindings, rule evaluation, approval flow | Governance administrators |
        | Runtime | Services, queues, nodes, throughput, health | Operations administrators |
        | Proof | Evidence, receipts, witness records, verification export | Trust and proof administrators |
        | Trust | Public trust, verification, certification, trust registry | Trust administrators |
        | Intelligence | Analytics, prediction, decision guidance, learning | Operations and product intelligence staff |
        | Economy | Tenants, subscriptions, billing, invoices, marketplace | Finance and SaaS administrators |
        | Organization OS | Intranet, extranet, workflows, knowledge, comms | Platform administrators |
        | Products | Mobility, logistics, health, commerce, and other services | Product operators |
        | Marketplace and Trust Network | Cross-tenant trust exchange and services | Platform strategy and trust leads |

        ## Control Surfaces

        The primary surfaces visible to administrators and staff are:

        - Dashboard
        - Governance
        - Runtime
        - Proof
        - Trust
        - Intelligence
        - Economy
        - Organization OS
        - Products
        - Marketplace
        - Settings

        Each surface is projection-only unless a specific authority layer explicitly grants action rights.
        """
    ),
    block(
        """
        ## 2. Roles and Access Model

        Every staff member must operate within a declared role. Role mismatch is a governance problem, not a convenience issue.

        | Role | Primary Responsibilities | Primary Surfaces | Approval Boundaries |
        |---|---|---|---|
        | System Administrator | Platform configuration, user management, access control, infrastructure monitoring | Settings, runtime, audit, trust registry | Highest administrative access; still bounded by governance |
        | Operations Administrator | Daily operations, incidents, alerts, service health, escalation | Runtime, dashboards, incidents | May coordinate actions but does not redefine truth |
        | Trust Administrator | Trust registry, evidence review, verification services, public verification | Trust, proof, public portal | Can verify and publish trust artifacts only through governed flow |
        | Finance Administrator | Treasury, payments, settlements, billing review, reporting | NovaPay, billing, economy | Financial review and reconciliation, not unbounded spending authority |
        | Developer | Source changes, tests, validation compliance, release support | NovaProgramming, source repos, CI/CD | Must preserve constitutional and release controls |
        | Business Operator | Product management, support, workflows, service delivery | Product dashboards, workflow, analytics | Operates within product and support boundaries |
        | SaaS Administrator | Tenant onboarding, org directory, subscription coordination, execution readiness | Organizations, billing, SaaS status | Can prepare readiness but not bypass safety gates |
        | Security Administrator | Access policy, incident support, credential hygiene, audit review | Security, access logs, policy surfaces | Handles security controls under governance |
        | Data Steward | Data quality, records, retention, export packages | Proof, evidence, records, analytics | Preserves data integrity and provenance |
        | Support Operator | User support, escalation intake, knowledge articles, incident triage | Support, comms, knowledge | Provides service support and escalation routing |

        ## Access Rules

        - Access is granted by role, not by informal request.
        - Access must be minimum necessary.
        - Temporary access must expire.
        - Shared credentials are prohibited.
        - Elevated access requires review and logging.
        - Public verification surfaces never grant authority to mutate proof or truth.

        ## Role Change Procedure

        When a person's responsibility changes:

        1. Update the identity record.
        2. Re-evaluate the access bundle.
        3. Remove old privileges before granting new ones where practical.
        4. Confirm audit logging remains intact.
        5. Document the effective date and approver.
        """
    ),
    block(
        """
        ## 3. Login, Identity, and Access

        The login process is designed to preserve identity, authorization, and audit traceability.

        ### Standard Login Flow

        1. Open the NovaTech portal or approved application.
        2. Enter the assigned username.
        3. Enter the password.
        4. Complete MFA or device verification.
        5. Confirm role and surface assignment.
        6. Land on the authorized dashboard only.

        ### Identity Rules

        - Identity is tied to a named human or service principal.
        - Access tokens must not be shared.
        - Device trust should be recorded where available.
        - Session expiration and re-authentication must be respected.
        - Any suspicious login activity must be reported immediately.

        ### Authentication Hygiene

        - Use strong unique passwords.
        - Use MFA whenever available.
        - Lock screens when unattended.
        - Never store credentials in notes, chat, or plain text.
        - Rotate secrets according to policy.

        ### Access Review Checklist

        - Is the account still active?
        - Is the role still correct?
        - Is MFA enabled?
        - Is the device trusted?
        - Are any elevated privileges still necessary?
        - Is the audit trail complete?
        """
    ),
    block(
        """
        ## 4. Dashboard Map and Navigation

        The dashboard is the first operational map staff should learn.

        | Navigation Item | What It Shows | Typical Use |
        |---|---|---|
        | Dashboard | Cross-platform overview, status, live signals | Start-of-day checks |
        | Governance | Policy registry, bindings, rule validation | Governance review |
        | Runtime | Service health, event throughput, queue health | Operations monitoring |
        | Proof | Evidence, receipts, witness records, export packages | Verification work |
        | Trust | Trust registry, public verification, certification | Trust administration |
        | Intelligence | Analytics, AI insights, predictive surfaces | Decision support |
        | Economy | Tenants, billing, invoices, subscriptions | Finance and SaaS |
        | Organization OS | Intranet, extranet, knowledge, workflows, comms | Organizational control |
        | Products | Product surfaces and operational views | Product operations |
        | Marketplace | Trust services and cross-tenant exchange | Partner strategy |
        | Settings | Access, preferences, environment configuration | Administration |

        ### Dashboard Reading Order

        1. Check system health.
        2. Check open incidents or alerts.
        3. Check trust and proof status.
        4. Check tenancy and billing readiness.
        5. Check active decisions or controlled execution surfaces.
        6. Check pending approvals or escalations.

        ### What Not to Do

        - Do not treat dashboard color alone as authority.
        - Do not ignore proof when the dashboard looks healthy.
        - Do not use screenshots as evidence of truth.
        - Do not reclassify a warning as healthy without review.
        """
    ),
    block(
        """
        ## 5. Governance and Constitution

        Governance defines the admissible operating surface. It does not exist to add bureaucracy; it exists to keep truth stable while the platform evolves.

        ### Governance Responsibilities

        - Maintain the policy registry.
        - Validate rule and binding changes.
        - Preserve policy version provenance.
        - Record governance receipts.
        - Ensure audit and verification pathways remain intact.

        ### Policy Evaluation Inputs

        - Trust score
        - Risk score
        - Federation verification status
        - Receipt verification status
        - Execution tier readiness
        - Safety gate state

        ### Approval Flow

        request
        -> policy evaluation
        -> trust review
        -> receipt issue
        -> certificate chain
        -> assurance
        -> audit or public verification

        ### Governance Checks

        - Is the policy version recorded?
        - Is the binding current?
        - Does the change preserve replay semantics?
        - Does it preserve claim discipline?
        - Does it preserve non-authority of dashboards and analytics?
        - Does it keep proof separate from opinion?

        ### Governance Boundary

        Governance decides what can be admitted. It does not replace legal review, production incident command, or field execution judgment.
        """
    ),
    block(
        """
        ## 6. Runtime Operations

        Runtime operations manage live services, orchestration, queues, throughput, and failure handling.

        ### Core Runtime Checks

        - Active services
        - Service dependencies
        - Node health
        - Queue backlog
        - Event throughput
        - Error rate
        - Memory pressure
        - CPU pressure
        - Recovery status

        ### Operational Cadence

        | Cadence | Checks |
        |---|---|
        | Start of day | Health dashboard, alerts, pending incidents |
        | Midday | Queue health, throughput, backlog, retry storms |
        | End of day | Incident log, resource trend, unresolved warnings |
        | Weekly | Dependency review, scaling review, recovery rehearsal |

        ### What Runtime Staff Must Preserve

        - Event ordering.
        - Replay fidelity.
        - Service traceability.
        - Minimal blast radius for changes.
        - Clear separation between observation and mutation.

        ### Common Failure Modes

        - Backlog accumulation
        - Timeouts
        - Missing heartbeat
        - Unexpected service restart
        - Queue poisoning
        - Dependency drift

        ### Runtime Response Pattern

        1. Observe the symptom.
        2. Confirm whether proof is affected.
        3. Confirm whether replay is affected.
        4. Isolate the failing component.
        5. Preserve evidence.
        6. Restore safely.
        7. Record the resolution.
        """
    ),
    block(
        """
        ## 7. Proof and Verification

        Proof is the record that a governed event occurred as declared.

        ### Proof Responsibilities

        - Search evidence.
        - Verify signatures.
        - Review witness records.
        - Validate registry entries.
        - Export verification packages.
        - Preserve receipt lineage.

        ### Verification Sequence

        1. Select the evidence item.
        2. Review metadata and source.
        3. Validate the signature or deterministic hash.
        4. Confirm registry match.
        5. Confirm replay alignment.
        6. Record the result.

        ### Evidence Types

        - Receipts
        - Replay traces
        - Witness bundles
        - Certificate chains
        - Public verification packages
        - Audit exports

        ### Proof Handling Rules

        - Never edit proof records manually.
        - Never publish unverified evidence as verified.
        - Never delete evidence to simplify reporting.
        - Preserve the chain from event to receipt to verification package.

        ### Operator Questions

        - What happened?
        - What source proves it?
        - What replay or receipt anchors it?
        - What remains unverified?
        - What can be published publicly?
        """
    ),
    block(
        """
        ## 8. Trust Management

        Trust management turns proof into a public-facing trust surface.

        ### Trust Responsibilities

        - Maintain the trust registry.
        - Review proposed trust features.
        - Publish or withhold trust badges.
        - Inspect evidence submissions.
        - Monitor public verification status.
        - Review certification eligibility.

        ### Trust Feature Requirements

        - Every new trust feature must map to a proof source.
        - Every trust badge must have a verification pathway.
        - Every certification must identify its evidence basis.
        - Every public trust claim must be reproducible.

        ### Trust States

        - Verified
        - Pending review
        - Degraded
        - Failed
        - Revoked

        ### Public Trust Portal Expectations

        - Clear receipt lookup.
        - Clear verification result.
        - Clear evidence package access.
        - No hidden mutation path.

        ### Trust Administrator Review Questions

        - Is the evidence complete?
        - Does replay match the claim?
        - Is the signature valid?
        - Does the trust score align with observed evidence?
        - Is the publication safe for external consumption?
        """
    ),
    block(
        """
        ## 9. NovaProgramming Operations

        NovaProgramming is the engineering control plane.

        ### What Developers Must Do

        1. Create the change.
        2. Run tests.
        3. Run validators.
        4. Review evidence.
        5. Document assumptions.
        6. Submit for approval.
        7. Deploy only through governed release paths.

        ### Engineering Controls

        - Use the repository as the source of truth.
        - Keep implementation and proof surfaces aligned.
        - Preserve tests that protect runtime legality.
        - Preserve validator coverage.
        - Preserve evidence links in release artifacts.

        ### Release Discipline

        - No unreviewed schema drift.
        - No untracked API surface addition.
        - No bypass of governance validators.
        - No release without evidence and rollback readiness.

        ### Developer Review Questions

        - Does this change alter runtime authority?
        - Does this change alter proof semantics?
        - Does this change alter public trust claims?
        - Does this change require a new test or validator?
        - Does this change require a release note or runbook update?
        """
    ),
    block(
        """
        ## 10. NovaScript, Analytics, and Decision Intelligence

        NovaScript is the AI and intelligence layer. It observes system conditions, explains them, predicts likely outcomes, and recommends next steps.

        ### Intelligence Surfaces

        - Live trust analytics
        - Replay exception alerts
        - Pilot evidence trends
        - Operator notifications
        - Historical snapshots
        - AI insights
        - Predictive analytics
        - Decision guidance
        - Controlled execution readiness

        ### Decision Lanes

        - Observe
        - Watch
        - Review
        - Escalate

        ### Decision Quality Fields

        - Decision lane
        - Decision action
        - Decision priority
        - Confidence
        - Stability index
        - Recommended actions
        - Watch items
        - Reasoning trace

        ### Controlled Execution Boundaries

        - Advisory does not equal authority.
        - Prediction does not equal permission.
        - Readiness does not equal automatic action.
        - Safety gate pass is necessary but not sufficient when human review is required.

        ### Operator Guidance Rule

        The system should tell operators what to review next, why it matters, and which evidence items justify the recommendation.
        """
    ),
    block(
        """
        ## 11. NovaPay, Finance, and Billing

        NovaPay and the billing surface manage financial visibility, subscriptions, and settlement review.

        ### Finance Responsibilities

        - Review daily transaction summaries.
        - Review settlement reports.
        - Review treasury balances.
        - Review billing previews and invoice drafts.
        - Preserve audit trails for financial operations.

        ### Billing Discipline

        - Usage tracking must be explainable.
        - Subscription previews must be readable.
        - Invoice creation must be governed.
        - No unapproved automatic charging behavior.
        - Billing visibility should not become billing authority without explicit policy.

        ### Finance Review Questions

        - Is the billed usage source identifiable?
        - Are the tenant records current?
        - Do invoices match the approved plan?
        - Are exceptions documented?
        - Are settlements backed by traceable records?
        """
    ),
    block(
        """
        ## 12. Organization OS

        The Organization OS is the internal operating layer that connects intranet, extranet, knowledge, workflows, and communication.

        ### Intranet

        Internal dashboards, operations, staff surfaces, and private coordination live here.

        ### Extranet

        External collaborators, clients, partners, suppliers, and investors use the controlled external view.

        ### Knowledge

        Project files, documents, references, and structured knowledge live here.

        ### Workflows

        Tasks, templates, approvals, and lifecycle states live here.

        ### Communications

        Messages, alerts, and routed operational notifications live here.

        ### Operating Rule

        The Organization OS must reduce cognitive load by putting the right surface in front of the right person at the right time.
        """
    ),
    block(
        """
        ## 13. Multi-Tenant SaaS Operations

        NovaTech SaaS turns the platform into a controlled multi-organization operating system.

        ### SaaS Core Objects

        - Organization directory
        - Tenant profile
        - Certification level
        - Billing plan
        - Execution readiness
        - Trust profile
        - Marketplace access

        ### Tenant Onboarding

        1. Collect legal and operational identity.
        2. Register the organization in the directory.
        3. Confirm trust domain assignment.
        4. Confirm billing plan and subscription preview.
        5. Confirm execution readiness state.
        6. Grant only the minimum necessary access.

        ### Tenant Isolation Rules

        - One tenant's data must not bleed into another's trust or billing view.
        - Cross-tenant exchange must be explicit.
        - Shared services must preserve auditability.
        - Execution readiness must be tenant-scoped.

        ### SaaS Administrator Questions

        - Is this tenant active?
        - Is the tenant trusted?
        - Is billing ready?
        - Is the requested execution tier allowed?
        - What is the current certification state?
        """
    ),
    block(
        """
        ## 14. Controlled Execution and Safety

        Controlled execution is the most powerful operational surface and must remain bounded.

        ### Execution Tiers

        - Advisory
        - Assisted
        - Controlled
        - Supervised

        ### Safety Gates

        - Tenant readiness
        - Billing readiness
        - Execution tier readiness
        - Operator acknowledgment
        - Safety gate pass

        ### Meaning of Safe Execution

        Safe execution means the platform can recommend or prepare bounded action paths, but it does not bypass review or constitutional authority.

        ### Safety Rules

        - Never treat readiness as automatic permission.
        - Never confuse recommendation with execution.
        - Never let a dashboard become the authority source.
        - Never activate automation without evidence-backed gating.

        ### Controlled Execution Review Questions

        - Is the action necessary?
        - Is the evidence strong enough?
        - Is the tier appropriate?
        - Is the operator aware?
        - Is rollback possible?
        """
    ),
    block(
        """
        ## 15. Outcome Intelligence and Learning

        Outcome intelligence closes the loop from observation to improvement.

        ### Outcome Loop

        Observe
        -> Decide
        -> Recommend
        -> Measure Outcome
        -> Learn
        -> Recalibrate

        ### Outcome Artifacts

        - Outcome registry
        - Outcome scoring
        - Outcome replay
        - Learning records
        - Recalibration notes
        - Outcome history

        ### Learning Questions

        - Did the decision improve the result?
        - Did the recommendation age well?
        - Did the evidence stay consistent?
        - Did a new pattern appear?
        - Should the confidence or stability model change?

        ### Learning Boundary

        Outcome intelligence supports improvement. It does not retroactively rewrite history.
        """
    ),
    block(
        """
        ## 16. Federated Trust Network and Marketplace

        The federated trust network connects tenants through proof and certification exchange. The marketplace exposes trust services as consumable platform capabilities.

        ### Exchange Modes

        - Trust exchange
        - Proof exchange
        - Certification exchange
        - Replay exchange

        ### Trust Marketplace Services

        - Verification services
        - Certification services
        - Replay services
        - Trust scoring services
        - Evidence packaging services

        ### Partner Onboarding Questions

        - What trust domain does the partner belong to?
        - What proof can the partner exchange?
        - What certification level is required?
        - What services can the partner consume?
        - What services can the partner offer?

        ### Marketplace Rule

        Platform services may be consumable across tenants only when the tenant boundary, verification chain, and contract terms are explicit.
        """
    ),
    block(
        """
        ## 17. Product Operations

        ### NovaRide / AfriRide

        - Ride booking, dispatch, driver assignment, live lifecycle, receipts, replay, trust

        ### NovaLogistics

        - Fleet management, route tracking, delivery traceability, proof packages

        ### NovaHealth

        - Scheduling, service verification, patient workflow controls, evidence retention

        ### NovaVirtualMall

        - Merchant onboarding, product listings, order processing, payment tracing, public trust

        ### Operating Rule

        Product teams must operate within the platform's proof and governance rules. Product convenience cannot outrank evidence integrity.
        """
    ),
    block(
        """
        ## 18. Security, Privacy, and Records

        ### Security Rules

        - Use MFA.
        - Use strong passwords.
        - Protect credentials.
        - Do not share secrets.
        - Do not bypass governance controls.
        - Do not alter evidence records.

        ### Records Rules

        - Preserve audit logs.
        - Preserve proof bundles.
        - Preserve replay lineage.
        - Preserve change history.
        - Preserve record retention according to policy.

        ### Privacy Rules

        - Collect only the data required for the role.
        - Restrict export rights.
        - Redact sensitive details when circulating evidence.
        - Treat public verification as a controlled disclosure surface.
        """
    ),
    block(
        """
        ## 19. Incident Management and Escalation

        ### Incident Levels

        | Level | Meaning | Response |
        |---|---|---|
        | 1 | Minor issue | Log and monitor |
        | 2 | Operational disruption | Triage and fix with owner |
        | 3 | Critical service impact | Escalate, preserve evidence, coordinate |
        | 4 | Platform emergency | Command structure, rollback or isolation, executive awareness |

        ### Incident Procedure

        1. Detect.
        2. Verify.
        3. Escalate.
        4. Resolve.
        5. Document.
        6. Review.

        ### Incident Minimums

        - Capture timestamps.
        - Capture affected surface.
        - Capture proof and logs.
        - Capture owner and resolver.
        - Capture the immediate containment action.

        ### Escalation Questions

        - Is truth affected?
        - Is proof affected?
        - Is trust publication affected?
        - Is tenant isolation affected?
        - Is production safety affected?
        """
    ),
    block(
        """
        ## 20. Change, Release, and Deployment Management

        ### Change Control

        - Every material change needs a description.
        - Every material change needs a review path.
        - Every material change needs test evidence.
        - Every material change needs rollback readiness.

        ### Release Checklist

        - Tests pass.
        - Validators pass.
        - Proof artifacts are complete.
        - Trust claims are accurate.
        - Release notes are written.
        - Rollback path is known.
        - Operators know what changed.

        ### Deployment Questions

        - Does the change alter an authority surface?
        - Does it alter the API contract?
        - Does it alter trust publication?
        - Does it alter tenant or billing behavior?
        - Does it require updated manual or runbook content?
        """
    ),
    block(
        """
        ## 21. Onboarding, Training, and Support

        New staff should receive:

        - Role-specific access walkthrough.
        - Governance and proof orientation.
        - Dashboard orientation.
        - Incident reporting walkthrough.
        - Security and records training.
        - Product surface training.
        - Escalation practice.

        ### Support Model

        - First-line support handles known workflows and basic triage.
        - Second-line support handles product or operational edge cases.
        - Trust and proof support handles evidence and verification questions.
        - Security support handles credential or access issues.
        - Finance support handles billing and settlement questions.

        ### Training Rule

        A staff member should not be handed a sensitive surface without understanding the proof and escalation rules that govern it.
        """
    ),
    block(
        """
        ## 22. Operational Cadence

        ### Daily

        - Check health dashboards.
        - Review alerts.
        - Review incidents.
        - Review trust and proof surfaces.
        - Review tenant and billing readiness.

        ### Weekly

        - Review trends.
        - Review unresolved issues.
        - Review access changes.
        - Review backlog and release readiness.
        - Review platform improvement notes.

        ### Monthly

        - Review governance changes.
        - Review policy drift.
        - Review tenant growth.
        - Review billing and revenue signals.
        - Review incident patterns and automation quality.

        ### Quarterly

        - Review manual updates.
        - Review training effectiveness.
        - Review role boundaries.
        - Review trust marketplace readiness.
        - Review long-term risk posture.
        """
    ),
    block(
        """
        ## 23. Appendix Templates and Forms

        This manual includes operational templates for:

        - Access request form
        - Incident report form
        - Change request form
        - Release readiness checklist
        - Trust review checklist
        - Evidence verification checklist
        - Tenant onboarding checklist
        - Partner onboarding checklist
        - Operator handover note
        - Daily operations log

        These forms should always capture:

        - Who
        - What
        - When
        - Where
        - Why
        - Evidence
        - Owner
        - Next action
        """
    ),
    block(
        """
        ## 24. Manual Maintenance Rules

        - Update this manual when a platform surface materially changes.
        - Keep role names and surface names synchronized with code and dashboards.
        - Preserve the authority boundary between explanation and action.
        - Add appendices for major operational packs instead of burying them in prose.
        - Treat this manual as a living internal control document.

        ### Maintenance Checklist

        - Confirm the appendix source list is current.
        - Confirm version and classification are current.
        - Confirm the document links still resolve.
        - Confirm any new platform layer has a manual section.
        - Confirm the change log reflects the last update.
        """
    ),
    block(
        """
        ## 26. Documentation Certification and Compliance Product

        The NovaTech documentation operating system is also a certification and compliance product.

        ### Product Purpose

        It connects the manual system to:

        - Policy Registry
        - Certification Registry
        - Trust Registry
        - Organization OS
        - Tenant Governance
        - Operator Training Records
        - Continuous Assurance Reports
        - Certification Issuance
        - Public Verification Portal

        ### Certification Model

        NovaTech uses an ISO-style certification layer to classify documents and operating packs as:

        - Verified
        - Compliant
        - Certified
        - Revoked

        Every certification must have:

        - source lineage
        - document hash
        - validation result
        - owner responsibility
        - training evidence where relevant
        - continuous assurance evidence where relevant

        ### Compliance Model

        The compliance layer is designed for government and enterprise review. It provides:

        - read-only proof surfaces
        - registry-backed publication
        - operator training acknowledgement
        - assurance history
        - certificate-ready exports

        Documentation does not create legal authority. It creates governed evidence that can support internal compliance, procurement review, public sector pilots, and partner verification.

        ### Policy Registry Connection

        The policy registry governs publication and change discipline for manuals and compliance packs.

        Typical policy questions:

        - Is the document source-backed?
        - Is the document authority boundary explicit?
        - Is the document hash aligned with the certificate?
        - Is the publication role allowed to receive this manual?
        - Is the document ready for compliance use?

        ### Organization OS and Public Verification Connection

        Documentation compliance links the manual system to tenant governance and the public verification portal.

        The connected surfaces include:

        - organization directory
        - tenant governance detail
        - billing preview
        - controlled execution readiness
        - certification issuance
        - public documentation portal
        - public verification portal

        This keeps documentation review tied to the organization, the tenant, and the public verification surface.

        ### Certification Registry Connection

        The certification registry records which manuals and packs have been certified, when they were issued, and what evidence supported the result.

        Certification records should include:

        - document id
        - title
        - owner
        - version
        - source count
        - hash
        - validator version
        - issued at

        ### Trust Registry Connection

        The trust registry turns certification into a public trust surface. It is the bridge between internal proof and external verification.

        It should answer:

        - What is trusted?
        - Who can verify it?
        - What evidence supports the claim?
        - What service or tenant can consume it?
        - What changed since the last assurance cycle?

        ### Operator Training Records

        Staff must acknowledge the manual set they use. Training records prove that the operator has been exposed to the correct role content.

        Training records should capture:

        - manual id
        - manual version
        - role
        - trainee and trainer
        - completion status
        - assessment score
        - evidence count
        - acknowledgement hash

        ### Continuous Assurance Reports

        Continuous assurance ties the documentation layer to live platform review. It tells operators and auditors whether the governing documents still match the platform state.

        Assurance reports should show:

        - document compliance status
        - policy alignment
        - trust posture
        - training coverage
        - open exceptions
        - renewal or review dates

        ### Trust-as-a-Service Monetization

        NovaTech can package documentation compliance as a service:

        - free public verification
        - team verification subscriptions
        - enterprise compliance exports
        - dedicated tenant certification
        - partner onboarding packages
        - annual assurance reporting

        ### AfriCPPT Expansion

        AfriCPPT is the protocol surface for cross-tenant proof and compliance exchange. The documentation product should publish protocol mappings and certificate-ready exports that can be consumed by partners, regulators, and enterprise customers.

        ### Global Marketplace and Partner Onboarding

        The marketplace exposes trust services across tenants, including verification, certification, replay, and assurance services. Partner onboarding should start with one narrow workflow, then expand to certification, training, and ongoing assurance.

        ### Operating Rule

        The documentation operating system is projection-only. It informs policy, certification, trust, and training. It does not mutate runtime truth.
        """
    ),
    block(
        """
        ## 25. Appendix Pack Overview

        The appendices are included to preserve detailed operational guidance already established across the NovaTech repository. They serve as the long-form reference pack for the manual.

        ### Appendix Use Rules

        - The appendices are reference material.
        - The appendices do not replace constitutional truth.
        - The appendices do not replace service-specific runbooks.
        - When a conflict exists, the more specific governed source wins.

        ### Appendix Index

        The appendix index below lists the curated source documents included in this manual package.
        """
    ),
]


APPENDIX_DOCS: list[AppendixDoc] = [
    AppendixDoc(
        title="Appendix A - NovaScript Governance Handbook",
        path=ROOT / "docs/governance/NOVASCRIPT_GOVERNANCE_HANDBOOK.md",
        note="Foundational governance handbook for policy registry, decision evaluation, approval flow, and audit chain.",
    ),
    AppendixDoc(
        title="Appendix B - AfriRide Operability Playbook",
        path=ROOT / "docs/operations/AfriRide_Operability_Playbook.md",
        note="Operational guidance for replay-aware, trust-native mobility execution.",
    ),
    AppendixDoc(
        title="Appendix C - City-Level Pilot Deployment Playbook",
        path=ROOT / "docs/operations/AfriRide_City_Level_Pilot_Deployment_Playbook.md",
        note="City pilot deployment planning, operational controls, and readiness framing.",
    ),
    AppendixDoc(
        title="Appendix D - First 10 Rides Runbook",
        path=ROOT / "docs/operations/AfriRide_First_10_Rides_Runbook.md",
        note="Day-one field runbook for the first controlled mobility rides.",
    ),
    AppendixDoc(
        title="Appendix E - Week 1-4 Launch Execution Plan",
        path=ROOT / "docs/operations/AfriRide_Week_1_4_Launch_Execution_Plan.md",
        note="Launch execution plan for early-stage operational ramp.",
    ),
    AppendixDoc(
        title="Appendix F - Pilot Execution Pack",
        path=ROOT / "docs/operations/AFRITECH_PILOT_EXECUTION_PACK.md",
        note="Pack that translates the architecture into a bounded pilot execution process.",
    ),
    AppendixDoc(
        title="Appendix G - Live Pilot Execution Checklist",
        path=ROOT / "docs/operations/AFRITECH_LIVE_PILOT_EXECUTION_CHECKLIST.md",
        note="Checklist that preserves admissibility, evidence, and execution boundary discipline.",
    ),
    AppendixDoc(
        title="Appendix H - Full-System Verification Runbook",
        path=ROOT / "docs/operations/AFRITECH_FULL_SYSTEM_VERIFICATION_RUNBOOK.md",
        note="Verification pack for platform-wide readiness and evidence capture.",
    ),
    AppendixDoc(
        title="Appendix I - Production Trust Node Runbook",
        path=ROOT / "docs/operations/AFRITECH_PRODUCTION_TRUST_NODE_RUNBOOK.md",
        note="Runbook for trust node operations, verification bundles, and production trust posture.",
    ),
    AppendixDoc(
        title="Appendix J - Operator Decision Protocol",
        path=ROOT / "docs/operations/AFRITECH_OPERATOR_DECISION_PROTOCOL.md",
        note="Operational decision protocol for event review and operator guidance.",
    ),
    AppendixDoc(
        title="Appendix K - Staging Deployment and Partner Demo Runbook",
        path=ROOT / "docs/operations/AFRITECH_STAGING_DEPLOYMENT_AND_PARTNER_DEMO_RUNBOOK.md",
        note="Partner-facing staging runbook and demonstration protocol.",
    ),
    AppendixDoc(
        title="Appendix L - Real-World Activation Playbook",
        path=ROOT / "docs/pilot/AFRIRIDE_REAL_WORLD_ACTIVATION_PLAYBOOK.md",
        note="Controlled activation playbook for real-world deployment readiness.",
    ),
    AppendixDoc(
        title="Appendix M - Phase 1 Setup Runbook",
        path=ROOT / "docs/pilot/AFRIRIDE_PHASE1_SETUP_RUNBOOK.md",
        note="Setup runbook for initial pilot infrastructure and readiness controls.",
    ),
    AppendixDoc(
        title="Appendix N - Postgres Cutover Runbook",
        path=ROOT / "docs/pilot/AFRIRIDE_POSTGRES_CUTOVER_RUNBOOK.md",
        note="Cutover process for persistence and deployment transition.",
    ),
    AppendixDoc(
        title="Appendix O - Multi-Node Production Pilot Prep",
        path=ROOT / "docs/pilot/AFRIRIDE_MULTI_NODE_PRODUCTION_PILOT_PREP.md",
        note="Pre-production preparation for distributed pilot operation.",
    ),
    AppendixDoc(
        title="Appendix P - Melbourne First Real Pilot Launch Plan",
        path=ROOT / "docs/pilot/AFRIRIDE_MELBOURNE_FIRST_REAL_PILOT_LAUNCH_PLAN.md",
        note="City pilot launch planning for the Melbourne deployment path.",
    ),
    AppendixDoc(
        title="Appendix Q - Partner Onboarding Playbook",
        path=ROOT / "docs/partners/AFRIRIDE_PARTNER_ONBOARDING_PLAYBOOK.md",
        note="Partner onboarding process and external collaboration controls.",
    ),
    AppendixDoc(
        title="Appendix R - Partner Architecture Whitepaper",
        path=ROOT / "docs/whitepaper/AFRIRIDE_PARTNER_ARCHITECTURE_WHITEPAPER.md",
        note="System architecture framing for partner-facing trust and proof surfaces.",
    ),
    AppendixDoc(
        title="Appendix S - Operational Civilization Master Plan",
        path=ROOT / "docs/roadmap/AfriTech_Operational_Civilization_Platform_Master_Plan.md",
        note="Long-range evolution path for the operational civilization platform.",
    ),
    AppendixDoc(
        title="Appendix T - Monetization and Ecosystem Expansion Blueprint",
        path=ROOT / "docs/strategy/AFRITECH_MONETIZATION_AND_ECOSYSTEM_EXPANSION_BLUEPRINT.md",
        note="Strategy for commercial expansion, ecosystem growth, and platform monetization.",
    ),
    AppendixDoc(
        title="Appendix U - Enterprise Readiness Review",
        path=ROOT / "docs/strategy/AFRITECH_ENTERPRISE_READINESS_REVIEW.md",
        note="Enterprise readiness framing and operational maturity review.",
    ),
    AppendixDoc(
        title="Appendix V - Nova Ecosystem Naming Strategy",
        path=ROOT / "docs/vision/Nova_Ecosystem_Naming_Strategy.md",
        note="Brand and naming guidance for the NovaTech ecosystem umbrella.",
    ),
    AppendixDoc(
        title="Appendix W - AfriRide GA Elite MVP",
        path=ROOT / "docs/vision/AfriRide_GA_Elite_MVP.md",
        note="Vision and product framing for the AfriRide launch path.",
    ),
    AppendixDoc(
        title="Appendix X - Pricing and Packaging Refinement",
        path=ROOT / "docs/business/AFRIRIDE_PRICING_AND_PACKAGING_REFINEMENT.md",
        note="Commercial packaging and pricing considerations for product operations.",
    ),
    AppendixDoc(
        title="Appendix Y - Planned Financial Surface",
        path=ROOT / "docs/operations/AFRIPAY_PLANNED_FINANCIAL_SURFACE.md",
        note="Finance surface planning and payment governance.",
    ),
    AppendixDoc(
        title="Appendix Z - AfriCPPT Protocol Spec",
        path=ROOT / "docs/standards/AFRICPPT_PROTOCOL_SPEC.md",
        note="Protocol specification for governance, evidence export, and trust portability.",
    ),
    AppendixDoc(
        title="Appendix AA - AfriRide Trust Protocol Spec",
        path=ROOT / "docs/standards/AFRIRIDE_TRUST_PROTOCOL_SPEC.md",
        note="Trust protocol for mobility proofs, public verification, and ecosystem bundles.",
    ),
    AppendixDoc(
        title="Appendix AB - Documentation Certification Program",
        path=ROOT / "docs/certification/NOVATECH_DOCUMENTATION_CERTIFICATION_PROGRAM.md",
        note="Certification model for governed manuals, compliance packs, and audit-ready documentation artifacts.",
    ),
    AppendixDoc(
        title="Appendix AC - Documentation Compliance and Marketplace Strategy",
        path=ROOT / "docs/strategy/NOVATECH_DOCUMENTATION_COMPLIANCE_AND_MARKETPLACE_STRATEGY.md",
        note="Commercial and marketplace strategy for certification, trust services, and partner onboarding.",
    ),
]


EXTRA_APPENDIX_DIRS = [
    ROOT / "docs/governance",
    ROOT / "docs/certification",
    ROOT / "docs/operations",
    ROOT / "docs/pilot",
    ROOT / "docs/proof",
    ROOT / "docs/partners",
    ROOT / "docs/roadmap",
    ROOT / "docs/strategy",
    ROOT / "docs/whitepaper",
    ROOT / "docs/vision",
    ROOT / "docs/business",
    ROOT / "docs/standards",
    ROOT / "docs/adoption",
    ROOT / "docs/mobile",
]


def discover_extra_docs() -> list[AppendixDoc]:
    seen: set[Path] = {item.path.resolve() for item in APPENDIX_DOCS}
    seen.add(OUT.resolve())
    docs: list[AppendixDoc] = []
    for base in EXTRA_APPENDIX_DIRS:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            resolved = path.resolve()
            if resolved in seen:
                continue
            if resolved == OUT.resolve():
                continue
            seen.add(resolved)
            rel = resolved.relative_to(ROOT)
            title = "Appendix " + rel.as_posix().replace("/", " ").replace(".md", "")
            docs.append(
                AppendixDoc(
                    title=title,
                    path=resolved,
                    note="Automatically curated governed reference document from the NovaTech repository.",
                )
            )
    return docs


def source_index(rows: Iterable[AppendixDoc]) -> str:
    lines = [
        "## Appendix Source Index",
        "",
        "| Appendix | Source File | Purpose |",
        "|---|---|---|",
    ]
    for item in rows:
        lines.append(
            f"| {item.title} | `{item.path.relative_to(ROOT)}` | {item.note} |"
        )
    return "\n".join(lines)


def manual_appendix(item: AppendixDoc) -> str:
    text = item.path.read_text(encoding="utf-8").strip()
    return block(
        f"""
        ---

        ## {item.title}

        Source file: `{item.path.relative_to(ROOT)}`

        {item.note}

        {text}
        """
    )


def build_manual() -> str:
    parts: list[str] = []
    parts.extend(CORE_SECTIONS)
    appendix_docs = APPENDIX_DOCS + discover_extra_docs()
    parts.append(source_index(appendix_docs))
    parts.extend(manual_appendix(item) for item in appendix_docs)
    return "\n\n".join(parts).rstrip() + "\n"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    manual = build_manual()
    OUT.write_text(manual, encoding="utf-8")
    word_count = len(manual.split())
    try:
        from afritech.docs.document_system import write_role_documents

        write_role_documents(OUT)
    except Exception as exc:  # pragma: no cover - build-time guard
        print(f"DOCUMENT_SYSTEM_WARNING: {exc}")
    print(f"NOVATECH_MANUAL_WRITTEN: {OUT}")
    print(f"NOVATECH_MANUAL_WORDS: {word_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
