import type { NovaPayRoleConfig } from "./roleApp";

export const legacyBusinessTabs = ["Overview", "Payments", "Approvals", "Reports", "Team"] as const;
export const legacyBusinessFlows = ["Bulk Payments", "Payroll", "Supplier Payments", "Approvals"] as const;

export const config: NovaPayRoleConfig = {
  appName: "NovaPay Business",
  role: "business",
  balanceLabel: "Business wallet",
  balance: "AUD 248,090.20",
  tabs: ["Overview", "Wallets", "Payments", "Approvals", "Invoices", "Payroll", "Reports", "Settings"],
  primaryFlows: ["Pay supplier", "Bulk payment", "Bank transfer", "Schedule payment"],
  features: [
    "Business Wallet", "Department Wallets", "Bulk Payments", "Payroll", "Supplier Payments",
    "Invoices", "Approvals", "Expense Cards", "Multi-user Roles", "Statements", "Audit Trail",
  ],
  sections: [
    {
      title: "Overview",
      description: "Balance, cashflow, approvals, and compliance.",
      buttons: [
        "View business balance",
        "View cashflow",
        "View pending approvals",
        "View recent payments",
        "View compliance alerts",
        "Export overview",
      ],
    },
    {
      title: "Wallets",
      description: "Department wallets and spending controls.",
      buttons: [
        "Create department wallet",
        "View wallet",
        "Transfer between wallets",
        "Set spending limit",
        "Freeze wallet",
        "Assign wallet manager",
        "View wallet statement",
      ],
    },
    {
      title: "Payments",
      description: "Supplier, payroll, and international payment execution.",
      buttons: [
        "Pay supplier",
        "Bulk payment",
        "Bank transfer",
        "Mobile money transfer",
        "International payment",
        "Schedule payment",
        "Review payment",
        "Submit for approval",
      ],
    },
    {
      title: "Approvals",
      description: "Governed payment approval chain.",
      buttons: [
        "Approve payment",
        "Reject payment",
        "Request changes",
        "View approval chain",
        "Escalate approval",
        "Add approval comment",
      ],
    },
    {
      title: "Invoices",
      description: "Invoice creation, reminders, and payment tracking.",
      buttons: [
        "Create invoice",
        "Send invoice",
        "View invoice",
        "Mark as paid",
        "Send reminder",
        "Cancel invoice",
        "Download invoice PDF",
      ],
    },
    {
      title: "Payroll",
      description: "Payroll upload, review, and release.",
      buttons: [
        "Upload payroll file",
        "Add employee payment",
        "Review payroll",
        "Approve payroll",
        "Run payroll",
        "Download payroll report",
      ],
    },
    {
      title: "Reports",
      description: "Statements, audit exports, and activity reporting.",
      buttons: [
        "Transaction report",
        "Settlement report",
        "Tax report",
        "Audit report",
        "User activity report",
        "Export CSV",
        "Export PDF",
      ],
    },
    {
      title: "Settings",
      description: "Business profile, users, permissions, and API control.",
      buttons: [
        "Manage business profile",
        "Verify NovaID Business",
        "Manage users",
        "Manage roles",
        "Manage permissions",
        "Manage API keys",
        "Manage webhooks",
        "Manage bank accounts",
        "Security settings",
        "Logout",
      ],
    },
  ],
};
