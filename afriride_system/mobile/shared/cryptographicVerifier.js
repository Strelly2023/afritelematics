import { stableCanonicalize, stableStringify } from "./canonicalize.js";
import { sha256Hex } from "./novarideStorage.js";
import { verifyReplay } from "./verificationLayer.js";
import { validateReplayPayload, validateZkBundle } from "./proofLayer.js";
import { toUtf8Bytes } from "./utf8.js";
import { canonicalizeProtocolValue, formatSignedMessage, PROTOCOL_HASH_VERSION } from "./protocol.js";

function isPlainObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

const HASH_DOMAINS = Object.freeze({
  PACKET: "packet",
  SIGNATURE: "signature",
  AGGREGATE: "aggregate",
  VIOLATIONS: "violations",
  CONSENSUS_ROOT: "consensus_root",
  VALIDATOR_ROOT: "validator_root",
  SEAL: "seal",
  QR_PAYLOAD: "qr_payload",
  SIGNED_PAYLOAD: "signed_payload",
  PROOF_RECEIPT: "proof_receipt",
  SIGNER_SET: "signer_set",
  ZK_RECEIPT_COMMITMENT: "zk_receipt_commitment",
  ZK_RECEIPT_PROOF: "zk_receipt_proof",
  ZK_QR_PAYLOAD: "zk_qr_payload",
});

// ⚠️ DO NOT CHANGE VALUES — part of the cryptographic protocol.

function normalizeText(value, fallback = "") {
  if (value === null || value === undefined) {
    return fallback;
  }
  const text = String(value).trim();
  return text.length > 0 ? text : fallback;
}

function canonicalText(value) {
  if (isPlainObject(value) || Array.isArray(value)) {
    return stableStringify(stableCanonicalize(value));
  }
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}

function normalizeHex(value) {
  return normalizeText(value, "").replace(/^0x/i, "").toLowerCase();
}

function normalizeHash(value) {
  if (typeof value !== "string") {
    return "";
  }
  return String(value).toLowerCase().replace(/\s+/g, "");
}

function declaredSignedMessageDomain(payload) {
  if (!isPlainObject(payload)) {
    return null;
  }

  const candidates = [
    payload.domain,
    payload.hash_domain,
    payload.message_domain,
    payload.signature_domain,
    payload.signature?.domain,
    payload.signature?.hash_domain,
    payload.receipt?.domain,
    payload.receipt?.hash_domain,
  ];

  const declaredDomains = [];

  for (const candidate of candidates) {
    if (candidate === undefined || candidate === null) {
      continue;
    }

    if (typeof candidate !== "string") {
      throw new Error("invalid_declared_hash_domain");
    }

    const declaredDomain = candidate.trim();
    if (!declaredDomain) {
      throw new Error("invalid_declared_hash_domain_empty");
    }

    if (!Object.values(HASH_DOMAINS).includes(declaredDomain)) {
      throw new Error("invalid_declared_hash_domain");
    }

    declaredDomains.push(declaredDomain);
  }

  if (declaredDomains.length === 0) {
    return null;
  }

  const uniqueDomains = new Set(declaredDomains);
  if (uniqueDomains.size > 1) {
    throw new Error("conflicting_declared_hash_domain");
  }

  return declaredDomains[0];
}

function resolveSignedMessageDomain(payload, requestedDomain) {
  const declaredDomain = declaredSignedMessageDomain(payload);
  if (requestedDomain === undefined || requestedDomain === null) {
    return declaredDomain || HASH_DOMAINS.SIGNED_PAYLOAD;
  }

  if (declaredDomain && declaredDomain !== requestedDomain) {
    throw new Error(`domain_mismatch:${declaredDomain}:${requestedDomain}`);
  }
  return requestedDomain;
}

function hexToBytes(value) {
  const normalized = normalizeHex(value);
  if (!normalized || normalized.length % 2 !== 0 || !/^[0-9a-f]+$/i.test(normalized)) {
    throw new Error("invalid_hex");
  }

  const bytes = new Uint8Array(normalized.length / 2);
  for (let index = 0; index < normalized.length; index += 2) {
    bytes[index / 2] = Number.parseInt(normalized.slice(index, index + 2), 16);
  }
  return bytes;
}

