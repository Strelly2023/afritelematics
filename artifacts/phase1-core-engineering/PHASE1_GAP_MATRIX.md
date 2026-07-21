# Phase 1 Core Engineering Gap Matrix

Baseline commit: `a41cbc84b3818cb41693f5f9f8888de2b5de1137`

This matrix tracks the remaining implementable gaps across NovaID, NovaRide, and NovaPay.

## NovaID

| Requirement ID | Capability | Baseline status | Final status | Missing implementation | Validation command | Evidence path | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NID-PERSIST-001 | PostgreSQL repositories | Partially implemented | In Progress | Repository coverage is still split between raw connection use and adapter-backed methods. | `python3 -m pytest -q afritech/tests/novaid/test_novaid_ecosystem.py afritech/tests/api/test_novaid_audit_replay_api.py` | `artifacts/phase1-core-engineering/novaid/` |  |
| NID-SESSION-001 | Transactional sessions | Implemented | In Progress | Multi-process revocation and Redis restart evidence still need broader certification. | `python3 -m pytest -q afritech/tests/novaid/test_novaid_ecosystem.py` | `artifacts/phase1-core-engineering/novaid/` |  |
| NID-RECOVERY-001 | Account and credential recovery | Implemented | In Progress | Negative-path and multi-process recovery certification remain incomplete. | `python3 -m pytest -q afritech/tests/novaid/test_novaid_ecosystem.py` | `artifacts/phase1-core-engineering/novaid/` |  |
| NID-AUDIT-001 | Transactional audit outbox | Implemented | In Progress | Publication, dead-letter, and replay evidence still need integration validation. | `python3 -m pytest -q afritech/tests/novaid/test_novaid_ecosystem.py` | `artifacts/phase1-core-engineering/novaid/` |  |
| NID-WEBAUTHN-001 | Standards-based WebAuthn | Implemented | In Progress | PostgreSQL-backed repository certification and negative origin/RP coverage remain incomplete. | `python3 -m pytest -q afritech/tests/novaid/test_novaid_ecosystem.py` | `artifacts/phase1-core-engineering/novaid/` |  |

## NovaRide

| Requirement ID | Capability | Baseline status | Final status | Missing implementation | Validation command | Evidence path | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NRD-PY311-001 | Python 3.11+ execution | Partially implemented | In Progress | Some scripts and build paths remain ambiguous about interpreter selection. | `python3 -m pytest -q afritech/tests/api/test_novaride_runtime_api.py` | `artifacts/phase1-core-engineering/novaride/` |  |
| NRD-RUNTIME-001 | Runtime, API, browser, mobile suites | Partially implemented | In Progress | Full browser/mobile/runtime certification remains incomplete. | `python3 -m pytest -q afritech/tests/api/test_novaride_phase1_api.py` | `artifacts/phase1-core-engineering/novaride/` | External runtime services may be required. |
| NRD-INFRA-001 | PostgreSQL, Redis, Kafka, multi-process certification | Partially implemented | In Progress | Operational evidence for Redis/Kafka/multi-process certification is incomplete. | `python3 -m pytest -q afritech/tests/governance/test_novaride_phase0_postgres_deployment.py` | `artifacts/phase1-core-engineering/novaride/` | Real Redis/Kafka infrastructure not yet validated. |
| NRD-MOBILE-001 | Mobile dependency closure | Partially implemented | In Progress | Dependency findings still need runtime verification and closure evidence. | `python3 -m pytest -q afritech/tests/api/test_afriride_next_gen_mobile_api.py` | `artifacts/phase1-core-engineering/novaride/` | Physical-device validation unavailable. |

## NovaPay

| Requirement ID | Capability | Baseline status | Final status | Missing implementation | Validation command | Evidence path | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NPY-PG-001 | Normalized PostgreSQL monetary persistence | Partially implemented | In Progress | Current repository remains record-oriented rather than normalized financial persistence. | `python3 -m pytest -q afritech/tests/novapay/test_runtime_backend.py afritech/tests/novapay/test_ecosystem.py` | `artifacts/phase1-core-engineering/novapay/` |  |
| NPY-LEDGER-001 | Transactional double-entry ledger | Missing | In Progress | Ledger is not yet normalized with invariant-enforcing persistence. | `python3 -m pytest -q afritech/tests/core_platform/test_novapay_transfer_flow.py` | `artifacts/phase1-core-engineering/novapay/` |  |
| NPY-OUTBOX-001 | Transactional financial outbox | Missing | In Progress | No durable financial outbox exists yet. | `python3 -m pytest -q afritech/tests/novapay/test_ecosystem.py` | `artifacts/phase1-core-engineering/novapay/` |  |
| NPY-STATE-001 | Settlement/reversal/refund/chargeback/reconciliation state machines | Partially implemented | In Progress | State transitions need normalized persistence and stronger invariant coverage. | `python3 -m pytest -q afritech/tests/novapay/test_ecosystem.py afritech/tests/api/test_novapay_runtime_api.py` | `artifacts/phase1-core-engineering/novapay/` |  |
| NPY-RUNTIME-001 | Deterministic test shutdown | Partially implemented | In Progress | No dedicated leak detection / repeat-execution certification yet. | `python3 -m pytest -q afritech/tests/novapay` | `artifacts/phase1-core-engineering/novapay/` |  |
