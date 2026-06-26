import React, { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  ScrollView,
  View,
} from "react-native";
import { formatCount, formatHash, formatMoney } from "./proofLayer";
import { selectZkBundle, summarizeZkBundle } from "./zkProofLayer.js";

export const colors = {
  background: "#07111f",
  backgroundAlt: "#0d1727",
  surface: "rgba(14, 24, 40, 0.92)",
  surfaceSoft: "rgba(18, 31, 49, 0.88)",
  surfaceElevated: "#132338",
  border: "rgba(160, 187, 220, 0.14)",
  text: "#f4f8ff",
  muted: "#97a9c2",
  faint: "#71849f",
  accent: "#66e3ff",
  accentSoft: "rgba(102, 227, 255, 0.16)",
  mint: "#88efba",
  mintSoft: "rgba(136, 239, 186, 0.16)",
  amber: "#ffc978",
  amberSoft: "rgba(255, 201, 120, 0.18)",
  danger: "#ff7d7d",
  dangerSoft: "rgba(255, 125, 125, 0.14)",
  success: "#8be8b2",
  successSoft: "rgba(139, 232, 178, 0.14)",
};

export function normalizeText(value, fallback = "—") {
  if (value === null || value === undefined) {
    return fallback;
  }
  const text = String(value).trim();
  return text.length > 0 ? text : fallback;
}

export function humanizeStatus(value, fallback = "Ready") {
  if (!value) {
    return fallback;
  }

  const text = String(value)
    .replace(/[_-]+/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

  return text || fallback;
}

export function statusTone(value) {
  const normalized = String(value || "").toUpperCase();
  if (["COMPLETED", "ACTIVE", "ONLINE", "VERIFIED", "SETTLED", "READY"].includes(normalized)) {
    return "success";
  }
  if (["ARRIVED", "STARTED", "IN_PROGRESS", "PENDING"].includes(normalized)) {
    return "amber";
  }
  if (["FAILED", "CANCELLED", "OFFLINE", "BLOCKED"].includes(normalized)) {
    return "danger";
  }
  return "neutral";
}

export { formatCount, formatHash, formatMoney };

export function AppShell({ children }) {
  return (
    <View style={styles.screen}>
      {children}
    </View>
  );
}

export function ShellScroll({ children, contentStyle }) {
  return (
    <ScrollView
      showsVerticalScrollIndicator={false}
      contentContainerStyle={[styles.scrollBody, contentStyle]}
    >
      {children}
    </ScrollView>
  );
}

export function Hero({ eyebrow, title, subtitle, right, children }) {
  return (
    <View style={styles.hero}>
      <View style={styles.heroRow}>
        <View style={{ flex: 1 }}>
          <Text style={styles.eyebrow}>{eyebrow}</Text>
          <Text style={styles.heroTitle}>{title}</Text>
          {subtitle ? <Text style={styles.heroSubtitle}>{subtitle}</Text> : null}
        </View>
        {right ? <View style={styles.heroRight}>{right}</View> : null}
      </View>
      {children}
    </View>
  );
}

export function StatGrid({ children }) {
  return <View style={styles.statGrid}>{children}</View>;
}

export function StatCard({ label, value, detail, tone = "neutral" }) {
  return (
    <View style={[styles.statCard, toneStyles[tone] || toneStyles.neutral]}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statValue}>{value}</Text>
      {detail ? <Text style={styles.statDetail}>{detail}</Text> : null}
    </View>
  );
}

export function SectionCard({ title, eyebrow, action, children, compact = false }) {
  return (
    <View style={[styles.sectionCard, compact ? styles.sectionCardCompact : null]}>
      <View style={styles.sectionHeader}>
        <View style={{ flex: 1 }}>
          {eyebrow ? <Text style={styles.sectionEyebrow}>{eyebrow}</Text> : null}
          <Text style={styles.sectionTitle}>{title}</Text>
        </View>
        {action ? <View>{action}</View> : null}
      </View>
      {children}
    </View>
  );
}

