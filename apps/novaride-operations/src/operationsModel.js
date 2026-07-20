export const operationsSections = [
  {
    key: "overview",
    label: "Overview",
    summary: "Live service health, dispatch posture, and active escalation count.",
    metrics: [
      { label: "Active rides", value: "184" },
      { label: "Available drivers", value: "61" },
      { label: "Dispatch latency", value: "3.1s" },
      { label: "Safety alerts", value: "2" },
    ],
    actions: ["Open incident", "Pause region", "Broadcast status"],
  },
  {
    key: "incidents",
    label: "Incidents",
    summary: "Staffed incident queue with command assignment and mitigation controls.",
    metrics: [
      { label: "Open incidents", value: "4" },
      { label: "Critical", value: "1" },
      { label: "Assigned", value: "3" },
      { label: "Postmortems", value: "12" },
    ],
    actions: ["Assign commander", "Freeze pricing", "Notify riders"],
  },
  {
    key: "safety",
    label: "Safety",
    summary: "SOS monitoring, trip risk review, and evidence preservation.",
    metrics: [
      { label: "SOS queue", value: "0 waiting" },
      { label: "Trips under watch", value: "6" },
      { label: "Evidence locked", value: "31" },
      { label: "Escalations", value: "1" },
    ],
    actions: ["Acknowledge SOS", "Preserve evidence", "Escalate support"],
  },
  {
    key: "support",
    label: "Support",
    summary: "Trip search, refund workflow, and resolution history.",
    metrics: [
      { label: "Open cases", value: "29" },
      { label: "Refunds pending", value: "7" },
      { label: "Median response", value: "4m" },
      { label: "Escalated cases", value: "3" },
    ],
    actions: ["Search rider", "Issue refund", "Escalate dispute"],
  },
  {
    key: "payments",
    label: "Payments",
    summary: "Settlement posture, duplicate-charge controls, and reconciliation.",
    metrics: [
      { label: "Captured today", value: "AUD 12.8k" },
      { label: "Unmatched", value: "2" },
      { label: "Payout failures", value: "0" },
      { label: "Reconciled", value: "99.9%" },
    ],
    actions: ["Review ledger", "Retry payout", "Open adjustment"],
  },
  {
    key: "evidence",
    label: "Evidence",
    summary: "Traceable ride evidence, timeline replay, and audit exports.",
    metrics: [
      { label: "Signed rides", value: "178" },
      { label: "Replay gaps", value: "0" },
      { label: "Exports", value: "12" },
      { label: "Legal holds", value: "1" },
    ],
    actions: ["View replay", "Export evidence", "Apply legal hold"],
  },
];

export const operationsQueues = {
  overview: [
    {
      id: "OV-9001",
      title: "Morning dispatch review",
      severity: "Medium",
      state: "Monitoring",
      owner: "Operations lead",
    },
    {
      id: "OV-9002",
      title: "Region health check",
      severity: "Low",
      state: "Healthy",
      owner: "Platform support",
    },
  ],
  incidents: [
    {
      id: "INC-2041",
      title: "Airport queue surge",
      severity: "High",
      state: "Mitigating",
      owner: "Operations lead",
    },
    {
      id: "INC-2042",
      title: "Driver no-show spike",
      severity: "Medium",
      state: "Investigating",
      owner: "Support lead",
    },
  ],
  safety: [
    {
      id: "SAFE-1103",
      title: "Ride deviation alert",
      severity: "High",
      state: "Acknowledged",
      owner: "Safety reviewer",
    },
    {
      id: "SAFE-1104",
      title: "Trusted contact escalation",
      severity: "Critical",
      state: "In progress",
      owner: "Safety commander",
    },
  ],
  support: [
    {
      id: "CASE-8811",
      title: "Refund request",
      severity: "Medium",
      state: "Awaiting approval",
      owner: "Support agent",
    },
    {
      id: "CASE-8812",
      title: "Lost property",
      severity: "Low",
      state: "Open",
      owner: "Support queue",
    },
  ],
  evidence: [
    {
      id: "EV-3101",
      title: "Ride replay package",
      severity: "Low",
      state: "Signed",
      owner: "Evidence service",
    },
    {
      id: "EV-3102",
      title: "Payment reconciliation",
      severity: "Medium",
      state: "Awaiting review",
      owner: "Finance",
    },
  ],
};

export function getOperationsSection(key) {
  return operationsSections.find((section) => section.key === key) || operationsSections[0];
}
