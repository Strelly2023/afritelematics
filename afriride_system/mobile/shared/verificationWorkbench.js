import React, { useMemo, useState } from "react";
import { Text, View } from "react-native";

import { ActionButton, Divider, Field, JsonCard, SectionCard, Timeline, ZkProofPanel, normalizeText } from "./novarideUi.js";
import { validateQrPayload, validateReplayPayload, validateZkBundle } from "./proofLayer.js";
import { verifyLivePayload, decodeVerifierPayload } from "./cryptographicVerifier.js";

function parsePayload(text) {
  return decodeVerifierPayload(text);
}

export function ProofWorkbench({
  title = "Scan + proof + replay + ZK",
  subtitle = "Paste a QR payload or inspect the current canonical state from the app shell.",
  canonicalState,
  replaySnapshot,
  receipt,
  zkBundle,
}) {
  const [rawPayload, setRawPayload] = useState("");
  const [parsedPayload, setParsedPayload] = useState(null);
  const [verification, setVerification] = useState(null);
  const [status, setStatus] = useState({ label: "Awaiting payload", valid: null, reason: "Paste a QR or proof payload to verify." });
  const resolvedReplay = replaySnapshot || null;
  const resolvedZkBundle = zkBundle || canonicalState?.zk_receipt || canonicalState?.zkReceipt || receipt?.zk_receipt || receipt?.zkReceipt || null;

  const quickFacts = useMemo(() => ([
    { label: "Replay state", value: normalizeText(resolvedReplay?.replayState?.status, "Pending"), tone: resolvedReplay?.replayState?.tone || "neutral" },
    { label: "UI hash", value: normalizeText(resolvedReplay?.uiHash, "—"), tone: "accent" },
    { label: "Snapshot", value: normalizeText(resolvedReplay?.snapshotHash, "—"), tone: "success" },
    { label: "Proof mode", value: normalizeText(resolvedReplay?.proofMode?.label, "Loaded"), tone: resolvedReplay?.proofMode?.tone || "accent" },
  ]), [resolvedReplay]);

  async function handleVerify() {
    try {
      const payload = parsePayload(rawPayload);
      const isQr = validateQrPayload(payload);
      const isReplay = validateReplayPayload(payload);
      const isZk = validateZkBundle(payload.zk_receipt || payload.zkReceipt || payload);
      const isReceipt = Boolean(
        payload?.receipt_hash ||
        payload?.receipt?.receipt_hash ||
        payload?.type === "novatrust-proof-receipt"
      );
      if (!isQr && !isReplay && !isZk && !isReceipt) {
        throw new Error("payload_schema_mismatch");
      }
      const result = await verifyLivePayload(payload);
      setParsedPayload(payload);
      setVerification(result);
      setStatus({
        label: result.valid === true ? "Verified" : result.valid === false ? "Invalid" : "Partial",
        valid: result.valid,
        reason:
          result.reason ||
          (payload.type ? `Accepted ${payload.type}` : "Payload verified"),
      });
    } catch (error) {
      setParsedPayload(null);
      setVerification(null);
      setStatus({ label: "Invalid", valid: false, reason: error instanceof Error ? error.message : "payload_invalid" });
    }
  }

  function loadCanonicalReceipt() {
    const candidate = receipt || canonicalState?.receipt || null;
    if (!candidate) {
      setStatus({ label: "No receipt", valid: false, reason: "No canonical receipt is available yet." });
      return;
    }
    setRawPayload(JSON.stringify(candidate, null, 2));
    setStatus({ label: "Loaded receipt", valid: null, reason: "Receipt pasted into verifier workspace." });
  }

  function loadLivePayload() {
    const candidate = canonicalState || receipt || resolvedZkBundle || resolvedReplay || null;
    if (!candidate) {
      setStatus({ label: "No payload", valid: false, reason: "No live payload is available yet." });
      return;
    }
    setRawPayload(JSON.stringify(candidate, null, 2));
    setStatus({ label: "Loaded payload", valid: null, reason: "Live payload pasted into verifier workspace." });
  }

  function loadZkBundle() {
    if (!resolvedZkBundle) {
      setStatus({ label: "No ZK bundle", valid: false, reason: "No privacy bundle is available in the current state." });
      return;
    }
    setRawPayload(JSON.stringify(resolvedZkBundle, null, 2));
    setStatus({ label: "Loaded ZK bundle", valid: null, reason: "ZK bundle pasted into verifier workspace." });
  }

  return (
    <SectionCard title={title} eyebrow="Verifier" compact>
      <Text style={{ color: "#97a9c2", fontSize: 13, lineHeight: 18 }}>{subtitle}</Text>
      <View style={{ marginTop: 12 }}>
        <Field label="QR / proof payload" value={rawPayload} onChangeText={setRawPayload} placeholder="Paste a QR envelope, proof receipt, or ZK bundle" multiline numberOfLines={8} />
      </View>
      <View style={{ flexDirection: "row", gap: 10, marginTop: 12, flexWrap: "wrap" }}>
        <ActionButton title="Verify payload" onPress={handleVerify} flex />
        <ActionButton title="Load receipt" tone="secondary" onPress={loadCanonicalReceipt} flex />
        <ActionButton title="Load live payload" tone="secondary" onPress={loadLivePayload} flex />
        <ActionButton title="Load ZK bundle" tone="secondary" onPress={loadZkBundle} flex />
      </View>
      <View style={{ marginTop: 12 }}>
        <Text style={{ color: "#f4f8ff", fontSize: 16, fontWeight: "800" }}>{status.label}</Text>
        <Text style={{ color: status.valid === false ? "#ff7d7d" : "#97a9c2", marginTop: 4 }}>{status.reason}</Text>
      </View>
      <Divider />
      <View style={{ gap: 8 }}>{quickFacts.map((item) => (<View key={item.label} style={{ flexDirection: "row", justifyContent: "space-between" }}><Text style={{ color: "#71849f" }}>{item.label}</Text><Text style={{ color: "#f4f8ff", fontWeight: "700" }}>{item.value}</Text></View>))}</View>
      <Divider />
      <Text style={{ color: "#f4f8ff", fontSize: 14, fontWeight: "800", marginBottom: 8 }}>Parsed payload</Text>
      <JsonCard value={parsedPayload} empty="No payload verified yet." maxHeight={220} />
      <Divider />
      <Text style={{ color: "#f4f8ff", fontSize: 14, fontWeight: "800", marginBottom: 8 }}>Verification layers</Text>
      <JsonCard value={verification?.layers || null} empty="No verification layers yet." maxHeight={220} />
      <Divider />
      <Text style={{ color: "#f4f8ff", fontSize: 14, fontWeight: "800", marginBottom: 8 }}>Replay timeline</Text>
      <Timeline items={resolvedReplay?.timeline || []} />
      <Divider />
      <ZkProofPanel bundle={resolvedZkBundle} receipt={receipt || canonicalState?.receipt || null} bridge={canonicalState?.bridge || canonicalState?.zk_bridge || null} />
    </SectionCard>
  );
}
