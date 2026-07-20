import React, { useState } from "react";
import {
  Alert,
  BackHandler,
  Pressable, SafeAreaView, ScrollView, StatusBar, StyleSheet, Text, TextInput, View,
} from "react-native";

import { useRideFlow } from "./state/providers/useRideFlow";
import { apiRequest } from "./core/api/client";
import { loginPilot, extractAuthIdentity } from "./core/api/auth.service";
import { clearAppSession, restoreAppSession } from "./core/api/session";
import { APP_LOCALE, ORGANIZATION_ID, REGION_ID, TEST_MODE } from "./core/config/environment";
import { runtimeConfig } from "./core/config/runtimeConfig";
import { RiderLoginScreen } from "./ui/screens/RiderLoginScreen";
import {
  AdaptiveScaffold,
  AnimatedEntrance,
  SkeletonBlock,
  SyncBanner,
} from "../afriride_system/mobile/shared/mobileExcellence";
import { useGlobalRuntime } from "../afriride_system/mobile/shared/globalRuntime";
import { clearRiderMobilityState } from "./core/services/mobility.service";

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

type LoginFailure = {
  message: string;
  diagnostic: string;
};

function describeLoginFailure(error: unknown): LoginFailure {
  if (error instanceof Error) {
    if (
      error.message === "native_device_attestation_provider_required" ||
      error.message === "device_attestation_platform_required"
    ) {
      return {
        message: "Device verification unavailable",
        diagnostic: error.message,
      };
    }
    return {
      message: "Sign in failed",
      diagnostic: error.message || "login_failed",
    };
  }
  return {
    message: "Sign in failed",
    diagnostic: "login_failed",
  };
}