export function LiveSurface({
  eyebrow,
  title,
  subtitle,
  status,
  assistant,
  primaryAction,
  secondaryActions,
  children,
}) {
  return (
    <View style={styles.liveSurface}>
      <View style={styles.liveSurfaceTop}>
        <View style={{ flex: 1 }}>
          {eyebrow ? <Text style={styles.sectionEyebrow}>{eyebrow}</Text> : null}
          <Text style={styles.liveTitle}>{title}</Text>
          {subtitle ? <Text style={styles.liveSubtitle}>{subtitle}</Text> : null}
        </View>
        {status ? <Pill label={status.label} tone={status.tone} /> : null}
      </View>

      <View style={styles.liveCanvas}>
        <View style={styles.liveMapGlowA} />
        <View style={styles.liveMapGlowB} />
        <View style={styles.liveRouteStart} />
        <View style={styles.liveRouteLine} />
        <View style={styles.liveRouteEnd} />
        <View style={styles.liveRoutePinA} />
        <View style={styles.liveRoutePinB} />
        <View style={styles.liveOverlayTop}>
          <Pill label="Live" tone="accent" />
          {status ? <Pill label={status.secondary || status.label} tone={status.tone} /> : null}
        </View>
        <View style={styles.liveOverlayBottom}>
          <View style={styles.assistantBubble}>
            <Text style={styles.assistantLabel}>Nova Assistant</Text>
            <Text style={styles.assistantText}>{assistant}</Text>
          </View>
        </View>
      </View>

      {children}

      {primaryAction ? <View style={styles.livePrimary}>{primaryAction}</View> : null}
      {secondaryActions ? <View style={styles.liveSecondary}>{secondaryActions}</View> : null}
    </View>
  );
}

