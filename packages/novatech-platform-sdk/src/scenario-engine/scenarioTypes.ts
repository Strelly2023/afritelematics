export type ScenarioDomain =
  | "Consumer Remittance"
  | "Wallet Operations"
  | "Merchant Payments"
  | "Business Payments"
  | "Agent Banking"
  | "Cards"
  | "Savings & Investments"
  | "Lending"
  | "Insurance"
  | "Payroll"
  | "Government Services"
  | "Compliance / AML"
  | "Fraud & Risk"
  | "Customer Support"
  | "Recovery & Disaster"
  | "API / Integration Testing";

export type ScenarioTestType =
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

export type ScenarioRiskLevel = "Low" | "Medium" | "High" | "Critical";

export type Scenario = Readonly<{
  scenarioId: string;
  domain: ScenarioDomain;
  title: string;
  actors: readonly string[];
  productsUsed: readonly string[];
  sharedServicesUsed: readonly string[];
  primaryProductOwner: "NovaID" | "NovaPay" | "NovaRide" | "NovaPower" | "NovaTrust" | "NovaTech Platform";
  userStory: string;
  preconditions: readonly string[];
  workflowSteps: readonly string[];
  expectedOutcome: string;
  evidenceRequired: readonly string[];
  policyChecks: readonly string[];
  uiSurfaces: readonly string[];
  apiSurfaces: readonly string[];
  testType: ScenarioTestType;
  riskLevel: ScenarioRiskLevel;
  complianceTags: readonly string[];
  independenceRule: string;
}>;

export type ScenarioCoverageTarget = Readonly<{
  domain: ScenarioDomain;
  minimum: number;
}>;

export const scenarioRegistryVersion = "2026.1";

export const scenarioCoverageTargets: readonly ScenarioCoverageTarget[] = [
  { domain: "Consumer Remittance", minimum: 100 },
  { domain: "Wallet Operations", minimum: 60 },
  { domain: "Merchant Payments", minimum: 50 },
  { domain: "Business Payments", minimum: 50 },
  { domain: "Agent Banking", minimum: 40 },
  { domain: "Cards", minimum: 40 },
  { domain: "Savings & Investments", minimum: 30 },
  { domain: "Lending", minimum: 30 },
  { domain: "Insurance", minimum: 30 },
  { domain: "Payroll", minimum: 30 },
  { domain: "Government Services", minimum: 40 },
  { domain: "Compliance / AML", minimum: 60 },
  { domain: "Fraud & Risk", minimum: 60 },
  { domain: "Customer Support", minimum: 40 },
  { domain: "Recovery & Disaster", minimum: 30 },
  { domain: "API / Integration Testing", minimum: 100 },
];
