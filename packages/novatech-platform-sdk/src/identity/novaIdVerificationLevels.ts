export type NovaIDVerificationLevel = Readonly<{
  level: number;
  description: string;
}>;

export const novaIdVerificationLevels: readonly NovaIDVerificationLevel[] = [
  { level: 0, description: "Account created" },
  { level: 1, description: "Email verified" },
  { level: 2, description: "Phone verified" },
  { level: 3, description: "Government identity verified" },
  { level: 4, description: "Biometric identity verified" },
  { level: 5, description: "Profession or organization verified" },
  { level: 6, description: "Fully trusted identity with continuous compliance monitoring" },
] as const;

export const novaIdVerificationLevelMap = Object.fromEntries(
  novaIdVerificationLevels.map((item) => [item.level, item.description]),
) as Record<number, string>;
