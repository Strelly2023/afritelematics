# NovaPay Agent Operations Framework 2026

NovaPay agents provide cash-in, cash-out, onboarding, and wallet support services. The operating model is built around identity verification, float management, compliance, and auditable settlement.

## Operating Model

1. The agent authenticates with NovaID.
2. The agent verifies the customer where required.
3. The agent performs the cash or wallet operation.
4. NovaPay updates wallet, settlement, and commission ledgers.
5. NovaTrust stores signed evidence for the transaction.

## Required Dashboard Fields

- Current float balance
- Cash balance
- Daily transaction summary
- Commission earnings
- Customer registrations
- Pending settlements
- Compliance alerts
- Device status
- Operational notifications

## App Tabs and Primary Actions

- Dashboard: open/close shift, daily summary, cash balance, float balance, commission, alerts, sync transactions
- Cash In: enter customer phone, scan customer QR, enter amount, collect cash, confirm deposit, print/share receipt, cancel transaction
- Cash Out: enter customer phone, scan customer QR, verify customer OTP, enter amount, pay cash, confirm withdrawal, print/share receipt, cancel withdrawal
- Customers: register customer, verify NovaID, upload customer ID, take customer selfie, update profile, reset PIN, view customer status
- Transactions: view transaction list, search, filter by date, download receipt, reverse pending transaction, report suspicious transaction, export daily report
- Float: view float balance, request float, transfer float, rebalance cash, view settlement, reconcile cash, submit cash report
- Support: open support ticket, report fraud, report device issue, report cash mismatch, call support, view training guide
- Profile: edit profile, verify agent NovaID, manage business location, manage device, change PIN, enable biometric login, logout

## Cash Management

- Float management
- Cash reconciliation
- Settlement reconciliation
- Liquidity monitoring
- Daily balancing
- Cash audit procedures

## Security Controls

- MFA
- Device binding
- Secure agent login
- Transaction PIN
- Audit logging
- Fraud detection
- Role-based permissions
- Remote device disable if compromised

## Compliance Controls

- KYC
- KYB
- AML
- CTF
- Customer Due Diligence
- Enhanced Due Diligence
- Suspicious transaction reporting
- Record retention
- Periodic compliance reviews

## Performance Metrics

- Transaction volume
- Cash availability
- Float utilization
- Customer satisfaction
- Compliance score
- Fraud incidents
- Service availability
- Settlement accuracy

## Agent Trust Profile

- Identity verification status
- Business verification status
- Compliance status
- Operational rating
- Fraud risk score
- Transaction success rate
- Settlement accuracy
- Trust score

## Evidence Requirements

Every operational transaction must produce NovaTrust evidence:

- Identity verified
- Wallet or customer verified
- Cash or ledger movement recorded
- Settlement record created
- Digital signature applied
- Replay evidence stored
- Audit package available

## Boundaries

- NovaPay Agent is a payment operations surface only.
- NovaRide is not required.
- NovaAI may suggest risk or support actions, but cannot approve transactions.
