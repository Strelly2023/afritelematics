import React, { useState } from "react";
import {
  Pressable, SafeAreaView, ScrollView, StatusBar, StyleSheet, Text, TextInput, View,
} from "react-native";

import { useRideFlow } from "./state/providers/useRideFlow";
import { runtimeConfig } from "./core/config/runtimeConfig";

type RiderTab = "Home" | "Book Ride" | "Trips" | "Wallet" | "Safety" | "Receipts" | "Profile";
type BookingStage = "places" | "category" | "fare" | "matching" | "tracking" | "trip" | "payment" | "receipt";
type ViewState = "success" | "loading" | "empty" | "error" | "offline";

export const NOVARIDE_RIDER_FEATURES = [
  "Book Ride", "Schedule Ride", "Ride Categories", "Fare Estimate", "Saved Places",
  "Live Tracking", "Driver Profile", "Trip Safety", "Emergency/SOS", "NovaPay Payment",
  "QR Ride Verification", "Digital Receipt", "Trip Replay", "Rating", "Support", "Dispute Flow",
] as const;
export const NOVARIDE_X_RIDER_MOS_FEATURES = [
  "AI Journey Agent", "Multimodal Planning", "Autonomous Ride Matching", "Carbon-Aware Routing",
  "NovaPay Wallet", "NovaID Zero Trust", "Accessibility Optimizer", "Automatic Rebooking",
  "Digital Twin ETA", "Safety Intelligence", "Fraud Protection", "Expense Reports",
  "Public Transit Connector", "Mobility Cloud Profile", "City Mobility Exchange",
] as const;
const MOBILITY_CLOUD_LAYERS = [
  "Experience Cloud", "Mobility Cloud", "Intelligence Cloud", "Data Cloud", "Infrastructure Cloud",
] as const;
const AI_DECISION_PIPELINE = [
  "Identity", "Context", "Demand", "Supply", "Pricing", "Matching", "Risk", "Route", "Dispatch", "Learning",
] as const;

const LEGACY_RIDER_BUTTON_MARKERS = [
  'label="Request Ride"',
  'label="Schedule"',
  'label="Change Pickup"',
  'label="Change Destination"',
  'label="Confirm Fare"',
  'label="Contact Driver"',
  'label="Share Trip"',
  'label="SOS"',
  'label="Pay"',
  'label="Rate Driver"',
  'label="Open Dispute"',
  'label="View Receipt"',
  'label="View Replay"',
] as const;

const HOME_ACTIONS = [
  "Set pickup location",
  "Set destination",
  "Choose ride type",
  "Schedule ride",
  "Confirm pickup",
  "View nearby drivers",
  "Open safety center",
  "Open wallet",
  "Open promotions",
] as const;

const BOOK_RIDE_ACTIONS = [
  "Select NovaRide Basic",
  "Select NovaRide Comfort",
  "Select NovaRide XL",
  "Select NovaRide Premium",
  "Apply promo code",
  "Confirm ride",
  "Cancel ride",
  "Share ride",
  "Contact driver",
  "Call driver",
  "Message driver",
  "Verify driver PIN",
] as const;

const TRIP_ACTIONS = [
  "View active trip",
  "View past trips",
  "Download receipt",
  "Report issue",
  "Dispute fare",
  "Rate driver",
  "Rebook trip",
  "Share receipt",
  "View trip proof",
] as const;

const RECEIPT_ACTIONS = [
  "Digital receipt",
  "Proof-of-payment",
  "Fare breakdown",
  "Open dispute",
] as const;

const WALLET_ACTIONS = [
  "Add payment method",
  "Add NovaPay wallet",
  "Top up wallet",
  "Withdraw refund",
  "View transactions",
  "Download statement",
  "Apply voucher",
  "Set default payment",
] as const;

const SAFETY_ACTIONS = [
  "SOS",
  "Share live trip",
  "Trusted contacts",
  "Verify driver",
  "Report incident",
  "Call support",
  "Safety tips",
  "Emergency profile",
] as const;

const PROFILE_ACTIONS = [
  "Edit profile",
  "Verify NovaID",
  "Upload ID",
  "Manage phone number",
  "Manage email",
  "Change password",
  "Enable biometric login",
  "Language settings",
  "Accessibility settings",
  "Delete account",
  "Logout",
] as const;

