import { stableCanonicalize, stableStringify } from "./canonicalize.js";
import { toUtf8Bytes } from "./utf8.js";

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function wordsToHex(words) {
  const bytes = [];
  for (let index = 0; index < words.length; index += 1) {
    const word = words[index] >>> 0;
    bytes.push((word >>> 24) & 0xff);
    bytes.push((word >>> 16) & 0xff);
    bytes.push((word >>> 8) & 0xff);
    bytes.push(word & 0xff);
  }
  return bytes.map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function sha256Hex(input) {
  const bytes =
    input instanceof Uint8Array
      ? new Uint8Array(input)
      : ArrayBuffer.isView(input)
        ? new Uint8Array(input.buffer.slice(input.byteOffset, input.byteOffset + input.byteLength))
        : input instanceof ArrayBuffer
          ? new Uint8Array(input.slice(0))
          : toUtf8Bytes(input);
  const words = new Uint32Array(64);
  const hash = new Uint32Array([
    0x6a09e667,
    0xbb67ae85,
    0x3c6ef372,
    0xa54ff53a,
    0x510e527f,
    0x9b05688c,
    0x1f83d9ab,
    0x5be0cd19,
  ]);
  const K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
  ];

  const bitLength = bytes.length * 8;
  const paddedLength = (((bytes.length + 9 + 63) >> 6) << 6);
  const message = new Uint8Array(paddedLength);
  message.set(bytes);
  message[bytes.length] = 0x80;
  const view = new DataView(message.buffer);
  const high = Math.floor(bitLength / 0x100000000) >>> 0;
  const low = bitLength >>> 0;
  view.setUint32(paddedLength - 8, high, false);
  view.setUint32(paddedLength - 4, low, false);

  const rotr = (value, amount) => (value >>> amount) | (value << (32 - amount));
  const ch = (x, y, z) => (x & y) ^ (~x & z);
  const maj = (x, y, z) => (x & y) ^ (x & z) ^ (y & z);
  const bigSigma0 = (x) => rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22);
  const bigSigma1 = (x) => rotr(x, 6) ^ rotr(x, 11) ^ rotr(x, 25);
  const smallSigma0 = (x) => rotr(x, 7) ^ rotr(x, 18) ^ (x >>> 3);
  const smallSigma1 = (x) => rotr(x, 17) ^ rotr(x, 19) ^ (x >>> 10);

  for (let offset = 0; offset < message.length; offset += 64) {
    for (let index = 0; index < 16; index += 1) {
      words[index] = view.getUint32(offset + index * 4, false);
    }
    for (let index = 16; index < 64; index += 1) {
      words[index] = (smallSigma1(words[index - 2]) + words[index - 7] + smallSigma0(words[index - 15]) + words[index - 16]) >>> 0;
    }

    let [a, b, c, d, e, f, g, h] = hash;
    for (let index = 0; index < 64; index += 1) {
      const temp1 = (h + bigSigma1(e) + ch(e, f, g) + K[index] + words[index]) >>> 0;
      const temp2 = (bigSigma0(a) + maj(a, b, c)) >>> 0;
      h = g;
      g = f;
      f = e;
      e = (d + temp1) >>> 0;
      d = c;
      c = b;
      b = a;
      a = (temp1 + temp2) >>> 0;
    }

    hash[0] = (hash[0] + a) >>> 0;
    hash[1] = (hash[1] + b) >>> 0;
    hash[2] = (hash[2] + c) >>> 0;
    hash[3] = (hash[3] + d) >>> 0;
    hash[4] = (hash[4] + e) >>> 0;
    hash[5] = (hash[5] + f) >>> 0;
    hash[6] = (hash[6] + g) >>> 0;
    hash[7] = (hash[7] + h) >>> 0;
  }

  return wordsToHex(hash);
}

function checksum(value) {
  const text = stableStringify(value || {});
  return sha256Hex(text);
}

export { checksum as createSnapshotChecksum };

async function sha256(text) {
  return sha256Hex(text);
}

