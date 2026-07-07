import type { NovaPayRoleConfig } from "./roleApp";
export const config: NovaPayRoleConfig = {
  appName: "NovaPay Merchant",
  role: "merchant",
  balanceLabel: "Available settlement",
  balance: "AUD 18,420.00",
  tabs: ["Dashboard", "Collect", "Sales", "Settlements", "More"],
  primaryFlows: ["QR Collections", "POS Payments", "Payment Links", "Refunds"],
  features: [
    "Merchant Dashboard", "QR Collections", "POS Payments", "Payment Links", "Refunds",
    "Settlements", "Sales Reports", "Staff Access", "Disputes", "Customer Receipts",
  ],
};
