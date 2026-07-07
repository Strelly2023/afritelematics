import React, { useState } from "react";
import {
  Pressable, SafeAreaView, ScrollView, StatusBar, StyleSheet, Text, TextInput, View,
} from "react-native";

type RiderTab = "Home" | "Trips" | "Safety" | "Receipts" | "Profile";
type BookingStage = "places" | "category" | "fare" | "matching" | "tracking" | "trip" | "payment" | "receipt";
type ViewState = "success" | "loading" | "empty" | "error" | "offline";

export const NOVARIDE_RIDER_FEATURES = [
  "Book Ride", "Schedule Ride", "Ride Categories", "Fare Estimate", "Saved Places",
  "Live Tracking", "Driver Profile", "Trip Safety", "Emergency/SOS", "NovaPay Payment",
  "QR Ride Verification", "Digital Receipt", "Trip Replay", "Rating", "Support", "Dispute Flow",
] as const;

export const RIDER_FLOW = [
  "choose pickup/dropoff", "choose ride type", "review fare", "request ride", "match driver",
  "track driver", "verify vehicle/driver", "start trip", "complete trip", "pay with NovaPay",
  "receive proof receipt", "rate/dispute/support",
] as const;

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

  const action = (label: string, next?: BookingStage) => {
    setMessage(label);
    setState("success");
    if (next) setStage(next);
  };

  const sos = () => {
    setMessage("SOS active · Operations notified · Live trip shared · Evidence frozen · Support case opened");
    setState("success");
  };

  return (
    <View style={[styles.screen, { backgroundColor: palette.background }]}>
      <StatusBar barStyle={dark ? "light-content" : "dark-content"} />
      <SafeAreaView style={styles.safe}>
        <View style={styles.header}>
          <View><Text style={[styles.brand, { color: palette.text }]}>NovaRide</Text><Text style={styles.kicker}>RIDER · NOVAID VERIFIED</Text></View>
          <Pressable accessibilityRole="button" accessibilityLabel="Toggle dark or light mode" onPress={() => setDark(!dark)} style={[styles.icon, { backgroundColor: palette.surface }]}><Text>{dark ? "☀" : "☾"}</Text></Pressable>
        </View>
        <ScrollView contentContainerStyle={styles.content}>
          <View accessibilityLabel="Live rides map" style={styles.map}>
            <Text style={styles.mapPin}>●</Text><Text style={styles.mapRoad}>╱━━━━━━●━━━━━━╲</Text>
            <Text style={styles.mapLabel}>Map-first live city view · Low-bandwidth ready</Text>
          </View>
          {tab === "Home" && (
            <View style={[styles.sheet, { backgroundColor: palette.surface }]}>
              <Text style={[styles.title, { color: palette.text }]}>Where are you going?</Text>
              <TextInput accessibilityLabel="Pickup" value={pickup} onChangeText={setPickup} style={[styles.input, { color: palette.text, borderColor: palette.border }]} />
              <TextInput accessibilityLabel="Destination" value={destination} onChangeText={setDestination} placeholder="Enter destination" placeholderTextColor={palette.muted} style={[styles.input, { color: palette.text, borderColor: palette.border }]} />
              <View style={styles.row}>
                <Action label="Change Pickup" onPress={() => action("Pickup changed", "places")} />
                <Action label="Change Destination" onPress={() => action("Destination changed", "places")} />
                <Action label="Schedule" onPress={() => action("Ride scheduled", "category")} />
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
              <Action primary label="Request Ride" onPress={() => action("Driver matched · 3 minutes away", "tracking")} />
              {stage === "tracking" && <DriverTrustCard />}
              {stage === "tracking" && <View style={styles.row}><Action label="Contact Driver" onPress={() => action("Calling driver")} /><Action label="Share Trip" onPress={() => action("Trip sharing enabled")} /></View>}
              <View style={styles.row}><Action danger label="SOS" onPress={sos} /><Action label="QR Ride Verification" onPress={() => action("Vehicle and driver QR verified", "trip")} /></View>
              <Action label="Pay" onPress={() => action("NovaPay payment completed", "receipt")} />
              <View style={styles.row}><Action label="Rate Driver" onPress={() => action("Driver rated 5 stars")} /><Action label="Open Dispute" onPress={() => action("Dispute case opened")} /></View>
              <View style={styles.row}><Action label="View Receipt" onPress={() => action("Digital proof receipt NRR-2026-001")} /><Action label="View Replay" onPress={() => action("Signed trip replay verified")} /></View>
            </View>
          )}
          {tab !== "Home" && <FeaturePanel tab={tab} palette={palette} onSOS={sos} />}
          <View style={[styles.timeline, { backgroundColor: palette.surface }]}>
            <Text style={[styles.title, { color: palette.text }]}>Trip evidence timeline</Text>
            {["Ride created", "Assignment recorded", "Pickup verified", "Trip started", "Location samples", "Payment completed", "Receipt generated", "Replay package signed"].map((event, index) => <Text key={event} style={{ color: palette.text }}>✓ {index + 1}. {event}</Text>)}
          </View>
          {!!message && <Text accessibilityLiveRegion="polite" style={styles.success}>{message}</Text>}
          <Text style={{ color: palette.muted, textAlign: "center" }}>{state === "offline" ? "Offline · request queued safely" : "Online · Live tracking available"}</Text>
        </ScrollView>
        <View style={[styles.tabs, { backgroundColor: palette.surface }]}>{(["Home", "Trips", "Safety", "Receipts", "Profile"] as RiderTab[]).map((item) => <Pressable accessibilityRole="tab" accessibilityLabel={`${item} tab`} key={item} onPress={() => setTab(item)}><Text style={{ color: item === tab ? "#5B3DF5" : palette.muted, fontWeight: "800" }}>{item}</Text></Pressable>)}</View>
      </SafeAreaView>
    </View>
  );
}

