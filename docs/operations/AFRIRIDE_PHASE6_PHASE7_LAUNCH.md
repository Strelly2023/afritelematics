# AfriRide Phase 6 payments, Phase 7 observability and launch readiness

## Payment abstraction

The canonical `/v1/payments` API separates payment methods from providers.
Methods are card, wallet, cash, regional and split. Provider adapters are
Stripe, Flutterwave, cash and internal wallet; replacing an adapter does not
change fare, split, wallet, payout, refund or dispute rules.

All amounts are integer minor units. Captures create deterministic driver,
commission, tax and promotion splits. Rider/driver wallets use an idempotent
append-only ledger. Promotion value is resolved and consumed server-side.
Charges require idempotency keys. Refunds retain the original transaction,
scheduled payouts are durable, and disputes are separate review records.

Provider credentials, webhook secrets and production calls must be supplied as
runtime secrets. Reference adapters intentionally generate stable references
until live provider certification is enabled.

## Enterprise observability

`GET /v1/operations/observability` is operator protected and projects:

- fleet health and stale telemetry;
- dispatch and API p50/p95/p99 latency;
- ride, realtime and push queue depth;
- notification outbox delivery states;
- GPS sample quality;
- payment capture/refund, payout and dispute health;
- existing trust metrics.

Export this contract to Prometheus/OpenTelemetry in multi-instance production;
per-process latency samples must be scraped from every replica.

## Store and launch checklist

- [ ] Android upload keystores stored in EAS/secret manager; never committed.
- [ ] `AFRIRIDE_ANDROID_KEYSTORE_*` values configured and release certificate fingerprints recorded.
- [ ] Apple distribution certificate, App Store Connect key and provisioning profiles configured.
- [ ] Production EAS profile builds AAB and non-simulator iOS archive with mocks/test mode disabled.
- [ ] FCM, APNs and restricted Maps keys configured for both apps.
- [ ] Stripe/Flutterwave live keys and signed webhook verification certified.
- [ ] Tax, commission, refunds, cash reconciliation and payout policies approved.
- [ ] Privacy disclosures cover background location, safety telemetry and payments.
- [ ] Play data safety, content rating, account deletion and TestFlight review metadata complete.
- [ ] Redis/PostgreSQL backups, outbox workers, observability alerts and incident drills pass.
- [ ] Real-device rider/driver ride, offline, SOS, payment, refund and payout rehearsals pass.
- [ ] Production signing is independently verified before Play Store/TestFlight upload.

## Operational Readiness Requirements

The remaining launch dependencies are external production prerequisites, not
missing software features. They are documented centrally in:

`docs/operations/PRODUCTION_READINESS_REQUIREMENTS.md`

Use that document for production credentials, live provider activation, app
store release prerequisites, and launch approval gates.