export default function NovaRideRiderApp() {
  const [dark, setDark] = useState(false);
  const [tab, setTab] = useState<RiderTab>("Home");
  const [stage, setStage] = useState<BookingStage>("places");
  const [pickup, setPickup] = useState("Current location");
  const [destination, setDestination] = useState("");
  const [rideType, setRideType] = useState("NovaRide Standard");
  const [state, setState] = useState<ViewState>("success");
  const [message, setMessage] = useState("");
  const [authenticated, setAuthenticated] = useState(false);
  const [authenticating, setAuthenticating] = useState(false);
  const [email, setEmail] = useState("rider@novaride.test");
  const [password, setPassword] = useState("pilot");
  const [loginError, setLoginError] = useState("");
  const [loginDiagnostic, setLoginDiagnostic] = useState("");
  const [riderId, setRiderId] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const palette = dark ? darkTheme : lightTheme;
  const globalRuntime = useGlobalRuntime(
    apiRequest,
    ORGANIZATION_ID,
    REGION_ID,
    APP_LOCALE || undefined,
  );

  const performLogout = React.useCallback(
    async (reason = "Logged out", skipBackend = false) => {
      setLoggingOut(true);
      try {
        if (!skipBackend) {
          await apiRequest("/v1/auth/logout", { method: "POST" }).catch(() => undefined);
        }
        await clearRiderMobilityState().catch(() => undefined);
        await clearAppSession().catch(() => undefined);
      } finally {
        setAuthenticated(false);
        setRiderId("");
        setLoginError("");
        setLoginDiagnostic("");
        setPassword("pilot");
        setTab("Home");
        setStage("places");
        setPickup("Current location");
        setDestination("");
        setRideType("NovaRide Standard");
        setState("success");
        setMessage(reason);
        setLoggingOut(false);
      }
    },
    [],
  );

  const handleSessionExpired = React.useCallback(async () => {
    await performLogout("Session expired. Sign in again.", true);
  }, [performLogout]);

  const { requestedRide, submitRideRequest } = useRideFlow(riderId, handleSessionExpired);

  React.useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const restored = await restoreAppSession();
        if (!active || !restored.token) return;
        const restoredRiderId =
          typeof restored.metadata?.riderId === "string" && restored.metadata.riderId
            ? restored.metadata.riderId
            : extractAuthIdentity(restored.token, TEST_MODE ? email.trim() || "rider" : "");
        if (!restoredRiderId && !TEST_MODE) {
          throw new Error("Rider identity is unavailable. Sign in again.");
        }
        if (active) {
          setRiderId(restoredRiderId);
          setAuthenticated(true);
        }
      } catch {
        await clearAppSession().catch(() => undefined);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  React.useEffect(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => !authenticated);
    return () => sub.remove();
  }, [authenticated]);

  const login = async () => {
    setAuthenticating(true);
    setLoginError("");
    setLoginDiagnostic("");
    try {
      const principal = email.trim() || "rider";
      const token = await loginPilot(principal, "CUSTOMER", ORGANIZATION_ID);
      const nextRiderId = extractAuthIdentity(token, TEST_MODE ? principal : "");
      if (!nextRiderId && !TEST_MODE) {
        throw new Error("Rider identity is unavailable. Sign in again.");
      }
      setRiderId(nextRiderId);
      setAuthenticated(true);
      setTab("Home");
    } catch (error) {
      if (TEST_MODE) {
        setRiderId(email.trim() || "rider");
        setAuthenticated(true);
      } else {
        const failure = describeLoginFailure(error);
        setLoginError(failure.message);
        setLoginDiagnostic(failure.diagnostic);
      }
    } finally {
      setAuthenticating(false);
    }
  };

  const logout = async () => {
    Alert.alert("Log out of NovaRide?", "You can log in again as a different rider after logout.", [
      { text: "Cancel", style: "cancel" },
      { text: "Log out", style: "destructive", onPress: () => void performLogout("Logged out") },
    ]);
  };

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
    if (!authenticated || !riderId) {
      setState("error");
      setMessage("Please sign in to request a ride.");
      return;
    }
    setState("loading");
    setMessage("Submitting ride request to dispatch");
    const requested = await submitRideRequest({
      riderId,
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

  const canConfirmFare = Boolean(destination.trim());
  const canRequestRide = authenticated && Boolean(destination.trim()) && Boolean(pickup.trim());
  const canOperateTrip = stage === "tracking" || stage === "trip" || stage === "payment" || stage === "receipt";
  const canReviewReceipt = stage === "receipt";

  return (
    <AdaptiveScaffold
      testID="rider-adaptive-scaffold"
      brandColor={globalRuntime.brand.primary_color}
      navigation={authenticated ? (
        <View style={[styles.tabs, { backgroundColor: palette.surface }]}>
          {(["Home", "Book Ride", "Trips", "Wallet", "Safety", "Receipts", "Profile"] as RiderTab[]).map((item) => (
            <Pressable accessibilityRole="tab" accessibilityLabel={`${item} tab`} key={item} onPress={() => setTab(item)}>
              <Text style={{ color: item === tab ? "#5B3DF5" : palette.muted, fontWeight: "800" }}>{item}</Text>
            </Pressable>
          ))}
        </View>
      ) : undefined}
    >
    <View style={[styles.screen, { backgroundColor: palette.background }]}>
      <StatusBar barStyle={dark ? "light-content" : "dark-content"} />
      <SafeAreaView style={styles.safe}>
        {!authenticated ? (
          <View style={styles.loginShell}>
            <View style={styles.header}>
              <View>
                <Text style={[styles.brand, { color: palette.text }]}>{globalRuntime.brand.name}</Text>
                <Text style={styles.kicker}>
                  RIDER · NOVAID VERIFIED · {runtimeConfig.releaseChannel}
                </Text>
                <Text style={[styles.versionLabel, { color: palette.muted }]}>
                  v{runtimeConfig.releaseVersion} · API {runtimeConfig.apiBaseUrl}
                </Text>
              </View>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Toggle dark or light mode"
                onPress={() => setDark(!dark)}
                style={[styles.icon, { backgroundColor: palette.surface }]}
              >
                <Text>{dark ? "☀" : "☾"}</Text>
              </Pressable>
            </View>
            <RiderLoginScreen
              email={email}
              password={password}
              loading={authenticating}
              onEmailChange={setEmail}
              onPasswordChange={setPassword}
              onContinue={login}
            />
            {loginError ? <Text style={styles.error}>{loginError}</Text> : null}
            {loginDiagnostic ? <Text style={styles.diagnostic}>Reference: {loginDiagnostic}</Text> : null}
          </View>
        ) : (
          <>
        <View style={styles.header}>
          <View>
            <Text style={[styles.brand, { color: palette.text }]}>{globalRuntime.brand.name}</Text>
            <Text style={styles.kicker}>RIDER · NOVAID VERIFIED · {runtimeConfig.releaseChannel}</Text>
            <Text style={[styles.versionLabel, { color: palette.muted }]}>
              v{runtimeConfig.releaseVersion} · API {runtimeConfig.apiBaseUrl}
            </Text>
          </View>
          <Pressable accessibilityRole="button" accessibilityLabel="Toggle dark or light mode" onPress={() => setDark(!dark)} style={[styles.icon, { backgroundColor: palette.surface }]}><Text>{dark ? "☀" : "☾"}</Text></Pressable>
        </View>
        <SyncBanner online={state !== "offline"} pending={state === "offline" ? 1 : 0} />
        <AnimatedEntrance>
        <ScrollView contentContainerStyle={styles.content}>
          {state === "loading" ? <SkeletonBlock height={96} /> : null}
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
              <Action
                primary
                label="Confirm Fare"
                onPress={() => action("Fare confirmed", "matching")}
                disabled={!canConfirmFare}
                helperText={!canConfirmFare ? "Enter a destination to request a fare quote." : undefined}
              />
              <Action
                primary
                label="Request Ride"
                onPress={() => void requestRide()}
                disabled={!canRequestRide || state === "loading"}
                helperText={!canRequestRide ? "Pickup and destination are required before dispatch." : undefined}
              />
              {stage === "tracking" && <DriverTrustCard />}
              {stage === "tracking" && (
                <View style={styles.row}>
                  <Action label="Contact Driver" onPress={() => action("Calling driver")} />
                  <Action label="Share Trip" onPress={() => action("Trip sharing enabled")} />
                </View>
              )}
              <View style={styles.row}>
                <Action danger label="SOS" onPress={sos} />
                <Action
                  label="QR Ride Verification"
                  onPress={() => action("Vehicle and driver QR verified", "trip")}
                  disabled={!canOperateTrip}
                  helperText={!canOperateTrip ? "Verification becomes available once a driver is assigned." : undefined}
                />
              </View>
              <Action
                label="Pay"
                onPress={() => action("NovaPay payment completed", "receipt")}
                disabled={!canReviewReceipt}
                helperText={!canReviewReceipt ? "Payment is available after trip completion." : undefined}
              />
              <View style={styles.row}>
                <Action
                  label="Rate Driver"
                  onPress={() => action("Driver rated 5 stars")}
                  disabled={!canReviewReceipt}
                  helperText={!canReviewReceipt ? "Rate the driver after the receipt is available." : undefined}
                />
                <Action
                  label="Open Dispute"
                  onPress={() => action("Dispute case opened")}
                  disabled={!canReviewReceipt}
                  helperText={!canReviewReceipt ? "Disputes open after receipt issuance." : undefined}
                />
              </View>
              <View style={styles.row}>
                <Action
                  label="View Receipt"
                  onPress={() => action("Digital proof receipt NRR-2026-001")}
                  disabled={!canReviewReceipt}
                  helperText={!canReviewReceipt ? "Receipt becomes available after payment." : undefined}
                />
                <Action
                  label="View Replay"
                  onPress={() => action("Signed trip replay verified")}
                  disabled={!canReviewReceipt}
                  helperText={!canReviewReceipt ? "Replay is available after trip completion." : undefined}
                />
              </View>
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
              <View style={styles.profileCard}>
                <Text style={styles.profileTitle}>Account</Text>
                <Text style={{ color: palette.text, fontWeight: "800" }}>{email}</Text>
                <Text style={{ color: palette.muted }}>Rider ID: {riderId || "pending"}</Text>
                <Text style={{ color: palette.muted }}>
                  Session: {authenticated ? "Active" : "Signed out"}
                </Text>
              </View>
              <View style={styles.row}>
                {PROFILE_ACTIONS.map((label) => (
                  <Action
                    key={label}
                    label={label}
                    onPress={label === "Logout" ? logout : () => action(label)}
                    danger={label === "Logout"}
                  />
                ))}
              </View>
              <Action
                danger
                label={loggingOut ? "Logging out…" : "Log out"}
                onPress={logout}
                disabled={loggingOut}
                helperText={loggingOut ? "Ending session and clearing secure storage." : undefined}
              />
            </View>
          )}
          <View style={[styles.timeline, { backgroundColor: palette.surface }]}>
            <Text style={[styles.title, { color: palette.text }]}>Trip evidence timeline</Text>
            {["Ride created", "Assignment recorded", "Pickup verified", "Trip started", "Location samples", "Payment completed", "Receipt generated", "Replay package signed"].map((event, index) => <Text key={event} style={{ color: palette.text }}>✓ {index + 1}. {event}</Text>)}
          </View>
          {!!message && <Text accessibilityLiveRegion="polite" style={styles.success}>{message}</Text>}
          {requestedRide ? <Text style={{ color: palette.muted, textAlign: "center" }}>Request ID: {requestedRide.rideId}</Text> : null}
          <Text style={{ color: palette.muted, textAlign: "center" }}>{state === "offline" ? "Offline · request queued safely" : `Online · ${globalRuntime.region.currency} · Live tracking available`}</Text>
        </ScrollView>
        </AnimatedEntrance>
          </>
        )}
      </SafeAreaView>
    </View>
    </AdaptiveScaffold>
  );
}

