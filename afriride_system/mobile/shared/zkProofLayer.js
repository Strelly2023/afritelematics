function hasValue(value) {
  return value !== null && value !== undefined && value !== "";
}

export function selectZkBundle(canonicalState = {}) {
  return (
    canonicalState.zkReceipt ||
    canonicalState.zk_receipt ||
    canonicalState.zkBundle ||
    canonicalState.zk_bundle ||
    canonicalState.proof?.zk_receipt ||
    canonicalState.proof?.zkReceipt ||
    canonicalState.receipt?.zk_receipt ||
    canonicalState.receipt?.zkReceipt ||
    canonicalState.receipt?.zk_bundle ||
    canonicalState.receipt?.zkBundle ||
    canonicalState.bundle ||
    null
  );
}

export function summarizeZkBundle(bundle) {
  if (!bundle) {
    return {
      label: "ZK unavailable",
      tone: "neutral",
      reason: "No privacy-preserving receipt is attached to this snapshot.",
      privacyLevel: "Public",
      hiddenFieldCount: 0,
      receiptHash: null,
      commitment: null,
      proofHash: null,
      bridgeHash: null,
      chainId: null,
      state: "missing",
    };
  }

  const verification = bundle.verification || bundle.zk_verification || bundle.proof_verification || null;
  const verified = verification?.valid === true || bundle.valid === true;
  const invalid = verification?.valid === false || bundle.valid === false;
  const hiddenFields = Array.isArray(bundle.hidden_fields) ? bundle.hidden_fields.filter(hasValue) : [];
  const publicInputs = bundle.public_inputs && typeof bundle.public_inputs === "object" ? bundle.public_inputs : {};
  const bridge = bundle.bridge && typeof bundle.bridge === "object" ? bundle.bridge : null;
  const chainId =
    publicInputs.chain_id ||
    bridge?.light_client_state?.chain_id ||
    bundle.chain_id ||
    null;

  return {
    label: invalid ? "ZK invalid" : verified ? "ZK verified" : "ZK ready",
    tone: invalid ? "danger" : verified ? "success" : "accent",
    reason:
      verification?.reason ||
      bundle.reason ||
      (verified ? "Zero-knowledge proof verified" : "Privacy bundle loaded"),
    privacyLevel: hiddenFields.length > 0 ? "Private" : "Protected",
    hiddenFieldCount: hiddenFields.length,
    receiptHash: publicInputs.receipt_hash || bundle.receipt_hash || null,
    commitment: bundle.commitment || null,
    proofHash: bundle.proof_hash || bundle.proof || null,
    bridgeHash: bridge?.bridge_hash || null,
    chainId,
    state: invalid ? "invalid" : verified ? "verified" : "ready",
    hiddenFields,
    publicInputs,
    bridge,
  };
}

