import { releaseStageById, type ReleaseStageId, type ReleasePaymentMode } from "./releaseStage";

export type ReleasePolicy = Readonly<{
  stage: ReleaseStageId;
  allowedPaymentModes: readonly ReleasePaymentMode[];
  allowedActivationGates: readonly string[];
  requiredGovernanceArtifacts: readonly string[];
}>;

export const releasePolicyForStage = (stage: ReleaseStageId): ReleasePolicy => {
  const definition = releaseStageById(stage);
  return {
    stage,
    allowedPaymentModes: definition.allowedPaymentModes,
    allowedActivationGates: definition.allowedActivationGates,
    requiredGovernanceArtifacts: definition.requiredGovernanceArtifacts,
  };
};

