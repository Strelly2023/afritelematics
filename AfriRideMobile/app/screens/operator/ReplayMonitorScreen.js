import React, { useState } from "react";
import { View } from "react-native";
import AppButton from "../../components/AppButton";
import AppHeader from "../../components/AppHeader";
import EvidenceCard from "../../components/EvidenceCard";
import { getReplayHealth } from "../../services/replayService";
import { theme } from "../../theme/theme";

export default function ReplayMonitorScreen() {
  const [health, setHealth] = useState(null);

  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Replay Monitor" subtitle="Displays replay health reported by backend." />
      <AppButton title="Refresh Replay Health" onPress={async () => setHealth(await getReplayHealth())} />
      <EvidenceCard title="Replay Health" evidence={health} />
    </View>
  );
}
