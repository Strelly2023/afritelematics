export type NovaIDTypeKey = "personal" | "business" | "employee" | "partner" | "inspector";

export type NovaIDTypeDefinition = Readonly<{
  key: NovaIDTypeKey;
  purpose: string;
  eligibility: readonly string[];
  requiredInformation: readonly string[];
  verificationRequirements: readonly string[];
  securityRequirements: readonly string[];
  allowedRoles: readonly string[];
  trustAttributes: readonly string[];
  verificationLevel: number;
}>;

export const novaIdIdentityTypes: readonly NovaIDTypeDefinition[] = [
  {
    key: "personal",
    purpose: "Digital identity for individual users.",
    eligibility: [
      "Minimum age according to local law",
      "Valid email address",
      "Verified mobile number",
      "Acceptance of Terms of Service and Privacy Policy",
    ],
    requiredInformation: [
      "Full legal name",
      "Date of birth",
      "Gender where permitted",
      "Nationality where required",
      "Residential address",
      "Email address",
      "Mobile number",
    ],
    verificationRequirements: [
      "Government-issued ID",
      "Passport or National ID where available",
      "Selfie/liveness verification",
      "Face matching",
      "Document authenticity verification",
    ],
    securityRequirements: [
      "Multi-factor authentication",
      "Biometric login",
      "Trusted devices",
      "Recovery email",
      "Recovery phone",
    ],
    allowedRoles: ["Personal User", "Consumer", "Rider", "Customer"],
    trustAttributes: [
      "Identity verification",
      "Phone verification",
      "Email verification",
      "Device verification",
    ],
    verificationLevel: 6,
  },
  {
    key: "business",
    purpose: "Digital identity for organizations.",
    eligibility: ["Registered organization", "Authorized representative available", "Compliance review completed"],
    requiredInformation: [
      "Registered business name",
      "Trading name",
      "Business registration number",
      "Tax identification number",
      "Registered office address",
      "Business email",
      "Business phone number",
    ],
    verificationRequirements: [
      "Certificate of incorporation or business registration",
      "Tax registration",
      "Proof of business address",
      "Authorized representative verification",
      "UBO information where required",
    ],
    securityRequirements: ["Organization-level MFA", "RBAC", "Audit logging", "Device management", "Session management"],
    allowedRoles: ["Business Owner", "Administrator", "Finance Manager", "Operations Manager", "Compliance Officer", "Auditor"],
    trustAttributes: ["Identity verification", "Organization verification", "Role verification", "Compliance status", "Device trust"],
    verificationLevel: 5,
  },
  {
    key: "employee",
    purpose: "Workforce identity.",
    eligibility: ["Employee record exists", "Manager or HR sponsor available", "Employment is active"],
    requiredInformation: [
      "Employee ID",
      "Full legal name",
      "Work email",
      "Mobile number",
      "Department",
      "Job title",
      "Employment start date",
    ],
    verificationRequirements: ["HR verification", "Identity verification", "Employment confirmation", "Manager approval"],
    securityRequirements: ["MFA", "Device registration", "Single Sign-On", "Session monitoring", "Access reviews"],
    allowedRoles: ["Employee", "Manager", "Finance Manager", "Operations Staff", "Support Staff"],
    trustAttributes: ["Identity verification", "Employment verification", "Role verification", "Device trust", "Compliance status"],
    verificationLevel: 5,
  },
  {
    key: "partner",
    purpose: "Identity for external organizations and integration partners.",
    eligibility: ["Partner organization is active", "Integration sponsor exists", "Security review can be completed"],
    requiredInformation: [
      "Organization name",
      "Business registration",
      "Contact person",
      "Business address",
      "Official email",
      "Support contacts",
    ],
    verificationRequirements: [
      "Business registration",
      "Tax registration",
      "Authorized representative verification",
      "API security review where applicable",
      "Compliance review",
    ],
    securityRequirements: ["API credentials", "OAuth/OpenID Connect", "IP allow-list optional", "Webhook verification", "Client certificates"],
    allowedRoles: ["Technology Partner", "Payment Provider", "Logistics Partner", "Mobility Partner", "Government Agency", "Merchant"],
    trustAttributes: ["Organization verification", "Role verification", "Compliance status", "Device trust", "Integration trust"],
    verificationLevel: 5,
  },
  {
    key: "inspector",
    purpose: "Identity for compliance, audit, inspection, and regulatory personnel.",
    eligibility: ["Inspector role exists", "Supervisor approval can be granted", "Background checks can be completed where required"],
    requiredInformation: [
      "Full legal name",
      "Employee or inspector ID",
      "Organization",
      "Position",
      "Work email",
      "Mobile number",
    ],
    verificationRequirements: [
      "Identity verification",
      "Employment verification",
      "Professional accreditation where applicable",
      "Supervisor approval",
      "Background screening where required",
    ],
    securityRequirements: ["MFA", "Device registration", "Session management", "Audit logging", "Read-only-by-default permissions"],
    allowedRoles: ["Internal Auditor", "Compliance Officer", "Fleet Inspector", "Vehicle Inspector", "Financial Auditor", "Safety Inspector"],
    trustAttributes: ["Identity verification", "Role verification", "Compliance status", "Device trust", "Audit access"],
    verificationLevel: 6,
  },
] as const;
