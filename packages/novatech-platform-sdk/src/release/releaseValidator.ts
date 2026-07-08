import { releaseStageById, releaseStageIndex, type ReleasePaymentMode, type ReleaseStageId } from "./releaseStage";

export type ReleaseReadinessStatus = "PASS" | "REVIEW" | "BLOCKED" | "FAIL";

export type ReleaseRuntimeConfiguration = Readonly<{
  releaseStage: ReleaseStageId;
  gaEnabled: boolean;
  prrRequired: boolean;
  paymentMode: ReleasePaymentMode;
  productionCredentialsAllowed: boolean;
  activationGates: Readonly<Record<string, boolean>>;
  readiness: Readonly<Record<string, ReleaseReadinessStatus>>;
}>;

export type ReleaseValidationIssue = Readonly<{
  field?: string;
  message: string;
}>;

export const validateReleaseConfiguration = (configuration: ReleaseRuntimeConfiguration): ReleaseValidationIssue[] => {
  const issues: ReleaseValidationIssue[] = [];
  const stage = releaseStageById(configuration.releaseStage);
  if (stage.id !== configuration.releaseStage) {
    issues.push({ field: "releaseStage", message: "invalid release stage" });
  }
  if (configuration.gaEnabled && !configuration.prrRequired) {
    issues.push({ field: "prrRequired", message: "GA requires PRR" });
  }
  if (configuration.releaseStage === "GENERAL_AVAILABILITY" && !configuration.gaEnabled) {
    issues.push({ field: "gaEnabled", message: "GA stage requires GA enabled" });
  }
  if (configuration.releaseStage === "PUBLIC_PILOT" && configuration.gaEnabled) {
    issues.push({ field: "gaEnabled", message: "public pilot must keep GA disabled" });
  }
  if (configuration.releaseStage === "PUBLIC_PILOT" && releaseStageIndex("PUBLIC_PILOT") < 0) {
    issues.push({ field: "releaseStage", message: "public pilot stage missing from registry" });
  }
  if (!stage.allowedPaymentModes.includes(configuration.paymentMode)) {
    issues.push({
      field: "paymentMode",
      message: `payment mode ${configuration.paymentMode} not allowed for stage ${stage.id}`,
    });
  }
  if (!configuration.productionCredentialsAllowed && configuration.releaseStage === "GLOBAL_MULTI_REGION_PLATFORM") {
    issues.push({ field: "productionCredentialsAllowed", message: "global platform requires production credentials" });
  }
  if (Object.keys(configuration.activationGates).length === 0) {
    issues.push({ field: "activationGates", message: "activation gates must be defined" });
  }
  if (Object.keys(configuration.readiness).length === 0) {
    issues.push({ field: "readiness", message: "readiness domains must be defined" });
  }
  return issues;
};