export function hashDomain(payload, domain) {
  if (!Object.values(HASH_DOMAINS).includes(domain)) {
    throw new Error("invalid_hash_domain");
  }

  const canonicalPayload = canonicalizeProtocolValue(payload);
  const input = toUtf8Bytes(JSON.stringify([PROTOCOL_HASH_VERSION, domain, canonicalPayload]));
  return sha256Hex(input);
}

function extractQrHashInput(payload) {
  if (!payload || typeof payload !== "object") {
    return {};
  }
  const { qr_hash: _qrHash, ...rest } = payload;
  return rest;
}

function extractReplayCandidate(payload) {
  if (!isPlainObject(payload)) {
    return null;
  }

  return (
    payload.replay ||
    payload.replay_snapshot ||
    payload.replayState ||
    payload.replay_state ||
    payload.receipt?.replay ||
    payload.receipt?.replay_snapshot ||
    payload.receipt?.replayState ||
    payload.receipt?.replay_state ||
    (payload.type === "novatrust-replay" ? payload : null) ||
    null
  );
}

function extractSignatureCandidate(payload) {
  if (!isPlainObject(payload)) {
    return null;
  }

  return (
    payload.signature ||
    payload.signature_bundle ||
    payload.signing ||
    payload.seal?.signature ||
    payload.receipt?.signature ||
    null
  );
}

function extractReceiptCandidate(payload) {
  if (!isPlainObject(payload)) {
    return null;
  }

  if (typeof payload.receipt_hash === "string" && payload.receipt_hash.trim().length > 0) {
    return payload;
  }

  if (isPlainObject(payload.receipt) && typeof payload.receipt.receipt_hash === "string") {
    return payload.receipt;
  }

  return null;
}

function extractZkCandidate(payload) {
  if (!isPlainObject(payload)) {
    return null;
  }

  return (
    payload.zk_bundle ||
    payload.zkBundle ||
    payload.zk_receipt ||
    payload.zkReceipt ||
    payload.proof?.zk_bundle ||
    payload.proof?.zk_receipt ||
    payload.receipt?.zk_bundle ||
    payload.receipt?.zk_receipt ||
    null
  );
}

function normalizeLayerResult(layer, valid, reason, extra = {}) {
  return {
    layer,
    valid,
    reason,
    ...extra,
  };
}

function toBytes(message) {
  if (message instanceof Uint8Array) {
    return message;
  }
  return toUtf8Bytes(canonicalText(message));
}

function buildCanonicalPayloadHash(payload, domain) {
  const candidate = payload && typeof payload === "object" ? payload : {};
  const resolvedDomain = resolveSignedMessageDomain(candidate, domain);
  const receipt = isPlainObject(candidate.receipt) ? candidate.receipt : null;

  if (typeof receipt?.receipt_hash === "string" && receipt.receipt_hash.length > 0) {
    return receipt.receipt_hash;
  }
  if (typeof candidate.receipt_hash === "string" && candidate.receipt_hash.length > 0) {
    return candidate.receipt_hash;
  }
  if (typeof candidate.qr_hash === "string" && candidate.qr_hash.length > 0) {
    return candidate.qr_hash;
  }

  const {
    message: _message,
    payload: _payload,
    type: _type,
    signature: _signature,
    signature_bundle: _signatureBundle,
    signing: _signing,
    signatures: _signatures,
    ...unsignedCandidate
  } = candidate;

  return hashDomain(unsignedCandidate, resolvedDomain);
}

export function buildSignedMessage(payload, domain) {
  const resolvedDomain = resolveSignedMessageDomain(payload, domain);
  const payloadHash = normalizeHash(buildCanonicalPayloadHash(payload, resolvedDomain));
  return formatSignedMessage(resolvedDomain, payloadHash);
}

