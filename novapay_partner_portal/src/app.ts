export const portal = {
  name: "NovaPay Partner",
  route: "/partners",
  role: "partner",
  features: ["Partner Onboarding", "API Keys", "Settlement Accounts", "Partner Reports", "Webhook Management", "Integration Status"],
} as const;
export const render = () => `<main aria-label="${portal.name}"><h1>${portal.name}</h1>${portal.features.map((feature) => `<button aria-label="Open ${feature}">${feature}</button>`).join("")}</main>`;
