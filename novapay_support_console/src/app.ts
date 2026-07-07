export const portal = {
  name: "NovaPay Support",
  route: "/support",
  role: "support",
  features: ["Customer Search", "Transaction Lookup", "Dispute Handling", "Refund Requests", "Ticket History", "Account Recovery", "Support Notes"],
} as const;
export const render = () => `<main aria-label="${portal.name}"><h1>${portal.name}</h1>${portal.features.map((feature) => `<button aria-label="Open ${feature}">${feature}</button>`).join("")}</main>`;
