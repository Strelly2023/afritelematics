export type NovaTechProduct = "novaid" | "novapay" | "novaride";
export type NovaTechSharedService = "novapower" | "novatrust" | "novaai";
export type NovaTechService = NovaTechProduct | NovaTechSharedService;
export type AssuranceLevel = "low" | "medium" | "high" | "verified";
export type NotificationChannel = "push" | "email" | "sms" | "in_app";

export type ProductRegistryEntry = Readonly<{
  product: NovaTechProduct;
  displayName: "NovaID" | "NovaPay" | "NovaRide";
  owns: readonly string[];
  publicContracts: readonly string[];
  independentlyDeployable: true;
}>;

export const productRegistry: readonly ProductRegistryEntry[] = [
  {
    product: "novaid",
    displayName: "NovaID",
    owns: ["identity", "authentication", "mfa", "passkeys", "credentials", "consent", "device_trust", "access_management"],
    publicContracts: ["novaid-auth-session", "novaid-consent-grant"],
    independentlyDeployable: true,
  },
  {
    product: "novapay",
    displayName: "NovaPay",
    owns: ["wallet", "ledger", "transfers", "merchant_payments", "agent_banking", "settlement", "receipts", "reconciliation"],
    publicContracts: ["novapay-payment-intent", "novapay-receipt-reference"],
    independentlyDeployable: true,
  },
  {
    product: "novaride",
    displayName: "NovaRide",
    owns: ["booking", "dispatch", "driver_workflow", "fleet", "ride_lifecycle", "safety", "ride_receipts", "trip_replay"],
    publicContracts: ["novaride-ride-evidence", "novaride-payment-status"],
    independentlyDeployable: true,
  },
];

export type ServiceDiscoveryEntry = Readonly<{
  serviceName: string;
  product: NovaTechProduct | "platform";
  baseUrl: string;
  healthPath: string;
  contractVersion: string;
}>;

export type SharedAuthSession = Readonly<{
  sessionId: string;
  subjectId: string;
  product: NovaTechProduct;
  assuranceLevel: AssuranceLevel;
  methods: readonly ("password" | "otp" | "passkey" | "biometric" | "device_trust")[];
  authenticatedAt: string;
  expiresAt: string;
  deviceTrustLevel: AssuranceLevel;
  consentGrantId?: string;
}>;

export type ConsentGrant = Readonly<{
  grantId: string;
  subjectId: string;
  requesterProduct: NovaTechProduct;
  scopes: readonly string[];
  purpose: string;
  issuedAt: string;
  expiresAt?: string;
  revokedAt?: string;
}>;

export type NotificationEvent = Readonly<{
  eventId: string;
  product: NovaTechProduct | "platform";
  eventType: string;
  recipientId: string;
  channels: readonly NotificationChannel[];
  priority: "low" | "normal" | "high" | "critical";
  title: string;
  body: string;
  deepLink?: string;
  evidenceReference?: TrustEvidenceReference;
  createdAt: string;
}>;

export type AuditEvent = Readonly<{
  eventId: string;
  product: NovaTechProduct | "platform";
  actorId: string;
  action: string;
  resourceType: string;
  resourceId: string;
  outcome: "success" | "failure" | "denied";
  createdAt: string;
  evidenceReference?: TrustEvidenceReference;
}>;

export type TrustEvidenceReference = Readonly<{
  evidenceId: string;
  product: NovaTechProduct;
  evidenceType: "identity" | "payment_receipt" | "ride_evidence" | "audit";
  hash: string;
  signature?: string;
  issuedAt: string;
  retentionPolicy?: string;
}>;

export type AdvisoryAIInsight = Readonly<{
  insightId: string;
  product: NovaTechProduct | "platform";
  subjectReference: string;
  category: "risk" | "support" | "compliance" | "operations" | "forecast";
  confidence: number;
  recommendation: string;
  rationale: string;
  sourceSignals: readonly string[];
  advisoryOnly: true;
  prohibitedActions: readonly ["dispatch_ride", "approve_payment", "approve_identity"];
  createdAt: string;
  expiresAt?: string;
  humanReviewRequired: boolean;
}>;

export type NovaPayToNovaRidePaymentContract = Readonly<{
  paymentIntentId: string;
  rideId: string;
  payerId: string;
  amount: number;
  currency: string;
  status: "requested" | "authorized" | "captured" | "failed" | "refunded";
  receiptReference?: TrustEvidenceReference;
  riskIndicator: "low" | "medium" | "high";
}>;

export const NOVAAI_ADVISORY_ONLY_PROHIBITED_ACTIONS = [
  "dispatch_ride",
  "approve_payment",
  "approve_identity",
] as const;

export type NovaTechScenario = Readonly<{
  id: number;
  title: string;
  primaryProduct: NovaTechProduct;
  servicesUsed: readonly NovaTechService[];
  customer: string;
  counterparty: string;
  origin: string;
  destination: string;
  amount: string;
  channel: string;
  purpose: string;
  reference: string;
  status: "completed" | "ready_for_collection" | "processing";
  evidence: readonly string[];
  independenceNote: string;
}>;