export function ModeStrip({ modes, active, onChange }) {
  return (
    <View style={styles.modeStrip}>
      {modes.map((mode) => {
        const selected = mode.value === active;
        return (
          <Pressable
            key={mode.value}
            onPress={() => onChange(mode.value)}
            style={[styles.modeChip, selected ? styles.modeChipActive : null]}
          >
            <Text style={[styles.modeChipText, selected ? styles.modeChipTextActive : null]}>
              {mode.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export function MetricBand({ items }) {
  return (
    <View style={styles.metricBand}>
      {items.map((item) => (
        <View key={item.label} style={[styles.metricItem, toneStyles[item.tone] || toneStyles.neutral]}>
          <Text style={styles.metricLabel}>{item.label}</Text>
          <Text style={styles.metricValue}>{item.value}</Text>
          {item.detail ? <Text style={styles.metricDetail}>{item.detail}</Text> : null}
        </View>
      ))}
    </View>
  );
}

export function ProofPanel({
  eyebrow = "Verification",
  title,
  subtitle,
  verdict,
  verdictTone = "accent",
  metrics = [],
  hashes = [],
  children,
}) {
  return (
    <View style={styles.proofPanel}>
      <View style={styles.proofHeader}>
        <View style={{ flex: 1 }}>
          {eyebrow ? <Text style={styles.sectionEyebrow}>{eyebrow}</Text> : null}
          <Text style={styles.sectionTitle}>{title}</Text>
          {subtitle ? <Text style={styles.sectionSummary}>{subtitle}</Text> : null}
        </View>
        {verdict ? <Pill label={verdict} tone={verdictTone} /> : null}
      </View>

      {metrics.length ? <MetricBand items={metrics} /> : null}

      {hashes.length ? (
        <View style={styles.proofHashes}>
          {hashes.map((item, index) => (
            <InfoRow
              key={`${item.label}-${index}`}
              label={item.label}
              value={item.value}
              tone={item.tone || "muted"}
            />
          ))}
        </View>
      ) : null}

      {children}
    </View>
  );
}

export function ZkProofPanel({
  title = "ZK proof mode",
  subtitle = "Privacy-preserving receipts verify without exposing raw sensitive fields.",
  bundle,
  receipt,
  bridge,
}) {
  const resolvedBundle = bundle || selectZkBundle({ receipt, bridge });
  const summary = summarizeZkBundle(resolvedBundle);

  return (
    <View style={styles.zkPanel}>
      <View style={styles.proofHeader}>
        <View style={{ flex: 1 }}>
          <Text style={styles.sectionEyebrow}>Privacy</Text>
          <Text style={styles.sectionTitle}>{title}</Text>
          <Text style={styles.sectionSummary}>{subtitle}</Text>
        </View>
        <Pill label={summary.label} tone={summary.tone} />
      </View>

      <View style={styles.zkSummaryRow}>
        <View style={styles.zkPrivacyBadge}>
          <Text style={styles.zkPrivacyLabel}>Privacy level</Text>
          <Text style={styles.zkPrivacyValue}>{summary.privacyLevel}</Text>
        </View>
        <View style={styles.zkPrivacyBadge}>
          <Text style={styles.zkPrivacyLabel}>Hidden fields</Text>
          <Text style={styles.zkPrivacyValue}>{formatCount(summary.hiddenFieldCount, "0")}</Text>
        </View>
        <View style={styles.zkPrivacyBadge}>
          <Text style={styles.zkPrivacyLabel}>Chain</Text>
          <Text style={styles.zkPrivacyValue}>{summary.chainId || "—"}</Text>
        </View>
      </View>

      <Text style={styles.zkReason}>{summary.reason}</Text>

      <View style={styles.zkHashes}>
        <InfoRow
          label="Receipt hash"
          value={formatHash(summary.receiptHash, "—")}
          tone={summary.receiptHash ? "accent" : "muted"}
        />
        <InfoRow
          label="Commitment"
          value={formatHash(summary.commitment, "—")}
          tone={summary.commitment ? "success" : "muted"}
        />
        <InfoRow
          label="Proof hash"
          value={formatHash(summary.proofHash, "—")}
          tone={summary.proofHash ? "accent" : "muted"}
        />
        <InfoRow
          label="Bridge hash"
          value={formatHash(summary.bridgeHash, "—")}
          tone={summary.bridgeHash ? "success" : "muted"}
        />
      </View>

      {summary.hiddenFields?.length ? (
        <View style={styles.zkHiddenFields}>
          <Text style={styles.zkHiddenTitle}>Hidden fields</Text>
          <Text style={styles.zkHiddenText}>{summary.hiddenFields.join(", ")}</Text>
        </View>
      ) : null}
    </View>
  );
}

export function MissionCard({ title, subtitle, step, trust, assistant, actionLabel, onPress }) {
  return (
    <View style={styles.missionCard}>
      <View style={styles.missionTopRow}>
        <View style={{ flex: 1 }}>
          <Text style={styles.sectionEyebrow}>Current Mission</Text>
          <Text style={styles.missionTitle}>{title}</Text>
          {subtitle ? <Text style={styles.missionSubtitle}>{subtitle}</Text> : null}
        </View>
        {trust ? <Pill label={trust} tone="accent" /> : null}
      </View>
      {step ? <Text style={styles.missionStep}>{step}</Text> : null}
      <View style={styles.assistantBubble}>
        <Text style={styles.assistantLabel}>Nova Assistant</Text>
        <Text style={styles.assistantText}>{assistant}</Text>
      </View>
      {actionLabel ? (
        <ActionButton title={actionLabel} onPress={onPress} />
      ) : null}
    </View>
  );
}

export function MapPanel({ title = "Spatial view", subtitle, children }) {
  return (
    <View style={styles.mapPanel}>
      <View style={styles.mapPanelHeader}>
        <View style={{ flex: 1 }}>
          <Text style={styles.sectionEyebrow}>Spatial</Text>
          <Text style={styles.sectionTitle}>{title}</Text>
          {subtitle ? <Text style={styles.sectionSummary}>{subtitle}</Text> : null}
        </View>
        <Pill label="Map" tone="accent" />
      </View>
      <View style={styles.mapCanvas}>
        <View style={styles.mapGlowA} />
        <View style={styles.mapGlowB} />
        <View style={styles.mapGridA} />
        <View style={styles.mapGridB} />
        {children}
      </View>
    </View>
  );
}

export function Pill({ label, tone = "neutral" }) {
  return (
    <View style={[styles.pill, pillToneStyles[tone] || pillToneStyles.neutral]}>
      <Text style={styles.pillText}>{label}</Text>
    </View>
  );
}

export function ActionButton({
  title,
  onPress,
  disabled,
  tone = "primary",
  compact = false,
  flex = false,
}) {
  return (
    <Pressable
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        flex ? styles.buttonFlex : null,
        compact ? styles.buttonCompact : null,
        buttonToneStyles[tone] || buttonToneStyles.primary,
        disabled ? styles.buttonDisabled : null,
        pressed && !disabled ? styles.buttonPressed : null,
      ]}
    >
      <Text style={[styles.buttonText, tone === "secondary" ? styles.buttonTextDark : null]}>
        {title}
      </Text>
    </Pressable>
  );
}

export function Field({ label, ...props }) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        autoCapitalize="none"
        autoCorrect={false}
        placeholderTextColor={colors.faint}
        style={styles.input}
        {...props}
      />
    </View>
  );
}

export function InfoRow({ label, value, tone = "muted" }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={[styles.infoValue, toneTextStyles[tone] || toneTextStyles.muted]}>
        {value}
      </Text>
    </View>
  );
}

export function Divider() {
  return <View style={styles.divider} />;
}

export function RouteGlyph() {
  return (
    <View style={styles.routeGlyph}>
      <View style={[styles.routeDot, styles.routeDotStart]} />
      <View style={styles.routeLine} />
      <View style={[styles.routeDot, styles.routeDotEnd]} />
    </View>
  );
}

export function Timeline({ items }) {
  return (
    <View style={styles.timeline}>
      {items.map((item, index) => (
        <View key={`${item.label}-${index}`} style={styles.timelineRow}>
          <View style={[styles.timelineDot, item.done ? styles.timelineDotDone : null]} />
          <View style={{ flex: 1 }}>
            <Text style={styles.timelineLabel}>{item.label}</Text>
            {item.detail ? <Text style={styles.timelineDetail}>{item.detail}</Text> : null}
          </View>
          {item.value ? <Text style={styles.timelineValue}>{item.value}</Text> : null}
        </View>
      ))}
    </View>
  );
}

export function ExpandableCard({ title, eyebrow, summary, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <View style={styles.expandableCard}>
      <Pressable onPress={() => setOpen((current) => !current)} style={styles.expandableHeader}>
        <View style={{ flex: 1 }}>
          {eyebrow ? <Text style={styles.sectionEyebrow}>{eyebrow}</Text> : null}
          <Text style={styles.sectionTitle}>{title}</Text>
          {summary ? <Text style={styles.sectionSummary}>{summary}</Text> : null}
        </View>
        <Text style={styles.expandableToggle}>{open ? "Hide" : "Show"}</Text>
      </Pressable>
      {open ? <View style={styles.expandableBody}>{children}</View> : null}
    </View>
  );
}

export function JsonCard({ value, empty, maxHeight = 240 }) {
  return (
    <View style={[styles.jsonCard, { maxHeight }]}>
      <Text style={styles.jsonText}>
        {value ? JSON.stringify(value, null, 2) : empty}
      </Text>
    </View>
  );
}

export function LoadingOverlay({ label = "Working" }) {
  return (
    <View style={styles.loadingWrap}>
      <ActivityIndicator color={colors.accent} />
      <Text style={styles.loadingText}>{label}</Text>
    </View>
  );
}

const toneStyles = {
  neutral: {
    backgroundColor: colors.surfaceSoft,
    borderColor: colors.border,
  },
  accent: {
    backgroundColor: colors.accentSoft,
    borderColor: "rgba(102, 227, 255, 0.34)",
  },
  success: {
    backgroundColor: colors.successSoft,
    borderColor: "rgba(139, 232, 178, 0.34)",
  },
  amber: {
    backgroundColor: colors.amberSoft,
    borderColor: "rgba(255, 201, 120, 0.34)",
  },
  danger: {
    backgroundColor: colors.dangerSoft,
    borderColor: "rgba(255, 125, 125, 0.34)",
  },
};

const pillToneStyles = {
  neutral: {
    backgroundColor: "rgba(148, 163, 184, 0.12)",
  },
  success: {
    backgroundColor: "rgba(139, 232, 178, 0.18)",
  },
  amber: {
    backgroundColor: "rgba(255, 201, 120, 0.18)",
  },
  danger: {
    backgroundColor: "rgba(255, 125, 125, 0.16)",
  },
  accent: {
    backgroundColor: "rgba(102, 227, 255, 0.18)",
  },
};

const buttonToneStyles = {
  primary: {
    backgroundColor: colors.accent,
  },
  secondary: {
    backgroundColor: "rgba(255, 255, 255, 0.08)",
    borderWidth: 1,
    borderColor: colors.border,
  },
  danger: {
    backgroundColor: colors.danger,
  },
};

const toneTextStyles = {
  muted: { color: colors.muted },
  accent: { color: colors.accent },
  success: { color: colors.success },
  danger: { color: colors.danger },
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  glowA: {
    position: "absolute",
    top: -90,
    right: -90,
    width: 220,
    height: 220,
    borderRadius: 220,
    backgroundColor: "rgba(102, 227, 255, 0.14)",
  },
  glowB: {
    position: "absolute",
    top: 120,
    left: -70,
    width: 180,
    height: 180,
    borderRadius: 180,
    backgroundColor: "rgba(136, 239, 186, 0.10)",
  },
  glowC: {
    position: "absolute",
    bottom: 100,
    right: -60,
    width: 160,
    height: 160,
    borderRadius: 160,
    backgroundColor: "rgba(255, 201, 120, 0.08)",
  },
  scrollBody: {
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 28,
    gap: 14,
  },
  hero: {
    borderRadius: 28,
    padding: 18,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 14,
  },
  heroRow: {
    flexDirection: "row",
    gap: 12,
    alignItems: "flex-start",
  },
  heroRight: {
    alignItems: "flex-end",
  },
  eyebrow: {
    color: colors.accent,
    textTransform: "uppercase",
    letterSpacing: 1.6,
    fontSize: 11,
    fontWeight: "800",
    marginBottom: 6,
  },
  heroTitle: {
    color: colors.text,
    fontSize: 29,
    lineHeight: 34,
    fontWeight: "800",
  },
  heroSubtitle: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 20,
    marginTop: 8,
  },
  statGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  statCard: {
    width: "48%",
    minWidth: 150,
    borderRadius: 22,
    padding: 14,
    borderWidth: 1,
    gap: 6,
  },
  statLabel: {
    color: colors.muted,
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: 1,
    fontWeight: "700",
  },
  statValue: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "800",
  },
  statDetail: {
    color: colors.faint,
    fontSize: 12,
    lineHeight: 17,
  },
  sectionCard: {
    borderRadius: 26,
    padding: 16,
    backgroundColor: colors.surfaceSoft,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 12,
  },
  proofPanel: {
    borderRadius: 26,
    padding: 16,
    backgroundColor: colors.surfaceSoft,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 12,
  },
  zkPanel: {
    borderRadius: 26,
    padding: 16,
    backgroundColor: "rgba(8, 20, 34, 0.92)",
    borderWidth: 1,
    borderColor: "rgba(102, 227, 255, 0.26)",
    gap: 12,
  },
  proofHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
  },
  proofHashes: {
    gap: 2,
  },
  zkSummaryRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  zkPrivacyBadge: {
    flexGrow: 1,
    minWidth: 96,
    borderRadius: 16,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    gap: 4,
  },
  zkPrivacyLabel: {
    color: colors.faint,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.6,
    textTransform: "uppercase",
  },
  zkPrivacyValue: {
    color: colors.text,
    fontSize: 15,
    fontWeight: "700",
  },
  zkReason: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
  },
  zkHashes: {
    gap: 2,
  },
  zkHiddenFields: {
    borderRadius: 16,
    padding: 12,
    backgroundColor: "rgba(102, 227, 255, 0.08)",
    borderWidth: 1,
    borderColor: "rgba(102, 227, 255, 0.16)",
    gap: 4,
  },
  zkHiddenTitle: {
    color: colors.accent,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.5,
    textTransform: "uppercase",
  },
  zkHiddenText: {
    color: colors.text,
    fontSize: 13,
    lineHeight: 18,
  },
  sectionCardCompact: {
    padding: 14,
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
  },
  sectionEyebrow: {
    color: colors.faint,
    fontSize: 11,
    textTransform: "uppercase",
    letterSpacing: 1.2,
    marginBottom: 4,
    fontWeight: "700",
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: "800",
  },
  sectionSummary: {
    color: colors.muted,
    fontSize: 13,
    marginTop: 4,
    lineHeight: 18,
  },
  pill: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderWidth: 1,
  },
  pillText: {
    color: colors.text,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.2,
  },
  button: {
    borderRadius: 18,
    paddingVertical: 14,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 50,
  },
  buttonFlex: {
    flex: 1,
  },
  buttonCompact: {
    minHeight: 44,
    paddingVertical: 12,
    paddingHorizontal: 14,
  },
  buttonDisabled: {
    opacity: 0.55,
  },
  buttonPressed: {
    transform: [{ scale: 0.985 }],
  },
  buttonText: {
    color: "#04111e",
    fontSize: 15,
    fontWeight: "800",
  },
  buttonTextDark: {
    color: colors.text,
  },
  field: {
    gap: 6,
  },
  fieldLabel: {
    color: colors.muted,
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: 0.9,
    fontWeight: "700",
  },
  input: {
    color: colors.text,
    backgroundColor: colors.surfaceElevated,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: 14,
    paddingVertical: 13,
    fontSize: 15,
  },
  infoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12,
    paddingVertical: 8,
  },
  infoLabel: {
    color: colors.muted,
    fontSize: 13,
    flex: 1,
  },
  infoValue: {
    fontSize: 13,
    fontWeight: "700",
    textAlign: "right",
    flexShrink: 1,
  },
  divider: {
    height: 1,
    backgroundColor: colors.border,
    marginVertical: 4,
  },
  routeGlyph: {
    width: 18,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 74,
  },
  routeDot: {
    width: 12,
    height: 12,
    borderRadius: 12,
    backgroundColor: colors.accent,
  },
  routeDotStart: {
    backgroundColor: colors.mint,
  },
  routeDotEnd: {
    backgroundColor: colors.amber,
  },
  routeLine: {
    width: 2,
    flex: 1,
    marginVertical: 6,
    backgroundColor: "rgba(160, 187, 220, 0.28)",
  },
  timeline: {
    gap: 10,
  },
  timelineRow: {
    flexDirection: "row",
    gap: 10,
    alignItems: "flex-start",
  },
  timelineDot: {
    width: 11,
    height: 11,
    borderRadius: 11,
    marginTop: 4,
    backgroundColor: "rgba(160, 187, 220, 0.34)",
  },
  timelineDotDone: {
    backgroundColor: colors.success,
  },
  timelineLabel: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
  },
  timelineDetail: {
    color: colors.muted,
    fontSize: 12,
    marginTop: 2,
    lineHeight: 17,
  },
  timelineValue: {
    color: colors.accent,
    fontSize: 12,
    fontWeight: "700",
  },
  expandableCard: {
    borderRadius: 24,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surfaceSoft,
    overflow: "hidden",
  },
  expandableHeader: {
    padding: 16,
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
  },
  expandableToggle: {
    color: colors.accent,
    fontSize: 12,
    fontWeight: "800",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  expandableBody: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    gap: 12,
  },
  jsonCard: {
    backgroundColor: colors.backgroundAlt,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 14,
    overflow: "hidden",
  },
  jsonText: {
    color: colors.text,
    fontFamily: "Courier",
    fontSize: 12,
    lineHeight: 17,
  },
  loadingWrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    justifyContent: "center",
    paddingVertical: 6,
  },
  loadingText: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
  },
  liveSurface: {
    borderRadius: 28,
    padding: 16,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 14,
  },
  liveSurfaceTop: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
  },
  liveTitle: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "800",
    lineHeight: 30,
  },
  liveSubtitle: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
    marginTop: 6,
  },
  liveCanvas: {
    minHeight: 220,
    borderRadius: 24,
    backgroundColor: colors.backgroundAlt,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: "hidden",
    padding: 16,
    justifyContent: "space-between",
  },
  liveMapGlowA: {
    position: "absolute",
    top: 24,
    right: 24,
    width: 120,
    height: 120,
    borderRadius: 120,
    backgroundColor: "rgba(102, 227, 255, 0.12)",
  },
  liveMapGlowB: {
    position: "absolute",
    bottom: 20,
    left: 22,
    width: 160,
    height: 160,
    borderRadius: 160,
    backgroundColor: "rgba(136, 239, 186, 0.08)",
  },
  liveRouteStart: {
    position: "absolute",
    left: 38,
    top: 42,
    width: 14,
    height: 14,
    borderRadius: 14,
    backgroundColor: colors.mint,
  },
  liveRouteEnd: {
    position: "absolute",
    right: 42,
    bottom: 46,
    width: 14,
    height: 14,
    borderRadius: 14,
    backgroundColor: colors.amber,
  },
  liveRoutePinA: {
    position: "absolute",
    top: 92,
    left: 92,
    width: 22,
    height: 22,
    borderRadius: 22,
    backgroundColor: "rgba(102, 227, 255, 0.18)",
    borderWidth: 1,
    borderColor: "rgba(102, 227, 255, 0.48)",
  },
  liveRoutePinB: {
    position: "absolute",
    bottom: 84,
    right: 76,
    width: 22,
    height: 22,
    borderRadius: 22,
    backgroundColor: "rgba(136, 239, 186, 0.18)",
    borderWidth: 1,
    borderColor: "rgba(136, 239, 186, 0.48)",
  },
  liveRouteLine: {
    position: "absolute",
    left: 48,
    right: 56,
    top: 52,
    bottom: 56,
    borderRadius: 22,
    borderWidth: 2,
    borderStyle: "dashed",
    borderColor: "rgba(160, 187, 220, 0.24)",
    transform: [{ rotate: "-18deg" }],
  },
  liveOverlayTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 8,
  },
  liveOverlayBottom: {
    alignItems: "stretch",
  },
  assistantBubble: {
    alignSelf: "flex-start",
    maxWidth: "88%",
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 12,
    backgroundColor: "rgba(10, 18, 30, 0.82)",
    borderWidth: 1,
    borderColor: colors.border,
    gap: 4,
  },
  assistantLabel: {
    color: colors.accent,
    fontSize: 11,
    textTransform: "uppercase",
    letterSpacing: 1,
    fontWeight: "800",
  },
  assistantText: {
    color: colors.text,
    fontSize: 13,
    lineHeight: 18,
  },
  livePrimary: {
    marginTop: 2,
  },
  liveSecondary: {
    flexDirection: "row",
    gap: 10,
  },
  modeStrip: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  modeChip: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: "rgba(255,255,255,0.03)",
  },
  modeChipActive: {
    backgroundColor: "rgba(102, 227, 255, 0.16)",
    borderColor: "rgba(102, 227, 255, 0.30)",
  },
  modeChipText: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "800",
  },
  modeChipTextActive: {
    color: colors.text,
  },
  metricBand: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  metricItem: {
    flexBasis: "48%",
    minWidth: 145,
    borderRadius: 20,
    padding: 14,
    borderWidth: 1,
    gap: 4,
  },
  metricLabel: {
    color: colors.muted,
    fontSize: 11,
    textTransform: "uppercase",
    letterSpacing: 0.9,
    fontWeight: "800",
  },
  metricValue: {
    color: colors.text,
    fontSize: 22,
    fontWeight: "800",
  },
  metricDetail: {
    color: colors.faint,
    fontSize: 12,
    lineHeight: 16,
  },
  missionCard: {
    borderRadius: 28,
    padding: 16,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 14,
  },
  missionTopRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
  },
  missionTitle: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "800",
    lineHeight: 30,
  },
  missionSubtitle: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
    marginTop: 6,
  },
  missionStep: {
    color: colors.accent,
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: 1,
    fontWeight: "800",
  },
  mapPanel: {
    borderRadius: 28,
    padding: 16,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 12,
  },
  mapPanelHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
  },
  mapCanvas: {
    minHeight: 220,
    borderRadius: 24,
    backgroundColor: colors.backgroundAlt,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: "hidden",
    position: "relative",
    padding: 16,
  },
  mapGlowA: {
    position: "absolute",
    top: 18,
    right: 14,
    width: 110,
    height: 110,
    borderRadius: 110,
    backgroundColor: "rgba(102, 227, 255, 0.10)",
  },
  mapGlowB: {
    position: "absolute",
    bottom: 16,
    left: 16,
    width: 140,
    height: 140,
    borderRadius: 140,
    backgroundColor: "rgba(136, 239, 186, 0.08)",
  },
  mapGridA: {
    position: "absolute",
    left: 18,
    right: 18,
    top: "50%",
    height: 1,
    backgroundColor: "rgba(160, 187, 220, 0.14)",
  },
  mapGridB: {
    position: "absolute",
    top: 18,
    bottom: 18,
    left: "50%",
    width: 1,
    backgroundColor: "rgba(160, 187, 220, 0.14)",
  },
});
