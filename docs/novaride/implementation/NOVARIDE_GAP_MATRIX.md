# NovaRide 11-phase gap matrix

Baseline commit: `94ba38da884ca9676cb500a7d32cac14ecefa055`

Status meanings: `IMPLEMENTED` requires current implementation and executable evidence; `PARTIAL` has useful implementation with material gaps; `EXTERNAL_BLOCKED` requires evidence or authority unavailable in the repository; `GA_BLOCKED` prevents General Availability.

| Phase | Current state | Status | Material gaps | Promotion impact |
|---|---|---|---|---|
| 1. Strategy, research, planning | Strategy, MVP scope, segments, pilot criteria | PARTIAL | Primary/local research, costed roadmap, resource plan, RACI, decision and change-control registers | Blocks evidence-based market launch |
| 2. Stack and business case | Production-oriented stack exists | PARTIAL | Business case, configurable unit economics, build/buy and provider decision register | Blocks commercial approval |
| 3. Requirements and traceability | 13 controlled-pilot requirements | PARTIAL / GA_BLOCKED | Enterprise catalogue, acceptance criteria, ownership, security/evidence/approval links, current-commit binding | Blocks GA scope certification |
| 4. UX and accessibility | Design system, screen and flow inventories | PARTIAL | Real usability sessions, manual accessibility, deterministic visual regression, production mock guards, backend wiring | Blocks supported-surface certification |
| 5. Enterprise architecture | Strong runtime, event and persistence foundation | PARTIAL | Complete diagrams/catalogues, threat/data/retention/capacity models, current production-integration evidence | Blocks architecture approval |
| 6. Web, mobile and APIs | Rider, driver, fleet, operator and several web portals | PARTIAL | Support/inspector and partner experiences, portal completeness, iOS/device certification, API quality proof | Blocks full product scope |
| 7. AI dispatch | Deterministic dispatch and limited forecasting | PARTIAL | Model/data registry, fairness, calibration, explainability, drift, shadow/canary, rollback and approval evidence | Advanced AI must remain disabled or advisory |
| 8. Mobility operations | Core MVP and several enterprise modules | PARTIAL | Scheduled/multi-stop, mature no-show/refund/dispute, airport/event, telematics and provider-certified payments | Limits controlled-pilot scope |
| 9. Portals | Operations/admin/corporate/fraud surfaces | PARTIAL | Rider/driver self-service and partner/government/developer portals with real integrations and consistent controls | Blocks enterprise ecosystem claim |
| 10. Analytics | Operational projections, SLOs and demand forecast | PARTIAL / GA_BLOCKED | Governed warehouse/lakehouse, semantic metrics, catalogue, lineage, BI, digital twin and grounded copilot | Blocks trusted analytics claim |
| 11. Readiness and GA | Historical release/pilot/PRR evidence exists | EXTERNAL_BLOCKED / GA_BLOCKED | Immutable clean RC, current evidence, live providers, real devices/users, independent security, production infrastructure and approvals | GA prohibited |

## Immediate engineering priorities

1. Replace the 13-item requirements baseline with a complete, validated enterprise catalogue.
2. Add current-commit evidence classification and stale-evidence rejection.
3. Add production mock/fallback guards and connect claimed portals to governed APIs.
4. Implement the semantic metrics and governed analytics foundation.
5. Extend deterministic dispatch with an auditable, policy-subordinate ML lifecycle.
6. Complete support, inspector, refund/dispute, and partner workflows.
7. Run infrastructure-backed and device/provider certification only in approved environments.

## External gates

The following cannot be completed by repository changes alone: market interviews, regulated/provider approvals, real payment certification, independent penetration testing, physical-device certification, real-user pilots, legal approval, PRR signatures, and executive GA approval.