export const novaTechScenarioCatalog: readonly NovaTechScenario[] = [
  {
    id: 2,
    title: "Family Support Transfer",
    primaryProduct: "novapay",
    servicesUsed: ["novaid", "novapay", "novatrust"],
    customer: "Sarah Johnson",
    counterparty: "Jean-Pierre Mukendi",
    origin: "Melbourne, Australia",
    destination: "Lubumbashi, Democratic Republic of Congo",
    amount: "AUD 250.00",
    channel: "Bank Deposit",
    purpose: "Family Support",
    reference: "NP-2026-00073215",
    status: "completed",
    evidence: ["NovaID Authentication", "Compliance Check", "Payment Authorized", "FX Conversion", "Bank Transfer Initiated", "Settlement Complete", "Recipient Credited", "Replay Evidence Stored"],
    independenceNote: "NovaPay executes a bank-deposit remittance without NovaRide.",
  },
  {
    id: 3,
    title: "Small Business Supplier Payment",
    primaryProduct: "novapay",
    servicesUsed: ["novaid", "novapower", "novapay", "novatrust"],
    customer: "Melbourne Fresh Foods Pty Ltd",
    counterparty: "Congo Coffee Export SARL",
    origin: "Melbourne, Australia",
    destination: "Goma, Democratic Republic of Congo",
    amount: "AUD 5,000.00",
    channel: "Business Bank Account",
    purpose: "Coffee Bean Purchase",
    reference: "NPB-2026-004812",
    status: "completed",
    evidence: ["Business Identity Verified", "Approval Recorded", "Ledger Entry Created", "Settlement Recorded", "Digital Signature", "Receipt Generated", "Replay Evidence", "Audit Bundle Available"],
    independenceNote: "NovaPay Business owns payment and settlement while NovaPower owns approval policy.",
  },
  {
    id: 4,
    title: "Cash Pickup Transfer",
    primaryProduct: "novapay",
    servicesUsed: ["novaid", "novapay", "novatrust"],
    customer: "Djuma Kikombe",
    counterparty: "Mama Chantal Ilunga",
    origin: "Melbourne, Australia",
    destination: "Kananga, Democratic Republic of Congo",
    amount: "AUD 300.00",
    channel: "Cash Pickup",
    purpose: "Family Emergency Support",
    reference: "NP-2026-009843",
    status: "ready_for_collection",
    evidence: ["Sender Authenticated", "Compliance Passed", "Transfer Signed", "Cash Pickup Authorized", "Recipient Identity Verified", "Cash Released", "Digital Receipt Generated", "Replay Evidence Stored"],
    independenceNote: "NovaPay supports recipients without bank accounts or mobile wallets.",
  },
  {
    id: 5,
    title: "Student Tuition Payment",
    primaryProduct: "novapay",
    servicesUsed: ["novaid", "novapower", "novapay", "novatrust"],
    customer: "Djuma Kikombe",
    counterparty: "University of Lubumbashi",
    origin: "Melbourne, Australia",
    destination: "Lubumbashi, Democratic Republic of Congo",
    amount: "AUD 1,200.00",
    channel: "Direct Institution Payment",
    purpose: "Semester Tuition Fee for Emmanuel Kikombe",
    reference: "NPE-2026-001284",
    status: "completed",
    evidence: ["NovaID Authentication", "Institution Verified", "Payment Authorized", "Ledger Updated", "Digital Signature Applied", "Receipt Generated", "Replay Evidence Stored", "Audit Package Available"],
    independenceNote: "NovaPay handles institutional payments outside the ride domain.",
  },
  {
    id: 6,
    title: "Medical Emergency Transfer",
    primaryProduct: "novapay",
    servicesUsed: ["novaid", "novapower", "novapay", "novatrust"],
    customer: "Djuma Kikombe",
    counterparty: "Dr. Denis Hospital Billing Office",
    origin: "Melbourne, Australia",
    destination: "Lubumbashi, Democratic Republic of Congo",
    amount: "AUD 750.00",
    channel: "Express Bank Deposit",
    purpose: "Emergency Medical Treatment for Kaskile Emanuel",
    reference: "NPM-2026-004251",
    status: "completed",
    evidence: ["Identity Verified", "Authorization Approved", "Ledger Recorded", "Digital Signature Applied", "Receipt Generated", "Replay Evidence Stored", "Audit Bundle Available"],
    independenceNote: "NovaPay supports urgent healthcare payments with policy controls.",
  },
  {
    id: 7,
    title: "Salary Payment to Family",
    primaryProduct: "novapay",
    servicesUsed: ["novaid", "novapower", "novapay", "novatrust", "novaai"],
    customer: "Djuma Kikombe",
    counterparty: "Rukia Kazibulaya",
    origin: "Melbourne, Australia",
    destination: "Kinshasa, Democratic Republic of Congo",
    amount: "AUD 500.00",
    channel: "Mobile Money",
    purpose: "Monthly Family Support",
    reference: "NP-2026-012548",
    status: "completed",
    evidence: ["Sender Identity Verified", "Risk Assessment", "Transfer Authorized", "Ledger Recorded", "Digital Signature", "Receipt Generated", "Replay Evidence Stored", "Audit Package Available"],
    independenceNote: "NovaAI may recommend recurring reminders but remains advisory only.",
  },
  {
    id: 8,
    title: "Tourist Sends Money Home",
    primaryProduct: "novapay",
    servicesUsed: ["novaid", "novapower", "novapay", "novatrust"],
    customer: "Grace Mwamba",
    counterparty: "Patrick Mwamba",
    origin: "Sydney, Australia",
    destination: "Bukavu, Democratic Republic of Congo",
    amount: "AUD 200.00",
    channel: "Mobile Money",
    purpose: "Family Support During Travel",
    reference: "NP-2026-014682",
    status: "completed",
    evidence: ["Identity Verified", "Payment Authorized", "Ledger Recorded", "Digital Signature", "Receipt Generated", "Replay Evidence Stored", "Audit Package Available"],
    independenceNote: "A visitor can use NovaPay with NovaID authentication and no NovaRide dependency.",
  },
  {
    id: 9,
    title: "International Payroll",
    primaryProduct: "novapay",
    servicesUsed: ["novaid", "novapower", "novapay", "novatrust"],
    customer: "NovaTech Australia Pty Ltd",
    counterparty: "Jean Claude Mbuyi",
    origin: "Melbourne, Australia",
    destination: "Lubumbashi, Democratic Republic of Congo",
    amount: "AUD 2,800.00",
    channel: "Bank Deposit",
    purpose: "Monthly Salary",
    reference: "NPB-2026-021584",
    status: "completed",
    evidence: ["Employer Verified", "Employee Verified", "Approval Recorded", "Payroll Executed", "Settlement Confirmed", "Digital Receipt", "Replay Evidence Stored"],
    independenceNote: "NovaPay Business owns payroll execution while NovaPower owns approval policy.",
  },
  {
    id: 10,
    title: "Tourist Airport Taxi",
    primaryProduct: "novaride",
    servicesUsed: ["novaid", "novaride", "novapay", "novatrust"],
    customer: "Maria Gonzalez",
    counterparty: "David Wilson",
    origin: "Melbourne Airport, Australia",
    destination: "Melbourne CBD Hotel",
    amount: "AUD 68.50",
    channel: "NovaPay Wallet",
    purpose: "Comfort Airport Ride",
    reference: "NR-2026-000984",
    status: "completed",
    evidence: ["Ride Requested", "Driver Assigned", "Passenger Verified", "Trip Completed", "Payment Authorized", "Receipt Signed", "Replay Evidence Stored", "Audit Package Available"],
    independenceNote: "NovaRide owns mobility; NovaPay only owns wallet payment and settlement.",
  },
  {
    id: 11,
    title: "Merchant QR Payment",
    primaryProduct: "novapay",
    servicesUsed: ["novaid", "novapay", "novatrust"],
    customer: "Djuma Kikombe",
    counterparty: "Congo African Grocery",
    origin: "Melbourne, Australia",
    destination: "Melbourne, Australia",
    amount: "AUD 86.40",
    channel: "NovaPay QR",
    purpose: "Groceries",
    reference: "NP-2026-015482",
    status: "completed",
    evidence: ["QR Generated", "Customer Authenticated", "Payment Authorized", "Wallet Debited", "Merchant Credited", "Receipt Signed", "Replay Evidence Stored"],
    independenceNote: "Retail QR payments use NovaPay without NovaRide.",
  },
  {
    id: 12,
    title: "NovaRide Driver Payout",
    primaryProduct: "novaride",
    servicesUsed: ["novaid", "novaride", "novapower", "novapay", "novatrust"],
    customer: "David Wilson",
    counterparty: "NovaRide Driver Earnings",
    origin: "Melbourne, Australia",
    destination: "NovaPay Wallet",
    amount: "AUD 328.27",
    channel: "NovaPay Wallet Payout",
    purpose: "Driver Payout for 12 Completed Trips",
    reference: "NRP-2026-003984",
    status: "completed",
    evidence: ["Trips Completed", "Earnings Calculated", "Commission Deducted", "Driver Authenticated", "Payout Authorized", "NovaPay Wallet Credited", "Receipt Signed", "Replay Evidence Stored"],
    independenceNote: "NovaRide owns trips and earnings; NovaPay owns payout settlement.",
  },
  {
    id: 13,
    title: "New Resident Onboarding",
    primaryProduct: "novaid",
    servicesUsed: ["novaid", "novapay", "novaride", "novapower", "novatrust", "novaai"],
    customer: "Amina Kasongo",
    counterparty: "NovaTech Services",
    origin: "Democratic Republic of Congo",
    destination: "Melbourne, Australia",
    amount: "AUD 100.00 wallet top-up and AUD 48.20 ride payment",
    channel: "Optional Service Activation",
    purpose: "Digital Identity, Wallet, and Airport Ride",
    reference: "NT-2026-ONBOARD-013",
    status: "completed",
    evidence: ["Identity Created", "Wallet Created", "Ride Booked", "Ride Completed", "Wallet Payment", "Receipt Signed", "Replay Stored"],
    independenceNote: "The customer chooses NovaID only, NovaPay, NovaRide, or all three.",
  },
  {
    id: 14,
    title: "Small Business Uses All Three Services",
    primaryProduct: "novapay",
    servicesUsed: ["novaid", "novapay", "novaride", "novapower", "novatrust"],
    customer: "Grace African Boutique",
    counterparty: "Customer Orders and African Textile Imports",
    origin: "Melbourne, Australia",
    destination: "Melbourne, Australia",
    amount: "AUD 1,485.00 sales and AUD 2,400.00 supplier payment",
    channel: "Business Wallet and NovaRide Delivery",
    purpose: "Retail Payments, Supplier Payment, Same-Day Delivery",
    reference: "NRD-2026-000815",
    status: "completed",
    evidence: ["Business Login", "Customer Payment", "Supplier Payment", "Delivery Requested", "Driver Assigned", "Delivery Completed", "Receipts Signed", "Replay Evidence Stored"],
    independenceNote: "The business can use each product separately or combine them through platform contracts.",
  },
  {
    id: 15,
    title: "Airport Arrival to Family Remittance",
    primaryProduct: "novaride",
    servicesUsed: ["novaid", "novaride", "novapay", "novapower", "novatrust", "novaai"],
    customer: "David Mukeba",
    counterparty: "Marie Mukeba",
    origin: "Melbourne International Airport, Australia",
    destination: "DR Congo",
    amount: "AUD 64.80 ride and AUD 250.00 remittance",
    channel: "NovaRide Comfort and NovaPay Mobile Money",
    purpose: "Airport Ride and Later Family Transfer",
    reference: "NP-2026-021482",
    status: "completed",
    evidence: ["NovaID Authentication", "Airport Ride Requested", "Ride Completed", "Wallet Payment", "International Transfer", "Receipt Signed", "Replay Stored", "Audit Complete"],
    independenceNote: "NovaRide and NovaPay are used at different times for unrelated jobs.",
  },
  {
    id: 16,
    title: "Ride With Existing Visa Card",
    primaryProduct: "novaride",
    servicesUsed: ["novaid", "novaride", "novapay", "novatrust"],
    customer: "Emma Thompson",
    counterparty: "Visa Network",
    origin: "Melbourne Airport, Australia",
    destination: "Docklands Hotel",
    amount: "AUD 42.80",
    channel: "Existing Visa Card via NovaPay Gateway",
    purpose: "Economy Ride",
    reference: "NR-2026-VISA-016",
    status: "completed",
    evidence: ["Ride Requested", "Driver Assigned", "Trip Completed", "Card Payment Authorized", "Receipt Signed", "Replay Evidence Stored"],
    independenceNote: "NovaPay Wallet is optional; NovaPay can act as a gateway for external cards.",
  },
  {
    id: 17,
    title: "International Student Arrival",
    primaryProduct: "novaid",
    servicesUsed: ["novaid", "novaride", "novapay", "novapower", "novatrust", "novaai"],
    customer: "Emmanuel Kabila",
    counterparty: "Melbourne Institute of Technology",
    origin: "Democratic Republic of Congo",
    destination: "Melbourne, Australia",
    amount: "AUD 47.80 ride, AUD 2,500.00 tuition, AUD 150.00 remittance",
    channel: "NovaRide, NovaPay Wallet, Education Payment, QR, Mobile Money",
    purpose: "Student Identity, Airport Ride, Tuition, Shopping, Family Remittance",
    reference: "MIT-2026-4587",
    status: "completed",
    evidence: ["Identity Created", "Ride Requested", "Ride Completed", "Wallet Created", "Tuition Paid", "Merchant QR Payment", "International Transfer", "Receipts Digitally Signed", "Replay Evidence Stored"],
    independenceNote: "The student gradually adopts products as needed; NovaAI stays advisory.",
  },
  {
    id: 18,
    title: "Agent Cash-In",
    primaryProduct: "novapay",
    servicesUsed: ["novaid", "novapay", "novapower", "novatrust"],
    customer: "Sarah Mwangi",
    counterparty: "Djuma Kikombe",
    origin: "Werribee, Melbourne",
    destination: "NovaPay Wallet",
    amount: "AUD 500.00",
    channel: "Agent Cash-In",
    purpose: "Cash Deposit and Wallet Credit",
    reference: "NPA-2026-008412",
    status: "completed",
    evidence: ["Agent Authenticated", "Customer Verified", "Cash Received", "Customer Approved", "Wallet Credited", "Receipt Signed", "Replay Evidence Stored", "Audit Package Generated"],
    independenceNote: "Agent banking converts cash to digital value without NovaRide.",
  },
  {
    id: 19,
    title: "Burundi to DR Congo Market Trader",
    primaryProduct: "novapay",
    servicesUsed: ["novaid", "novapay", "novapower", "novatrust"],
    customer: "Chantal Fashion Boutique",
    counterparty: "Bahati Kasereka",
    origin: "Bujumbura, Burundi",
    destination: "Uvira, DR Congo",
    amount: "USD 450.00",
    channel: "Cross-Border Mobile Money",
    purpose: "Wholesale Clothing Purchase",
    reference: "NPB-2026-030841",
    status: "completed",
    evidence: ["Business Authenticated", "Supplier Verified", "Payment Authorized", "Wallet Credited", "Receipt Digitally Signed", "Replay Evidence Stored", "Audit Package Available"],
    independenceNote: "NovaPay Business supports regional trade corridors through licensed partners.",
  },
  {
    id: 20,
    title: "Cross-Border Patient Transport and Hospital Payment",
    primaryProduct: "novaride",
    servicesUsed: ["novaid", "novaride", "novapay", "novapower", "novatrust", "novaai"],
    customer: "Bahati Kasereka",
    counterparty: "Amani Kasereka and Bujumbura Hospital",
    origin: "Uvira, DR Congo",
    destination: "Bujumbura, Burundi",
    amount: "USD 85.00 transport and USD 300.00 hospital deposit",
    channel: "Medical Transport and Healthcare Payment",
    purpose: "Cross-Border Patient Transport and Emergency Admission Deposit",
    reference: "NMC-2026-002419",
    status: "completed",
    evidence: ["NovaID Authentication", "Medical Ride Requested", "Driver & Vehicle Verified", "Border Checkpoint Recorded", "Trip Completed", "Transport Payment Authorized", "Hospital Payment Authorized", "Receipts Digitally Signed", "Replay Evidence Stored", "Audit Bundle Available"],
    independenceNote: "NovaRide owns transport; NovaPay owns hospital payment; NovaAI may recommend routes only.",
  },
];

