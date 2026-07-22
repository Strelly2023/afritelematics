# GA service inventory assessment

Assessment commit: `11afddf2ab8777d520e2e1ab56a8bab9e1ca6765`

Classification: `STAGING_TESTED`

Decision impact: `NO-GO`

The live compose project exposes one aggregate API plus the dashboard, public
web, NovaCodePro portal, NGINX, Prometheus, Grafana, and OpenTelemetry. It does
not independently deploy the required NovaID, NovaPay, NovaRide,
NovaLogistics, NovaTrust, or NovaPolicy APIs. PostgreSQL, Redis, and Kafka or
Redpanda are also absent from the active compose project.

The four locally built application images use the mutable `latest` tag. The
live checkout is not clean or synchronized with the recovery branch, so none
of those images is accepted as an immutable GA artifact.

See `service-inventory.json` for the observed container-level status.
