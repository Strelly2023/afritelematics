export const portal = {
  name: "NovaPay Operations",
  route: "/operations",
  role: "operator",
  features: ["Live Transactions", "Failed Payments", "Settlement Monitoring", "Agent Monitoring", "Merchant Monitoring", "Fraud Alerts", "Customer Support Handoff", "System Health"],
} as const;
export const render = () => `<main aria-label="${portal.name}"><h1>${portal.name}</h1>${portal.features.map((feature) => `<button aria-label="Open ${feature}">${feature}</button>`).join("")}</main>`;