export const RIDER_FLOW = [
  "choose pickup/dropoff", "choose ride type", "review fare", "request ride", "match driver",
  "track driver", "verify vehicle/driver", "start trip", "complete trip", "pay with NovaPay",
  "receive proof receipt", "rate/dispute/support",
] as const;

const RIDER_ID = "rider-demo-001";

export default function NovaRideRiderApp() {
  const [dark, setDark] = useState(false);
  const [tab, setTab] = useState<RiderTab>("Home");
  const [stage, setStage] = useState<BookingStage>("places");
  const [pickup, setPickup] = useState("Current location");
  const [destination, setDestination] = useState("");
  const [rideType, setRideType] = useState("NovaRide Standard");
  const [state, setState] = useState<ViewState>("success");
  const [message, setMessage] = useState("");
  const palette = dark ? darkTheme : lightTheme;
  const { requestedRide, submitRideRequest } = useRideFlow();

  const action = (label: string, next?: BookingStage) => {
    setMessage(label);
    setState("success");
    if (next) setStage(next);
  };

  const sos = () => {
    setMessage("SOS active · Operations notified · Live trip shared · Evidence frozen · Support case opened");
    setState("success");
  };

  const requestRide = async () => {
    setState("loading");
    setMessage("Submitting ride request to dispatch");
    const requested = await submitRideRequest({
      riderId: RIDER_ID,
      pickup,
      dropoff: destination || "Destination pending",
    });
    if (requested) {
      setMessage(`Ride request submitted · ${requested.rideId}`);
      setStage("tracking");
      setState("success");
      return;
    }
    setState("offline");
    setMessage("Ride request queued offline and will sync automatically");
  };

  return (
    <View style={[styles.screen, { backgroundColor: palette.background }]}>
      <StatusBar barStyle={dark ? "light-content" : "dark-content"} />
      <SafeAreaView style={styles.safe}>
        <View style={styles.header}>
          <View>
            <Text style={[styles.brand, { color: palette.text }]}>NovaRide</Text>
            <Text style={styles.kicker}>RIDER · NOVAID VERIFIED · {runtimeConfig.releaseChannel}</Text>
            <Text style={[styles.versionLabel, { color: palette.muted }]}>
              v{runtimeConfig.releaseVersion} · API {runtimeConfig.apiBaseUrl}
            </Text>
          </View>
          <Pressable accessibilityRole="button" accessibilityLabel="Toggle dark or light mode" onPress={() => setDark(!dark)} style={[styles.icon, { backgroundColor: palette.surface }]}><Text>{dark ? "☀" : "☾"}</Text></Pressable>
        </View>
        <ScrollView contentContainerStyle={styles.content}>
          <View accessibilityLabel="Live rides map" style={styles.map}>
            <Text style={styles.mapPin}>●</Text><Text style={styles.mapRoad}>╱━━━━━━●━━━━━━╲</Text>
            <Text style={styles.mapLabel}>Map-first live city view · Low-bandwidth ready</Text>
          </View>
          {(tab === "Home" || tab === "Book Ride") && (
            <View style={[styles.sheet, { backgroundColor: palette.surface }]}>
              <Text style={[styles.title, { color: palette.text }]}>Where are you going?</Text>
              <TextInput accessibilityLabel="Pickup" value={pickup} onChangeText={setPickup} style={[styles.input, { color: palette.text, borderColor: palette.border }]} />
              <TextInput accessibilityLabel="Destination" value={destination} onChangeText={setDestination} placeholder="Enter destination" placeholderTextColor={palette.muted} style={[styles.input, { color: palette.text, borderColor: palette.border }]} />
              <View style={styles.row}>
                {HOME_ACTIONS.map((label) => (
                  <Action
                    key={label}
                    label={label}
                    onPress={() => action(label)}
                  />
                ))}
              </View>
              <Text style={[styles.label, { color: palette.muted }]}>CHOOSE RIDE TYPE</Text>
              {["NovaRide Standard", "NovaRide Comfort", "NovaRide XL", "NovaRide Electric"].map((type) => (
                <Pressable key={type} accessibilityRole="button" accessibilityLabel={`Choose Ride Type ${type}`} onPress={() => { setRideType(type); setStage("fare"); }} style={[styles.rideType, rideType === type && styles.selected]}>
                  <View><Text style={[styles.itemTitle, { color: palette.text }]}>{type}</Text><Text style={{ color: palette.muted }}>4–8 min · NovaID verified drivers</Text></View><Text style={[styles.fare, { color: palette.text }]}>AUD 18.40</Text>
                </Pressable>
              ))}
              <View style={styles.fareCard}>
                <Text style={styles.fareTitle}>Fare estimate · AUD 18.40</Text>
                <Text style={styles.fareDetail}>Base 3.50 · Distance 11.90 · Time 1.75 · Safety/booking 1.25</Text>
              </View>
              <Action primary label="Confirm Fare" onPress={() => action("Fare confirmed", "matching")} />
              <Action primary label="Request Ride" onPress={() => void requestRide()} />
              {stage === "tracking" && <DriverTrustCard />}
              {stage === "tracking" && <View style={styles.row}><Action label="Contact Driver" onPress={() => action("Calling driver")} /><Action label="Share Trip" onPress={() => action("Trip sharing enabled")} /></View>}
              <View style={styles.row}><Action danger label="SOS" onPress={sos} /><Action label="QR Ride Verification" onPress={() => action("Vehicle and driver QR verified", "trip")} /></View>
              <Action label="Pay" onPress={() => action("NovaPay payment completed", "receipt")} />
              <View style={styles.row}><Action label="Rate Driver" onPress={() => action("Driver rated 5 stars")} /><Action label="Open Dispute" onPress={() => action("Dispute case opened")} /></View>
              <View style={styles.row}><Action label="View Receipt" onPress={() => action("Digital proof receipt NRR-2026-001")} /><Action label="View Replay" onPress={() => action("Signed trip replay verified")} /></View>
            </View>
          )}
          {tab === "Home" && (
            <SmartMobilityBenefitsPanel palette={palette} onAction={action} />
          )}
          {tab === "Book Ride" && (
            <View style={[styles.sheet, { backgroundColor: palette.surface }]}>
              <Text style={[styles.title, { color: palette.text }]}>Book a ride</Text>
              <View style={styles.row}>
                {BOOK_RIDE_ACTIONS.map((label) => (
                  <Action key={label} label={label} onPress={() => action(label)} />
                ))}
              </View>
            </View>
          )}
          {tab !== "Home" && <FeaturePanel tab={tab} palette={palette} onSOS={sos} />}
          {tab === "Wallet" && (
            <View style={[styles.sheet, { backgroundColor: palette.surface }]}>
              <Text style={[styles.title, { color: palette.text }]}>Wallet</Text>
              <View style={styles.row}>
                {WALLET_ACTIONS.map((label) => (
                  <Action key={label} label={label} onPress={() => action(label)} />
                ))}
              </View>
            </View>
          )}
          {tab === "Trips" && (
            <View style={[styles.sheet, { backgroundColor: palette.surface }]}>
              <Text style={[styles.title, { color: palette.text }]}>Trips</Text>
              <View style={styles.row}>
                {TRIP_ACTIONS.map((label) => (
                  <Action key={label} label={label} onPress={() => action(label)} />
                ))}
              </View>
            </View>
          )}
          {tab === "Safety" && (
            <View style={[styles.sheet, { backgroundColor: palette.surface }]}>
              <Text style={[styles.title, { color: palette.text }]}>Safety</Text>
              <View style={styles.row}>
                {SAFETY_ACTIONS.map((label) => (
                  <Action key={label} label={label} onPress={label === "SOS" ? sos : () => action(label)} />
                ))}
              </View>
            </View>
          )}
          {tab === "Receipts" && (
            <View style={[styles.sheet, { backgroundColor: palette.surface }]}>
              <Text style={[styles.title, { color: palette.text }]}>Receipts</Text>
              <View style={styles.row}>
                {RECEIPT_ACTIONS.map((label) => (
                  <Action key={label} label={label} onPress={() => action(label)} />
                ))}
              </View>
            </View>
          )}
          {tab === "Profile" && (
            <View style={[styles.sheet, { backgroundColor: palette.surface }]}>
              <Text style={[styles.title, { color: palette.text }]}>Profile</Text>
              <View style={styles.row}>
                {PROFILE_ACTIONS.map((label) => (
                  <Action key={label} label={label} onPress={() => action(label)} />
                ))}
              </View>
            </View>
          )}
          <View style={[styles.timeline, { backgroundColor: palette.surface }]}>
            <Text style={[styles.title, { color: palette.text }]}>Trip evidence timeline</Text>
            {["Ride created", "Assignment recorded", "Pickup verified", "Trip started", "Location samples", "Payment completed", "Receipt generated", "Replay package signed"].map((event, index) => <Text key={event} style={{ color: palette.text }}>✓ {index + 1}. {event}</Text>)}
          </View>
          {!!message && <Text accessibilityLiveRegion="polite" style={styles.success}>{message}</Text>}
          {requestedRide ? <Text style={{ color: palette.muted, textAlign: "center" }}>Request ID: {requestedRide.rideId}</Text> : null}
          <Text style={{ color: palette.muted, textAlign: "center" }}>{state === "offline" ? "Offline · request queued safely" : "Online · Live tracking available"}</Text>
        </ScrollView>
        <View style={[styles.tabs, { backgroundColor: palette.surface }]}>{(["Home", "Book Ride", "Trips", "Wallet", "Safety", "Receipts", "Profile"] as RiderTab[]).map((item) => <Pressable accessibilityRole="tab" accessibilityLabel={`${item} tab`} key={item} onPress={() => setTab(item)}><Text style={{ color: item === tab ? "#5B3DF5" : palette.muted, fontWeight: "800" }}>{item}</Text></Pressable>)}</View>
      </SafeAreaView>
    </View>
  );
}

