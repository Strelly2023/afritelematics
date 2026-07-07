import { apiIntegrationTestingCatalog } from "./catalogs/apiIntegrationTesting";
import { agentBankingCatalog } from "./catalogs/agentBanking";
import { businessPaymentsCatalog } from "./catalogs/businessPayments";
import { cardsCatalog } from "./catalogs/cards";
import { complianceAmlCatalog } from "./catalogs/complianceAml";
import { consumerRemittanceCatalog } from "./catalogs/consumerRemittance";
import { customerSupportCatalog } from "./catalogs/customerSupport";
import { fraudRiskCatalog } from "./catalogs/fraudRisk";
import { governmentServicesCatalog } from "./catalogs/governmentServices";
import { insuranceCatalog } from "./catalogs/insurance";
import { lendingCatalog } from "./catalogs/lending";
import { merchantPaymentsCatalog } from "./catalogs/merchantPayments";
import { payrollCatalog } from "./catalogs/payroll";
import { recoveryDisasterCatalog } from "./catalogs/recoveryDisaster";
import { savingsInvestmentsCatalog } from "./catalogs/savingsInvestments";
import { walletOperationsCatalog } from "./catalogs/walletOperations";
import type { Scenario } from "./scenarioTypes";

export const scenarioDomainCatalogs = {
  "Consumer Remittance": consumerRemittanceCatalog,
  "Wallet Operations": walletOperationsCatalog,
  "Merchant Payments": merchantPaymentsCatalog,
  "Business Payments": businessPaymentsCatalog,
  "Agent Banking": agentBankingCatalog,
  "Cards": cardsCatalog,
  "Savings & Investments": savingsInvestmentsCatalog,
  "Lending": lendingCatalog,
  "Insurance": insuranceCatalog,
  "Payroll": payrollCatalog,
  "Government Services": governmentServicesCatalog,
  "Compliance / AML": complianceAmlCatalog,
  "Fraud & Risk": fraudRiskCatalog,
  "Customer Support": customerSupportCatalog,
  "Recovery & Disaster": recoveryDisasterCatalog,
  "API / Integration Testing": apiIntegrationTestingCatalog,
} as const;

export const scenarioCatalog: readonly Scenario[] = Object.values(scenarioDomainCatalogs).flat();

export const scenarioCatalogByDomain = (domain: keyof typeof scenarioDomainCatalogs): readonly Scenario[] =>
  scenarioDomainCatalogs[domain];

export const scenarioLibrarySummary = {
  total: scenarioCatalog.length,
  domains: Object.fromEntries(
    Object.entries(scenarioDomainCatalogs).map(([domain, catalog]) => [domain, catalog.length]),
  ) as Record<keyof typeof scenarioDomainCatalogs, number>,
} as const;
