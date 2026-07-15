# NovaRide Verified Replay Evidence

Replay is considered verified only when source event hashes are valid, schemas are compatible, event order is deterministic, aggregate versions are continuous, a shadow projection rebuild completes, canonical state hashes match, and external side effects are blocked.

Current repository evidence:
- deterministic replay verifier implemented
- event hash tamper quarantine implemented
- replay side-effect firewall implemented
- operator replay plan and promotion controls implemented

Live certification pending:
- production event store replay
- production projection shadow rebuild
- NovaTrust-signed replay evidence
- approved promotion in a live maintenance window
