# NovaTech Security Operations Standard

NovaTech uses zero trust. Every human, workload, device, node, and integration is
authenticated and authorized for each bounded operation. Controls require least
privilege, short-lived credentials, workload identity, encryption in transit
and at rest, tenant-aware key context, secret-manager storage, network
segmentation, dependency provenance, signed releases, and tamper-evident audit.

Production services MUST define asset owner, data classification, threat model,
abuse cases, security SLOs, vulnerability response, key rotation, backup and
restore tests, incident severity, containment, evidence preservation,
notification obligations, and post-incident review.

Integrity or identity ambiguity fails closed. Break-glass access is time-bound,
multi-party approved, fully recorded, and reviewed. It does not disable evidence
or replay requirements.
