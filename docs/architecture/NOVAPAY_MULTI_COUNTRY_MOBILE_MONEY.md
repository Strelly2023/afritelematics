# NOVAPAY MULTI-COUNTRY MOBILE MONEY

## Classification

`controlled_provider_integration_ready`

This implementation provides country-aware collection adapters and signed
settlement evidence. It does not claim operator approval, payment licensing, or
live settlement authority.

## Countries and rails

| Country | Currency | Default | Additional rails |
| --- | --- | --- | --- |
| Kenya (`KE`) | `KES` | Safaricom M-PESA | Airtel Money |
| Burundi (`BI`) | `BIF` | Lumicash | EcoCash |
| DR Congo (`CD`) | `CDF` | Orange Money | Airtel Money, Vodacom M-PESA |

Safaricom M-PESA uses the public Daraja STK Push contract. The remaining
operators use configurable partner-contract adapters because production API
details and credentials are issued through local commercial onboarding.

## Execution contract

```text
NovaID
  -> NovaPower
  -> NovaPay mobile-money adapter
  -> pending provider/customer authorization
  -> authenticated callback gateway
  -> settlement evidence
  -> NovaTrust receipt
  -> public Trust Explorer
```

Provider initiation never means settlement. A payment remains `pending` until
an authenticated callback is matched to an existing payment ID or provider
reference.

## API

```text
GET  /v1/core-platform/payments/mobile-money/catalog
POST /v1/core-platform/payments/execute
POST /webhooks/payments
```

Example controlled request:

```json
{
  "intent_id": "ride-ke-001",
  "amount": "125",
  "currency": "KES",
  "destination": "+254700000001",
  "provider": "mobile_money",
  "live_provider": false,
  "metadata": {
    "country": "KE",
    "description": "NovaRide trip"
  }
}
```

Live requests must additionally include:

```json
{
  "metadata": {
    "commercial_approval_reference": "operator-contract-reference"
  }
}
```

## Security invariants

1. Mobile numbers must use E.164 format.
2. The provider country must match the payment country.
3. Domestic collection currency must match the configured country currency.
4. Live execution requires global and provider-specific activation.
5. Live execution requires operator credentials and a commercial approval
   reference.
6. Provider initiation returns `pending`, never `settled`.
7. Settlement callbacks require gateway authentication, freshness validation,
   replay protection, and matching to an existing payment.
8. Settlement callbacks produce separate signed NovaTrust receipts.
9. Settlement evidence does not itself grant accounting, payout, or regulatory
   authority.

## Callback boundary

Operators expose different callback authentication mechanisms. NovaPay expects
an ingress adapter or provider gateway to verify the native callback and then
sign the normalized payload using the configured NovaPay webhook secret.

## Production activation

Production activation requires all of:

- local payment-services licensing or an approved licensed provider;
- operator merchant and API approval;
- KYC/KYB and AML controls;
- transaction, velocity, and jurisdiction limits;
- approved callback gateway;
- production signing key;
- managed PostgreSQL;
- reconciliation and incident runbooks.

Until those controls exist, providers remain controlled-pilot integrations.
