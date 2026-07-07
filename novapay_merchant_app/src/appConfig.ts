import type { NovaPayRoleConfig } from "./roleApp";

export const legacyMerchantTabs = ["Dashboard", "Collect", "Sales", "Settlements", "More"] as const;
export const legacyMerchantFlows = ["QR Collections", "POS Payments", "Payment Links", "Refunds"] as const;

export const config: NovaPayRoleConfig = {
  appName: "NovaPay Merchant",
  role: "merchant",
  balanceLabel: "Available settlement",
  balance: "AUD 18,420.00",
  tabs: ["Dashboard", "Accept Payment", "Sales", "Refunds", "Settlements", "Products", "Profile"],
  primaryFlows: ["Show merchant QR", "Enter amount", "Create payment request", "Scan customer QR"],
  features: [
    "Merchant Dashboard", "Show Merchant QR", "Accept Payment", "Payment Request", "Refunds",
    "Settlements", "Sales Reports", "Staff Access", "Disputes", "Customer Receipts", "Inventory",
  ],
  sections: [
    {
      title: "Dashboard",
      description: "Today’s sales, settlement status, and support.",
      buttons: [
        "View today sales",
        "View pending settlement",
        "View QR code",
        "Accept payment",
        "Create payment link",
        "View alerts",
        "Open support",
      ],
    },
    {
      title: "Accept Payment",
      description: "Merchant checkout and QR collection.",
      buttons: [
        "Show merchant QR",
        "Enter amount",
        "Generate payment request",
        "Scan customer QR",
        "Confirm payment",
        "Print receipt",
        "Share receipt",
        "Cancel request",
      ],
    },
    {
      title: "Sales",
      description: "Sales history and receipts.",
      buttons: [
        "View sale",
        "Search sale",
        "Filter sales",
        "Download receipt",
        "Export sales report",
        "View customer payment",
      ],
    },
    {
      title: "Refunds",
      description: "Governed refund review and approval.",
      buttons: [
        "Search transaction",
        "Review refund",
        "Approve refund",
        "Reject refund",
        "Submit refund reason",
        "Share refund receipt",
      ],
    },
    {
      title: "Settlements",
      description: "Payouts, reconciliation, and bank settlement.",
      buttons: [
        "View settlement balance",
        "View bank settlement",
        "Request settlement",
        "Download settlement report",
        "Reconcile settlement",
      ],
    },
    {
      title: "Products",
      description: "Product catalogue and inventory controls.",
      buttons: [
        "Add product",
        "Edit product",
        "Delete product",
        "Create price list",
        "Generate product QR",
        "Manage inventory",
      ],
    },
    {
      title: "Profile",
      description: "Business identity and security settings.",
      buttons: [
        "Edit merchant profile",
        "Verify NovaID Business",
        "Upload business documents",
        "Manage bank account",
        "Manage staff users",
        "Manage permissions",
        "Security settings",
        "Logout",
      ],
    },
  ],
};
