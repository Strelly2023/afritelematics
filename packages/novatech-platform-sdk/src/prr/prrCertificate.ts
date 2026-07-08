import type { PRRStatus } from "./prrValidator";

export type PRRCertificate = Readonly<{
  prrId: string;
  status: PRRStatus;
  approvedBy?: string;
  approvedAt?: string;
  stage: "PRODUCTION_READINESS_REVIEW";
  gaAllowed: boolean;
  evidencePackage: readonly string[];
}>;

export const createPRRCertificate = (certificate: PRRCertificate): PRRCertificate => certificate;

