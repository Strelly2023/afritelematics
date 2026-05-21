# AfriRide - AWS Deployment Plan

## Document Classification

```text
STATUS: CLOUD DEPLOYMENT ROADMAP
CLASSIFICATION: ISOLATED OPERATIONAL DEPLOYMENT SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE
```

This document defines a bounded AWS deployment path for the AfriRide production MVP pipeline.

It is not runtime authority, replay authority, proof authority, security certification, compliance certification, and not evidence that AfriRide is already deployed on AWS.

It does not redefine:

```text
constitutional truth
replay authority
execution legality
core invariants
identity ontology
claim admissibility
production deployment proof
```

The purpose is to move the current deterministic MVP pipeline toward real cloud deployment while preserving:

```text
deterministic core execution
adapter-normalization-ingestion admission
partitioned queue semantics
worker-mediated core invocation
append-only replay ledger
bounded production claims
```

---

# 1. Deployment Principle

AfriRide must not scale the constitutional core by making it directly reachable from the open world.

Deployment scales controlled access to the core:

```text
Client
-> API Gateway
-> Lambda API adapter
-> Edge adapter and normalization
-> Partition router
-> SQS partition queue
-> ECS worker pool
-> AfriTech deterministic core
-> RDS event_log
-> replay verification
```

Permanent rule:

```text
Only declared workers may invoke the AfriTech core.
External clients may only submit normalized-admissible requests through the API and queue layer.
```

---

# 2. Target AWS Architecture

```text
Mobile or Web Client
-> Amazon API Gateway
-> AWS Lambda API layer
-> AfriTech edge adapter
-> AfriTech normalization
-> AfriTech partition router
-> Amazon SQS partition queues
-> Amazon ECS Fargate worker pool
-> AfriTech core engine
-> Amazon RDS PostgreSQL event_log
-> DynamoDB or ElastiCache read model
-> replay verification Lambda or scheduled batch job
-> CloudWatch observability
```

This architecture maps the existing MVP surfaces to AWS without changing the core truth model.

| Local MVP Surface | AWS Deployment Surface |
| --- | --- |
| FastAPI TestClient API | API Gateway plus Lambda |
| in-process partitioned queue | SQS queues by partition |
| WorkerPool | ECS Fargate worker service |
| in-memory event log | RDS PostgreSQL event_log |
| replay engine | Lambda or scheduled batch replay job |
| read response from worker output | DynamoDB, ElastiCache, or PostgreSQL read model |

---

# 3. Step 1 - IAM and Network Boundary

## API Role

The API execution role may:

```text
write to SQS partition queues
write CloudWatch logs
read deployment configuration
```

The API execution role must not:

```text
write directly to RDS event_log
invoke the deterministic core directly
mutate replay records
delete queue messages after worker admission
```

## Worker Role

The Worker execution role may:

```text
read from assigned SQS partition queues
delete processed SQS messages
write to RDS event_log
write read-model projections
write CloudWatch logs
```

The Worker execution role must not:

```text
accept raw external HTTP input
call undeclared adapters
mutate constitutional proof surfaces
rewrite existing replay ledger rows
```

For MVP deployment, the default VPC may be used. Production hardening should introduce a dedicated VPC with private subnets for workers and RDS.

---

# 4. Step 2 - Lambda API Layer

The Lambda API layer wraps the existing FastAPI application using Mangum:

```python
from afritech.api.app import app
from mangum import Mangum

handler = Mangum(app)
```

Required dependencies:

```text
fastapi
mangum
pydantic
httpx for tests
```

Required API route:

```text
POST /process
```

Expected response:

```json
{
  "status": "accepted",
  "request_id": "request-id",
  "partition_id": 0
}
```

The API response is an admission acknowledgement, not proof of completed execution.

---

# 5. Step 3 - SQS Partition Queues

Create one SQS queue per partition:

```text
afriride-partition-0
afriride-partition-1
afriride-partition-2
afriride-partition-3
afriride-partition-4
afriride-partition-5
afriride-partition-6
afriride-partition-7
```

The local deterministic partition router maps:

```text
partition_id -> SQS queue URL
```

Routing must remain deterministic and based on declared routing keys:

```text
city_id
trip_id
request_id
user_id
```

The SQS message body must contain the normalized input, not raw HTTP payloads.

Dead-letter queues should be configured per partition:

```text
afriride-partition-0-dlq
...
afriride-partition-7-dlq
```

This preserves failure isolation and replay recovery boundaries.

---

# 6. Step 4 - ECS Fargate Worker Pool

