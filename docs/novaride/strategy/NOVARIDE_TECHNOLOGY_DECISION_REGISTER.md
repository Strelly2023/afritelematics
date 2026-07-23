# NovaRide technology decision register

`APPROVED_EXISTING` means the repository has an established architecture boundary; it does not prove a live provider contract. Provider selections remain `PENDING` until security, compliance, commercial and exit reviews are approved.

| Capability | Direction/options | State | Security/compliance and portability | Owner / next gate |
|---|---|---|---|---|
| Backend | FastAPI domain services | APPROVED_EXISTING | Server authority; OpenAPI and compatibility required | Platform / production certification |
| Operational database | PostgreSQL/PostGIS | APPROVED_EXISTING | RLS, encryption, backup/restore; portable SQL | Data / infrastructure proof |
| Coordination | Redis | APPROVED_EXISTING | No durable sole authority; authenticated TLS | Platform / interruption tests |
| Events | Kafka plus transactional outbox | APPROVED_EXISTING | Schema governance, replay, DLQ; protocol portability | Platform / multi-process proof |
| Mobile | React Native/Expo with native projects | APPROVED_EXISTING | Secure storage and release signing | Mobile / physical devices |
| Web | React/TypeScript/Vite | APPROVED_EXISTING | CSP, dependency and browser gates | Frontend / browser certification |
| Identity | NovaID integration | APPROVED_EXISTING_BOUNDARY | MFA/passkeys, tenant/region, revocation | Identity / live integration |
| Payments | NovaPay/provider abstraction | APPROVED_EXISTING_BOUNDARY | PCI scope, idempotency and reconciliation | Payments / contracts and live evidence |
| Mapping | Provider adapter; Mapbox/Google candidates | PENDING | Location privacy, regional terms, cache/exit policy | Mobile/platform / RFP |
| Messaging | Provider adapter | PENDING | Consent, delivery evidence, regional data | Platform / RFP |
| Fraud | Internal policy plus qualified provider option | PENDING | Explainability, appeals, data minimisation | Trust / risk review |
| Observability | OpenTelemetry with managed/self-hosted backend | APPROVED_DIRECTION | Redaction, retention and tenant controls | SRE / platform selection |
| Cloud | Container/Kubernetes/GitOps-compatible | PENDING_PROVIDER | Multi-zone/region, digest pinning, exit plan | Platform / commercial approval |
| Analytics | Governed warehouse/lakehouse and semantic layer | PENDING_IMPLEMENTATION | RLS, lineage, regional retention, open formats | Data / architecture decision |
| ML | Registry/feature/evaluation adapters | PENDING_IMPLEMENTATION | Fairness, drift, rollback, non-authority | AI governance / approval |
| Support | Governed support capability and optional SaaS adapter | PENDING | Data masking, privileged approval, export/exit | Support/security / RFP |
| Insurance | Regional provider adapter | PENDING_EXTERNAL | Coverage, claims, regulated data and exit | Legal/partnerships / contract |
| Roadside | Regional provider adapter | PENDING_EXTERNAL | Location sharing, SLA and data minimisation | Partnerships / contract |

Every provider decision must record options, cost model, security assessment, data residency, subprocessors, SLA, lock-in risk, export/deletion, failure mode, fallback, contract owner and authenticated approval.
