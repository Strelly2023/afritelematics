import { novaIdIdentityTypes } from "./novaIdTypes";

export const novaIdCommonSecurityRequirements = [
  "Email verification",
  "Phone verification",
  "Multi-factor authentication",
  "Device registration",
  "Biometric authentication where supported",
  "Login history",
  "Session management",
  "Passwordless authentication optional",
  "Security alerts",
  "Account recovery",
  "Audit logging",
] as const;

export const novaIdModernStandards = [
  "OAuth 2.0",
  "OpenID Connect",
  "SAML 2.0",
  "WebAuthn",
  "Passkeys",
  "SCIM",
] as const;

export const novaIdRequirements = {
  identityTypes: novaIdIdentityTypes,
  commonSecurityRequirements: novaIdCommonSecurityRequirements,
  standards: novaIdModernStandards,
} as const;