export type NovaPayConsumerPaymentScenario = Readonly<{
  consumerScenarioId: number;
  title: string;
  sender: string;
  receiver: string;
  origin: string;
  destination: string;
  receiveMethod: string;
  category: "remittance" | "education" | "medical" | "bill_pay" | "donation" | "government" | "trade" | "travel" | "freelance";
  novaIdRequired: true;
  novaPayOwns: "payment_execution";
  novaTrustEvidence: true;
  novaRideRequired: false;
}>;

const consumerScenario = (
  consumerScenarioId: number,
  title: string,
  sender: string,
  receiver: string,
  receiveMethod: string,
  category: NovaPayConsumerPaymentScenario["category"],
  origin = "Australia",
  destination = "Democratic Republic of Congo",
): NovaPayConsumerPaymentScenario => ({
  consumerScenarioId,
  title,
  sender,
  receiver,
  origin,
  destination,
  receiveMethod,
  category,
  novaIdRequired: true,
  novaPayOwns: "payment_execution",
  novaTrustEvidence: true,
  novaRideRequired: false,
});

export const novapayConsumerScenarioCatalog: readonly NovaPayConsumerPaymentScenario[] = [
  consumerScenario(20, "First Salary Sent Home", "Employee in Australia", "Family in Kinshasa", "Mobile Money", "remittance"),
  consumerScenario(21, "Monthly Rent Payment", "Australia", "Landlord in DR Congo", "Bank Deposit", "remittance"),
  consumerScenario(22, "School Fees for Child", "Australia", "Primary School", "Institution Payment", "education"),
  consumerScenario(23, "University Tuition Installment", "Australia", "University", "Institution", "education"),
  consumerScenario(24, "Emergency Funeral Support", "Australia", "Family", "Cash Pickup", "remittance"),
  consumerScenario(25, "Wedding Contribution", "Australia", "Relative", "Mobile Money", "remittance"),
  consumerScenario(26, "Birthday Gift Transfer", "Australia", "Friend", "Wallet", "remittance"),
  consumerScenario(27, "Christmas Family Support", "Australia", "Family", "Mobile Money", "remittance"),
  consumerScenario(28, "Easter Holiday Transfer", "Australia", "Parents", "Bank Deposit", "remittance"),
  consumerScenario(29, "Mother's Day Gift", "Australia", "Mother", "Mobile Money", "remittance"),
  consumerScenario(30, "Father's Day Gift", "Australia", "Father", "Mobile Money", "remittance"),
  consumerScenario(31, "Medical Insurance Payment", "Australia", "Hospital", "Bank Deposit", "medical"),
  consumerScenario(32, "Pharmacy Payment", "Australia", "Pharmacy", "Wallet", "medical"),
  consumerScenario(33, "Hospital Deposit Before Surgery", "Australia", "Hospital", "Bank Deposit", "medical"),
  consumerScenario(34, "Utility Bill Payment", "Australia", "Electricity Company", "Bill Pay", "bill_pay"),
  consumerScenario(35, "Water Bill Payment", "Australia", "Water Utility", "Bill Pay", "bill_pay"),
  consumerScenario(36, "Internet Bill Payment", "Australia", "ISP", "Bill Pay", "bill_pay"),
  consumerScenario(37, "Mobile Airtime Purchase", "Australia", "Mobile Phone", "Airtime", "bill_pay"),
  consumerScenario(38, "Mobile Data Bundle", "Australia", "Mobile Wallet", "Data Purchase", "bill_pay"),
  consumerScenario(39, "TV Subscription Payment", "Australia", "TV Provider", "Bill Pay", "bill_pay"),
  consumerScenario(40, "Church Offering", "Australia", "Church", "Wallet", "donation"),
  consumerScenario(41, "Mosque Donation", "Australia", "Mosque", "Wallet", "donation"),
  consumerScenario(42, "Charity Donation", "Australia", "NGO", "Wallet", "donation"),
  consumerScenario(43, "Disaster Relief Donation", "Australia", "Relief Organization", "Wallet", "donation"),
  consumerScenario(44, "Refugee Family Assistance", "Australia", "Refugee Camp", "Cash Pickup", "donation"),
  consumerScenario(45, "Student Living Expenses", "Australia", "Student", "Mobile Money", "education"),
  consumerScenario(46, "Visa Application Fee", "Australia", "Government", "Institution", "government"),
  consumerScenario(47, "Passport Renewal Fee", "Australia", "Embassy", "Institution", "government"),
  consumerScenario(48, "Immigration Service Fee", "Australia", "Immigration Office", "Institution", "government"),
  consumerScenario(49, "Court Fee Payment", "Australia", "Government", "Institution", "government"),
  consumerScenario(50, "Tax Payment", "Australia", "Tax Authority", "Institution", "government"),
  consumerScenario(51, "Import Goods Payment", "Australia", "Supplier", "Bank Deposit", "trade"),
  consumerScenario(52, "Export Invoice Settlement", "Australia", "Exporter", "Bank Deposit", "trade"),
  consumerScenario(53, "Wholesale Purchase", "Burundi", "DR Congo Supplier", "Mobile Money", "trade", "Burundi", "Democratic Republic of Congo"),
  consumerScenario(54, "Retail Inventory Purchase", "Australia", "Supplier", "Bank Deposit", "trade"),
  consumerScenario(55, "Construction Materials", "Australia", "Building Supplier", "Bank Deposit", "trade"),
  consumerScenario(56, "Vehicle Purchase Deposit", "Australia", "Dealer", "Bank Deposit", "trade"),
  consumerScenario(57, "Motorcycle Purchase", "Australia", "Dealer", "Mobile Money", "trade"),
  consumerScenario(58, "Livestock Purchase", "Australia", "Farmer", "Mobile Money", "trade"),
  consumerScenario(59, "Agricultural Seeds Payment", "Australia", "Supplier", "Wallet", "trade"),
  consumerScenario(60, "Farmer Cooperative Payment", "Australia", "Cooperative", "Bank Deposit", "trade"),
  consumerScenario(61, "Hotel Reservation Abroad", "Australia", "Hotel", "Card/Wallet", "travel"),
  consumerScenario(62, "Flight Booking Payment", "Australia", "Airline", "Card", "travel"),
  consumerScenario(63, "Travel Insurance Purchase", "Australia", "Insurance Company", "Card", "travel"),
  consumerScenario(64, "Family Vacation Transfer", "Australia", "Relative Abroad", "Wallet", "travel"),
  consumerScenario(65, "Digital Freelancer Payment", "Australia", "Freelancer", "Wallet", "freelance"),
  consumerScenario(66, "Remote Software Developer Payment", "Australia", "Developer", "Bank Deposit", "freelance"),
  consumerScenario(67, "Graphic Designer Payment", "Australia", "Designer", "Wallet", "freelance"),
  consumerScenario(68, "Consultant Invoice Payment", "Australia", "Consultant", "Bank Deposit", "freelance"),
  consumerScenario(69, "Contractor Final Payment", "Australia", "Contractor", "Bank Deposit", "freelance"),
  consumerScenario(70, "Salary to Family", "United States", "Family in DR Congo", "Mobile Money", "remittance", "United States", "Democratic Republic of Congo"),
  consumerScenario(71, "School Fees", "United States", "School in Kenya", "Institution Payment", "education", "United States", "Kenya"),
  consumerScenario(72, "Emergency Medical Support", "United States", "Hospital in Uganda", "Bank Deposit", "medical", "United States", "Uganda"),
  consumerScenario(73, "Mortgage Support", "United States", "Mortgage Provider in Nigeria", "Bank Deposit", "remittance", "United States", "Nigeria"),
  consumerScenario(74, "Business Supplier Payment", "United States", "Supplier in Ghana", "Bank Deposit", "trade", "United States", "Ghana"),
  consumerScenario(75, "Church Donation", "United States", "Church in Rwanda", "Wallet", "donation", "United States", "Rwanda"),
  consumerScenario(76, "University Tuition", "United States", "University in India", "Institution Payment", "education", "United States", "India"),
  consumerScenario(77, "Freelancer Payment", "United States", "Freelancer in Philippines", "Wallet", "freelance", "United States", "Philippines"),
  consumerScenario(78, "Vacation Support", "United States", "Family in Tanzania", "Mobile Money", "travel", "United States", "Tanzania"),
  consumerScenario(79, "Cash Pickup Transfer", "United States", "Family in Burundi", "Cash Pickup", "remittance", "United States", "Burundi"),
  consumerScenario(80, "Family Monthly Support", "Canada", "Family in DR Congo", "Mobile Money", "remittance", "Canada", "Democratic Republic of Congo"),
  consumerScenario(81, "Parent Medical Bills", "Canada", "Hospital in Rwanda", "Bank Deposit", "medical", "Canada", "Rwanda"),
  consumerScenario(82, "Student Allowance", "Canada", "Student in Uganda", "Mobile Money", "education", "Canada", "Uganda"),
  consumerScenario(83, "Import Goods Payment", "Canada", "Supplier in Kenya", "Bank Deposit", "trade", "Canada", "Kenya"),
  consumerScenario(84, "Mobile Money Transfer", "Canada", "Family in Tanzania", "Mobile Money", "remittance", "Canada", "Tanzania"),
  consumerScenario(85, "Business Invoice", "Canada", "Business in Nigeria", "Bank Deposit", "trade", "Canada", "Nigeria"),
  consumerScenario(86, "Passport Fee Payment", "Canada", "Government in India", "Institution Payment", "government", "Canada", "India"),
  consumerScenario(87, "Charity Donation", "Canada", "NGO in Malawi", "Wallet", "donation", "Canada", "Malawi"),
  consumerScenario(88, "Emergency Cash Pickup", "Canada", "Family in Zambia", "Cash Pickup", "remittance", "Canada", "Zambia"),
  consumerScenario(89, "Hotel Deposit", "Canada", "Hotel in South Africa", "Card/Wallet", "travel", "Canada", "South Africa"),
  consumerScenario(90, "Salary Remittance", "United Kingdom", "Family in DR Congo", "Mobile Money", "remittance", "United Kingdom", "Democratic Republic of Congo"),
  consumerScenario(91, "House Construction Payment", "United Kingdom", "Builder in Burundi", "Bank Deposit", "trade", "United Kingdom", "Burundi"),
  consumerScenario(92, "Family Support", "United Kingdom", "Family in Rwanda", "Mobile Money", "remittance", "United Kingdom", "Rwanda"),
  consumerScenario(93, "University Fees", "United Kingdom", "University in Kenya", "Institution Payment", "education", "United Kingdom", "Kenya"),
  consumerScenario(94, "Medical Treatment", "United Kingdom", "Hospital in Uganda", "Bank Deposit", "medical", "United Kingdom", "Uganda"),
  consumerScenario(95, "Merchant Payment", "United Kingdom", "Merchant in Tanzania", "Wallet", "trade", "United Kingdom", "Tanzania"),
  consumerScenario(96, "Business Supplier Settlement", "United Kingdom", "Supplier in Nigeria", "Bank Deposit", "trade", "United Kingdom", "Nigeria"),
  consumerScenario(97, "Church Donation", "United Kingdom", "Church in Ghana", "Wallet", "donation", "United Kingdom", "Ghana"),
  consumerScenario(98, "Freelancer Payment", "United Kingdom", "Freelancer in India", "Wallet", "freelance", "United Kingdom", "India"),
  consumerScenario(99, "Cash Pickup Transfer", "United Kingdom", "Family in Zimbabwe", "Cash Pickup", "remittance", "United Kingdom", "Zimbabwe"),
];

