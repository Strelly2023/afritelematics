import { DigitalCertificate } from "../models";

const now = () => new Date().toISOString();

export async function issueDigitalCertificate(
  subjectId: string,
  title: string,
  scope: string[],
): Promise<DigitalCertificate> {
  return {
    id: `cert-${Math.random().toString(36).slice(2, 8)}`,
    subjectId,
    title,
    issuer: "NovaID Authority",
    issuedAt: now(),
    sealHash: `seal-${Math.random().toString(36).slice(2, 10)}`,
    replayHash: `replay-${Math.random().toString(36).slice(2, 10)}`,
    status: "verified",
    scope,
  };
}
