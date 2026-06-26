import { createTrustRuntime } from "./novarideRuntime";

export function createPlatformTrustRuntime(seed = {}) {
  const trust = createTrustRuntime(seed);

  return {
    trust,
    ingestContext(context = {}, projection = {}) {
      const nodeId = context.user?.id || context.actor || "platform";
      const node = trust.upsertNode(nodeId, {
        trust: Number(context.trust?.score || 0),
        risk: Math.max(0, 100 - Number(context.trust?.score || 0)),
        confidence: Number(projection.confidence || context.environment?.confidence || 0),
        evidence: context.trust?.evidence ? [context.trust.evidence] : [],
        status: context.mission?.online ? "online" : "offline",
      });

      trust.upsertNode("platform", {
        trust: Number(context.trust?.score || 0),
        risk: context.telemetry?.guards || 0,
        confidence: Number(projection.confidence || 0),
        status: projection.offlineReady ? "degraded" : "healthy",
      });

      trust.relate(nodeId, "platform", {
        trust: Number(context.trust?.score || 0),
        risk: Math.max(0, 100 - Number(context.trust?.score || 0)),
        confidence: Number(projection.confidence || 0),
        evidence: context.trust?.evidence ? [context.trust.evidence] : [],
      });

      return {
        node,
        snapshot: trust.snapshot(),
      };
    },
  };
}
