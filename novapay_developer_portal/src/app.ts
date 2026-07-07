export const portal = {
  name: "NovaPay Developer",
  route: "/developers",
  role: "developer",
  features: ["API Documentation", "Sandbox", "OAuth Clients", "Webhooks", "SDK Examples", "API Analytics", "Test Transactions"],
} as const;
export const render = () => `<main aria-label="${portal.name}"><h1>${portal.name}</h1>${portal.features.map((feature) => `<button aria-label="Open ${feature}">${feature}</button>`).join("")}</main>`;
