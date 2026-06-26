# NovaTech Platform Operations Standard

Machine authority: `afritech/platform_operations/operations.yaml`

## Policy service

NovaPower is a versioned policy decision point. Application services provide
identity, tenant, role, scope, ownership, action, and risk inputs. NovaPower
returns an allow/deny decision, ordered checks, policy version, policy hash, and
trace identifier. Products do not embed alternative authorization rules.

## Durable workflows

Long-running payment, onboarding, settlement, and federation-import operations
use checkpointed workflow instances. Every transition persists a revision,
state, step index, context, and history entry. Recovery resumes from the last
checkpoint. Failed work enters compensation rather than silently continuing.

## Reliability

Tier-1 services publish availability, p95 latency, error-budget windows, RTO,
RPO, ownership, and fast/slow burn thresholds. An exhausted or rapidly burning
error budget blocks release promotion unless an approved emergency exception is
recorded.

## Progressive delivery

Promotion follows `development -> integration -> staging -> production`.
Production requires approved change, contract validation, security review,
available error budget, verified rollback, observability, and safe data
migration. Canary stages are 1%, 5%, 25%, 50%, and 100%.

Replay mismatch, signature failure, tenant isolation violation, excessive schema
errors, or SLO burn triggers automatic rollback.

Feature flags require an owner, tenant scope, expiry, rollout percentage, and
audit record. Expired flags evaluate false.

## Data lifecycle

Every governed resource declares classification, residency, retention, schema
compatibility, and deletion behavior. Legal hold prevents deletion. Audit data
requires approval after retention expires. Deletion emits a tombstone and
evidence record.