export type NovaPayConsumerFeatureScenario = Readonly<{
  featureId: string;
  title: string;
  domain: "onboarding" | "beneficiary" | "transfer_control" | "receipt" | "wallet" | "card_bank" | "history_analytics" | "support_security" | "compliance_settings";
  requiresNovaID: boolean;
  novaPayOwns: true;
  novaRideRequired: false;
}>;

const consumerFeature = (
  featureId: string,
  title: string,
  domain: NovaPayConsumerFeatureScenario["domain"],
  requiresNovaID = true,
): NovaPayConsumerFeatureScenario => ({
  featureId,
  title,
  domain,
  requiresNovaID,
  novaPayOwns: true,
  novaRideRequired: false,
});

export const novapayConsumerFeatureScenarios: readonly NovaPayConsumerFeatureScenario[] = [
  consumerFeature("NPF-001", "New user registration", "onboarding"),
  consumerFeature("NPF-002", "Identity verification with NovaID", "onboarding"),
  consumerFeature("NPF-003", "Wallet creation", "onboarding"),
  consumerFeature("NPF-004", "Wallet upgrade to verified account", "onboarding"),
  consumerFeature("NPF-005", "Add beneficiary", "beneficiary"),
  consumerFeature("NPF-006", "Edit beneficiary", "beneficiary"),
  consumerFeature("NPF-007", "Delete beneficiary", "beneficiary"),
  consumerFeature("NPF-008", "Favorite recipients", "beneficiary"),
  consumerFeature("NPF-009", "Schedule recurring transfers", "transfer_control"),
  consumerFeature("NPF-010", "Transfer cancellation before processing", "transfer_control"),
  consumerFeature("NPF-011", "Refund request", "transfer_control"),
  consumerFeature("NPF-012", "Chargeback dispute", "transfer_control"),
  consumerFeature("NPF-013", "Transaction replay", "receipt"),
  consumerFeature("NPF-014", "Download PDF receipt", "receipt"),
  consumerFeature("NPF-015", "Share receipt", "receipt"),
  consumerFeature("NPF-016", "Currency conversion", "wallet"),
  consumerFeature("NPF-017", "Multi-currency wallet", "wallet"),
  consumerFeature("NPF-018", "QR payment", "wallet"),
  consumerFeature("NPF-019", "Scan-to-pay", "wallet"),
  consumerFeature("NPF-020", "Request money", "wallet"),
  consumerFeature("NPF-021", "Split bill", "wallet"),
  consumerFeature("NPF-022", "Receive payment request", "wallet"),
  consumerFeature("NPF-023", "Wallet top-up", "wallet"),
  consumerFeature("NPF-024", "Wallet cash-in", "wallet"),
  consumerFeature("NPF-025", "Wallet cash-out", "wallet"),
  consumerFeature("NPF-026", "Agent-assisted cash withdrawal", "wallet"),
  consumerFeature("NPF-027", "Card linking", "card_bank"),
  consumerFeature("NPF-028", "Card removal", "card_bank"),
  consumerFeature("NPF-029", "Bank account linking", "card_bank"),
  consumerFeature("NPF-030", "Transaction history search", "history_analytics"),
  consumerFeature("NPF-031", "Monthly spending analytics", "history_analytics"),
  consumerFeature("NPF-032", "Budget insights", "history_analytics"),
  consumerFeature("NPF-033", "Loyalty rewards", "history_analytics", false),
  consumerFeature("NPF-034", "Referral bonus", "history_analytics", false),
  consumerFeature("NPF-035", "Promo code redemption", "history_analytics", false),
  consumerFeature("NPF-036", "Live chat support", "support_security"),
  consumerFeature("NPF-037", "Voice/video customer support", "support_security"),
  consumerFeature("NPF-038", "Lost phone recovery", "support_security"),
  consumerFeature("NPF-039", "Device replacement", "support_security"),
  consumerFeature("NPF-040", "Biometric reset", "support_security"),
  consumerFeature("NPF-041", "Fraud alert handling", "support_security"),
  consumerFeature("NPF-042", "Suspicious login verification", "support_security"),
  consumerFeature("NPF-043", "Transfer status tracking", "transfer_control"),
  consumerFeature("NPF-044", "Compliance document resubmission", "compliance_settings"),
  consumerFeature("NPF-045", "Transaction export CSV/PDF", "history_analytics"),
  consumerFeature("NPF-046", "Tax statement generation", "history_analytics"),
  consumerFeature("NPF-047", "Account closure", "compliance_settings"),
  consumerFeature("NPF-048", "Account reactivation", "compliance_settings"),
  consumerFeature("NPF-049", "Notification preferences", "compliance_settings", false),
  consumerFeature("NPF-050", "Language switching", "compliance_settings", false),
  consumerFeature("NPF-051", "Accessibility mode", "compliance_settings", false),
];

