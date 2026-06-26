export const PROTOCOL_HASH_VERSION = "v1";
export const SIGNED_MESSAGE_PREFIX = "NOVATECH";

export function canonicalizeProtocolValue(value) {
  if (value === null || value === undefined) {
    return null;
  }

  if (Array.isArray(value)) {
    return value.map((item) => canonicalizeProtocolValue(item));
  }

  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value.toISOString();
  }

  if (value instanceof Map) {
    const entries = Array.from(value.entries()).map(([key, entryValue]) => [
      canonicalizeProtocolValue(key),
      canonicalizeProtocolValue(entryValue),
    ]);
    entries.sort((left, right) => {
      const leftKey = JSON.stringify(left[0]);
      const rightKey = JSON.stringify(right[0]);
      if (leftKey < rightKey) return -1;
      if (leftKey > rightKey) return 1;
      return 0;
    });
    return Object.fromEntries(entries);
  }

  if (value instanceof Set) {
    return Array.from(value.values())
      .map((item) => canonicalizeProtocolValue(item))
      .sort((left, right) => {
        const leftKey = JSON.stringify(left);
        const rightKey = JSON.stringify(right);
        if (leftKey < rightKey) return -1;
        if (leftKey > rightKey) return 1;
        return 0;
      });
  }

  if (typeof value === "object") {
    const output = {};
    for (const key of Object.keys(value).sort()) {
      output[key] = canonicalizeProtocolValue(value[key]);
    }
    return output;
  }

  return value;
}

export function formatSignedMessage(domain, payloadHash) {
  return `${SIGNED_MESSAGE_PREFIX}::${domain}::${payloadHash}`;
}
