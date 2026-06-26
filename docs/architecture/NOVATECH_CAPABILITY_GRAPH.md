# NovaTech Capability Graph

Generated authority: `afritech/platform_contracts/platform.yaml`

```mermaid
graph BT
  identity["L1 NovaID"] --> infrastructure["L0 Infrastructure"]
  policy["L2 NovaPower"] --> identity
  execution["L3 NovaScript"] --> identity
  execution --> policy
  payments["L3 NovaPay"] --> identity
  payments --> policy
  payments --> execution
  ai["L3 NovaAI"] --> identity
  ai --> policy
  ai --> execution
  evidence["L4 NovaTrust"] --> identity
  evidence --> policy
  evidence --> execution
  replay["L5 NovaReplay"] --> evidence
  federation["L6 NovaFederation"] --> identity
  federation --> policy
  federation --> evidence
  federation --> replay
  products["L7 NovaTech Products"] --> identity
  products --> policy
  products --> execution
  products --> evidence
  products --> replay
  products --> federation
```

The CI contract validator verifies that all referenced capabilities exist,
dependencies point to the same or lower layers, and the dependency graph is
acyclic.
