import React, { useEffect, useMemo, useState } from "react";

const API_BASE_URL =
  import.meta?.env?.VITE_AFRIRIDE_API_URL || "http://127.0.0.1:8000";

function toWsUrl(url) {
  if (url.startsWith("https://")) {
    return `wss://${url.slice("https://".length)}`;
  }
  if (url.startsWith("http://")) {
    return `ws://${url.slice("http://".length)}`;
  }
  if (url.startsWith("wss://") || url.startsWith("ws://")) {
    return url;
  }
  return `ws://${url}`;
}

async function readJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`fetch_failed:${path}`);
  }
  return response.json();
}

function Pill({ label, value }) {
  return (
    <div className="pill">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default function AnchorExplorer() {
  const [status, setStatus] = useState(null);
  const [indexSnapshot, setIndexSnapshot] = useState(null);
  const [verification, setVerification] = useState(null);
  const [reconciliation, setReconciliation] = useState(null);
  const [evidencePolicy, setEvidencePolicy] = useState(null);
  const [operationalSemantics, setOperationalSemantics] = useState(null);
  const [governedProtocol, setGovernedProtocol] = useState(null);
  const [mainnetGate, setMainnetGate] = useState(null);
  const [adrPreview, setAdrPreview] = useState(null);
  const [adrContractLink, setAdrContractLink] = useState(null);
  const [selectedAnchor, setSelectedAnchor] = useState(null);
  const [anchorDetail, setAnchorDetail] = useState(null);
  const [streamEvents, setStreamEvents] = useState([]);
  const [streamState, setStreamState] = useState("connecting");
  const [error, setError] = useState(null);
  const [adrId, setAdrId] = useState("ADR-0045");

  const wsUrl = useMemo(
    () => `${toWsUrl(API_BASE_URL)}/public/architecture/anchors/stream/ws`,
    [],
  );

  async function refreshAll() {
    setError(null);
    Promise.all([
      readJson("/public/architecture/anchors/status"),
      readJson("/public/architecture/anchors"),
      readJson("/public/architecture/anchors/verification"),
      readJson("/public/architecture/anchors/reconciliation"),
      readJson("/public/architecture/evidence/policy"),
      readJson("/public/architecture/evidence/semantics"),
      readJson("/public/architecture/evidence/protocol"),
      readJson("/public/architecture/anchors/mainnet-promotion-gate"),
      readJson("/public/architecture/adr/ADR-0045/hash"),
      readJson("/public/architecture/adr/ADR-0045/contract-link"),
      readJson("/public/architecture/anchors/stream/replay"),
    ])
      .then(([
        statusPayload,
        indexPayload,
        verificationPayload,
        reconciliationPayload,
        policyPayload,
        semanticsPayload,
        protocolPayload,
        gatePayload,
        adrPayload,
        contractLinkPayload,
        replayPayload,
      ]) => {
        setStatus(statusPayload);
        setIndexSnapshot(indexPayload);
        setVerification(verificationPayload);
        setReconciliation(reconciliationPayload);
        setEvidencePolicy(policyPayload);
        setOperationalSemantics(semanticsPayload);
        setGovernedProtocol(protocolPayload);
        setMainnetGate(gatePayload);
        setAdrPreview(adrPayload);
        setAdrContractLink(contractLinkPayload);
        setStreamEvents((current) => {
          const merged = [...(replayPayload.events || []), ...current];
          const seen = new Set();
          return merged.filter((event) => {
            const key = event.stream_event_id || JSON.stringify(event);
            if (seen.has(key)) {
              return false;
            }
            seen.add(key);
            return true;
          }).slice(0, 24);
        });
      })
      .catch((err) => {
        setError(err.message);
      });
  }

  useEffect(() => {
    let mounted = true;
    if (mounted) {
      refreshAll();
    }
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let socket;
    let retryTimer;
    let alive = true;

    function connect() {
      socket = new WebSocket(wsUrl);
      socket.onopen = () => {
        setStreamState("live");
        setError(null);
        socket.send("status");
      };
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.classification === "BLOCKCHAIN_ANCHOR_STREAM_SOCKET") {
            setStatus((current) => current ? { ...current, stream: payload.stream } : current);
            setIndexSnapshot((current) => current ? { ...current, latest: payload.index?.latest ?? current.latest, entries: payload.index?.entries ?? current.entries, count: payload.index?.count ?? current.count } : current);
          }
          if (payload.classification === "BLOCKCHAIN_ANCHOR_STREAM_REPLAY") {
            setStreamEvents((current) => [...(payload.events || []), ...current].slice(0, 24));
            return;
          }
          setStreamEvents((current) => [payload, ...current].slice(0, 24));
        } catch (err) {
          setStreamEvents((current) => [{ classification: "STREAM_PARSE_ERROR", message: String(err), raw: event.data }, ...current].slice(0, 24));
        }
      };
      socket.onerror = () => {
        setStreamState("error");
      };
      socket.onclose = () => {
        if (!alive) {
          return;
        }
        setStreamState("reconnecting");
        retryTimer = setTimeout(connect, 2000);
      };
    }

    connect();

    return () => {
      alive = false;
      if (retryTimer) {
        clearTimeout(retryTimer);
      }
      if (socket) {
        socket.close();
      }
    };
  }, [wsUrl]);

  async function loadAdrPreview() {
    try {
      const encoded = encodeURIComponent(adrId);
      const [hashPayload, linkPayload] = await Promise.all([
        readJson(`/public/architecture/adr/${encoded}/hash`),
        readJson(`/public/architecture/adr/${encoded}/contract-link`),
      ]);
      setAdrPreview(hashPayload);
      setAdrContractLink(linkPayload);
    } catch (err) {
      setError(err.message);
    }
  }

  async function selectAnchor(anchorId) {
    setSelectedAnchor(anchorId);
    try {
      setAnchorDetail(await readJson(`/public/architecture/anchors/${encodeURIComponent(anchorId)}`));
    } catch (err) {
      setError(err.message);
    }
  }

  async function replayStream() {
    try {
      const latestSequence = streamEvents.reduce(
        (max, event) => Math.max(max, Number(event.stream_sequence || 0)),
        0,
      );
      const replayPayload = await readJson(`/public/architecture/anchors/stream/replay?after_sequence=${latestSequence}`);
      setStreamEvents((current) => [...(replayPayload.events || []), ...current].slice(0, 24));
    } catch (err) {
      setError(err.message);
    }
  }

  const latestAnchor = indexSnapshot?.latest || null;
  const entryRows = indexSnapshot?.entries || [];
  const reconciliationRows = reconciliation?.entries || [];

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">AfriTech public trust surface</p>
          <h1>Anchor Explorer</h1>
          <p className="lede">
            Inspect blockchain anchors, stream updates over WebSocket, and reconcile
            cross-network publications without granting authority to the chain.
          </p>
          <div className="metrics">
            <Pill label="Stream" value={streamState} />
            <Pill label="Anchors" value={indexSnapshot?.count ?? 0} />
            <Pill label="Network" value={verification?.network ?? "n/a"} />
            <Pill label="Reconciled" value={reconciliation?.reconciled_count ?? 0} />
            <Pill label="Mainnet" value={mainnetGate?.status ?? "loading"} />
          </div>
        </div>
        <aside className="status-card">
          <div className="status-label">Verification</div>
          <strong>{verification?.verification_stage ?? "loading"}</strong>
          <span>{verification?.contract_explorer_url || "Awaiting contract verification packet."}</span>
          <code>{verification?.abi_fingerprint || "n/a"}</code>
          <button type="button" onClick={refreshAll}>Refresh</button>
        </aside>
      </header>

      {error ? <div className="error">{error}</div> : null}

      <section className="grid">
        <article className="panel">
          <h2>Anchor status</h2>
          <div className="kv">
            <div><span>Backend</span><strong>{indexSnapshot?.backend?.backend || "n/a"}</strong></div>
            <div><span>Transport</span><strong>{status?.stream?.transport || "websocket"}</strong></div>
            <div><span>Clients</span><strong>{status?.stream?.broadcast?.connected_clients ?? 0}</strong></div>
            <div><span>Last error</span><strong>{status?.stream?.last_error || "none"}</strong></div>
          </div>
        </article>

        <article className="panel">
          <h2>Latest publication</h2>
          <div className="kv compact">
            <div><span>Anchor</span><strong>{latestAnchor?.anchor_id || "n/a"}</strong></div>
            <div><span>Tx</span><strong>{latestAnchor?.transaction_hash || "n/a"}</strong></div>
            <div><span>Source</span><strong>{latestAnchor?.source || "n/a"}</strong></div>
            <div><span>Mode</span><strong>{latestAnchor?.anchor_mode || "n/a"}</strong></div>
          </div>
        </article>
      </section>

      <section className="panel">
        <div className="section-head">
          <h2>Live stream</h2>
          <button type="button" onClick={replayStream}>Replay</button>
        </div>
        <span className="mono-line">{wsUrl}</span>
        <div className="stream-list">
          {streamEvents.length === 0 ? <p>No events yet.</p> : null}
          {streamEvents.map((event, index) => (
            <article key={`${event.classification || "evt"}-${index}`} className="stream-event">
              <div className="stream-title">
                <strong>{event.event_type || event.classification || "STREAM_EVENT"}</strong>
                <span>#{event.stream_sequence || "n/a"} {event.network || event.status || "n/a"}</span>
              </div>
              <code>{event.anchor_id || event.transaction_hash || event.message || "n/a"}</code>
            </article>
          ))}
        </div>
      </section>

      <section className="grid">
        <article className="panel">
          <div className="section-head">
            <h2>Cross-network reconciliation</h2>
            <a href="/public/architecture/anchors/reconciliation">API</a>
          </div>
          <div className="kv compact">
            <div><span>Entries</span><strong>{reconciliation?.entries?.length ?? 0}</strong></div>
            <div><span>Divergent</span><strong>{reconciliation?.divergent_count ?? 0}</strong></div>
            <div><span>Partial</span><strong>{reconciliation?.partial_count ?? 0}</strong></div>
            <div><span>Reconciled</span><strong>{reconciliation?.reconciled_count ?? 0}</strong></div>
          </div>
          <div className="reconciliation-list">
            {reconciliationRows.slice(0, 6).map((row) => (
              <div key={`${row.proof_hash}-${row.anchor_id}`} className="reconciliation-row">
                <strong>{row.reconciliation_status}</strong>
                <span>{row.observed_networks?.join(", ") || "n/a"}</span>
                <code>{row.proof_hash}</code>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="section-head">
            <h2>ADR hash</h2>
            <a href={`/public/architecture/adr/${encodeURIComponent(adrId)}/hash`}>API</a>
          </div>
          <div className="adr-form">
            <input value={adrId} onChange={(event) => setAdrId(event.target.value)} />
            <button type="button" onClick={loadAdrPreview}>Load</button>
          </div>
          <div className="kv compact">
            <div><span>Title</span><strong>{adrPreview?.title || "n/a"}</strong></div>
            <div><span>State</span><strong>{adrPreview?.state || "n/a"}</strong></div>
            <div><span>Hash</span><strong>{adrPreview?.content_hash || "n/a"}</strong></div>
            <div><span>Method</span><strong>{adrContractLink?.contract_signature || "n/a"}</strong></div>
          </div>
          <code className="wide-code">
            {adrContractLink
              ? `${adrContractLink.contract_arguments.anchorId} / ${adrContractLink.contract_arguments.proofHash}`
              : "n/a"}
          </code>
        </article>
      </section>

      <section className="grid">
        <article className="panel">
          <div className="section-head">
            <h2>Mainnet gate</h2>
            <a href="/public/architecture/anchors/mainnet-promotion-gate">API</a>
          </div>
          <div className="kv compact">
            <div><span>Status</span><strong>{mainnetGate?.status || "n/a"}</strong></div>
            <div><span>Approved</span><strong>{String(mainnetGate?.approved ?? false)}</strong></div>
            <div><span>Required</span><strong>{mainnetGate?.required_networks?.join(", ") || "n/a"}</strong></div>
            <div><span>Blocks</span><strong>{mainnetGate?.blocking_findings?.length ?? 0}</strong></div>
          </div>
          <code className="wide-code">{mainnetGate?.promotion_rule || "n/a"}</code>
        </article>

        <article className="panel">
          <div className="section-head">
            <h2>Evidence policy</h2>
            <a href="/public/architecture/evidence/policy">API</a>
          </div>
          <div className="kv compact">
            <div><span>Invariants</span><strong>{evidencePolicy?.invariants?.length ?? 0}</strong></div>
            <div><span>Transport</span><strong>{evidencePolicy?.streaming_policy?.primary_transport || "n/a"}</strong></div>
            <div><span>Polling</span><strong>{evidencePolicy?.streaming_policy?.poll_endpoint_role || "n/a"}</strong></div>
            <div><span>Replay</span><strong>{evidencePolicy?.streaming_policy?.replay_endpoint || "n/a"}</strong></div>
          </div>
        </article>

        <article className="panel">
          <div className="section-head">
            <h2>Operational semantics</h2>
            <a href="/public/architecture/evidence/semantics">API</a>
          </div>
          <div className="kv compact">
            <div><span>States</span><strong>{operationalSemantics?.states?.length ?? 0}</strong></div>
            <div><span>Transitions</span><strong>{operationalSemantics?.transitions?.length ?? 0}</strong></div>
            <div><span>Truth</span><strong>{operationalSemantics?.truth_model?.truth_authority || "n/a"}</strong></div>
            <div><span>Initial</span><strong>{operationalSemantics?.lifecycle?.initial_state || "n/a"}</strong></div>
          </div>
          <code className="wide-code">{operationalSemantics?.semantics_hash || "n/a"}</code>
        </article>

        <article className="panel">
          <div className="section-head">
            <h2>Evidence protocol</h2>
            <a href="/public/architecture/evidence/protocol">API</a>
          </div>
          <div className="kv compact">
            <div><span>Status</span><strong>{governedProtocol?.status || "n/a"}</strong></div>
            <div><span>Version</span><strong>{governedProtocol?.protocol_version || "n/a"}</strong></div>
            <div><span>System</span><strong>{governedProtocol?.system_identity?.name || "n/a"}</strong></div>
            <div><span>Artifacts</span><strong>{governedProtocol?.governance_artifacts?.length ?? 0}</strong></div>
          </div>
          <code className="wide-code">{governedProtocol?.protocol_hash || "n/a"}</code>
        </article>
      </section>

      <section className="grid">
        <article className="panel">
          <div className="section-head">
            <h2>Anchor detail</h2>
            <span>{selectedAnchor || "none selected"}</span>
          </div>
          <div className="kv compact">
            <div><span>Status</span><strong>{anchorDetail?.status || "n/a"}</strong></div>
            <div><span>Rows</span><strong>{anchorDetail?.related_entries?.length ?? 0}</strong></div>
            <div><span>Network</span><strong>{anchorDetail?.entry?.network || "n/a"}</strong></div>
            <div><span>Block</span><strong>{anchorDetail?.entry?.block_number || "n/a"}</strong></div>
          </div>
          <code className="wide-code">{anchorDetail?.entry?.explorer_url || "n/a"}</code>
        </article>

        <article className="panel">
          <div className="section-head">
            <h2>Contract link</h2>
            <a href={`/public/architecture/adr/${encodeURIComponent(adrId)}/contract-link`}>API</a>
          </div>
          <div className="kv compact">
            <div><span>Contract</span><strong>{adrContractLink?.contract_name || "n/a"}</strong></div>
            <div><span>Chain</span><strong>{adrContractLink?.chain_id || "n/a"}</strong></div>
            <div><span>Anchor</span><strong>{adrContractLink?.anchor_id || "n/a"}</strong></div>
            <div><span>Publication</span><strong>{adrContractLink?.publication_id || "n/a"}</strong></div>
          </div>
        </article>
      </section>

      <section className="panel">
        <div className="section-head">
          <h2>Anchor index</h2>
          <a href="/public/architecture/anchors">API</a>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Anchor</th>
                <th>Network</th>
                <th>Status</th>
                <th>Tx</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {entryRows.length === 0 ? (
                <tr>
                  <td colSpan="6">No anchors indexed yet.</td>
                </tr>
              ) : (
                entryRows.map((entry) => (
                  <tr key={`${entry.anchor_id}-${entry.sequence}`}>
                    <td>{entry.sequence}</td>
                    <td><button type="button" className="link-button" onClick={() => selectAnchor(entry.anchor_id)}>{entry.anchor_id}</button></td>
                    <td>{entry.network}</td>
                    <td>{entry.status}</td>
                    <td>{entry.transaction_hash || "n/a"}</td>
                    <td>{entry.source}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
