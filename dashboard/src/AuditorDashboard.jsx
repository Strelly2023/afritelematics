import React, { useEffect, useMemo, useState } from "react";

export function AuditorDashboard({ receiptIds = [], apiBaseUrl = "" }) {
  const [dashboard, setDashboard] = useState(null);
  const [state, setState] = useState(receiptIds.length ? "loading" : "idle");
  const ids = useMemo(() => receiptIds.filter(Boolean), [receiptIds]);

  useEffect(() => {
    if (!ids.length) return;
    let cancelled = false;
    setState("loading");
    fetch(`${apiBaseUrl}/trust/auditor/dashboard?ids=${encodeURIComponent(ids.join(","))}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Auditor dashboard failed: ${res.status}`);
        return res.json();
      })
      .then((body) => {
        if (!cancelled) {
          setDashboard(body);
          setState("ready");
        }
      })
      .catch(() => {
        if (!cancelled) setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, ids]);

  const items = dashboard?.items || ids.map((id) => ({
    identifier: id,
    signature_verified: "pending",
    explorer: `/trust/explorer/${id}`,
    pdf: `/trust/explorer/${id}/audit.pdf`,
  }));

  return (
    <div className="auditor-dashboard">
      <div className="record-card-header">
        <strong>Real-time Auditor Dashboard</strong>
        <span>{state}</span>
      </div>
      <p>Multi-receipt verification for external auditors and regulators.</p>
      <div className="auditor-dashboard-grid">
        {items.map((item) => (
          <article key={item.identifier} className="record-card">
            <div className="record-card-header">
              <strong>{item.identifier}</strong>
              <span>{String(item.signature_verified)}</span>
            </div>
            <p>{item.explorer}</p>
            <p>{item.pdf}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
