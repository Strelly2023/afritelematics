import { InspectionRecord } from "../models";

const now = () => new Date().toISOString();

export async function saveInspection(
  inspectorId: string,
  credentialId: string,
  offlineMode: boolean,
): Promise<InspectionRecord> {
  return {
    id: `inspection-${Math.random().toString(36).slice(2, 8)}`,
    inspectorId,
    credentialId,
    result: "verified",
    offlineMode,
    savedAt: now(),
    syncedAt: offlineMode ? null : now(),
  };
}
