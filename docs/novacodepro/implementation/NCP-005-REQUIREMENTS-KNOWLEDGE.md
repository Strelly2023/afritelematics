# NCP-005 Requirements Traceability and Knowledge Hub

Status: IMPLEMENTED_INTERNAL

Scope:

- governed requirements lifecycle
- requirement versioning and baselines
- traceability links and coverage reporting
- knowledge documents, ADRs, runbooks, standards, policies, postmortems
- permission-aware keyword search and retrieval with citations
- audit and evidence emission for reads and mutations

Current limits:

- semantic retrieval is backed by the repository's deterministic local implementation when no external vector service is configured
- browser automation remains repository-local source verification unless a real browser harness is provisioned
