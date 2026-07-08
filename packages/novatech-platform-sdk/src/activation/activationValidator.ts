import { activationGateDefinitions, type ActivationGateId } from "./activationGate";

export type ActivationGateRuntime = Readonly<Record<ActivationGateId, boolean>>;

export type ActivationValidationIssue = Readonly<{
  gateId?: ActivationGateId;
  message: string;
}>;

export const validateActivationGates = (gates: ActivationGateRuntime): ActivationValidationIssue[] => {
  const issues: ActivationValidationIssue[] = [];
  for (const definition of activationGateDefinitions) {
    const value = gates[definition.gateId];
    if (typeof value !== "boolean") {
      issues.push({ gateId: definition.gateId, message: "missing activation gate value" });
    }
  }
  return issues;
};