export type ScenarioRegistryDomain =
  | "Consumer"
  | "Business"
  | "Merchant"
  | "Wallet"
  | "Agent Banking"
  | "Government"
  | "Compliance"
  | "Fraud"
  | "Customer Support"
  | "Recovery"
  | "API Integration"
  | "Mobile UI"
  | "Performance"
  | "Accessibility";

export type ScenarioClassification =
  | "Happy Path"
  | "Alternative Path"
  | "Exception"
  | "Compliance"
  | "Fraud"
  | "Recovery"
  | "Performance"
  | "Security"
  | "Accessibility"
  | "Offline"
  | "Integration"
  | "Disaster Recovery"
  | "Negative Testing"
  | "Boundary Testing";

export type ScenarioTestSuite =
  | "Unit"
  | "Integration"
  | "API"
  | "UI"
  | "Mobile"
  | "Performance"
  | "Security"
  | "Compliance"
  | "Accessibility"
  | "End-to-End"
  | "Regression"
  | "Pilot"
  | "Production Certification";

export type ScenarioEvidenceArtifact =
  | "Identity Verified"
  | "KYC Complete"
  | "AML Check"
  | "Sanctions Check"
  | "Device Trust"
  | "Risk Score"
  | "Ledger Entry"
  | "Settlement Record"
  | "Digital Signature"
  | "Replay Evidence"
  | "Audit Package"
  | "PDF Receipt"
  | "Customer Notification"
  | "Operator Log";

