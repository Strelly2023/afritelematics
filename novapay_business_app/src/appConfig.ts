import type { NovaPayRoleConfig } from "./roleApp";
export const config: NovaPayRoleConfig = {
  appName: "NovaPay Business",
  role: "business",
  balanceLabel: "Business wallet",
  balance: "AUD 248,090.20",
  tabs: ["Overview", "Payments", "Approvals", "Reports", "Team"],
  primaryFlows: ["Bulk Payments", "Payroll", "Supplier Payments", "Approvals"],
  features: [
    "Business Wallet", "Bulk Payments", "Payroll", "Supplier Payments", "Invoices",
    "Approvals", "Expense Cards", "Multi-user Roles", "Statements", "Audit Trail",
  ],
};
