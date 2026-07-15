# NovaRide Production-Operated Platform

NovaRide production operation is composed of:

- FastAPI runtime created from typed settings
- PostgreSQL as source of truth
- transactional outbox
- Kafka event publication
- Redis coordination for locks, duplicate suppression, circuit state, and emergency broadcasts
- signed mobile synchronization
- provider probes and policy routing
- circuit breakers
- operations APIs
- Prometheus metrics, Alertmanager routing, and Grafana dashboards
- multi-zone Kubernetes deployment assets
- DR exercise evidence generation
- readiness certificate generation

This repository does not mark GA readiness unless live PostgreSQL, Kafka, Kubernetes failover, emergency path, security, accessibility, and DR evidence are present.
