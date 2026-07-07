# NovaPay Consumer and Agent Requirements 2026

This document defines the NovaPay consumer wallet model and the NovaPay agent operating model. NovaPay is a financial services product, not a mobility product.

## Product Boundary

- NovaID authenticates and verifies identity.
- NovaPay executes financial services.
- NovaRide handles mobility only.
- NovaTrust records evidence and audit trails.
- NovaAI remains advisory only.

## Consumer Requirements

### Eligibility

- Valid NovaID Personal account
- Minimum legal age in the operating jurisdiction
- Acceptance of NovaPay Terms of Service and Privacy Policy
- Not listed on applicable sanctions or prohibited-persons lists

### Required Information

- Full legal name
- Date of birth
- Mobile phone number
- Email address
- Residential address
- Nationality where required
- Preferred language
- Preferred currency

### KYC

- Basic: phone and email verification
- Standard: government ID, selfie/liveness, face matching, device registration
- Enhanced: proof of address, source of funds when required, additional due diligence

### Security

- Multi-factor authentication
- Biometric login
- Passkeys optional
- Trusted device management
- Session management
- Login alerts
- Sensitive action confirmation

### Wallet Setup

- NovaPay Wallet ID
- QR payment profile
- Multi-currency wallet where supported
- Wallet limits by verification level
- Transaction history
- Digital receipts

### Consumer UI Surfaces

- Tabs: Home, Send, Receive, Wallet, Payments, History, Profile
- Home actions: wallet balance, top up, send money, receive money, scan QR, pay merchant, pay bill, buy airtime/data, recent transactions, NovaID verification, security center
- Send actions: send to user, phone number, bank account, mobile money, international transfer, choose recipient, enter amount, add note, review, confirm, cancel, share receipt
- Receive actions: show QR, request money, copy wallet ID, share payment link, receive from agent, receive from bank, confirm received payment
- Wallet actions: top up, cash out, link bank, link card, link mobile money, set default funding source, view limits, upgrade level, freeze wallet
- Payments actions: merchant QR, bill payment, airtime, data, school fees, utilities, schedule payment, recurring payments
- History actions: view transaction, download receipt, share receipt, report, dispute, filter, export statement
- Profile actions: edit profile, verify NovaID, upload ID, security settings, change PIN, biometric login, manage devices, language, notifications, help, logout

### Consumer Services

- Send money
- Receive money
- QR payments
- Merchant payments
- Bill payments
- Airtime and data purchases
- Bank transfers
- Mobile money transfers
- International remittance
- Wallet top-up
- Cash withdrawal via agent
- Scheduled payments

### Consumer Trust Profile

- Identity status
- Wallet verification level
- Device trust
- Fraud risk score
- Transaction risk score
- Compliance status
- Security score

## Agent Requirements

### Eligibility

- Individual entrepreneur
- Retail shop
- Pharmacy
- Supermarket
- Fuel station
- Bank partner
- Mobile money outlet
- Financial services provider

### Registration and KYB

- Valid NovaID Business or NovaID Personal depending on agent type
- Agent application
- Business location
- Operating hours
- Contact details
- Business registration certificate where applicable
- Tax registration
- Business licence
- Proof of address
- Authorized representative verification

### Personal Verification

- Government-issued ID
- Selfie/liveness verification
- Face matching
- Phone verification
- Background screening where applicable

### Financial and Operational Requirements

- Agent wallet
- Settlement account
- Float account
- Minimum operating balance
- Bank account verification
- Commission account
- Android tablet or smartphone
- Internet connection
- QR scanner
- Receipt printer optional
- Barcode scanner optional
- Biometric scanner optional
- Secure POS terminal optional

### Agent Services

- Customer registration
- Identity verification
- Cash deposit
- Cash withdrawal
- Wallet funding
- Money transfer initiation
- Bill payments
- Merchant payments
- Account recovery assistance
- Customer support

### Agent UI Surfaces

- Tabs: Dashboard, Cash In, Cash Out, Customers, Transactions, Float, Support, Profile
- Dashboard actions: open/close shift, daily summary, cash balance, float balance, commission, alerts, sync transactions
- Cash In actions: enter phone, scan QR, enter amount, collect cash, confirm deposit, print/share receipt, cancel transaction
- Cash Out actions: enter phone, scan QR, verify OTP, enter amount, pay cash, confirm withdrawal, print/share receipt, cancel withdrawal
- Customers actions: register customer, verify NovaID, upload customer ID, take selfie, update profile, reset PIN, view status
- Transactions actions: list/search/filter/export/reverse/report suspicious transaction
- Float actions: view balance, request/transfer float, rebalance cash, settlement, reconcile cash, submit report
- Support actions: open ticket, report fraud/device issue/cash mismatch, call support, view training guide
- Profile actions: edit profile, verify NovaID, manage business location/device, change PIN, biometric login, logout

### Agent Trust Profile

- Identity verification status
- Business verification status
- Compliance status
- Operational rating
- Fraud risk score
- Transaction success rate
- Settlement accuracy
- Trust score

## Evidence and Boundaries

- Financial actions require NovaTrust evidence.
- NovaPay Consumer does not require NovaRide.
- NovaPay Agent does not require NovaRide.
- NovaAI may provide advisory insights only.
