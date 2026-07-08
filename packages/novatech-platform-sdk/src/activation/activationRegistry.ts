import { activationGateDefinitions } from "./activationGate";

export const activationRegistry = {
  gates: activationGateDefinitions,
  gateIds: activationGateDefinitions.map((gate) => gate.gateId),
} as const;