export async function verifyProofReceiptLayer(payload) {
  const receipt = extractReceiptCandidate(payload);
  if (!receipt) {
    return normalizeLayerResult("receipt", null, "receipt_not_present");
  }

  const { receipt_hash: _receiptHash, receipt_id: _receiptId, ...unsignedReceipt } = receipt;
  const expectedHash = hashDomain(unsignedReceipt, HASH_DOMAINS.PROOF_RECEIPT);
  if (normalizeText(receipt.receipt_hash, "") !== expectedHash) {
    return normalizeLayerResult("receipt", false, "receipt_hash_mismatch", {
      expectedHash,
      receiptHash: receipt.receipt_hash,
    });
  }

  const aggregateScheme = normalizeText(receipt.aggregate_scheme || receipt.aggregateSignatureScheme, "");
  if (aggregateScheme === "bls-threshold") {
    const signerSet = Array.isArray(receipt.signer_set) ? receipt.signer_set : [];
    const normalizedSignerSet = signerSet.map((value) => normalizeText(value, "")).filter(Boolean).sort();
    const expectedSignerSetHash = hashDomain({ signers: normalizedSignerSet }, HASH_DOMAINS.SIGNER_SET);
    const signerSetHash = normalizeText(receipt.signer_set_hash, "");

    if (!normalizedSignerSet.length) {
      return normalizeLayerResult("receipt", false, "empty_signer_set");
    }

    if (signerSetHash !== expectedSignerSetHash) {
      return normalizeLayerResult("receipt", false, "signer_set_hash_mismatch", {
        expectedSignerSetHash,
        signerSetHash,
      });
    }

    const aggregateSignature = normalizeText(receipt.aggregate_signature, "");
    const consensusRoot = normalizeText(receipt.consensus_root, "");
    if (!aggregateSignature || !consensusRoot) {
      return normalizeLayerResult("receipt", false, "missing_bls_receipt_fields");
    }

    const blsResult = await verifyBlsAggregateSignature({
      message: consensusRoot,
      aggregateSignatureHex: aggregateSignature,
      publicKeysHex: normalizedSignerSet,
    });

    if (blsResult.valid !== true) {
      return normalizeLayerResult("receipt", false, blsResult.reason || "bls_aggregate_invalid", {
        expectedHash,
        receiptHash: receipt.receipt_hash,
      });
    }
  }

  return normalizeLayerResult("receipt", true, "receipt_verified", {
    receiptHash: receipt.receipt_hash,
    expectedHash,
  });
}

export function verifyQrEnvelope(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return normalizeLayerResult("qr", false, "invalid_payload_type");
  }

  const looksLikeQrEnvelope =
    payload.type === "novatrust-qr-proof" ||
    payload.type === "novatrust-zk-qr" ||
    (typeof payload.qr_hash === "string" &&
      payload.qr_hash.trim().length > 0 &&
      (payload.receipt || payload.zk_bundle || payload.zk_receipt));

  if (!looksLikeQrEnvelope) {
    return normalizeLayerResult("qr", null, "qr_not_present");
  }

  if (typeof payload.qr_hash !== "string" || payload.qr_hash.trim().length === 0) {
    return normalizeLayerResult("qr", false, "missing_qr_hash");
  }

  const receipt = payload.receipt;
  if (payload.receipt !== undefined && !isPlainObject(receipt)) {
    return normalizeLayerResult("qr", false, "qr_invalid_receipt");
  }

  const expectedHash = normalizeHash(hashDomain(extractQrHashInput(payload), HASH_DOMAINS.QR_PAYLOAD));
  const actualHash = normalizeHash(payload.qr_hash);
  if (actualHash !== expectedHash) {
    return normalizeLayerResult("qr", false, "qr_integrity_failure", {
      expectedHash,
      actualHash,
    });
  }

  return normalizeLayerResult("qr", true, "qr_verified", {
    receipt,
    expectedHash,
  });
}

async function importEthers() {
  try {
    return await import("ethers");
  } catch {
    return null;
  }
}

async function importBls() {
  try {
    return await import("@noble/bls12-381");
  } catch {
    return null;
  }
}

async function importSnarkjs() {
  try {
    return await import("snarkjs");
  } catch {
    return null;
  }
}

let snarkjsPromise = null;

