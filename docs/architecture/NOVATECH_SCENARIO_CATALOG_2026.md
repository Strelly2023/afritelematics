# NovaTech Scenario Catalog 2026

This catalog records production reference scenarios for NovaID, NovaPay, NovaRide, NovaPower, NovaTrust, and NovaAI. The scenarios are examples of integration through explicit contracts. They are not permission to merge product ownership or duplicate business logic across apps.

## Boundary Rule

- NovaID owns authentication and identity.
- NovaPay owns payments, wallet, ledger, settlement, and receipts.
- NovaRide owns mobility, dispatch, trip lifecycle, safety, and ride evidence.
- NovaPower owns authorization and policy enforcement.
- NovaTrust owns signed receipts, evidence references, replay, and audit packages.
- NovaAI is advisory only and cannot approve identity, approve payments, or dispatch rides.

## Scenario Matrix

| ID | Scenario | Primary Product | Services | Corridor / Context | Channel |
| --- | --- | --- | --- | --- | --- |
| 2 | Family Support Transfer | NovaPay | NovaID, NovaPay, NovaTrust | Melbourne -> Lubumbashi | Bank Deposit |
| 3 | Small Business Supplier Payment | NovaPay Business | NovaID, NovaPower, NovaPay, NovaTrust | Melbourne -> Goma | Business Bank Account |
| 4 | Cash Pickup Transfer | NovaPay | NovaID, NovaPay, NovaTrust | Melbourne -> Kananga | Cash Pickup |
| 5 | Student Tuition Payment | NovaPay | NovaID, NovaPower, NovaPay, NovaTrust | Melbourne -> University of Lubumbashi | Direct Institution Payment |
| 6 | Medical Emergency Transfer | NovaPay | NovaID, NovaPower, NovaPay, NovaTrust | Melbourne -> Lubumbashi | Express Bank Deposit |
| 7 | Salary Payment to Family | NovaPay | NovaID, NovaPower, NovaPay, NovaTrust, NovaAI | Melbourne -> Kinshasa | Mobile Money |
| 8 | Tourist Sends Money Home | NovaPay | NovaID, NovaPower, NovaPay, NovaTrust | Sydney -> Bukavu | Mobile Money |
| 9 | International Payroll | NovaPay Business | NovaID, NovaPower, NovaPay, NovaTrust | Melbourne -> Lubumbashi | Bank Deposit |
| 10 | Tourist Airport Taxi | NovaRide | NovaID, NovaRide, NovaPay, NovaTrust | Melbourne Airport -> CBD Hotel | NovaPay Wallet |
| 11 | Merchant QR Payment | NovaPay Merchant | NovaID, NovaPay, NovaTrust | Melbourne retail | NovaPay QR |
| 12 | NovaRide Driver Payout | NovaRide | NovaID, NovaRide, NovaPower, NovaPay, NovaTrust | Driver earnings -> wallet | NovaPay Wallet Payout |
| 13 | New Resident Onboarding | NovaID | NovaID, NovaPay, NovaRide, NovaPower, NovaTrust, NovaAI | DR Congo -> Melbourne | Optional Service Activation |
| 14 | Small Business Uses All Three Services | NovaPay Business | NovaID, NovaPay, NovaRide, NovaPower, NovaTrust | Melbourne retail | Business Wallet and Delivery |
| 15 | Airport Arrival to Family Remittance | NovaRide | NovaID, NovaRide, NovaPay, NovaPower, NovaTrust, NovaAI | Airport ride and later remittance | NovaRide + NovaPay |
| 16 | Ride With Existing Visa Card | NovaRide | NovaID, NovaRide, NovaPay Gateway, NovaTrust | Melbourne Airport -> Docklands | Existing Visa Card |
| 17 | International Student Arrival | NovaID | NovaID, NovaRide, NovaPay, NovaPower, NovaTrust, NovaAI | DR Congo -> Melbourne | Ride, Tuition, QR, Remittance |
| 18 | Agent Cash-In | NovaPay Agent | NovaID, NovaPay, NovaPower, NovaTrust | Werribee agent branch | Cash-In |
| 19 | Burundi to DR Congo Market Trader | NovaPay Business | NovaID, NovaPay, NovaPower, NovaTrust | Bujumbura -> Uvira | Cross-Border Mobile Money |
| 20 | Cross-Border Patient Transport and Hospital Payment | NovaRide | NovaID, NovaRide, NovaPay, NovaPower, NovaTrust, NovaAI | Uvira -> Bujumbura | Medical Transport and Healthcare Payment |