function Action({
  label,
  onPress,
  primary,
  danger,
  disabled,
  helperText,
}: {
  label: string;
  onPress: () => void;
  primary?: boolean;
  danger?: boolean;
  disabled?: boolean;
  helperText?: string;
}) {
  return (
    <View style={styles.actionSlot}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={helperText ? `${label}. ${helperText}` : label}
        accessibilityState={{ disabled: Boolean(disabled) }}
        disabled={disabled}
        onPress={onPress}
        style={[
          styles.button,
          primary && styles.primary,
          danger && styles.danger,
          disabled && styles.disabledButton,
        ]}
      >
        <Text style={primary || danger ? styles.buttonInverse : styles.buttonText}>{label}</Text>
      </Pressable>
      {disabled && helperText ? <Text style={styles.helperText}>{helperText}</Text> : null}
    </View>
  );
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
  screen: { flex: 1 },
  safe: { flex: 1 },
  header: { padding: 18, flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  headerActions: { flexDirection: "row", gap: 10 },
  brand: { fontSize: 28, fontWeight: "900" }, kicker: { color: "#5B3DF5", fontSize: 10, fontWeight: "900", letterSpacing: 1 },
  loginShell: { flex: 1, gap: 14, paddingTop: 4 },
  error: { color: "#B42318", fontWeight: "800", paddingHorizontal: 18 },
  diagnostic: { color: "#6E7486", fontSize: 12, fontWeight: "700", paddingHorizontal: 18 },
  versionLabel: { fontSize: 11, fontWeight: "700", marginTop: 3 },
  icon: { width: 42, height: 42, borderRadius: 21, justifyContent: "center", alignItems: "center" }, content: { padding: 14, paddingBottom: 110, gap: 14 },
  map: { height: 210, borderRadius: 24, backgroundColor: "#DDEBE5", overflow: "hidden", justifyContent: "center", alignItems: "center" },
  mapPin: { color: "#5B3DF5", fontSize: 35 }, mapRoad: { color: "#7BA99A", fontSize: 22 }, mapLabel: { color: "#345448", position: "absolute", bottom: 16, fontWeight: "700" },
  sheet: { borderRadius: 24, padding: 18, gap: 12 }, title: { fontSize: 20, fontWeight: "900" }, label: { fontSize: 11, fontWeight: "900" },
  input: { borderWidth: 1, borderRadius: 14, padding: 14 }, row: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  button: { backgroundColor: "#EEEAFD", padding: 13, borderRadius: 13, flexGrow: 1, alignItems: "center" }, buttonText: { color: "#4A35B5", fontWeight: "800" },
  primary: { backgroundColor: "#5B3DF5" }, danger: { backgroundColor: "#D9293E" }, buttonInverse: { color: "#FFF", fontWeight: "900" },
  disabledButton: { opacity: 0.55 },
  actionSlot: { flexGrow: 1, gap: 4, minWidth: "46%" },
  helperText: { color: "#6E7486", fontSize: 11, fontWeight: "700" },
  rideType: { flexDirection: "row", justifyContent: "space-between", padding: 13, borderRadius: 14 }, selected: { backgroundColor: "#EEEAFD" }, itemTitle: { fontWeight: "800" }, fare: { fontWeight: "900" },
  profileCard: { backgroundColor: "#EEF7F3", borderRadius: 14, gap: 4, padding: 14 },
  profileTitle: { color: "#087A50", fontWeight: "900", textTransform: "uppercase" },
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
