import React, { useMemo, useState } from "react";

function normalizeText(value, fallback = "—") {
  if (value === null || value === undefined) {
    return fallback;
  }

  const text = String(value).trim();
  return text.length > 0 ? text : fallback;
}

function summarizeResult(result) {
  if (!result) {
    return {
      tone: "neutral",
      label: "Awaiting verification",
      detail: "Paste a QR proof payload and verify it against the live API.",
    };
  }

  const isValid = result.status === true || result.valid === true;
  const isInvalid = result.status === false || result.valid === false;

  if (isValid) {
    return {
      tone: "success",
      label: "Verified",
      detail: result.reason || "Live verifier accepted the payload.",
    };
  }

  if (isInvalid) {
    return {
      tone: "danger",
      label: "Rejected",
      detail: result.reason || "Live verifier rejected the payload.",
    };
  }

  return {
    tone: "accent",
    label: "Partial",
    detail: result.reason || "Payload parsed, but verification is incomplete.",
  };
}

export function LiveVerifierPanel({ apiBaseUrl = "" }) {
  const [rawPayload, setRawPayload] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [parsedPayload, setParsedPayload] = useState(null);
  const [error, setError] = useState("");
  const [endpoint, setEndpoint] = useState("/trust/consensus/proof-receipt/mobile-verify");

  const summary = useMemo(() => summarizeResult(result), [result]);

  async function verifyViaApi() {
    const payloadText = rawPayload.trim();
    if (!payloadText) {
      setError("Paste a QR payload, proof receipt, or ZK bundle first.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      let parsed = null;
      try {
        parsed = JSON.parse(payloadText);
      } catch {
        parsed = null;
      }

      setParsedPayload(parsed);

      const looksLikeQrEnvelope = Boolean(
        parsed &&
        typeof parsed === "object" &&
        (parsed.qr_hash || parsed.type === "novatrust-qr-proof" || parsed.type === "novatrust-zk-qr")
      );

      const looksLikeReceipt = Boolean(
        parsed &&
        typeof parsed === "object" &&
        typeof parsed.receipt_hash === "string" &&
        !looksLikeQrEnvelope
      );

      const targetEndpoint = looksLikeReceipt
        ? "/trust/consensus/proof-receipt/verify"
        : "/trust/consensus/proof-receipt/mobile-verify";

      setEndpoint(targetEndpoint);

      const requestBody =
        targetEndpoint === "/trust/consensus/proof-receipt/verify"
          ? {
              receipt: parsed,
              group_public_keys:
                parsed?.group_public_keys ||
                parsed?.groupPublicKeys ||
                parsed?.signer_set ||
                parsed?.signerSet ||
                [],
            }
          : { qr_data: payloadText };

      const response = await fetch(`${apiBaseUrl}${targetEndpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      const responseBody = await response.json();
      if (!response.ok) {
        throw new Error(responseBody?.detail || responseBody?.error || `HTTP ${response.status}`);
      }

      setResult(responseBody);
    } catch (cause) {
      setResult({
        status: false,
        reason: cause instanceof Error ? cause.message : String(cause),
        trust_level: "UNTRUSTED",
        verification: { valid: false },
      });
    } finally {
      setLoading(false);
    }
  }

  function loadSample() {
    setRawPayload(
      JSON.stringify(
        {
          type: "novatrust-qr-proof",
          version: "1.0",
          issued_at: new Date().toISOString(),
          receipt: {
            receipt_hash: "demo-receipt-hash",
            signature_threshold: 1,
            signer_set: ["validator-1"],
          },
          qr_hash: "paste-a-live-qr-payload-from-the-api",
        },
        null,
        2
      )
    );
    setParsedPayload(null);
    setResult(null);
    setError("");
  }

  const validators = Array.isArray(result?.validators) ? result.validators : [];
  const verification = result?.verification || { valid: result?.valid ?? result?.status ?? null };

  return (
    <div className="record-card live-verifier-panel">
      <div className="record-card-header">
        <strong>Live Verifier</strong>
        <span>{summary.label}</span>
      </div>
      <p>
        This panel verifies the same QR and proof payloads that the mobile app
        consumes, through the live verifier API.
      </p>
      <textarea
        className="live-verifier-input"
        rows={10}
        value={rawPayload}
        onChange={(event) => setRawPayload(event.target.value)}
        placeholder="Paste a QR payload or proof receipt here"
      />
      <div className="chip-row">
        <button className="surface-chip" type="button" onClick={verifyViaApi} disabled={loading}>
          {loading ? "Verifying…" : "Verify via API"}
        </button>
        <button className="surface-chip" type="button" onClick={loadSample}>
          Load sample
        </button>
        <span className="surface-chip">Endpoint: {endpoint}</span>
      </div>
      {error ? <p className="error-text">{error}</p> : null}
      <div className="record-card-header">
        <strong>Result</strong>
        <span>{summary.tone}</span>
      </div>
      <p>{summary.detail}</p>
      <div className="stack">
        <article className="record-card">
          <div className="record-card-header">
            <strong>Status</strong>
            <span>{normalizeText(result?.status, "pending")}</span>
          </div>
          <p>Trust level: {normalizeText(result?.trust_level, "UNTRUSTED")}</p>
          <p>Reason: {normalizeText(result?.reason, summary.detail)}</p>
        </article>
        <article className="record-card">
          <div className="record-card-header">
            <strong>Validators</strong>
            <span>{validators.length}</span>
          </div>
          <p>{validators.length ? validators.join(", ") : "No validators returned."}</p>
        </article>
        <article className="record-card">
          <div className="record-card-header">
            <strong>Verification detail</strong>
            <span>{verification?.valid === true ? "valid" : verification?.valid === false ? "invalid" : "partial"}</span>
          </div>
          <p>Receipt hash: {normalizeText(result?.receipt?.receipt_hash || result?.receipt_hash, "—")}</p>
          <p>Proof hash: {normalizeText(result?.receipt?.proof_hash, "—")}</p>
          <p>UI hash: {normalizeText(result?.uiHash, "—")}</p>
        </article>
        <article className="record-card">
          <div className="record-card-header">
            <strong>Parsed payload</strong>
            <span>{parsedPayload ? "json" : "unparsed"}</span>
          </div>
          <pre className="verifier-json">{parsedPayload ? JSON.stringify(parsedPayload, null, 2) : "No parsed payload yet."}</pre>
        </article>
      </div>
    </div>
  );
}
