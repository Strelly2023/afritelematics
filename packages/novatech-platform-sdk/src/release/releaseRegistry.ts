import { releaseStageById, releaseStageOrder, type ReleaseStageId } from "./releaseStage";

export type ReleaseRegistry = Readonly<{
  currentStage: ReleaseStageId;
  stages: readonly ReleaseStageId[];
  currentStageDefinition: ReturnType<typeof releaseStageById>;
}>;

export const defaultReleaseRegistry: ReleaseRegistry = {
  currentStage: "PUBLIC_PILOT",
  stages: releaseStageOrder,
  currentStageDefinition: releaseStageById("PUBLIC_PILOT"),
} as const;

export const releaseRegistry = defaultReleaseRegistry;

