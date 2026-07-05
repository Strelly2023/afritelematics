import { ConsentGrant } from "../models";

const now = () => new Date().toISOString();

export async function createConsentGrant(
  subjectId: string,
  requester: string,
  credentialId: string,
  attributes: string[],
): Promise<ConsentGrant> {
  return {
    id: `consent-${Math.random().toString(36).slice(2, 8)}`,
    subjectId,
    requester,
    credentialId,
    attributes,
    grantedAt: now(),
    status: "active",
  };
}

export async function revokeConsentGrant(grant: ConsentGrant): Promise<ConsentGrant> {
  return {
    ...grant,
    status: "revoked",
    revokedAt: now(),
  };
}