async function getSnarkjs() {
  if (!snarkjsPromise) {
    snarkjsPromise = importSnarkjs();
  }
  return snarkjsPromise;
}

export async function verifySecp256k1Signature({
  message,
  signature,
  expectedAddress,
}) {
  if (!signature || !expectedAddress) {
    return normalizeLayerResult("signature", false, "secp256k1_inputs_missing");
  }

  const ethers = await importEthers();
  if (!ethers?.verifyMessage) {
    return normalizeLayerResult("signature", false, "ethers_unavailable");
  }

  try {
    const signer = ethers.verifyMessage(canonicalText(message), normalizeText(signature));
    return normalizeLayerResult(
      "signature",
      signer.toLowerCase() === normalizeText(expectedAddress).toLowerCase(),
      signer.toLowerCase() === normalizeText(expectedAddress).toLowerCase()
        ? "secp256k1_verified"
        : "secp256k1_address_mismatch",
      { signer }
    );
  } catch (error) {
    return normalizeLayerResult("signature", false, "secp256k1_verification_failed", {
      error: error instanceof Error ? error.message : String(error),
    });
  }
}

export async function verifyBlsSignature({
  message,
  signatureHex,
  publicKeyHex,
}) {
  if (!signatureHex || !publicKeyHex) {
    return normalizeLayerResult("signature", false, "bls_inputs_missing");
  }

  const bls = await importBls();
  if (!bls?.verify) {
    return normalizeLayerResult("signature", false, "bls_unavailable");
  }

  try {
    const signatureBytes = hexToBytes(signatureHex);
    const publicKeyBytes = hexToBytes(publicKeyHex);
    const verified = await bls.verify(signatureBytes, toBytes(message), publicKeyBytes);
    return normalizeLayerResult("signature", Boolean(verified), verified ? "bls_verified" : "bls_signature_mismatch");
  } catch (error) {
    return normalizeLayerResult("signature", false, "bls_verification_failed", {
      error: error instanceof Error ? error.message : String(error),
    });
  }
}

export async function verifyBlsAggregateSignature({
  message,
  aggregateSignatureHex,
  publicKeysHex,
}) {
  if (!aggregateSignatureHex || !Array.isArray(publicKeysHex) || publicKeysHex.length === 0) {
    return normalizeLayerResult("signature", false, "bls_aggregate_inputs_missing");
  }

  const bls = await importBls();
  if (!bls?.verify || !bls?.aggregatePublicKeys) {
    return normalizeLayerResult("signature", false, "bls_aggregate_unavailable");
  }

  try {
    const aggregateSignature = hexToBytes(aggregateSignatureHex);
    const publicKeys = publicKeysHex.map(hexToBytes);
    const aggregatePublicKey = bls.aggregatePublicKeys(publicKeys);
    const verified = await bls.verify(aggregateSignature, toBytes(message), aggregatePublicKey);
    return normalizeLayerResult("signature", Boolean(verified), verified ? "bls_aggregate_verified" : "bls_aggregate_mismatch");
  } catch (error) {
    return normalizeLayerResult("signature", false, "bls_aggregate_failed", {
      error: error instanceof Error ? error.message : String(error),
    });
  }
}

function collectPublicSignals(bundle) {
  const candidates = [
    bundle?.publicSignals,
    bundle?.public_signals,
    bundle?.publicInputs,
    bundle?.public_inputs,
    bundle?.inputs,
  ];

  for (const candidate of candidates) {
    if (Array.isArray(candidate)) {
      return candidate.map((value) => normalizeText(value, ""));
    }
  }

  if (isPlainObject(bundle?.public_inputs)) {
    const canonical = stableCanonicalize(bundle.public_inputs);
    return Object.keys(canonical)
      .sort()
      .map((key) => canonical[key])
      .map((value) => normalizeText(value, ""));
  }

  return null;
}

function collectVerificationKey(bundle) {
  return bundle?.verification_key || bundle?.verificationKey || bundle?.vkey || bundle?.vk || null;
}