function base64UrlEncode(bytes) {
  const input = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  const hasNodeBuffer = typeof Buffer !== "undefined" && typeof Buffer.from === "function";
  if (hasNodeBuffer) {
    return Buffer.from(input).toString("base64url");
  }
  let binary = "";
  input.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return globalThis.btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function base64UrlDecode(text = "") {
  const hasNodeBuffer = typeof Buffer !== "undefined" && typeof Buffer.from === "function";
  if (hasNodeBuffer) {
    return new Uint8Array(Buffer.from(text, "base64url"));
  }
  const normalized = text.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
  const binary = globalThis.atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

export function createSnapshotIntegrity({ signer = null } = {}) {
  let keyPairPromise = null;
  const externalSigner = signer && typeof signer.sign === "function" ? signer : null;

  const getKeyPair = async () => {
    if (keyPairPromise) {
      return keyPairPromise;
    }
    keyPairPromise = (async () => {
      try {
        if (globalThis.crypto?.subtle?.generateKey) {
          const keyPair = await globalThis.crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
          const publicKey = await globalThis.crypto.subtle.exportKey("jwk", keyPair.publicKey);
          return {
            algorithm: "ed25519",
            keyPair,
            publicKey: {
              kind: "jwk",
              value: publicKey,
            },
            privateKeyFormat: "subtle-jwk",
          };
        }
      } catch {
        // fall through to digest fallback
      }

      try {
        const crypto = await import("node:crypto");
        const { publicKey, privateKey } = crypto.generateKeyPairSync("ed25519");
        return {
          algorithm: "ed25519",
          keyPair: { publicKey, privateKey, kind: "node" },
          publicKey: {
            kind: "pem",
            value: publicKey.export({ type: "spki", format: "pem" }),
          },
          privateKeyFormat: "node-key-object",
        };
      } catch {
        return null;
      }
    })();
    return keyPairPromise;
  };

  return {
    canonicalize(value) {
      return stableCanonicalize(value);
    },
    fingerprint(value) {
      return `sha256:${checksum(stableCanonicalize(value))}`;
    },
    async sign(value, meta = {}) {
      const payload = {
        value: stableCanonicalize(value),
        meta: stableCanonicalize(meta),
      };
      const material = stableStringify(payload);

      if (externalSigner) {
        const signed = await externalSigner.sign(material, meta);
        if (typeof signed === "string") {
          return {
            algorithm: externalSigner.algorithm || "external",
            signature: signed,
            publicKey: externalSigner.publicKey || null,
            signedAt: new Date().toISOString(),
          };
        }
        return {
          algorithm: signed.algorithm || externalSigner.algorithm || "external",
          signature: signed.signature || signed.digest || null,
          digest: signed.digest || null,
          publicKey: signed.publicKey || externalSigner.publicKey || null,
          signedAt: signed.signedAt || new Date().toISOString(),
          ...signed,
        };
      }

      const keyMaterial = await getKeyPair();
      if (!keyMaterial) {
        const digest = await sha256(material);
        return {
          algorithm: "sha-256",
          digest,
          signedAt: new Date().toISOString(),
          fallback: true,
        };
      }

      if (keyMaterial.privateKeyFormat === "subtle-jwk") {
        const encoded = toUtf8Bytes(material);
        const signature = await globalThis.crypto.subtle.sign({ name: "Ed25519" }, keyMaterial.keyPair.privateKey, encoded);
        return {
          algorithm: keyMaterial.algorithm,
          signature: base64UrlEncode(signature),
          publicKey: keyMaterial.publicKey,
          signedAt: new Date().toISOString(),
        };
      }

      const crypto = await import("node:crypto");
      const signature = crypto.sign(null, Buffer.from(material), keyMaterial.keyPair.privateKey);
      return {
        algorithm: keyMaterial.algorithm,
        signature: signature.toString("base64url"),
        publicKey: keyMaterial.publicKey,
        signedAt: new Date().toISOString(),
      };
    },
    async verify(value, signature, meta = {}) {
      if (!signature?.signature && !signature?.digest) {
        return false;
      }
      if (externalSigner?.verify) {
        return Boolean(await externalSigner.verify(value, signature, meta));
      }
      if (signature.digest) {
        const expected = await this.sign(value, meta);
        return expected.digest === signature.digest;
      }

      const payload = {
        value: stableCanonicalize(value),
        meta: stableCanonicalize(meta),
      };
      const material = stableStringify(payload);

      if (signature.publicKey && signature.algorithm === "ed25519") {
        const publicKey = signature.publicKey?.value || signature.publicKey?.jwk || signature.publicKey;

        if ((signature.publicKey?.kind === "jwk" || signature.publicKey?.jwk) && globalThis.crypto?.subtle) {
          const key = await globalThis.crypto.subtle.importKey(
            "jwk",
            publicKey,
            { name: "Ed25519" },
            true,
            ["verify"],
          );
          const verified = await globalThis.crypto.subtle.verify(
            { name: "Ed25519" },
            key,
            base64UrlDecode(signature.signature),
            toUtf8Bytes(material),
          );
          return verified;
        }

        try {
          const crypto = await import("node:crypto");
          const key = signature.publicKey?.kind === "pem" ? publicKey : signature.publicKey?.value || publicKey;
          const publicKeyObject = crypto.createPublicKey(key);
          return crypto.verify(null, Buffer.from(material), publicKeyObject, Buffer.from(signature.signature, "base64url"));
        } catch {
          return false;
        }
      }

      return false;
    },
  };
}

export function createMemoryEventStoreAdapter(seedEvents = []) {
  let events = Array.isArray(seedEvents) ? [...seedEvents] : [];

  return {
    kind: "memory",
    append(event) {
      events.push(event);
      return event;
    },
    load() {
      return [...events];
    },
    replay(reducer, initialState = {}) {
      if (typeof reducer !== "function") {
        return initialState;
      }
      return events.reduce((state, event) => reducer(state, event), initialState);
    },
    snapshot(limit = events.length) {
      const tail = events.slice(Math.max(0, events.length - Math.max(0, limit)));
      return {
        size: events.length,
        tail,
        checksum: checksum(tail),
      };
    },
    compact(keepLast = 50) {
      if (events.length > keepLast) {
        events = events.slice(events.length - keepLast);
      }
      return [...events];
    },
    clear() {
      events = [];
    },
  };
}

export function createProjectionStoreAdapter(seedProjections = {}) {
  let projections = clone(seedProjections || {});

  return {
    kind: "memory",
    write(name, projection) {
      projections[name] = projection;
      return projection;
    },
    read(name) {
      return name ? projections[name] || null : clone(projections);
    },
    list() {
      return Object.entries(projections).map(([name, projection]) => ({ name, projection }));
    },
    load(snapshot = {}) {
      const nextProjections =
        snapshot && typeof snapshot === "object" && "projections" in snapshot
          ? snapshot.projections
          : snapshot;
      projections = clone(nextProjections || {});
      return this.read();
    },
    snapshot() {
      const snapshot = clone(projections);
      return {
        projections: snapshot,
        checksum: checksum(snapshot),
      };
    },
    clear() {
      projections = {};
    },
  };
}

export function createStorageAdapters({ events = [], projections = {} } = {}) {
  return {
    eventStore: createMemoryEventStoreAdapter(events),
    projectionStore: createProjectionStoreAdapter(projections),
  };
}
