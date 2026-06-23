import React, { useEffect, useState } from "react";

export function TrustExplorerFrontend({ explorer, receiptId, apiBaseUrl = "" }) {
  const data = explorer || {
    route: "/trust/explorer/:receipt_id",
    apiRoute: "/v1/core-platform/trust/explorer/:receipt_id",
    pilotFlow: "/v1/core-platform/pilot/flow",
    zones: [
      "Timeline",
      "Actor",
      "Authority decision",
      "Payment receipt",
      "Replay result",
      "AI explanation",
    ],
  };
  const [packet, setPacket] = useState(null);
  const [loadState, setLoadState] = useState(receiptId ? "loading" : "idle");

  useEffect(() => {
    if (!receiptId) return;
    let cancelled = false;
    setLoadState("loading");
    fetch(`${apiBaseUrl}/v1/core-platform/trust/explorer/${receiptId}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Explorer request failed: ${res.status}`);
        return res.json();
      })
      .then((body) => {
        if (!cancelled) {
          setPacket(body);
          setLoadState("ready");
        }
      })
      .catch(() => {
        if (!cancelled) setLoadState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, receiptId]);

  const timeline = packet?.timeline || data.zones.map((zone) => ({
    label: zone,
    status: "ready",
    value: data.route,
  }));

  return (
    <div className="trust-explorer-frontend">
      <div className="record-card-header">
        <strong>Trust Explorer React Frontend</strong>
        <span>production UI</span>
      </div>
      <p>
        Public verification opens at {data.route}; authenticated operators can
        fetch the same packet from {data.apiRoute}.
      </p>
      {receiptId ? (
        <p>Live packet status: {loadState}</p>
      ) : null}
      <div className="trust-explorer-flow" aria-label="NovaTrust explorer verification flow">
        {timeline.map((item) => (
          <div key={item.label} className="trust-explorer-step">
            <span>{item.label}</span>
            <small>{item.status}</small>
          </div>
        ))}
      </div>
      <div className="chip-row">
        <span className="surface-chip">PDF audit export</span>
        <span className="surface-chip">Ed25519 signature</span>
        <span className="surface-chip">Read-only verification</span>
        <span className="surface-chip">{data.pilotFlow}</span>
      </div>
    </div>
  );
}
