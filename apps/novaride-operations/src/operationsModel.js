export const operationsSections = [
  { key: "overview", label: "Overview", summary: "Operational summary, dependency health, and recent activity." },
  { key: "map", label: "Live map", summary: "Trip and driver visibility with precision-aware location handling." },
  { key: "trips", label: "Trips", summary: "Live trip list, timelines, and evidence references." },
  { key: "drivers", label: "Drivers", summary: "Online status, dispatch readiness, and region scope." },
  { key: "dispatch", label: "Dispatch", summary: "Queue posture and dispatch health with governed controls." },
  { key: "incidents", label: "Incidents", summary: "Incident lifecycle, assignment, and command history." },
  { key: "safety", label: "Safety", summary: "Safety cases, escalation, and restricted evidence." },
  { key: "support", label: "Support", summary: "Search, case handling, resolution, and audit trails." },
  { key: "refunds", label: "Refunds", summary: "Refund workflow, approvals, execution, and verification." },
  { key: "payments", label: "Payment investigations", summary: "Payment failure review and remediation." },
  { key: "disputes", label: "Disputes", summary: "Decision records, evidence requests, and appeals." },
  { key: "actions", label: "Actions", summary: "Governed operational actions with approvals and verification." },
  { key: "evidence", label: "Evidence", summary: "Evidence search, lifecycle, integrity, and export controls." },
];

export const operationsNavigation = operationsSections.map((section) => section.label);

export function getOperationsSection(key) {
  return operationsSections.find((section) => section.key === key) || operationsSections[0];
}
