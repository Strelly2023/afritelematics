import type { NovaPayRoleConfig } from "./roleApp";

export const config: NovaPayRoleConfig = {
  appName: "NovaPay Consumer",
  role: "consumer",
  balanceLabel: "Wallet balance",
  balance: "AUD 2,480.50",
  tabs: ["Home", "Pay", "Activity", "Cards", "Profile"],
  primaryFlows: ["Send Money", "Receive Money", "QR Pay", "Bank Transfer"],
  features: [
    "Wallet Balance", "Send Money", "Receive Money", "QR Pay", "Bank Transfer",
    "Mobile Money", "International Transfer", "Bills", "Airtime/Data", "Cards",
    "Savings", "Receipts", "Activity", "Security Center", "Support", "AI Assistant",
  ],
};
