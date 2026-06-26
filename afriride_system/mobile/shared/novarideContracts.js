export const RUNTIME_CONTRACT = {
  name: "NovaRuntimeContract",
  version: "1.0.0",
  domain: "runtime",
};

export const EVENT_CONTRACT = {
  name: "NovaEventContract",
  version: "1.0.0",
  domain: "events",
};

export const PROJECTION_CONTRACT = {
  name: "NovaProjectionContract",
  version: "1.0.0",
  domain: "projection",
};

export const PLUGIN_CONTRACT = {
  name: "NovaPluginContract",
  version: "1.0.0",
  domain: "plugin",
};

export const TWIN_CONTRACT = {
  name: "NovaTwinContract",
  version: "1.0.0",
  domain: "digital-twin",
};

export const COMMAND_CONTRACT = {
  name: "NovaCommandContract",
  version: "1.0.0",
  domain: "command",
};

export function normalizeContract(contract = {}) {
  return {
    name: contract.name || "UnknownContract",
    version: contract.version || "1.0.0",
    domain: contract.domain || "general",
    revision: contract.revision || 1,
  };
}

export function createRuntimeContracts() {
  return {
    runtime: normalizeContract(RUNTIME_CONTRACT),
    event: normalizeContract(EVENT_CONTRACT),
    projection: normalizeContract(PROJECTION_CONTRACT),
    plugin: normalizeContract(PLUGIN_CONTRACT),
    twin: normalizeContract(TWIN_CONTRACT),
    command: normalizeContract(COMMAND_CONTRACT),
  };
}

export function createPlatformContracts() {
  return createRuntimeContracts();
}

export function validateContractCompatibility(expected, actual) {
  const left = normalizeContract(expected);
  const right = normalizeContract(actual);
  return left.name === right.name && left.version === right.version;
}
