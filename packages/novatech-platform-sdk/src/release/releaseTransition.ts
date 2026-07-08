import { releaseStageIndex, type ReleaseStageId } from "./releaseStage";

export type ReleaseTransition = Readonly<{
  from: ReleaseStageId;
  to: ReleaseStageId;
  approvedBy?: string;
  approvedAt?: string;
  notes?: string;
}>;

export const canTransitionReleaseStage = (from: ReleaseStageId, to: ReleaseStageId): boolean => {
  const fromIndex = releaseStageIndex(from);
  const toIndex = releaseStageIndex(to);
  return fromIndex >= 0 && toIndex >= 0 && toIndex >= fromIndex;
};

export const describeReleaseTransition = (transition: ReleaseTransition): string =>
  `${transition.from} -> ${transition.to}`;

