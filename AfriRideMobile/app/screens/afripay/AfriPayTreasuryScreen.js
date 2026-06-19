import React, { useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import AppButton from "../../components/AppButton";
import AppCard from "../../components/AppCard";
import StatusBadge from "../../components/StatusBadge";
import { getNovaPayTreasuryPools } from "../../services/afripayService";
import { theme } from "../../theme/theme";

export default function NovaPayTreasuryScreen() {
  const [pools, setPools] = useState([]);
  const [error, setError] = useState(null);

  async function loadPools() {
    setError(null);
    try {
      const response = await getNovaPayTreasuryPools();
      setPools(response.pools || []);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadPools();
  }, []);

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Treasury</Text>
        <AppButton title="Refresh" variant="secondary" onPress={loadPools} />
      </View>
      <StatusBadge label="Liquidity-aware routing" tone="success" />
      {pools.map((pool) => (
        <AppCard key={pool.pool_id}>
          <View style={styles.poolHeader}>
            <Text style={styles.provider}>{pool.provider}</Text>
            <Text style={styles.currency}>{pool.currency}</Text>
          </View>
          <View style={styles.metrics}>
            <Metric label="Balance" value={pool.balance} />
            <Metric label="Reserved" value={pool.reserved} />
            <Metric label="Available" value={pool.available_balance} />
          </View>
        </AppCard>
      ))}
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </ScrollView>
  );
}

function Metric({ label, value }) {
  return (
    <View style={styles.metric}>
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
  poolHeader: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  provider: { color: theme.colors.text, fontSize: 16, fontWeight: "800" },
  currency: { color: theme.colors.muted, fontSize: 13, fontWeight: "800" },
  metrics: { flexDirection: "row", gap: theme.spacing.sm },
  metric: { flex: 1 },
  metricLabel: { color: theme.colors.muted, fontSize: 12, fontWeight: "700" },
  metricValue: { color: theme.colors.text, fontSize: 15, fontWeight: "800" },
  error: { color: theme.colors.danger, fontSize: 14, fontWeight: "700" },
});
