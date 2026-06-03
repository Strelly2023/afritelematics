# AfriRide Realtime Dispatch + GPS Evidence Layer

This package is a GA Elite scaffold for replay-safe real-time dispatch, GPS
evidence capture, route reconstruction, and operator route replay visibility.

## Authority Boundary

```text
WebSocket notifies.
GPS evidence records.
Fare calculation prices verified movement.
Region policy selects currency, tax, and provider.
Payment captures after replay.
Earnings ledger records.
Business accounts allocate access.
Subscriptions gate platform access.
Fleet assignments organize vehicles and drivers.
Prediction informs.
Risk informs.
Policy bounds optimization.
Trust score signals.
Regulators receive reports.
Public transport enriches journeys.
Pilot operations capture reality.
Readiness certification evaluates operations.
Regional deployment activates certified markets.
Network operations monitor live regions.
MOS coordinates multi-modal journeys.
Replay verifies.
EventLog records.
Backend decides.
Mobile displays.
```

The WebSocket layer is notification-only. It may publish backend-confirmed ride
events to rider, driver, and operator surfaces, but it must not define canonical
ride state, validate replay, mutate certification, or become an evidence source.

The GPS layer records observed location facts in an immutable hash chain. It may
support route replay and visual proof, but it must not complete rides, certify
routes, or override EventLog and ReplayEngine authority.

The payments layer calculates fare from replay-derived distance and duration,
authorizes/captures through a mock gateway, and ledgers driver earnings only
after replay verifies completed ride state.

The enterprise payments layer applies active country policy for currency, tax,
and provider routing. Provider implementations are mocked; this is not real
payment-provider or tax-compliance certification.

The business account layer manages organizations, fleets, subscriptions, and
billing accounts. Subscriptions may grant access, but they do not authorize ride
truth. Business ride charges remain gated by replay-verified completion.

The intelligence layer may forecast demand, suggest surge, recommend driver
positioning, and rank dispatch candidates. It is non-authoritative. It cannot
invent ride truth, bypass replay, charge users, mutate evidence, or override
policy.

The trust and fraud layer may detect anomalies, adjust bounded trust signals,
and recommend manual review or limited access. It may not perform hidden,
irreversible, or AI-only punishment. Replay-backed evidence remains required.

The civic infrastructure layer may generate replay-backed regulatory reports,
prepare government submissions, and enrich journeys with public transport data.
Government partners receive approved reports; public transport providers enrich
journeys. Neither becomes AfriRide truth authority.

The pilot operations layer registers controlled pilots, participants, evidence,
metrics, reports, success gates, and certificates. It does not manufacture
success. Pilot certification requires collected ride evidence and gate passage.

The production readiness certification layer evaluates pilot evidence across
replay, payments, route evidence, fraud, uptime, finance, and compliance. It may
classify readiness only from measured operational evidence.

The regional deployment and network operations layer activates regions only
after production readiness certification. It monitors regional health, incidents,
failover, tenancy, and expansion candidates without redefining ride truth.

The Mobility Operating System layer coordinates multi-modal journeys, mobility
graph entities, policies, optimization, and command-center projections. It
coordinates segments; it does not certify segment truth. Each segment remains
bound to its own evidence and replay proof.

## Runtime Model

```text
Ride request
  -> backend dispatch service
  -> EventLog append
  -> WebSocket notification
  -> mobile/operator display
  -> replay verification from EventLog

Driver GPS update
  -> GPS admission API
  -> immutable LocationEvidence append
  -> GPS hash-chain verification
  -> RouteReplayEngine reconstruction
  -> operator visual proof projection

Trip completion
  -> ReplayEngine verified completion
  -> replay-derived fare calculation
  -> mock payment authorization
  -> mock payment capture
  -> driver earning ledger append
  -> customer and driver receipt projection

Regional trip payment
  -> ReplayEngine verified completion
  -> replay-derived subtotal
  -> active RegionPolicy
  -> tax calculation
  -> provider router
  -> mocked provider capture
  -> EventLog financial record

Business/fleet access
  -> Organization or Fleet account
  -> Subscription access check
  -> Ride execution through canonical backend
  -> ReplayEngine verified completion
  -> BusinessRideCharge ledger append
  -> organization or fleet receipt/report projection

Intelligence proposal
  -> ServiceZone demand snapshot
  -> bounded prediction
  -> surge or dispatch recommendation
  -> policy-bound backend decision
  -> EventLog recommendation record
  -> replay remains proof authority

Fraud review
  -> Route replay evidence
  -> anomaly checks
  -> bounded trust event
  -> enforcement recommendation
  -> manual or policy review
  -> no irreversible AI-only action

Civic reporting
  -> Replay-verified ride set
  -> RegulatoryReport hash
  -> compliance export or certificate
  -> government submission prepared
  -> no external system redefines internal truth

Public transport enrichment
  -> external/public transport stop data
  -> normalized journey enrichment projection
  -> rider/operator display
  -> no proof authority transfer

Controlled pilot
  -> PilotProgram registration
  -> participants and roles
  -> real rides
  -> replay-backed PilotEvidence
  -> PilotMetrics refresh
  -> success gate evaluation
  -> PilotCertificate only if gates pass

Production readiness
  -> Pilot evidence and metrics
  -> replay integrity check
  -> payment and financial integrity checks
  -> route and fraud checks
  -> uptime and compliance checks
  -> ProductionReadinessCertificate only if gates pass

Regional operations
  -> ProductionReadinessCertificate
  -> region launch gate
  -> Region activation
  -> NOC health snapshots
  -> incident and failover management
  -> network dashboard projection

Mobility Operating System
  -> Mobility graph nodes and edges
  -> Journey request
  -> policy constraints
  -> journey option ranking
  -> Journey and JourneySegment projections
  -> segment evidence and replay remain authoritative
```