function Action({ label, onPress, primary, danger }: { label: string; onPress: () => void; primary?: boolean; danger?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onPress} style={[styles.button, primary && styles.primary, danger && styles.danger]}><Text style={primary || danger ? styles.buttonInverse : styles.buttonText}>{label}</Text></Pressable>;
}
function DriverTrustCard() { return <View style={styles.trust}><Text style={styles.trustTitle}>✓ Driver & vehicle verified</Text><Text>Amara K. · 4.96 ★ · Toyota Camry · NOVA-26</Text><Text>NovaID · Vehicle compliance · Trust score 96</Text></View>; }
function FeaturePanel({ tab, palette, onSOS }: { tab: RiderTab; palette: typeof lightTheme; onSOS: () => void }) {
  const items = tab === "Trips" ? ["Scheduled rides", "Active trip", "Trip replay", "Support"] : tab === "Safety" ? ["Safety Center", "Share live trip", "Emergency contacts", "SOS"] : tab === "Receipts" ? ["Digital receipt", "Proof-of-payment", "Fare breakdown", "Open dispute"] : ["NovaID identity", "Saved places", "NovaPay wallet", "Accessibility"];
  return <View style={[styles.sheet, { backgroundColor: palette.surface }]}><Text style={[styles.title, { color: palette.text }]}>{tab}</Text>{items.map((item) => <Pressable accessibilityRole="button" accessibilityLabel={item} key={item} onPress={item === "SOS" ? onSOS : () => undefined} style={[styles.listItem, { borderBottomColor: palette.border }]}><Text style={{ color: palette.text }}>{item}</Text><Text style={{ color: palette.muted }}>›</Text></Pressable>)}</View>;
}
const lightTheme = { background: "#F3F5FA", surface: "#FFFFFF", text: "#15182A", muted: "#6E7486", border: "#DFE3EC" };
const darkTheme = { background: "#101321", surface: "#1B2033", text: "#F8F9FC", muted: "#ABB3C8", border: "#363D52" };
const styles = StyleSheet.create({
  screen: { flex: 1 }, safe: { flex: 1 }, header: { padding: 18, flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  brand: { fontSize: 28, fontWeight: "900" }, kicker: { color: "#5B3DF5", fontSize: 10, fontWeight: "900", letterSpacing: 1 },
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
  timeline: { borderRadius: 20, padding: 18, gap: 8 }, success: { backgroundColor: "#E8FBF2", color: "#087A50", padding: 14, borderRadius: 12, fontWeight: "800" },
  listItem: { paddingVertical: 14, borderBottomWidth: 1, flexDirection: "row", justifyContent: "space-between" },
  tabs: { padding: 18, flexDirection: "row", justifyContent: "space-around" },
});
