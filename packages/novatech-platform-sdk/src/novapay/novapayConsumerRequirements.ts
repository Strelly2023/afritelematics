export type NovapayConsumerRequirements = Readonly<{
  eligibility: readonly string[];
  personalInformation: readonly string[];
  basicKyc: readonly string[];
  standardKyc: readonly string[];
  enhancedKyc: readonly string[];
  walletSetup: readonly string[];
  securityRequirements: readonly string[];
  consumerServices: readonly string[];
  complianceRules: readonly string[];
  consumerTrustProfile: readonly string[];
  uiTabs: readonly string[];
  uiButtons: Readonly<Record<string, readonly string[]>>;
  apiSurfaces: readonly string[];
  requiresNovaRide: false;
  requiresNovaAI: false;
  advisoryOnly: true;
  novaTrustEvidenceRequired: readonly string[];
}>;

export const novapayConsumerRequirements: NovapayConsumerRequirements = {
  eligibility: [
    "Valid NovaID Personal account",
    "Minimum legal age in the operating jurisdiction",
    "Acceptance of NovaPay Terms of Service and Privacy Policy",
    "Not listed on applicable sanctions or prohibited-persons lists",
  ],
  personalInformation: [
    "Full legal name",
    "Date of birth",
    "Mobile phone number",
    "Email address",
    "Residential address",
    "Nationality where required",
    "Preferred language",
    "Preferred currency",
  ],
  basicKyc: ["Mobile number verification", "Email verification"],
  standardKyc: ["Government-issued ID", "Selfie/liveness verification", "Face matching", "Device registration"],
  enhancedKyc: ["Proof of address", "Source of funds information where required", "Additional due diligence for higher-risk accounts"],
  walletSetup: [
    "NovaPay Wallet ID",
    "QR payment profile",
    "Multi-currency wallet where supported",
    "Wallet limits based on verification level",
    "Transaction history",
    "Digital receipts",
  ],
  securityRequirements: [
    "Multi-factor authentication",
    "Biometric login",
    "Passkeys optional",
    "Trusted device management",
    "Session management",
    "Login alerts",
    "Sensitive action confirmation",
  ],
  consumerServices: [
    "Send money",
    "Receive money",
    "QR payments",
    "Merchant payments",
    "Bill payments",
    "Airtime and data purchases",
    "Bank transfers",
    "Mobile money transfers",
    "International remittance",
    "Wallet top-up",
    "Cash withdrawal via agent",
    "Scheduled payments",
  ],
  complianceRules: ["KYC", "AML/CTF", "Fraud prevention", "Transaction monitoring", "Ongoing verification"],
  consumerTrustProfile: [
    "Identity status",
    "Wallet verification level",
    "Device trust",
    "Fraud risk score",
    "Transaction risk score",
    "Compliance status",
    "Security score",
  ],
  uiTabs: ["Home", "Send", "Receive", "Wallet", "Payments", "History", "Profile"],
  uiButtons: {
    Home: [
      "View wallet balance",
      "Top up wallet",
      "Send money",
      "Receive money",
      "Scan QR",
      "Pay merchant",
      "Pay bill",
      "Buy airtime/data",
      "View recent transactions",
      "Open NovaID verification",
      "Open security center",
    ],
    Send: [
      "Send to NovaPay user",
      "Send to phone number",
      "Send to bank account",
      "Send to mobile money",
      "International transfer",
      "Choose recipient",
      "Enter amount",
      "Add note",
      "Review transfer",
      "Confirm transfer",
      "Cancel transfer",
      "Share receipt",
    ],
    Receive: [
      "Show QR code",
      "Request money",
      "Copy wallet ID",
      "Share payment link",
      "Receive from agent",
      "Receive from bank",
      "Confirm received payment",
    ],
    Wallet: [
      "Top up",
      "Cash out",
      "Link bank account",
      "Link card",
      "Link mobile money",
      "Set default funding source",
      "View limits",
      "Upgrade wallet level",
      "Freeze wallet",
    ],
    Payments: [
      "Scan merchant QR",
      "Pay with QR",
      "Pay bill",
      "Buy airtime",
      "Buy data",
      "Pay school fees",
      "Pay utilities",
      "Schedule payment",
      "Manage recurring payments",
    ],
    History: [
      "View transaction",
      "Download receipt",
      "Share receipt",
      "Report transaction",
      "Dispute transaction",
      "Filter history",
      "Export statement",
    ],
    Profile: [
      "Edit profile",
      "Verify NovaID",
      "Upload ID",
      "Security settings",
      "Change PIN",
      "Enable biometric login",
      "Manage devices",
      "Language settings",
      "Notification settings",
      "Help and support",
      "Logout",
    ],
  },
  apiSurfaces: [
    "/auth/register",
    "/auth/login",
    "/auth/otp/verify",
    "/novaid/verify",
    "/novapay/wallet",
    "/novapay/balance",
    "/novapay/topup",
    "/novapay/transactions",
    "/novapay/receipts",
    "/novapay/refunds",
    "/novapay/disputes",
  ],
  requiresNovaRide: false,
  requiresNovaAI: false,
  advisoryOnly: true,
  novaTrustEvidenceRequired: [
    "Identity Verified",
    "KYC Complete",
    "Ledger Entry",
    "Settlement Record",
    "Digital Signature",
    "Replay Evidence",
    "Audit Package",
    "PDF Receipt",
  ],
};
