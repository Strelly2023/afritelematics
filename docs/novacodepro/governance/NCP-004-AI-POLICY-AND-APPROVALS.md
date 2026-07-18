# NCP-004 AI Policy and Approvals

Policy flow:

Request
→ classification
→ clarification
→ requirements
→ planning
→ risk review
→ policy review
→ approval request
→ approval decision
→ execution
→ verification
→ evidence

Risk handling:

- LOW: execution within granted permissions
- MODERATE: product/owner approval required
- HIGH: designated approver plus policy approval
- CRITICAL: prohibited or multi-party approval

Approval rules:

- approval state must be open
- the approval must match the plan digest
- approval decisions are recorded with actor, reason, and timestamps
- wrong-role approvals are rejected by the service

Rollback:

- rollback is recorded
- rollback executes in reverse order for reversible work
- irreversible actions are documented in the evidence trail