## Independence Examples

Scenario 11 uses NovaPay without NovaRide. Scenario 16 uses NovaRide with an existing Visa card and does not require a NovaPay wallet. Scenario 13 lets a new resident activate only NovaID, NovaPay, NovaRide, or all three. Scenario 20 combines NovaRide and NovaPay, but NovaRide still owns transport while NovaPay owns payment.

## Evidence Pattern

Each scenario ends with a NovaTrust evidence chain. Common evidence events include authentication, policy validation, payment authorization, ledger recording, ride or payout completion, digital signature, receipt generation, replay evidence storage, and audit package availability.

## SDK Source

The typed scenario source of truth is `novaTechScenarioCatalog` in `packages/novatech-platform-sdk/src/index.ts`.

## NovaPay Consumer Expansion

The NovaPay Consumer platform also maintains a dedicated scenario catalog for product design, QA, UAT, training, API testing, and demonstrations.

Typed SDK sources:

- `novapayConsumerScenarioCatalog`: payment corridor scenarios `20` through `99`
- `novapayConsumerFeatureScenarios`: wallet, onboarding, support, compliance, receipt, history, and settings journeys

These are NovaPay Consumer scenarios. They intentionally use their own `consumerScenarioId` field so they do not collide with the cross-product NovaTech scenario IDs above.

### Payment Corridor Coverage

The Consumer payment catalog covers these categories:

- Remittances and family support
- Education and tuition
- Medical and hospital payments
- Bill payments, airtime, data, and subscriptions
- Donations and religious/community giving
- Government and institution payments
- Trade, supplier, inventory, and agricultural payments
- Travel payments
- Freelancer, consultant, and contractor payments

Representative scenarios include:

| Consumer ID | Title | Receive Method |
| --- | --- | --- |
| 20 | First Salary Sent Home | Mobile Money |
| 21 | Monthly Rent Payment | Bank Deposit |
| 22 | School Fees for Child | Institution Payment |
| 24 | Emergency Funeral Support | Cash Pickup |
| 31 | Medical Insurance Payment | Bank Deposit |
| 34 | Utility Bill Payment | Bill Pay |
| 37 | Mobile Airtime Purchase | Airtime |
| 43 | Disaster Relief Donation | Wallet |
| 46 | Visa Application Fee | Institution |
| 53 | Wholesale Purchase | Mobile Money |
| 61 | Hotel Reservation Abroad | Card/Wallet |
| 65 | Digital Freelancer Payment | Wallet |
| 69 | Contractor Final Payment | Bank Deposit |
| 70 | Salary to Family | Mobile Money |
| 79 | Cash Pickup Transfer | Cash Pickup |
| 80 | Family Monthly Support | Mobile Money |
| 89 | Hotel Deposit | Card/Wallet |
| 90 | Salary Remittance | Mobile Money |
| 99 | Cash Pickup Transfer | Cash Pickup |

### Feature Journey Coverage

The Consumer feature catalog covers:

- New user registration
- NovaID identity verification
- Wallet creation and verified wallet upgrades
- Beneficiary management and favorite recipients
- Recurring transfers, cancellation, refunds, and disputes
- Transaction replay, PDF receipts, and receipt sharing
- Currency conversion and multi-currency wallets
- QR payment, scan-to-pay, request money, and split bills
- Wallet top-up, cash-in, cash-out, and agent-assisted withdrawal
- Card and bank account linking
- Transaction history, analytics, budget insights, rewards, referrals, and promo codes
- Live chat, voice/video support, lost phone recovery, device replacement, biometric reset, fraud alerts, and suspicious login verification
- Compliance document resubmission, exports, tax statements, account closure/reactivation, notification preferences, language switching, and accessibility mode

All NovaPay Consumer scenarios preserve the product doctrine:

```text
NovaID authenticates.
NovaPay executes financial services.
NovaTrust records verifiable evidence.
NovaRide is not required for NovaPay Consumer scenarios.
```
