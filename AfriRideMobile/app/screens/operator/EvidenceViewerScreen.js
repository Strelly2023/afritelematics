import React, { useState } from "react";
import { View } from "react-native";
import AppButton from "../../components/AppButton";
import AppHeader from "../../components/AppHeader";
import EvidenceCard from "../../components/EvidenceCard";
import { getEvidenceSummary, getGuardViolations } from "../../services/evidenceService";
import { theme } from "../../theme/theme";

export default function EvidenceViewerScreen() {
  const [evidence, setEvidence] = useState(null);
  const [guards, setGuards] = useState(null);

  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, gap: 14 }}>
      <AppHeader title="Evidence Viewer" subtitle="Evidence visibility without certification authority." />
      <AppButton title="Load Evidence Summary" onPress={async () => setEvidence(await getEvidenceSummary())} />
      <AppButton title="Load Guard Violations" onPress={async () => setGuards(await getGuardViolations())} />
      <EvidenceCard title="Evidence Summary" evidence={evidence} />
      <EvidenceCard title="Guard Violations" evidence={guards} />
    </View>
  );
}