export type ScenarioPersona = Readonly<{
  personaId: string;
  label: string;
  description: string;
  defaultKycLevel: "basic" | "standard" | "enhanced";
  accessibilityConsiderations?: readonly string[];
}>;

export const scenarioPersonas: readonly ScenarioPersona[] = [
  { personaId: "PER-FIRST-TIME", label: "First-time customer", description: "New customer completing registration, identity checks, and first transaction.", defaultKycLevel: "standard" },
  { personaId: "PER-RETURNING", label: "Returning customer", description: "Existing verified customer using saved recipients and established devices.", defaultKycLevel: "standard" },
  { personaId: "PER-REFUGEE", label: "Refugee", description: "Customer with alternative documentation and assisted verification needs.", defaultKycLevel: "enhanced" },
  { personaId: "PER-STUDENT", label: "International student", description: "Student managing arrival, wallet, tuition, bills, and remittances.", defaultKycLevel: "standard" },
  { personaId: "PER-TOURIST", label: "Tourist", description: "Temporary visitor using cards, rides, QR payments, or remittances while travelling.", defaultKycLevel: "basic" },
  { personaId: "PER-MIGRANT-WORKER", label: "Migrant worker", description: "Recurring remittance sender supporting family abroad.", defaultKycLevel: "enhanced" },
  { personaId: "PER-FREELANCER", label: "Freelancer", description: "Independent worker receiving or sending invoice payments.", defaultKycLevel: "standard" },
  { personaId: "PER-SMALL-BUSINESS", label: "Small business owner", description: "Owner using merchant payments, supplier payments, and delivery workflows.", defaultKycLevel: "enhanced" },
  { personaId: "PER-MERCHANT", label: "Merchant", description: "Retail merchant accepting QR, wallet, and settlement payments.", defaultKycLevel: "enhanced" },
  { personaId: "PER-CORP-FINANCE", label: "Corporate finance officer", description: "Business user approving payroll, supplier, treasury, and reconciliation workflows.", defaultKycLevel: "enhanced" },
  { personaId: "PER-NGO-ADMIN", label: "NGO administrator", description: "Administrator managing donations, relief disbursements, and audit evidence.", defaultKycLevel: "enhanced" },
  { personaId: "PER-GOV-OFFICER", label: "Government officer", description: "Officer validating institution payments, permits, or public service collections.", defaultKycLevel: "enhanced" },
  { personaId: "PER-ELDERLY", label: "Elderly customer", description: "Customer requiring simpler flows, recovery options, and assisted support.", defaultKycLevel: "standard", accessibilityConsiderations: ["large_text", "voice_support"] },
  { personaId: "PER-VISUAL", label: "Visually impaired customer", description: "Customer using screen reader, high contrast, and accessible authentication flows.", defaultKycLevel: "standard", accessibilityConsiderations: ["screen_reader", "high_contrast", "voiceover"] },
  { personaId: "PER-AGENT", label: "Agent operator", description: "Agent serving walk-in customers for cash-in, cash-out, and assisted transfers.", defaultKycLevel: "enhanced" },
  { personaId: "PER-COMPLIANCE", label: "Compliance analyst", description: "Operations user reviewing alerts, investigations, and audit artifacts.", defaultKycLevel: "enhanced" },
];

