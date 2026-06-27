# NovaPay MFS / Onafriq first transaction runbook

This runbook governs the first NovaPay transaction through the MFS Africa /
Onafriq partner rail.

## Default posture

- Dry-run is the default.
- Real money movement is blocked until live readiness is true.
- Operator confirmation is required for live execution.
- The live provider adapter fails closed if credentials or commercial approval
  references are missing.

## 1. Check readiness

```bash
curl -H "Authorization: Bearer $OPERATOR_TOKEN" \
  "$API_BASE_URL/v1/core-platform/transfers/live-test/readiness"
```

Expected before production activation:

- `default_mode` is `dry_run`
- `provider.provider` is `mfs_africa`
- `real_money_movement_blocked` is `true`

## 2. Run the dry-run transaction

```bash
curl -X POST "$API_BASE_URL/v1/core-platform/transfers/live-test/run" \
  -H "Authorization: Bearer $OPERATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "1.00",
    "source_currency": "AUD",
    "recipient_name": "Amina Okello",
    "recipient_identifier": "+254700000001",
    "recipient_country": "KE"
  }'
```

Expected result:

- `status` is `dry_run_complete`
- `live_network_called` is `false`
- `quote.route_hint` is `mfs_africa`
- `verification.valid` is `true`

## 3. Configure live controls

Set these only in the production secret manager:

```bash
MFS_AFRICA_LIVE_MODE=true
MFS_AFRICA_API_BASE_URL=...
MFS_AFRICA_TOKEN_URL=...
MFS_AFRICA_CLIENT_ID=...
MFS_AFRICA_CLIENT_SECRET=...
MFS_AFRICA_CALLBACK_URL=...
MFS_AFRICA_COMMERCIAL_APPROVAL_REFERENCE=...
NOVAPAY_MOBILE_MONEY_LIVE_ENABLED=true
NOVAPAY_COMPLIANCE_LIVE_ENABLED=true
```

Optional partner-contract overrides:

```bash
MFS_AFRICA_TRANSFER_PATH=/v1/transfers
MFS_AFRICA_VERIFY_PATH=/v1/transfers/{reference}
MFS_AFRICA_REFERENCE_FIELD=transaction_id
MFS_AFRICA_REQUEST_TEMPLATE_JSON='{}'
```

## 4. Run the live transaction

Only after readiness reports `live_ready: true`:

```bash
curl -X POST "$API_BASE_URL/v1/core-platform/transfers/live-test/run" \
  -H "Authorization: Bearer $OPERATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "1.00",
    "source_currency": "AUD",
    "recipient_name": "Amina Okello",
    "recipient_identifier": "+254700000001",
    "recipient_country": "KE",
    "live": true,
    "operator_confirmed": true
  }'
```

Expected result:

- `status` is `submitted`
- `live_network_called` is `true`
- the receipt includes provider `mfs_africa`
- the verification block is valid

If any control is missing, the endpoint returns `status: blocked`.