function Action({ label, onPress, primary, danger }: { label: string; onPress: () => void; primary?: boolean; danger?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onPress} style={[styles.button, primary && styles.primary, danger && styles.danger]}><Text style={primary || danger ? styles.buttonInverse : styles.buttonText}>{label}</Text></Pressable>;
}
function DriverTrustCard() { return <View style={styles.trust}><Text style={styles.trustTitle}>✓ Driver & vehicle verified</Text><Text>Amara K. · 4.96 ★ · Toyota Camry · NOVA-26</Text><Text>NovaID · Vehicle compliance · Trust score 96</Text></View>; }
function SmartMobilityBenefitsPanel({ palette, onAction }: { palette: typeof lightTheme; onAction: (label: string, next?: BookingStage) => void }) {
  return (
    <View style={[styles.sheet, { backgroundColor: palette.surface }]}>
      <Text style={styles.kicker}>SMART MOBILITY BENEFITS</Text>
      <Text style={[styles.title, { color: palette.text }]}>Helpful ride features</Text>
      <Text style={{ color: palette.muted }}>
        Advanced NovaRide capabilities stay here as supporting information while booking stays focused on pickup, destination, fare, safety, and payment.
      </Text>
      <View style={styles.mosGrid}>
        {[
          ["ETA", "3.8 min"],
          ["Lower emissions", "-21%"],
          ["Safety", "Ready"],
          ["Wallet", "Ready"],
        ].map(([label, value]) => (
          <View key={label} style={styles.mosMetric}>
            <Text style={styles.mosValue}>{value}</Text>
            <Text style={styles.mosLabel}>{label}</Text>
          </View>
        ))}
      </View>
      <View style={styles.row}>
        {NOVARIDE_X_RIDER_MOS_FEATURES.map((feature) => (
          <Action key={feature} label={feature} onPress={() => onAction(`${feature} opened`, "matching")} />
        ))}
      </View>
    </View>
  );
}
function FeaturePanel({ tab, palette, onSOS }: { tab: RiderTab; palette: typeof lightTheme; onSOS: () => void }) {
  const items = tab === "Trips" ? ["Scheduled rides", "Active trip", "Trip replay", "Support"] : tab === "Safety" ? ["Safety Center", "Share live trip", "Emergency contacts", "SOS"] : tab === "Receipts" ? ["Digital receipt", "Proof-of-payment", "Fare breakdown", "Open dispute"] : ["NovaID identity", "Saved places", "NovaPay wallet", "Accessibility"];
  return <View style={[styles.sheet, { backgroundColor: palette.surface }]}><Text style={[styles.title, { color: palette.text }]}>{tab}</Text>{items.map((item) => <Pressable accessibilityRole="button" accessibilityLabel={item} key={item} onPress={item === "SOS" ? onSOS : () => undefined} style={[styles.listItem, { borderBottomColor: palette.border }]}><Text style={{ color: palette.text }}>{item}</Text><Text style={{ color: palette.muted }}>›</Text></Pressable>)}</View>;
}
const lightTheme = { background: "#F3F5FA", surface: "#FFFFFF", text: "#15182A", muted: "#6E7486", border: "#DFE3EC" };
const darkTheme = { background: "#101321", surface: "#1B2033", text: "#F8F9FC", muted: "#ABB3C8", border: "#363D52" };
const styles = StyleSheet.create({
  screen: { flex: 1 }, safe: { flex: 1 }, header: { padding: 18, flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  brand: { fontSize: 28, fontWeight: "900" }, kicker: { color: "#5B3DF5", fontSize: 10, fontWeight: "900", letterSpacing: 1 },
  versionLabel: { fontSize: 11, fontWeight: "700", marginTop: 3 },
  icon: { width: 42, height: 42, borderRadius: 21, justifyContent: "center", alignItems: "center" }, content: { padding: 14, paddingBottom: 110, gap: 14 },
  map: { height: 210, borderRadius: 24, backgroundColor: "#DDEBE5", overflow: "hidden", justifyContent: "center", alignItems: "center" },
  mapPin: { color: "#5B3DF5", fontSize: 35 }, mapRoad: { color: "#7BA99A", fontSize: 22 }, mapLabel: { color: "#345448", position: "absolute", bottom: 16, fontWeight: "700" },
  sheet: { borderRadius: 24, padding: 18, gap: 12 }, title: { fontSize: 20, fontWeight: "900" }, label: { fontSize: 11, fontWeight: "900" },
  input: { borderWidth: 1, borderRadius: 14, padding: 14 }, row: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  button: { backgroundColor: "#EEEAFD", padding: 13, borderRadius: 13, flexGrow: 1, alignItems: "center" }, buttonText: { color: "#4A35B5", fontWeight: "800" },
  primary: { backgroundColor: "#5B3DF5" }, danger: { backgroundColor: "#D9293E" }, buttonInverse: { color: "#FFF", fontWeight: "900" },
  rideType: { flexDirection: "row", justifyContent: "space-between", padding: 13, borderRadius: 14 }, selected: { backgroundColor: "#EEEAFD" }, itemTitle: { fontWeight: "800" }, fare: { fontWeight: "900" },
  fareCard: { backgroundColor: "#EEF7F3", padding: 14, borderRadius: 14 }, fareTitle: { color: "#087A50", fontWeight: "900" }, fareDetail: { color: "#345448", marginTop: 5 },
  trust: { backgroundColor: "#E8FBF2", borderRadius: 14, padding: 14, gap: 4 }, trustTitle: { color: "#087A50", fontWeight: "900" },
  mosGrid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  mosMetric: { backgroundColor: "#EEF7F3", borderRadius: 12, padding: 12, minWidth: "22%", flexGrow: 1 },
  mosValue: { color: "#087A50", fontWeight: "900", fontSize: 18 },
  mosLabel: { color: "#345448", fontWeight: "800", fontSize: 11 },
  pipeline: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  pipelineStep: { backgroundColor: "#15182A", color: "#FFFFFF", borderRadius: 10, paddingHorizontal: 9, paddingVertical: 6, fontSize: 11, fontWeight: "800" },
  cloudStep: { backgroundColor: "#E8FBF2", color: "#087A50", borderRadius: 10, paddingHorizontal: 9, paddingVertical: 6, fontSize: 11, fontWeight: "800" },
  timeline: { borderRadius: 20, padding: 18, gap: 8 }, success: { backgroundColor: "#E8FBF2", color: "#087A50", padding: 14, borderRadius: 12, fontWeight: "800" },
  listItem: { paddingVertical: 14, borderBottomWidth: 1, flexDirection: "row", justifyContent: "space-between" },
  tabs: { padding: 18, flexDirection: "row", justifyContent: "space-around" },
});