export type ScenarioCorridor = Readonly<{
  corridorId: string;
  fromCountry: string;
  toCountry: string;
  supportedCurrencies: readonly string[];
  receiveMethods: readonly string[];
  settlementTime: string;
  complianceRequirements: readonly ("KYC" | "AML" | "Sanctions" | "Device Trust" | "Source of Funds" | "Purpose of Payment")[];
}>;

const countryCodes: Record<string, string> = {
  Australia: "AU",
  "United States": "US",
  Canada: "CA",
  "United Kingdom": "UK",
  France: "FR",
  Belgium: "BE",
  Germany: "DE",
  Netherlands: "NL",
  Italy: "IT",
  Spain: "ES",
  Portugal: "PT",
  "United Arab Emirates": "AE",
  Qatar: "QA",
  "Saudi Arabia": "SA",
  Kuwait: "KW",
  Oman: "OM",
  "South Africa": "ZA",
  Kenya: "KE",
  Uganda: "UG",
  Burundi: "BI",
  Rwanda: "RW",
  Nigeria: "NG",
  Ghana: "GH",
  "DR Congo": "CD",
  Tanzania: "TZ",
  Zambia: "ZM",
  Zimbabwe: "ZW",
  Malawi: "MW",
  India: "IN",
  Philippines: "PH",
  Indonesia: "ID",
  Vietnam: "VN",
  Nepal: "NP",
  Pakistan: "PK",
  Bangladesh: "BD",
  Mexico: "MX",
  "Sri Lanka": "LK",
  Angola: "AO",
};

const sendCurrencyByCountry: Record<string, string> = {
  Australia: "AUD",
  "United States": "USD",
  Canada: "CAD",
  "United Kingdom": "GBP",
  France: "EUR",
  Belgium: "EUR",
  Germany: "EUR",
  Netherlands: "EUR",
  Italy: "EUR",
  Spain: "EUR",
  Portugal: "EUR",
  "United Arab Emirates": "AED",
  Qatar: "QAR",
  "Saudi Arabia": "SAR",
  Kuwait: "KWD",
  Oman: "OMR",
  "South Africa": "ZAR",
  Kenya: "KES",
  Uganda: "UGX",
  Burundi: "BIF",
  Rwanda: "RWF",
  Nigeria: "NGN",
  Ghana: "GHS",
};

const receiveCurrencyByCountry: Record<string, string> = {
  "DR Congo": "CDF",
  Burundi: "BIF",
  Rwanda: "RWF",
  Uganda: "UGX",
  Kenya: "KES",
  Tanzania: "TZS",
  Zambia: "ZMW",
  Zimbabwe: "USD",
  Malawi: "MWK",
  Nigeria: "NGN",
  Ghana: "GHS",
  "South Africa": "ZAR",
  India: "INR",
  Philippines: "PHP",
  Indonesia: "IDR",
  Vietnam: "VND",
  Nepal: "NPR",
  Pakistan: "PKR",
  Bangladesh: "BDT",
  Mexico: "MXN",
  "Sri Lanka": "LKR",
  Angola: "AOA",
};

const mobileMoneyCountries = new Set(["DR Congo", "Burundi", "Rwanda", "Uganda", "Kenya", "Tanzania", "Zambia", "Zimbabwe", "Malawi", "Ghana", "Philippines"]);
const cashPickupCountries = new Set(["DR Congo", "Burundi", "Zambia", "Zimbabwe", "Malawi", "Philippines", "Nepal", "Bangladesh", "Pakistan"]);

const corridor = (fromCountry: string, toCountry: string): ScenarioCorridor => ({
  corridorId: `COR-${countryCodes[fromCountry]}-${countryCodes[toCountry]}`,
  fromCountry,
  toCountry,
  supportedCurrencies: [sendCurrencyByCountry[fromCountry] ?? "USD", receiveCurrencyByCountry[toCountry] ?? "USD", "USD"].filter((currency, index, currencies) => currencies.indexOf(currency) === index),
  receiveMethods: [
    ...(mobileMoneyCountries.has(toCountry) ? ["Mobile Money"] : []),
    "Bank Deposit",
    ...(cashPickupCountries.has(toCountry) ? ["Cash Pickup"] : []),
    "Wallet",
  ],
  settlementTime: mobileMoneyCountries.has(toCountry) ? "Within minutes to same day" : "Same day to next business day",
  complianceRequirements: ["KYC", "AML", "Sanctions", "Device Trust", "Purpose of Payment"],
});

export const scenarioCorridors: readonly ScenarioCorridor[] = [
  ...["DR Congo", "Burundi", "Rwanda", "Uganda", "Kenya", "Tanzania", "Zambia", "Zimbabwe", "Malawi", "Nigeria", "Ghana", "South Africa", "India", "Philippines", "Indonesia", "Vietnam", "Nepal"].map((toCountry) => corridor("Australia", toCountry)),
  ...["DR Congo", "Burundi", "Rwanda", "Uganda", "Kenya", "Tanzania", "Zambia", "Zimbabwe", "Malawi", "Nigeria", "Ghana", "South Africa", "Mexico", "India", "Pakistan", "Philippines", "Vietnam"].map((toCountry) => corridor("United States", toCountry)),
  ...["DR Congo", "Burundi", "Rwanda", "Uganda", "Kenya", "Tanzania", "Zambia", "Zimbabwe", "Malawi", "Nigeria", "Ghana", "South Africa", "India", "Pakistan", "Philippines", "Nepal", "Bangladesh"].map((toCountry) => corridor("Canada", toCountry)),
  ...["DR Congo", "Burundi", "Rwanda", "Uganda", "Kenya", "Tanzania", "Zambia", "Zimbabwe", "Malawi", "Nigeria", "Ghana", "South Africa", "India", "Pakistan", "Bangladesh", "Sri Lanka", "Nepal"].map((toCountry) => corridor("United Kingdom", toCountry)),
  corridor("France", "DR Congo"),
  corridor("Belgium", "DR Congo"),
  corridor("Germany", "DR Congo"),
  corridor("Netherlands", "DR Congo"),
  corridor("Italy", "DR Congo"),
  corridor("Spain", "DR Congo"),
  corridor("Portugal", "Angola"),
  corridor("Belgium", "Rwanda"),
  corridor("France", "Burundi"),
  corridor("Germany", "Nigeria"),
  corridor("United Arab Emirates", "India"),
  corridor("United Arab Emirates", "Pakistan"),
  corridor("United Arab Emirates", "Philippines"),
  corridor("United Arab Emirates", "Kenya"),
  corridor("United Arab Emirates", "Uganda"),
  corridor("Qatar", "Nepal"),
  corridor("Saudi Arabia", "Bangladesh"),
  corridor("Kuwait", "India"),
  corridor("Oman", "Pakistan"),
  corridor("South Africa", "Zimbabwe"),
  corridor("South Africa", "Malawi"),
  corridor("South Africa", "Zambia"),
  corridor("Kenya", "Uganda"),
  corridor("Kenya", "Tanzania"),
  corridor("Uganda", "Rwanda"),
  corridor("Burundi", "DR Congo"),
  corridor("Rwanda", "DR Congo"),
  corridor("Nigeria", "Ghana"),
  corridor("Ghana", "Nigeria"),
];

