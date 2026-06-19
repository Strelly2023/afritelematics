import React, { useCallback, useEffect, useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import AppButton from "../../components/AppButton";
import AppCard from "../../components/AppCard";
import StatusBadge from "../../components/StatusBadge";
import { anchorNovaPayProof, exportNovaPayProof } from "../../services/afripayService";
import { theme } from "../../theme/theme";

export default function NovaPayAuditScreen() {
  const [proof, setProof] = useState(null);
  const [anchorReceipt, setAnchorReceipt] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const proofHash = proof?.proof_hash || proof?.global_proof_hash || proof?.transaction_report_hash || null;
  const anchorProfile = useMemo(() => "mainnet", []);

  const loadProof = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const response = await exportNovaPayProof({ anchor_network: "external_log" });
      setProof(response);
      setAnchorReceipt(response.chain_receipt || null);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }, []);

  const anchorProof = useCallback(async () => {
    if (!proofHash) {
      setError("Load a proof before anchoring.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const response = await anchorNovaPayProof(
        {
          proof_hash: proofHash,
          profile_name: anchorProfile,
          require_live: true,
        }
      );
      setAnchorReceipt(response.chain_receipt || null);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }, [anchorProfile, proofHash]);

  useEffect(() => {
    loadProof();
  }, [loadProof]);

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Audit Proofs</Text>
        <AppButton title="Refresh" variant="secondary" onPress={loadProof} />
      </View>

      <StatusBadge label="Verifiable payment evidence" tone="success" />

      <AppCard style={styles.highlight}>
        <Text style={styles.label}>Proof hash</Text>
        <Text style={styles.hash}>{proofHash || "Loading..."}</Text>
        <Text style={styles.muted}>
          Exported proof bundle for the current global ledger snapshot.
        </Text>
      </AppCard>

      <View style={styles.actions}>
        <AppButton title="Anchor mainnet" onPress={anchorProof} disabled={busy || !proofHash} />
        <AppButton title="Reload" variant="secondary" onPress={loadProof} disabled={busy} />
      </View>

      <Text style={styles.sectionTitle}>Ledger proof</Text>
      <AppCard>
        <Metric label="Scope" value={proof?.scope || "-"} />
        <Metric label="Anchor network" value={proof?.anchor_network || "-"} />
        <Metric label="Global proof" value={proof?.global_proof_hash || "-"} />
        <Metric label="Audit root" value={proof?.audit_merkle_root || "-"} />
        <Metric label="Ledger root" value={proof?.ledger_merkle_root || "-"} />
      </AppCard>

      <Text style={styles.sectionTitle}>Transaction proof</Text>
      <AppCard>
        <Metric label="Reference" value={proof?.reference || "Global export"} />
        <Metric label="Report hash" value={proof?.transaction_report_hash || proof?.global_proof_hash || "-"} />
        <Metric label="Inclusion proof" value={proof?.transaction_inclusion_proof?.verified ? "Verified" : "Not loaded"} />
        <Metric label="ZK attestation" value={proof?.transaction_zk_attestation?.verified ? "Verified" : "Not loaded"} />
      </AppCard>

      <Text style={styles.sectionTitle}>Chain receipt</Text>
      <AppCard>
        <Metric label="Status" value={anchorReceipt?.status || "Not anchored"} />
        <Metric label="Network" value={anchorReceipt?.network || "-"} />
        <Metric label="Tx hash" value={anchorReceipt?.tx_hash || "-"} />
        <Metric label="Explorer" value={anchorReceipt?.explorer_url || "-"} />
      </AppCard>

      {error ? <Text style={styles.error}>{error}</Text> : null}
    </ScrollView>
  );
}

function Metric({ label, value }) {
  return (
    <View style={styles.metricRow}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { backgroundColor: theme.colors.background },
  content: { gap: theme.spacing.md, padding: theme.spacing.md },
  header: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  title: { color: theme.colors.text, fontSize: 24, fontWeight: "800" },
  highlight: { backgroundColor: "#F7FAFF" },
  label: { color: theme.colors.muted, fontSize: 12, fontWeight: "700" },
  hash: { color: theme.colors.text, fontSize: 15, fontWeight: "800" },
  muted: { color: theme.colors.muted, fontSize: 13 },
  actions: { flexDirection: "row", gap: theme.spacing.sm },
  sectionTitle: { color: theme.colors.text, fontSize: 18, fontWeight: "700", marginTop: theme.spacing.sm },
  metricRow: { marginBottom: theme.spacing.sm },
  metricLabel: { color: theme.colors.muted, fontSize: 12, fontWeight: "700" },
  metricValue: { color: theme.colors.text, fontSize: 14, fontWeight: "800" },
  error: { color: theme.colors.danger, fontSize: 14, fontWeight: "700" },
});
