# NovaAI Governance Standard

NovaAI governs model registration, approved use cases, prompt templates,
inference policy, tool permissions, data classification, evaluations, human
approval, evidence, monitoring, and retirement.

Every governed inference records tenant, use case, model provider and immutable
model/version identifier, prompt-template version, input/output hashes, policy
decision, tool calls, safety checks, reviewer decision when required, and
evidence reference. Raw sensitive prompts are retained only when policy permits.

AI output is advisory by default. It may cause state mutation only by producing
a schema-valid command that passes normal identity, policy, idempotency,
execution, evidence, and replay controls. High-impact use cases require bias,
privacy, security, robustness, human-oversight, and rollback evaluations.
Models and prompts have explicit lifecycle, owners, approval, monitoring, and
decommissioning criteria.