export async function verifySnarkProofBundle(bundle) {
  if (!isPlainObject(bundle)) {
    return normalizeLayerResult("zk", false, "zk_invalid_payload");
  }

  const proof = bundle.proof || bundle.zk_proof || bundle.groth16_proof || null;
  const publicSignals = collectPublicSignals(bundle);
  const verificationKey = collectVerificationKey(bundle);

  if (!proof || !publicSignals || !verificationKey) {
    return normalizeLayerResult("zk", null, "zk_bundle_incomplete", {
      proof,
      publicSignals,
      verificationKey,
    });
  }

  const snarkjs = await getSnarkjs();
  const groth16 = snarkjs?.groth16 || null;
  if (!groth16?.verify) {
    return normalizeLayerResult("zk", null, "snarkjs_unavailable", {
      proof,
      publicSignals,
    });
  }

  try {
    const valid = await groth16.verify(verificationKey, publicSignals, proof);
    return normalizeLayerResult("zk", Boolean(valid), valid ? "zk_verified" : "zk_invalid_proof", {
      proof,
      publicSignals,
    });
  } catch (error) {
    return normalizeLayerResult("zk", false, "zk_verification_failed", {
      error: error instanceof Error ? error.message : String(error),
    });
  }
}

export async function verifyInternalZkReceipt(bundle) {
  if (!isPlainObject(bundle)) {
    return normalizeLayerResult("zk", false, "zk_invalid_payload");
  }

  if (!validateZkBundle(bundle)) {
    return normalizeLayerResult("zk", false, "zk_bundle_schema_invalid");
  }

  const verification = bundle.verification || bundle.zk_verification || null;
  const proofHash = normalizeText(bundle.proof_hash || bundle.proof, "");
  const commitment = normalizeText(bundle.commitment, "");
  const publicInputs = bundle.public_inputs;
  const hiddenFields = Array.isArray(bundle.hidden_fields) ? bundle.hidden_fields : [];

  if (!commitment || !proofHash || !isPlainObject(publicInputs)) {
    return normalizeLayerResult("zk", false, "zk_internal_bundle_incomplete");
  }

  const expectedCommitment = hashDomain(
    {
      public_inputs: publicInputs,
      hidden_fields: hiddenFields.map((field) => normalizeText(field, "")).filter(Boolean).sort(),
    },
    HASH_DOMAINS.ZK_RECEIPT_COMMITMENT,
  );

  if (bundle.commitment !== expectedCommitment) {
    return normalizeLayerResult("zk", false, "zk_commitment_mismatch", {
      expectedCommitment,
      commitment: bundle.commitment,
    });
  }

  const expectedProof = hashDomain(
    {
      scheme: normalizeText(bundle.scheme, "mock-zk-receipt-v1"),
      commitment,
      public_inputs: publicInputs,
    },
    HASH_DOMAINS.ZK_RECEIPT_PROOF,
  );

  if (proofHash !== expectedProof) {
    return normalizeLayerResult("zk", false, "zk_proof_hash_mismatch", {
      expectedProof,
      proofHash,
    });
  }

  if (verification && verification.valid === false) {
    return normalizeLayerResult("zk", false, verification.reason || "zk_verification_failed");
  }

  return normalizeLayerResult("zk", true, "zk_receipt_verified", {
    proofHash,
    commitment,
  });
}

export async function verifyZkLayer(payload) {
  const bundle = extractZkCandidate(payload) || payload?.zk_bundle || payload?.zk_receipt || null;
  if (!bundle) {
    return normalizeLayerResult("zk", null, "zk_not_present");
  }

  if (bundle.type === "zk_receipt" || bundle.public_inputs || bundle.redacted_receipt) {
    return verifyInternalZkReceipt(bundle);
  }

  return verifySnarkProofBundle(bundle);
}

export function verifyReplayLayer(payload) {
  const replay = extractReplayCandidate(payload) || (validateReplayPayload(payload) ? payload : null);
  if (!replay) {
    return normalizeLayerResult("replay", null, "replay_not_present");
  }

  const result = verifyReplay(replay);
  return normalizeLayerResult("replay", result.valid, result.reason, {
    replay: result.replay,
  });
}

