import { Credential } from "../models";

const now = () => new Date().toISOString();

export async function issueMockCredential(
  type: Credential["type"],
  label: string,
  issuer: string,
): Promise<Credential> {
  return {
    id: `${type}-${Math.random().toString(36).slice(2, 8)}`,
    type,
    label,
    issuer,
    status: "verified",
    issuedAt: now(),
  };
}

export async function revokeMockCredential(credential: Credential): Promise<Credential> {
  return {
    ...credential,
    status: "revoked",
  };
}
