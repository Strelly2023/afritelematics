export type NovapayVerificationLevel = Readonly<{
  level: number;
  description: string;
}>;

export const novapayConsumerVerificationLevels: readonly NovapayVerificationLevel[] = [
  { level: 0, description: "Account created" },
  { level: 1, description: "Email and phone verified" },
  { level: 2, description: "Government ID verified" },
  { level: 3, description: "Enhanced KYC" },
  { level: 4, description: "Full regulated financial services access" },
] as const;

export const novapayAgentVerificationLevels: readonly NovapayVerificationLevel[] = [
  { level: 0, description: "Application submitted" },
  { level: 1, description: "Identity verified" },
  { level: 2, description: "Business and location verified" },
  { level: 3, description: "Settlement, float, and compliance approved" },
  { level: 4, description: "Full agent operations authorized" },
] as const;

export const novapayVerificationLevelMap = {
  consumer: Object.fromEntries(novapayConsumerVerificationLevels.map((item) => [item.level, item.description])),
  agent: Object.fromEntries(novapayAgentVerificationLevels.map((item) => [item.level, item.description])),
} as const;
