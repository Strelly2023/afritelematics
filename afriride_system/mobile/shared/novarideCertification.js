import { validateContractCompatibility } from "./novarideContracts";

function normalizeContracts(value = {}) {
  return {
    runtime: value.runtime || null,
    event: value.event || null,
    projection: value.projection || null,
    plugin: value.plugin || null,
    twin: value.twin || null,
    command: value.command || null,
  };
}

function compatibilityMatrix(left = {}, right = {}) {
  const a = normalizeContracts(left);
  const b = normalizeContracts(right);
  return {
    runtime: validateContractCompatibility(a.runtime, b.runtime),
    event: validateContractCompatibility(a.event, b.event),
    projection: validateContractCompatibility(a.projection, b.projection),
    plugin: validateContractCompatibility(a.plugin, b.plugin),
    twin: validateContractCompatibility(a.twin, b.twin),
    command: validateContractCompatibility(a.command, b.command),
  };
}

export function createRuntimeCertification(runtime = {}) {
  const report = () => {
    const contracts = normalizeContracts(runtime.contracts || {});
    const runtimeHealth = typeof runtime.health === "function" ? runtime.health() : null;
    const metrics = typeof runtime.metrics === "function" ? runtime.metrics() : null;

    return {
      certified: Boolean(runtimeHealth && runtimeHealth.status !== "critical"),
      runtime: {
        id: runtime.runtime?.id || runtime.id || null,
        name: runtime.runtime?.name || runtime.name || null,
        version: runtime.runtime?.version || runtime.version || null,
      },
      checks: {
        contracts: compatibilityMatrix(contracts, contracts),
        health: runtimeHealth,
        metrics,
      },
      issues: [],
    };
  };

  return {
    report,
    self() {
      return report();
    },
    compare(peer = {}) {
      const left = runtime.contracts || {};
      const right = peer.contracts || peer;
      return compatibilityMatrix(left, right);
    },
    against(peer = {}) {
      const compatibility = this.compare(peer);
      return {
        self: report(),
        compatibility,
        certified: Object.values(compatibility).every(Boolean) && report().certified,
      };
    },
    deployment(peer = {}) {
      const comparison = this.compare(peer);
      const selfReport = report();
      const certified = selfReport.certified && Object.values(comparison).every(Boolean);
      return {
        certified,
        self: selfReport,
        comparison,
      };
    },
    validate(otherContracts = {}) {
      return compatibilityMatrix(runtime.contracts || {}, otherContracts || {});
    },
  };
}