Workers run as ECS Fargate tasks.

Each worker service is assigned one or more partitions:

```text
worker-service-partition-0 -> afriride-partition-0
worker-service-partition-1 -> afriride-partition-1
...
```

Worker responsibility:

```text
receive normalized event
validate edge trace
invoke deterministic core
generate output
generate replay_hash
append event_log record
delete SQS message only after successful event_log write
update read model
```

Workers are stateless with respect to authority. Durable truth is the append-only event log plus replay-verifiable output.

---

# 7. Step 5 - RDS PostgreSQL Event Log

Initial schema:

```sql
CREATE TABLE event_log (
    id BIGSERIAL PRIMARY KEY,
    request_id TEXT NOT NULL,
    partition_id INTEGER NOT NULL,
    normalized_input JSONB NOT NULL,
    output JSONB NOT NULL,
    trace JSONB NOT NULL,
    replay_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX event_log_request_id_idx ON event_log (request_id);
CREATE INDEX event_log_partition_id_idx ON event_log (partition_id);
CREATE INDEX event_log_created_at_idx ON event_log (created_at);
```

Operational hardening should add:

```text
append-only database permissions
point-in-time recovery
automated backups
read replica for replay jobs
connection pooling
partitioning by created_at or partition_id
```

The event_log is an operational replay ledger. It does not replace constitutional proof authority.

---

# 8. Step 6 - Read Model

The read model exists for speed only.

Allowed options:

```text
DynamoDB ride_state table
ElastiCache read-through cache
PostgreSQL ride_state projection table
```

Suggested minimal DynamoDB key:

```text
partition key: request_id
```

Read-model entries may be rebuilt from `event_log`.

Read-model failures must not mutate replay truth.

---

# 9. Step 7 - Replay Verification Job

Replay verification can run as:

```text
manual Lambda invocation
scheduled EventBridge Lambda
ECS batch task
CI-triggered validation against staging data
```

Replay job responsibility:

```text
load event_log rows
re-execute deterministic core over normalized_input
recalculate replay_hash
compare stored replay_hash
emit replay status
fail loudly on mismatch
```

Replay mismatch is a critical operational incident.

---

# 10. Step 8 - Observability

CloudWatch logs and metrics must cover:

```text
API request count
API admission failures
SQS queue depth per partition
SQS oldest message age
worker success count
worker failure count
event_log write failures
replay mismatch count
dead-letter queue count
```

Production hardening should later add:

```text
OpenTelemetry traces
Grafana dashboards
PagerDuty or Opsgenie alerts
structured JSON logs
```

Minimum incident triggers:

```text
replay mismatch > 0
dead-letter queue count > 0
event_log write failures > 0
worker lag beyond threshold
```

---

# 11. Step 9 - Deployment Test

Initial AWS deployment acceptance test:

```text
1. POST /process through API Gateway
2. API returns status accepted
3. Correct SQS partition receives normalized message
4. ECS worker consumes message
5. Worker writes RDS event_log row
6. Read model reflects completed processing
7. Replay verification passes
```

The deployment is not production-ready until every step is repeatable in staging.

---

# 12. Cost-Bounded MVP

Expected low-traffic MVP service set:

```text
API Gateway
Lambda
SQS
ECS Fargate one to two workers
RDS PostgreSQL small instance
CloudWatch logs and metrics
optional DynamoDB read model
```

Cost classification:

```text
bounded MVP infrastructure estimate
not a contractual cost guarantee
not a production scale cost model
```

---

# 13. Security and Secret Handling

Secrets must not be committed to the repository.

Use:

```text
AWS Secrets Manager
SSM Parameter Store
IAM task roles
least-privilege policies
```

Required production hardening:

```text
TLS everywhere
WAF on public API
rate limits
idempotency keys
structured audit logs
RDS encryption at rest
SQS encryption
private RDS subnet
```

---

# 14. Bounded Non-Claims

This document does not claim:

```text
AWS deployment completed
AfriRide production readiness achieved
global marketplace readiness achieved
universal fault tolerance achieved
complete state-space exhaustiveness achieved
infinite-scale dispatch guarantees achieved
PCI compliance achieved
SOC 2 compliance achieved
multi-region commercial readiness achieved
```

---

# 15. Safe Final Classification

```text
AfriRide AWS deployment planning is a bounded operational cloud roadmap
for deploying the replay-governed MVP pipeline through API Gateway,
Lambda, SQS partition queues, ECS workers, RDS event logging,
read-model projection, and replay verification without redefining
AfriTech constitutional truth or proof authority.
```
