export const portal={
  name:"NovaRide Fleet Manager",
  role:"fleet_manager",
  channel:"web",
  features:[
    "Live Rides Map",
    "Dispatch Queue",
    "Driver roster",
    "Vehicle roster",
    "Driver Lookup",
    "Driver to vehicle assignment",
    "Compliance status",
    "Vehicle Compliance",
    "Document expiry",
    "Maintenance tracking",
    "Active trips",
    "Availability freshness",
    "Incident alerts",
    "City Operations",
    "Trust Alerts",
    "Earnings summaries",
    "Audit history",
    "Performance Analytics",
    "Evidence Package Review",
  ]
} as const;
export const render=()=>`<main aria-label="${portal.name}"><h1>${portal.name}</h1><p>authenticated web portal · secure web product · secure online access only</p>${portal.features.map(feature=>`<button aria-label="Open ${feature}">${feature}</button>`).join("")}</main>`;
