export const portal = {
  name: "NovaPay Finance",
  route: "/finance",
  role: "finance",
  features: ["Settlement Reconciliation", "Ledger Balancing", "Fees", "Commissions", "Treasury View", "Bank Settlement Exports", "Revenue Reports"],
} as const;
export const render = () => `<main aria-label="${portal.name}"><h1>${portal.name}</h1>${portal.features.map((feature) => `<button aria-label="Open ${feature}">${feature}</button>`).join("")}</main>`;
