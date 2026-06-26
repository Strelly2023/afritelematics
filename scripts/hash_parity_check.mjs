import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import {
  buildSignedMessage,
  hashDomain,
} from "../afriride_system/mobile/shared/cryptographicVerifier.js";
import {
  PROTOCOL_HASH_VERSION,
  SIGNED_MESSAGE_PREFIX,
} from "../afriride_system/mobile/shared/protocol.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const corpusPath = path.resolve(
  __dirname,
  "../afritech/tests/fixtures/crypto_corpus/hash_corpus.json",
);

const corpus = JSON.parse(await fs.readFile(corpusPath, "utf8"));

function errorMessage(error) {
  return String(error?.message || error);
}

function hasErrorCode(error, code) {
  const msg = errorMessage(error);
  const escaped = code.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&");
  return new RegExp(`^${escaped}(?:$|[:\\s\\-\\(])`).test(msg);
}

if (corpus.protocol?.hash_version !== PROTOCOL_HASH_VERSION) {
  throw new Error(`hash version mismatch: ${corpus.protocol?.hash_version} != ${PROTOCOL_HASH_VERSION}`);
}

if (corpus.protocol?.signed_message_prefix !== SIGNED_MESSAGE_PREFIX) {
  throw new Error(
    `signed message prefix mismatch: ${corpus.protocol?.signed_message_prefix} != ${SIGNED_MESSAGE_PREFIX}`,
  );
}

for (const item of corpus.cases) {
  const computedHash = hashDomain(item.payload, item.domain);
  const computedMessage = item.use_payload_domain
    ? buildSignedMessage(item.payload)
    : buildSignedMessage(item.payload, item.domain);

  if (computedHash !== item.hash) {
    throw new Error(`hash mismatch for ${item.name}: ${computedHash} != ${item.hash}`);
  }

  if (computedMessage !== item.signed_message) {
    throw new Error(
      `signed message mismatch for ${item.name}: ${computedMessage} != ${item.signed_message}`,
    );
  }

  if (item.use_payload_domain) {
    let mismatchRaised = false;
    try {
      buildSignedMessage(item.payload, "signed_payload");
    } catch (error) {
      mismatchRaised = hasErrorCode(error, "domain_mismatch");
    }

    if (!mismatchRaised) {
      throw new Error(`expected domain mismatch for ${item.name}`);
    }
  }
}

let emptyDomainRaised = false;
try {
  buildSignedMessage({ domain: "", text: "domain-bound" });
} catch (error) {
  emptyDomainRaised = hasErrorCode(error, "invalid_declared_hash_domain_empty");
}

if (!emptyDomainRaised) {
  throw new Error("expected empty declared domain to be rejected");
}

let emptyBeforeConflictRaised = false;
try {
  buildSignedMessage({
    domain: "",
    signature: { domain: "proof_receipt" },
    text: "domain-bound",
  });
} catch (error) {
  emptyBeforeConflictRaised = hasErrorCode(error, "invalid_declared_hash_domain_empty");
}

if (!emptyBeforeConflictRaised) {
  throw new Error("expected empty declared domain to win before conflict");
}

let conflictingDomainRaised = false;
try {
  buildSignedMessage({
    domain: "proof_receipt",
    signature: { domain: "signed_payload" },
    text: "domain-bound",
  });
} catch (error) {
  conflictingDomainRaised = hasErrorCode(error, "conflicting_declared_hash_domain");
}

if (!conflictingDomainRaised) {
  throw new Error("expected conflicting declared domains to be rejected");
}

let nonStringDomainRaised = false;
try {
  buildSignedMessage({ domain: 123, text: "domain-bound" });
} catch (error) {
  nonStringDomainRaised = hasErrorCode(error, "invalid_declared_hash_domain");
}

if (!nonStringDomainRaised) {
  throw new Error("expected non-string domain to be rejected");
}

process.stdout.write(`hash parity ok (${corpus.cases.length} cases)\n`);
