# NCP-005 API Contracts

Base paths:

- `/v1/novacodepro/requirements`
- `/v1/novacodepro/requirement-sets`
- `/v1/novacodepro/traceability`
- `/v1/novacodepro/knowledge`
- `/v1/novacodepro/search`

Contracts implemented:

- requirement CRUD, versioning, approvals, baselines, and acceptance criteria
- traceability link CRUD, snapshots, coverage, and gap reporting
- knowledge space/document CRUD, versioning, review, approval, publication, archive, search, and retrieval
- citations, provenance, retention, and audit evidence

All routes enforce tenant, workspace, permission, and classification checks through the session context.