export type ScenarioDomainTarget = Readonly<{
  domain: ScenarioRegistryDomain;
  target: number;
  subdomains: readonly string[];
}>;

export const scenarioDomainTargets: readonly ScenarioDomainTarget[] = [
  { domain: "Consumer", target: 150, subdomains: ["Remittance", "Wallet", "QR Payments", "Cards", "Savings", "Investments", "Lending", "Insurance", "Bill Payments"] },
  { domain: "Business", target: 120, subdomains: ["Merchant", "SME", "Corporate", "Payroll", "Treasury", "Supplier Payments"] },
  { domain: "Merchant", target: 80, subdomains: ["QR Acceptance", "POS", "Settlement", "Refunds", "Disputes"] },
  { domain: "Wallet", target: 70, subdomains: ["Top-up", "Cash-in", "Cash-out", "Multi-currency", "Limits"] },
  { domain: "Agent Banking", target: 60, subdomains: ["Agent Onboarding", "Cash-in", "Cash-out", "Assisted Transfer", "Float"] },
  { domain: "Government", target: 60, subdomains: ["Fees", "Taxes", "Permits", "Embassy", "Benefits"] },
  { domain: "Compliance", target: 80, subdomains: ["KYC", "AML", "Sanctions", "EDD", "Reporting"] },
  { domain: "Fraud", target: 80, subdomains: ["Account Takeover", "Device Risk", "Velocity", "Social Engineering", "Chargeback"] },
  { domain: "Customer Support", target: 60, subdomains: ["Live Chat", "Voice", "Video", "Disputes", "Recovery"] },
  { domain: "Recovery", target: 40, subdomains: ["Lost Phone", "Disaster", "Offline", "Account Recovery"] },
  { domain: "API Integration", target: 120, subdomains: ["Auth", "Payments", "Webhooks", "Idempotency", "Partner Sandbox"] },
  { domain: "Mobile UI", target: 100, subdomains: ["Onboarding", "Send Money", "Wallet", "Receipts", "Support"] },
  { domain: "Performance", target: 60, subdomains: ["Load", "Spike", "Latency", "Settlement Batch", "Webhook Throughput"] },
  { domain: "Accessibility", target: 40, subdomains: ["Screen Reader", "High Contrast", "Large Text", "Keyboard", "Voice"] },
];

export type EnterpriseScenarioMetadata = Readonly<{
  scenarioId: string;
  version: "2026.1";
  domain: ScenarioRegistryDomain;
  category: string;
  personaId: string;
  corridorId?: string;
  currencies?: string;
  amount?: string;
  receiveMethod?: string;
  riskLevel: "Low" | "Medium" | "High";
  kycLevel: "Basic" | "Standard" | "Enhanced";
  amlRequired: boolean;
  sanctionsCheck: boolean;
  fraudChecks: readonly string[];
  classifications: readonly ScenarioClassification[];
  expectedStatus: "Completed" | "Pending" | "Rejected" | "Manual Review" | "Failed";
  services: readonly NovaTechService[];
  evidence: readonly ScenarioEvidenceArtifact[];
  testSuites: readonly ScenarioTestSuite[];
  automation: boolean;
  uiTest: boolean;
  apiTest: boolean;
  regression: boolean;
}>;

export const enterpriseScenarioRegistrySeed: readonly EnterpriseScenarioMetadata[] = [
  {
    scenarioId: "NP-CONS-001",
    version: "2026.1",
    domain: "Consumer",
    category: "International Transfer",
    personaId: "PER-MIGRANT-WORKER",
    corridorId: "COR-AU-CD",
    currencies: "AUD -> CDF",
    amount: "AUD 500",
    receiveMethod: "Mobile Money",
    riskLevel: "Low",
    kycLevel: "Enhanced",
    amlRequired: true,
    sanctionsCheck: true,
    fraudChecks: ["Device", "Velocity"],
    classifications: ["Happy Path", "Integration"],
    expectedStatus: "Completed",
    services: ["novaid", "novapay", "novatrust"],
    evidence: ["Identity Verified", "KYC Complete", "AML Check", "Sanctions Check", "Device Trust", "Risk Score", "Ledger Entry", "Settlement Record", "Digital Signature", "Replay Evidence", "Audit Package", "PDF Receipt", "Customer Notification"],
    testSuites: ["Unit", "Integration", "API", "UI", "Mobile", "Compliance", "End-to-End", "Regression", "Pilot", "Production Certification"],
    automation: true,
    uiTest: true,
    apiTest: true,
    regression: true,
  },
  {
    scenarioId: "NP-FRAUD-001",
    version: "2026.1",
    domain: "Fraud",
    category: "Suspicious Login Verification",
    personaId: "PER-RETURNING",
    corridorId: "COR-AU-CD",
    riskLevel: "High",
    kycLevel: "Enhanced",
    amlRequired: true,
    sanctionsCheck: true,
    fraudChecks: ["New Device", "Impossible Travel", "Velocity"],
    classifications: ["Fraud", "Security", "Exception", "Negative Testing"],
    expectedStatus: "Manual Review",
    services: ["novaid", "novapay", "novapower", "novatrust"],
    evidence: ["Identity Verified", "Device Trust", "Risk Score", "Operator Log", "Audit Package"],
    testSuites: ["Integration", "API", "Security", "Compliance", "Regression", "Production Certification"],
    automation: true,
    uiTest: true,
    apiTest: true,
    regression: true,
  },
  {
    scenarioId: "NP-API-001",
    version: "2026.1",
    domain: "API Integration",
    category: "Payment Webhook Idempotency",
    personaId: "PER-CORP-FINANCE",
    riskLevel: "Medium",
    kycLevel: "Enhanced",
    amlRequired: true,
    sanctionsCheck: true,
    fraudChecks: ["Webhook Signature", "Duplicate Event"],
    classifications: ["Integration", "Boundary Testing", "Negative Testing"],
    expectedStatus: "Completed",
    services: ["novapay", "novatrust"],
    evidence: ["Ledger Entry", "Settlement Record", "Digital Signature", "Replay Evidence", "Operator Log"],
    testSuites: ["Unit", "Integration", "API", "Performance", "Security", "Regression", "Production Certification"],
    automation: true,
    uiTest: false,
    apiTest: true,
    regression: true,
  },
];

export const scenarioRegistrySummary = {
  name: "NovaTech Enterprise Scenario Registry",
  version: "2026.1",
  totalTarget: scenarioDomainTargets.reduce((sum, item) => sum + item.target, 0),
  personaCount: scenarioPersonas.length,
  corridorCount: scenarioCorridors.length,
  classificationCount: 14,
  testSuiteCount: 13,
  evidenceArtifactCount: 14,
  currentDocumentedJourneys:
    novaTechScenarioCatalog.length + novapayConsumerScenarioCatalog.length + novapayConsumerFeatureScenarios.length,
} as const;