## Integration Notes

- Add `channels`, `rest_framework`, `dispatch`, `realtime`, `gps`,
  `route_replay`, `pricing`, `payments`, `earnings`, and `receipts` to the
  Django project settings.
- Set `ASGI_APPLICATION = "config.asgi.application"`.
- Use the in-memory channel layer only for local testing.
- Use `channels_redis.core.RedisChannelLayer` for shared or production-like
  environments.
- Keep EventLog and ReplayEngine as the only authoritative proof surfaces.
- Keep route replay receipts classified as evidence projections until certified
  by the replay/evidence pipeline.
- Keep the mock payment gateway classified as controlled-test infrastructure
  until replaced by a real provider and certified under field execution.
- Keep country tax policy and exchange rates as declared policy inputs. They
  require legal/provider validation before any production claim.
- Keep subscription status classified as access control. It cannot certify rides,
  alter replay, or authorize billing without replay-verified completion.
- Keep intelligence outputs classified as recommendations. They cannot mutate
  canonical evidence or become payment/dispatch truth by themselves.
- Keep fraud and trust outputs classified as bounded risk signals. They cannot
  deny payment, suspend users irreversibly, or mutate evidence without policy
  guard and replay-backed reason.
- Keep government and public transport integrations classified as external
  interoperability. They cannot redefine EventLog, GPS evidence, or ReplayEngine
  truth.
- Keep pilot status classified as evidence-dependent. Architecture and scaffold
  readiness cannot create pilot certification without real ride evidence.
- Keep production readiness classified as operational evidence certification.
  It cannot be produced by architecture, scaffold completeness, or synthetic
  checks alone.
- Keep regional deployment classified as certification-gated. A region cannot be
  activated from demand, investor pressure, or configuration alone.
- Keep MOS classified as coordination, not proof. A journey plan cannot certify
  ride, delivery, public transport, emergency, or fleet segment truth.

## Classification

```text
Layer: realtime_dispatch
Status: scaffold_ready
Authority: notification_only
Legitimacy_effect: 0
Replay_safe: true
Production_claim: false
```

```text
Layer: mobility_operating_system
Status: scaffold_ready
Authority: coordination_projection
Allowed: journey_planning mobility_graph policy_constraints command_center_projection
Forbidden: segment_truth_certification replay_bypass evidence_mutation cross_system_authority_takeover
Legitimacy_effect: 0_until_segment_evidence_replay
Production_claim: false
```

```text
Layer: regional_network_operations
Status: scaffold_ready
Authority: certification_gated_operations
Required: production_readiness_certificate replay_integrity payment_integrity fraud_controls compliance_ready
Forbidden: uncertified_region_launch failover_without_evidence_loss_protection external_truth_override
Legitimacy_effect: 0_until_certified_region_launch
Production_claim: false
```

```text
Layer: production_readiness_certification
Status: scaffold_ready
Authority: operational_evidence_gate
Required: pilot_verified replay_integrity payment_integrity route_integrity fraud_integrity uptime financial_integrity compliance_integrity
Forbidden: architecture_only_certification synthetic_readiness production_claim_without_pilot
Legitimacy_effect: 0_until_certified_field_evidence
Production_claim: false
```

```text
Layer: controlled_pilot_operations
Status: scaffold_ready
Authority: evidence_gate_only
Required: real_rides replay_verified_evidence payment_metrics fraud_review satisfaction_metrics
Forbidden: synthetic_certification premature_success_claim manual_evidence_repair
Legitimacy_effect: 0_until_field_execution
Production_claim: false
```

```text
Layer: civic_infrastructure
Status: scaffold_ready
Authority: external_reporting_only
Allowed: regulatory_reports compliance_exports government_submission_preparation public_transport_enrichment
Forbidden: external_truth_override internal_evidence_mutation uncontrolled_transmission
Legitimacy_effect: 0
Production_claim: false
```

```text
Layer: trust_fraud_enforcement
Status: scaffold_ready
Authority: bounded_risk_signal
Allowed: anomaly_detection trust_delta manual_review_recommendation
Forbidden: ai_only_punishment hidden_enforcement evidence_mutation
Legitimacy_effect: 0
Production_claim: false
```

```text
Layer: intelligence
Status: scaffold_ready
Authority: recommendation_only
Allowed: demand_forecast surge_proposal driver_positioning dispatch_ranking
Forbidden: ride_truth replay_bypass payment_capture evidence_mutation
Legitimacy_effect: 0
Production_claim: false
```

```text
Layer: business_fleet_subscriptions
Status: scaffold_ready
Authority: access_control_only
Billing_authority: replay_engine_eventlog
Restriction: subscription_does_not_authorize_ride_truth
Legitimacy_effect: 0
Production_claim: false
```

```text
Layer: enterprise_payments
Status: scaffold_ready
Authority: replay_engine_eventlog_region_policy
Gateway: mocked_providers
Restriction: no_charge_without_replay_verified_completion
Compliance_claim: false
Production_claim: false
```

```text
Layer: replay_backed_payments
Status: scaffold_ready
Authority: replay_engine_eventlog
Gateway: mock
Restriction: no_capture_without_replay_verified_completion
Legitimacy_effect: 0
Production_claim: false
```

```text
Layer: gps_route_replay
Status: scaffold_ready
Authority: evidence_projection
Legitimacy_effect: 0
Replay_safe: true
Production_claim: false
```
