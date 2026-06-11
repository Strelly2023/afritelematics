export const systems = [
  {
    id: "afriride",
    name: "AfriRide",
    domain: "Mobility workflow",
    version: "v0.9.3",
    environment: "Controlled Pilot",
    region: "Melbourne",
    status: "DRIFT_DETECTED",
    drift: {
      id: "DRIFT-0421",
      severity: "HIGH",
      confidence: "0.94",
      contract: "Order must be paid before shipping",
      observed: "Pending -> Shipped",
      expected: "Paid -> Shipped",
      trace: ["OrderCreated", "OrderShipped"],
      proposal: "PROP-1198",
    },
    uml: {
      entity: "Order",
      fields: ["state"],
      states: ["Pending", "Paid", "Shipped"],
    },
    replayTrace: [
      "OrderCreated -> Pending",
      "PaymentProcessed -> Paid",
      "OrderShipped -> Shipped",
    ],
    contracts: [
      "Payment required before shipping",
      "State must be Paid before shipment",
    ],
  },
  {
    id: "agro",
    name: "AgroSolidarite",
    domain: "Poultry operations",
    version: "v0.8.1",
    environment: "Controlled Pilot",
    region: "Kalemie",
    status: "STABLE",
    drift: {
      id: "DRIFT-AGRO-17",
      severity: "OBSERVED",
      confidence: "0.88",
      contract: "Feeding must occur before egg collection",
      observed: "EggCollected before Feeding",
      expected: "Feeding -> EggCollected",
      trace: ["EggCollected", "InventoryUpdated"],
      proposal: "PROP-AGRO-071",
    },
    uml: {
      entity: "EggCollection",
      fields: ["state", "batchId"],
      states: ["Scheduled", "Fed", "Collected"],
    },
    replayTrace: [
      "FeedingScheduled -> Scheduled",
      "FeedDistributed -> Fed",
      "EggCollected -> Collected",
    ],
    contracts: [
      "Feeding required before egg collection",
      "Collection must bind to inventory batch",
    ],
  },
];

export const auditLog = [
  "[14:22:01] Observation received",
  "[14:22:04] Contract drift detected",
  "[14:22:06] Replay proof generated",
  "[14:22:10] Governance proposal prepared",
];

export const aiMessages = {
  dashboard: [
    "Monitoring controlled-pilot systems.",
    "One drift signal requires governance review.",
    "No automatic mutation is permitted.",
  ],
  drift: [
    "Analyzing observed behavior against active contract.",
    "State transition violates expected contract path.",
    "Recommendation: prepare governed proposal.",
  ],
  uml: [
    "Reading UML state model.",
    "Expected transition path is design-derived.",
    "Design remains non-authoritative.",
  ],
  replay: [
    "Synthesizing deterministic replay trace.",
    "Replay shows valid baseline behavior.",
    "Synthetic replay is not runtime truth.",
  ],
  contracts: [
    "Inferring candidate constraints.",
    "Contracts require replay validation.",
    "Enforcement requires governance approval.",
  ],
  proposal: [
    "Packaging replay, contract, and rollback evidence.",
    "Proposal is governance-ready.",
    "Activation remains blocked.",
  ],
  governance: [
    "Validation passed.",
    "Governance approval is the authority boundary.",
    "Approval does not bypass activation checks.",
  ],
  activation: [
    "Checking activation gate.",
    "Validation, governance, and replay must align.",
    "Runtime mutation is allowed only through this gate.",
  ],
  runtime: [
    "Drift marked resolved in the simulated flow.",
    "Replay consistency preserved.",
    "System remains controlled-pilot-ready.",
  ],
};
