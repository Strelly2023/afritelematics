const CANONICAL_MARKER = Symbol("afritelematics.canonical");

export function stableCanonicalize(value, path = new WeakMap()) {
  const RESERVED_TYPE_KEY = "\u0000type";
  const RESERVED_VALUE_KEY = "\u0000value";
  const TYPE_ORDER = {
    null: 0,
    boolean: 1,
    number: 2,
    bigint: 3,
    string: 4,
    symbol: 5,
    array: 6,
    object: 7,
  };

  const makeTaggedValue = (type, value) => {
    const tagged = Object.create(null);
    tagged[RESERVED_TYPE_KEY] = type;
    if (value !== undefined) {
      tagged[RESERVED_VALUE_KEY] = value;
    }
    Object.defineProperty(tagged, CANONICAL_MARKER, {
      value: true,
      enumerable: false,
    });
    return deepFreeze(tagged);
  };

  const finalizeCanonicalObject = (output) => {
    Object.defineProperty(output, CANONICAL_MARKER, {
      value: true,
      enumerable: false,
    });
    return deepFreeze(output);
  };

  const getDataDescriptor = (input, key) => {
    const descriptor = Object.getOwnPropertyDescriptor(input, key);
    if (!descriptor) {
      return null;
    }
    if ("get" in descriptor || "set" in descriptor) {
      throw new Error("Accessor properties are not supported in canonical data");
    }
    if (
      descriptor.enumerable !== true ||
      descriptor.configurable !== true ||
      descriptor.writable !== true
    ) {
      throw new Error("Non-plain property descriptors are not supported in canonical data");
    }
    return descriptor;
  };

  const deepFreeze = (input, seen = new WeakSet()) => {
    if (!input || typeof input !== "object" || Object.isFrozen(input)) {
      return input;
    }

    if (seen.has(input)) {
      return input;
    }

    seen.add(input);

    for (const key of Object.getOwnPropertyNames(input)) {
      deepFreeze(input[key], seen);
    }

    for (const key of Object.getOwnPropertySymbols(input)) {
      deepFreeze(input[key], seen);
    }

    return Object.freeze(input);
  };

  const getType = (input) => {
    if (input === null) {
      return "null";
    }
    if (Array.isArray(input)) {
      return "array";
    }
    return typeof input;
  };

  if (value && typeof value === "object" && value[CANONICAL_MARKER]) {
    return value;
  }

  const encodeObjectKey = (key) => {
    const text = String(key);
    return `__KEYL__:${text.length}:${text}`;
  };

  const compareCanonical = (left, right) => {
    const leftType = getType(left);
    const rightType = getType(right);

    if (leftType !== rightType) {
      return TYPE_ORDER[leftType] - TYPE_ORDER[rightType];
    }

    if (left === right) {
      if (leftType === "number") {
        const leftIsNegZero = Object.is(left, -0);
        const rightIsNegZero = Object.is(right, -0);
        if (leftIsNegZero !== rightIsNegZero) {
          return leftIsNegZero ? -1 : 1;
        }
      }
      return 0;
    }

    if (leftType === "number") {
      if (Number.isNaN(left)) return Number.isNaN(right) ? 0 : -1;
      if (Number.isNaN(right)) return 1;
      const leftIsNegZero = Object.is(left, -0);
      const rightIsNegZero = Object.is(right, -0);
      if (leftIsNegZero !== rightIsNegZero) {
        return leftIsNegZero ? -1 : 1;
      }
      return left < right ? -1 : 1;
    }

    if (leftType === "string" || leftType === "boolean" || leftType === "bigint") {
      return left < right ? -1 : 1;
    }

    if (leftType === "array") {
      for (let index = 0; index < Math.min(left.length, right.length); index += 1) {
        const itemCompare = compareCanonical(left[index], right[index]);
        if (itemCompare !== 0) {
          return itemCompare;
        }
      }
      return left.length - right.length;
    }

    if (leftType === "object" && left && right) {
      const leftKeys = Object.keys(left);
      const rightKeys = Object.keys(right);

      const allKeys = Array.from(new Set([...leftKeys, ...rightKeys])).sort();

      for (const key of allKeys) {
        const hasLeft = Object.prototype.hasOwnProperty.call(left, key);
        const hasRight = Object.prototype.hasOwnProperty.call(right, key);

        if (hasLeft !== hasRight) {
          return hasLeft ? -1 : 1;
        }

        const itemCompare = compareCanonical(left[key], right[key]);
        if (itemCompare !== 0) {
          return itemCompare;
        }
      }

      return 0;
    }

    throw new Error(`Unsupported canonical comparison state: ${leftType} vs ${rightType}`);
  };

  if (value instanceof Date) {
    return Number.isNaN(value.getTime())
      ? makeTaggedValue("InvalidDate")
      : makeTaggedValue("Date", value.toISOString());
  }

  if (value instanceof ArrayBuffer) {
    throw new Error("ArrayBuffer values are not supported in canonical data");
  }

  if (ArrayBuffer.isView(value)) {
    throw new Error("TypedArray values are not supported in canonical data");
  }

  if (value === undefined) {
    return makeTaggedValue("Undefined");
  }

  if (Array.isArray(value)) {
    if (path.has(value)) {
      return makeTaggedValue("Circular");
    }
    path.set(value, true);
    try {
      for (const key of Object.getOwnPropertyNames(value)) {
        if (key === "length") {
          continue;
        }
        getDataDescriptor(value, key);
      }
      for (const key of Object.getOwnPropertySymbols(value)) {
        getDataDescriptor(value, key);
      }
      const result = Array.from({ length: value.length }, (_, index) => (
        (() => {
          const descriptor = getDataDescriptor(value, String(index));
          if (!descriptor) {
            return makeTaggedValue("Hole");
          }
          return stableCanonicalize(descriptor.value, path);
        })()
      ));
      return finalizeCanonicalObject(result);
    } finally {
      path.delete(value);
    }
  }

  if (value instanceof Map) {
    if (path.has(value)) {
      return makeTaggedValue("Circular");
    }
    path.set(value, true);
    try {
      const entries = Array.from(value.entries()).map(([key, entryValue]) => [
        stableCanonicalize(key, path),
        stableCanonicalize(entryValue, path),
      ]);
      const seenKeys = new Set();
      for (const [key] of entries) {
        const keyId = stableStringify(key);
        if (seenKeys.has(keyId)) {
          throw new Error("Canonical key collision in Map");
        }
        seenKeys.add(keyId);
      }
      entries.sort((left, right) => compareCanonical(left[0], right[0]));
      return makeTaggedValue("Map", entries);
    } finally {
      path.delete(value);
    }
  }

  if (value instanceof Set) {
    if (path.has(value)) {
      return makeTaggedValue("Circular");
    }
    path.set(value, true);
    try {
      const items = Array.from(value.values()).map((item) => stableCanonicalize(item, path));
      items.sort(compareCanonical);
      return makeTaggedValue("Set", items);
    } finally {
      path.delete(value);
    }
  }

  if (value && typeof value === "object") {
    const proto = Object.getPrototypeOf(value);
    if (proto !== Object.prototype && proto !== null) {
      throw new Error("Only plain objects are supported in canonical data");
    }

    if (path.has(value)) {
      return makeTaggedValue("Circular");
    }
    path.set(value, true);
    try {
      for (const key of Object.getOwnPropertyNames(value)) {
        getDataDescriptor(value, key);
      }
      for (const key of Object.getOwnPropertySymbols(value)) {
        getDataDescriptor(value, key);
      }
      const result = Object.create(null);
      const stringEntries = Object.keys(value)
        .map((key) => {
          const descriptor = getDataDescriptor(value, key);
          return {
            encodedKey: encodeObjectKey(key),
            value: descriptor.value,
          };
        })
        .sort((left, right) => {
          if (left.encodedKey < right.encodedKey) return -1;
          if (left.encodedKey > right.encodedKey) return 1;
          return 0;
        });
      for (const { encodedKey, value: entryValue } of stringEntries) {
        result[encodedKey] = stableCanonicalize(entryValue, path);
      }
    const symbolKeys = Object.getOwnPropertySymbols(value)
      .map((symbolKey) => {
        const descriptor = getDataDescriptor(value, symbolKey);
        const registeredKey = Symbol.keyFor(symbolKey);
        if (registeredKey === undefined) {
          throw new Error("Unsupported non-global Symbol key in canonical data");
        }
        return {
          encodedKey: `__SYM__:${encodeObjectKey(registeredKey)}`,
          value: descriptor.value,
        };
      })
      .sort((left, right) => {
        if (left.encodedKey < right.encodedKey) return -1;
        if (left.encodedKey > right.encodedKey) return 1;
        return 0;
      });
    symbolKeys.forEach(({ encodedKey, value: symbolValue }) => {
      result[encodedKey] = stableCanonicalize(symbolValue, path);
    });
      return finalizeCanonicalObject(result);
    } finally {
      path.delete(value);
    }
  }

  if (typeof value === "symbol") {
    const globalKey = Symbol.keyFor(value);
    if (globalKey === undefined) {
      throw new Error("Unsupported non-global Symbol value in canonical data");
    }
    return makeTaggedValue("Symbol", globalKey);
  }

  if (typeof value === "function") {
    throw new Error("Unsupported function value in canonical data");
  }

  if (typeof value === "bigint") {
    return makeTaggedValue("BigInt", value.toString());
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number") {
    if (Number.isFinite(value)) {
      if (Object.is(value, -0)) {
        return makeTaggedValue("NegativeZero");
      }
      return Number(value);
    }
    if (Number.isNaN(value)) {
      return makeTaggedValue("NaN");
    }
    if (value === Infinity) {
      return makeTaggedValue("Infinity");
    }
    if (value === -Infinity) {
      return makeTaggedValue("NegativeInfinity");
    }
    throw new Error("Unsupported non-finite number value in canonical data");
  }

  return value;
}

export function stableStringify(value) {
  const canonical =
    value && typeof value === "object" && value[CANONICAL_MARKER]
      ? value
      : stableCanonicalize(value);

  if (canonical === null || typeof canonical !== "object") {
    return JSON.stringify(canonical);
  }

  if (Array.isArray(canonical)) {
    return `[${canonical.map((item) => stableStringify(item)).join(",")}]`;
  }

  const keys = Object.keys(canonical).sort();
  const entries = keys
    .filter((key) => canonical[key] !== undefined)
    .map((key) => `${JSON.stringify(key)}:${stableStringify(canonical[key])}`);
  return `{${entries.join(",")}}`;
}