export async function verifySignatureLayer(payload) {
  const signature = extractSignatureCandidate(payload);
  if (!signature) {
    return normalizeLayerResult("signature", null, "signature_not_present");
  }

  const message = buildSignedMessage(payload);

  const signatureType = normalizeText(
    signature?.type || signature?.scheme || payload?.signature_type || payload?.scheme,
    "",
  ).toLowerCase();

  if (signatureType === "secp256k1" || signatureType === "ethers") {
    return verifySecp256k1Signature({
      message,
      signature: signature.value || signature.signature || signature.hex || signature,
      expectedAddress: signature.address || signature.expected_address || payload.expected_address,
    });
  }

  if (signatureType === "bls") {
    if (Array.isArray(signature.publicKeys) || Array.isArray(signature.public_keys)) {
      return verifyBlsAggregateSignature({
        message,
        aggregateSignatureHex: signature.value || signature.signature || signature.aggregate_signature || signature,
        publicKeysHex: signature.publicKeys || signature.public_keys,
      });
    }

    return verifyBlsSignature({
      message,
      signatureHex: signature.value || signature.signature || signature.hex || signature,
      publicKeyHex: signature.publicKey || signature.public_key || signature.publicKeyHex || payload.public_key,
    });
  }

  if (signature.aggregate_signature || signature.aggregateSignature) {
    return verifyBlsAggregateSignature({
      message,
      aggregateSignatureHex: signature.aggregate_signature || signature.aggregateSignature,
      publicKeysHex: signature.publicKeys || signature.public_keys || payload.signer_set || payload.public_keys || [],
    });
  }

  if (signature.value || signature.signature || signature.hex) {
    return verifySecp256k1Signature({
      message,
      signature: signature.value || signature.signature || signature.hex,
      expectedAddress: signature.address || signature.expected_address || payload.expected_address || payload.address,
    });
  }

  return normalizeLayerResult("signature", null, "signature_unrecognized");
}

export async function verifyLivePayload(payload) {
  const qr = verifyQrEnvelope(payload);
  const receipt = await verifyProofReceiptLayer(payload);
  const replay = verifyReplayLayer(payload);
  const signature = await verifySignatureLayer(payload);
  const zk = await verifyZkLayer(payload);

  const layers = { qr, receipt, replay, signature, zk };
  const recognizedLayers = Object.values(layers).filter((layer) => layer.valid !== null);

  if (recognizedLayers.length === 0) {
    return {
      valid: false,
      reason: "no_verifiable_layers",
      layers,
      message: buildSignedMessage(payload),
    };
  }

  const fatalFailure = recognizedLayers.some((layer) => layer.valid === false);
  const allVerified = recognizedLayers.length > 0 && recognizedLayers.every((layer) => layer.valid === true);

  const reasons = Object.values(layers)
    .filter((layer) => layer.valid === false && layer.reason)
    .map((layer) => layer.reason);

  return {
    valid: fatalFailure ? false : allVerified ? true : null,
    reason: reasons[0] || (fatalFailure ? "verification_failed" : "verification_partial"),
    layers,
    message: buildSignedMessage(payload),
  };
}

export function decodeVerifierPayload(text) {
  const normalized = normalizeText(text, "");
  if (!normalized) {
    throw new Error("empty_payload");
  }

  if (normalized.startsWith("{") || normalized.startsWith("[")) {
    return JSON.parse(normalized);
  }

  if (typeof globalThis.atob === "function") {
    const binary = globalThis.atob(normalized);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    if (typeof TextDecoder !== "undefined") {
      return JSON.parse(new TextDecoder("utf-8").decode(bytes));
    }
    if (typeof Buffer !== "undefined") {
      return JSON.parse(Buffer.from(bytes).toString("utf8"));
    }
    let raw = "";
    for (const byte of bytes) raw += String.fromCharCode(byte);
    return JSON.parse(raw);
  }

  if (typeof Buffer !== "undefined") {
    return JSON.parse(Buffer.from(normalized, "base64").toString("utf8"));
  }

  throw new Error("base64_decode_unavailable");
}
