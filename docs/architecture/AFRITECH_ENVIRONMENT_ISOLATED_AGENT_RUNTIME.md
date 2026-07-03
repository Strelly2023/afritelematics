# Environment-Isolated Agent Runtime

## Purpose

AfriTech agents may use probabilistic models and therefore produce different
recommendations for equivalent inputs. They do not receive execution
authority. The runtime captures each recommendation as an immutable proposal,
applies deterministic admission policy, and persists the result before any
downstream executor can consume it.

## Boundary

```text
Non-deterministic agent
        |
        v
Immutable proposal artifact
        |
        v
Deterministic environment policy
        |
        +-- rejected
        +-- review_required
        +-- admitted
                |
                v
        downstream executor
```

The executor must consume only decisions where `executable` is `true`. Agent
output alone is never an authorization.

## Environment separation

| Property | Production | Staging |
| --- | --- | --- |
| Runtime environment | `production` | `staging` |
| API host port | `127.0.0.1:8000` | `127.0.0.1:18000` |
| State file | `agents/production.sqlite3` | `agents/staging.sqlite3` |
| Default confidence | `0.85` | `0.70` |
| Low-risk admission | Explicit approval required | Automatic |
| High/critical risk | Rejected | Rejected |

Cross-environment proposals and state writes raise
`AgentRuntimeViolation`. Production and staging state files live in different
Compose volumes.

## Persistence

`AgentDecisionStore` maintains an append-only SQLite ledger. Each record
contains:

- the canonical proposal and proposal hash;
- the deterministic admission decision and decision hash;
- the previous record hash;
- the environment identity.

The first decision points to `GENESIS`; every subsequent record points to the
preceding record hash. Reopening the runtime preserves the ledger and chain.

Repeated writes are idempotent only when both the canonical proposal hash and
the decision hash match a stored record. Reusing a proposal identifier with
different proposal content raises `proposal_id_conflict`.

A proposal may have multiple append-only decisions. Workflow rules are owned
by `DecisionTransitionPolicy`, not by SQLite persistence. The default policy
permits:

```text
review_required -> admitted
review_required -> rejected
```

Custom workflow states must be explicitly registered in
`allowed_states`. States appearing in `transitions` that are not present in
`allowed_states` raise `transition_state_not_registered:<state>`.

The admitted decision must contain an approver identity and external approval
reference. Terminal decisions cannot be replaced. Deployments may inject an
expanded transition map for intermediate states such as
`investigation_required`; unsupported transitions raise
`invalid_decision_transition`.

Every transition must remain in one environment. A staging-to-production
transition raises `cross_environment_decision_transition`. Existing
single-decision ledgers are migrated in an immediate transaction, verified,
and rolled back on failure without deleting their records.

Each inference invocation receives a UUID-based proposal identifier when the
agent does not provide one. This intentionally records repeated model calls as
separate governance events. An agent must provide a stable `proposal_id` when
the caller is retrying the same proposal and requires idempotency. The
`generate_proposal_id(payload, deterministic=True)` helper provides a
content-addressed identifier for that case.

The reserved decision vocabulary is:

- `review_required`
- `admitted`
- `rejected`

`RESERVED_DECISION_STATES` and `DEFAULT_ALLOWED_DECISION_STATES` are kept as
separate constants so future policy expansions can change the default allowed
set without redefining the reserved vocabulary.

Deployments that need additional states must register them explicitly in
`allowed_states` and describe the transition edges in the workflow policy.

## Production approval

Production policy never auto-admits a proposal. An admitted proposal requires:

- an allowed action;
- low or medium declared risk;
- confidence at or above the production threshold;
- a non-empty approver identity;
- a non-empty external approval reference.

Approval does not make the AI agent authoritative. It satisfies one input to
the deterministic admission policy.

## Configuration

The runtime requires explicit configuration:

```text
AFRITECH_RUNTIME_ENVIRONMENT
AFRITECH_AGENT_STATE_PATH
AFRITECH_AGENT_MINIMUM_CONFIDENCE
```

Missing environment or state configuration fails closed.

Migration failures include a reason suffix such as:

- `legacy_decision_migration_failed:missing_hash`
- `legacy_decision_migration_failed:decision_json_invalid`
- `legacy_decision_migration_failed:count_or_hash_mismatch`
