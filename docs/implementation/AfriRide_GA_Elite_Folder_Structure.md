# AfriRide GA Elite Folder Structure

STATUS: FOLDER STRUCTURE PLAN
CLASSIFICATION: ISOLATED PRODUCT ARCHITECTURE SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE

## Claim Discipline Statement

This folder structure describes a target AfriRide product organization. It does not define proof truth, does not claim that every listed module is currently implemented, and does not claim global deployment readiness.

Folder structure planning must preserve or isolate all claims.

## Governing Boundary

```text
AfriTech (core truth) -> PRESERVE
AfriRide (product system) -> ISOLATE
```

AfriRide product modules may coordinate product behavior, but they may not redefine constitutional truth, mutate invariants, bypass enforcement, or claim authority over admissibility.

## Root Structure

```text
afriride/
├── apps/                        # Django modular applications (product layer)
├── core/                        # Shared configuration (isolated from AfriTech core)
├── api/                         # External API layer
├── interfaces/                  # API contracts, schemas, DTOs
├── mobile/                      # Mobile app (React Native / Flutter)
├── web/                         # Web dashboard / admin UI
├── integrations/                # External systems (maps, payments, SMS)
├── orchestration/               # Product orchestration (isolated logic)
├── simulation/                  # AfriRide operational simulations
├── tests/                       # Product tests
├── docs/                        # Product documentation (non-authoritative)
├── config/                      # Environment configs
├── docker/                      # Deployment setup
└── manage.py
```

This root structure is a target architecture, not a claim that the current repository has already been reshaped into this exact layout.

## Apps - Product Domain

```text
apps/
├── ride_request/                # Rider trip creation
├── ride_matching/               # Driver assignment (deterministic)
├── ride_lifecycle/              # State machine
├── pricing/                     # Fare calculation (deterministic v1)
├── driver/                      # Driver management
├── rider/                       # Rider profiles
├── trip_tracking/               # Real-time trip updates
├── safety/                      # PIN, ETA sharing, logs
├── payments/                    # Payment handling (future-safe)
├── notifications/               # SMS, push notifications
├── support/                     # Lost items, help system
└── categories/                  # Ride types (S, L, Go, Animal)
```

These apps belong to the isolated product domain. They may implement rider, driver, trip, pricing, and support workflows, but they may not become sources of constitutional truth.

## Core Product Runtime - Not AfriTech Core

```text
core/
├── settings/
│   ├── base.py
│   ├── dev.py
│   └── prod.py
├── middleware/
│   ├── request_logging.py
│   └── auth_middleware.py
├── services/
│   ├── orchestrator.py         # coordinates flows; no truth authority
│   └── validation_bridge.py    # calls AfriTech validators
├── constants/
├── utils/
└── bootstrap/
```

The AfriRide `core/` directory is a product-runtime configuration surface. It is not the AfriTech constitutional core.

## API Layer

```text
api/
├── v1/
│   ├── ride/
│   ├── driver/
│   ├── pricing/
│   └── safety/
├── gateways/
├── serializers/
├── permissions/
└── rate_limiting/
```

The API layer may expose product behavior, validate requests, and route operations. It may not override validator output or move decision authority out of admitted product execution paths.

## Interfaces

```text
interfaces/
├── dto/
├── schemas/
├── contracts/
│   ├── ride_contract.yaml
│   └── pricing_contract.yaml
└── mapping/
```

Interfaces define product contracts and mappings. They are not proof artifacts unless separately validator-backed.

## Orchestration Layer

```text
orchestration/
├── ride_flow/
│   ├── create_ride_flow.py
│   ├── assign_driver_flow.py
│   └── complete_trip_flow.py
├── policies/
│   ├── pricing_policy.py
│   └── matching_policy.py
└── guards/
    └── flow_integrity_guard.py
```

Rule:

```text
This layer coordinates behavior,
but cannot define truth or admissibility.
```

Orchestration may sequence product flows. It may not redefine invariants, proof meaning, replay authority, or enforcement integrity.

## Integrations

```text
integrations/
├── maps/
├── payments/
├── sms/
├── notifications/
└── gps/
```

External integrations are operational surfaces. They must remain replaceable, bounded, and non-authoritative.

## Mobile App

```text
mobile/
├── screens/
├── components/
├── services/
├── hooks/
├── state/
└── assets/
```

Mobile state may display confirmed product state. It may not infer constitutional truth or treat notification events as authoritative state.

## Web Dashboard

```text
web/
├── admin/
├── dashboards/
├── analytics/
└── monitoring/
```

Dashboard surfaces support operation, monitoring, and DFM. They are observational and non-authoritative.

## Simulation

```text
simulation/
├── continuity/
├── mobility_scenarios/
└── load_testing/
```

Simulation validates ride execution, edge cases, and operational consistency. Simulation may produce evidence, but it may not bypass replay or replace constitutional validation.

## Tests

```text
tests/
├── unit/
├── integration/
├── e2e/
└── performance/
```

Product tests do not replace AfriTech constitutional validation.

## Documentation

```text
docs/
├── requirements/
├── architecture/
├── api/
├── user_guides/
└── product/
```

Product documentation is an isolated, non-authoritative explanation layer.

## Config

```text
config/
├── env/
├── secrets/
└── feature_flags.yaml
```

Feature flags may control product exposure. They may not disable validators, bypass enforcement, or redefine admissibility.

## Docker and Deployment

```text
docker/
├── Dockerfile
├── docker-compose.yml
└── k8s/
```

Deployment configuration supports reproducibility. It may not introduce a path around validation or constitutional admission.

## AfriTech Integration Boundary

AfriRide connects to AfriTech only through:

```text
core/services/validation_bridge.py
```

Allowed:

- calling validators
- reading proof outputs
- verifying replay traces

Not allowed:

- modifying invariants
- bypassing enforcement
- redefining proof
- importing protected internal modules

The validation bridge is a verification boundary. It is not an authority transfer mechanism.

## Data Flow

```text
Mobile App
   ↓
API Layer
   ↓
Orchestration
   ↓
Apps (ride, pricing, matching)
   ↓
Validation Bridge
   ↓
AfriTech Validators
   ↓
Replay Logs + Proof Surface
```

Product flow may consume validation outputs. It may not reinterpret proof truth.

## Drift Detection - Folder Level

Reject if product structure introduces:

- product importing AfriTech internal core
- orchestration redefining invariants
- pricing introducing randomness as authority
- simulation bypassing replay
- API overriding validator outputs
- feature flags disabling enforcement
- mobile state becoming truth authority

## Final Compression

```text
AfriRide is a modular product system
built entirely in the isolated layer,
consuming AfriTech truth
without ever redefining it.
```

## Boundary Clause

This folder structure is an isolated product architecture surface. It does not modify `afritech.demo.proof`, `FIVE_INVARIANT_CONTRACT.yaml`, or the enforcement chain. It does not expand proof scope beyond the bounded AfriRide domain. It does not claim global deployment readiness or assert that every listed folder currently exists in the repository.
