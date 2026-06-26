// Generated from afritech/platform_contracts/platform.yaml. Do not hand-edit.
export const versionVector = {
  platform: "2.0.0", contract: "2.0.0", schema: "1.0.0",
  api: "1.0.0", replay: "1.0.0", evidence: "1.0.0", signature: "1.0.0",
} as const;

export type TrustLevel = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export interface GovernedRequest<T extends object = Record<string, unknown>> {
  request_id: string;
  operation: string;
  tenant_id: string;
  actor_id: string;
  idempotency_key: string;
  contract_version: typeof versionVector.contract;
  schema_version: typeof versionVector.schema;
  payload: T;
}
