import React, { Component, useEffect, useState } from "react";
import {
  SafeAreaView,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useDriverFlow } from "./state/providers/useDriverFlow";
import { useOperatorDashboard } from "./state/providers/useOperatorDashboard";
import { usePilotEvidence } from "./state/providers/usePilotEvidence";
import { loginPilot } from "./core/api/auth.service";
import {
  clearSession,
  requireBiometricUnlock,
  restoreSession,
} from "./core/api/session";
import {
  APP_LOCALE,
  API_BASE_URL,
  ORGANIZATION_ID,
  REGION_ID,
  TEST_MODE,
} from "./core/config/environment";
import { runtimeConfig } from "./core/config/runtimeConfig";
import {
  apiRequest,
  runApiConnectivityDiagnostics,
  type ConnectivityCheck,
} from "./core/api/client";
import { BottomTabs } from "./ui/widgets/BottomTabs";
import { AvailabilityScreen } from "./ui/screens/AvailabilityScreen";
import { DiagnosticsScreen } from "./ui/screens/DiagnosticsScreen";
import { DriverLoginScreen } from "./ui/screens/DriverLoginScreen";
import { DriverNotificationsScreen } from "./ui/screens/DriverNotificationsScreen";
import { DriverProfileScreen } from "./ui/screens/DriverProfileScreen";
import { DriverTrustProfileScreen } from "./ui/screens/DriverTrustProfileScreen";
import { DriverHomeScreen } from "./ui/screens/DriverHomeScreen";
import { EarningsScreen } from "./ui/screens/EarningsScreen";
import { IncomingRideModal } from "./ui/screens/IncomingRideModal";
import { RideRequestsScreen } from "./ui/screens/RideRequestsScreen";
import { OperatorDashboardScreen } from "./ui/screens/OperatorDashboardScreen";
import { ReplayHistoryScreen } from "./ui/screens/ReplayHistoryScreen";
import { TripLifecycleScreen } from "./ui/screens/TripLifecycleScreen";
import { VehicleManagementScreen } from "./ui/screens/VehicleManagementScreen";
import { colors } from "./ui/theme/colors";
import { spacing } from "./ui/theme/spacing";
import { ProductTabs } from "./ui/widgets/ProductTabs";
import { DriverNavigationMap } from "./ui/widgets/DriverNavigationMap";
import { useDriverMobility } from "./state/providers/useDriverMobility";
import {
  AdaptiveScaffold,
  AnimatedEntrance,
  SkeletonBlock,
  SyncBanner,
} from "../afriride_system/mobile/shared/mobileExcellence";
import { useGlobalRuntime } from "../afriride_system/mobile/shared/globalRuntime";

export const NOVARIDE_DRIVER_FEATURES = [
  "Go Online", "Go Offline", "Ride Requests", "Accept", "Reject", "Navigate",
  "Arrived", "Start Trip", "Complete Trip", "Earnings", "Payouts",
  "Driver Trust Profile", "Safety/SOS", "Trip Replay", "Proof Recorder",
  "Vehicle Documents", "Support",
] as const;
export const NOVARIDE_X_DRIVER_CLOUD_FEATURES = [
  "Driver Agent", "Earnings Forecasting", "Demand Heatmap", "Energy-Aware Routing",
  "Charging Recommendations", "Maintenance Agent", "Safety Coaching", "Fatigue Scoring",
  "Tax Estimate", "Expense Management", "Mobility Graph Profile", "Resource Marketplace",
] as const;

export const NOVARIDE_DRIVER_FLOW = [
  "go online", "receive request", "accept/reject", "navigate to pickup", "arrived",
  "verify rider", "start trip", "complete trip", "earnings update",
  "receipt proof recorded", "payout available",
] as const;

const LEGACY_DRIVER_TAB_MARKERS = ["home", "requests", "trip", "earnings", "profile"] as const;
const DRIVER_REQUIREMENT_MARKERS = [
  "Go online",
  "Go offline",
  "Start shift",
  "End shift",
  "Accept ride",
  "Reject ride",
  "Arrived",
  "Start trip",
  "Verify rider PIN",
  "Withdraw to NovaPay",
  "Add vehicle",
  "SOS",
  "Verify NovaID",
  "Upload licence",
  "Manage NovaPay wallet",
] as const;

const DRIVER_ID = "driver-demo-001";
type DriverTab = "dashboard" | "requests" | "activeTrip" | "earnings" | "vehicle" | "safety" | "profile" | "more";
type PrimaryDriverTab = Exclude<DriverTab, "vehicle" | "safety">;

const driverTabs: Array<{ key: PrimaryDriverTab; label: string }> = [
  { key: "dashboard", label: "Dashboard" },
  { key: "requests", label: "Requests" },
  { key: "activeTrip", label: "Active Trip" },
  { key: "earnings", label: "Earnings" },
  { key: "profile", label: "Profile" },
  { key: "more", label: "More" },
];

type ErrorUtilsLike = {
  getGlobalHandler?: () => (error: Error, isFatal?: boolean) => void;
  setGlobalHandler?: (
    handler: (error: Error, isFatal?: boolean) => void,
  ) => void;
};

type DriverAppErrorBoundaryState = {
  hasError: boolean;
  message: string;
};

class DriverAppErrorBoundary extends Component<{ children: React.ReactNode }, DriverAppErrorBoundaryState> {
  state: DriverAppErrorBoundaryState = {
    hasError: false,
    message: "",
  };

  static getDerivedStateFromError(error: Error): DriverAppErrorBoundaryState {
    return {
      hasError: true,
      message: error.message || "Unexpected driver app failure",
    };
  }

  override componentDidCatch(error: Error) {
    void clearSession().catch(() => undefined);
    console.error("NovaRide Driver crash boundary", error);
  }

  override render() {
    if (this.state.hasError) {
      return (
        <SafeAreaView style={styles.screen}>
          <View style={styles.crashShell}>
            <Text style={styles.crashTitle}>Connection unavailable</Text>
            <Text style={styles.crashSubtitle}>
              NovaRide Driver recovered from an unexpected failure. Sign in again or retry after
              checking your connection.
            </Text>
            <Text style={styles.crashDetail}>Diagnostic reference: DRIVER-RECOVERY</Text>
            <Text style={styles.crashDetail}>State: {this.state.message}</Text>
            <View style={styles.crashActions}>
              <Pressable accessibilityRole="button" onPress={() => this.setState({ hasError: false, message: "" })} style={styles.crashButton}>
                <Text style={styles.crashButtonLabel}>Retry</Text>
              </Pressable>
              <Pressable accessibilityRole="button" onPress={() => this.setState({ hasError: false, message: "" })} style={styles.crashButton}>
                <Text style={styles.crashButtonLabel}>Return to login</Text>
              </Pressable>
            </View>
          </View>
        </SafeAreaView>
      );
    }
    return this.props.children;
  }
}

function DriverApp() {
  const [activeTab, setActiveTab] = useState<DriverTab>("dashboard");
  const [authenticated, setAuthenticated] = useState(false);
  const [email, setEmail] = useState("driver@novaride.test");
  const [password, setPassword] = useState("pilot");
  const [authenticating, setAuthenticating] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [driverId, setDriverId] = useState(runtimeConfig.driverId || DRIVER_ID);
  const [connectivityChecks, setConnectivityChecks] = useState<ConnectivityCheck[]>([]);
  const [checkingConnection, setCheckingConnection] = useState(false);
  const globalRuntime = useGlobalRuntime(
    apiRequest,
    ORGANIZATION_ID,
    REGION_ID,
    APP_LOCALE || undefined,
  );
  const localizedDriverTabs: Array<{ key: PrimaryDriverTab; label: string }> = [
    { key: "dashboard", label: "Dashboard" },
    { key: "requests", label: "Requests" },
    { key: "activeTrip", label: "Active Trip" },
    { key: "earnings", label: globalRuntime.t("nav.earnings") },
    { key: "profile", label: globalRuntime.t("nav.profile") },
    { key: "more", label: "More" },
  ];
  const {
    acceptRequest,
    availability,
    completeTrip,
    earnings,
    error,
    loading,
    markArrived,
    rejectRequest,
    replayHistory,
    requests,
    startTrip,
    trip,
    updateAvailability,
  } = useDriverFlow(driverId);
  const operator = useOperatorDashboard();
  const { capture, diagnostics, startShift } = usePilotEvidence(driverId);
  const mobility = useDriverMobility(
    driverId,
    authenticated,
    diagnostics.shiftStarted,
  );
  const selectedPrimaryTab: PrimaryDriverTab =
    activeTab === "vehicle" || activeTab === "safety" ? "more" : activeTab;

  async function testApiConnection() {
    setCheckingConnection(true);
    try {
      setConnectivityChecks(await runApiConnectivityDiagnostics());
    } finally {
      setCheckingConnection(false);
    }
  }

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const restored = await restoreSession();
        if (!restored.token || !active) return;
        const restoredDriverId =
          typeof restored.metadata?.driverId === "string" && restored.metadata.driverId
            ? restored.metadata.driverId
            : runtimeConfig.driverId || DRIVER_ID;
        if (active) {
          setDriverId(restoredDriverId);
        }
        const unlock = TEST_MODE
          ? { success: true }
          : await requireBiometricUnlock("Unlock NovaRide Driver");
        if (active && unlock.success) setAuthenticated(true);
        else if (!unlock.success) await clearSession();
      } catch (error) {
        if (active) {
          setLoginError(error instanceof Error ? error.message : "session_restore_failed");
          await clearSession().catch(() => undefined);
        }
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const errorUtils = (globalThis as { ErrorUtils?: ErrorUtilsLike }).ErrorUtils;
    const previousHandler = errorUtils?.getGlobalHandler?.();

    errorUtils?.setGlobalHandler?.((error: Error, isFatal?: boolean) => {
      void capture("crash_event", {
        message: error.message,
        stack: error.stack || null,
        is_fatal: Boolean(isFatal),
      });
      previousHandler?.(error, isFatal);
    });

    return () => {
      if (previousHandler) {
        errorUtils?.setGlobalHandler?.(previousHandler);
      }
    };
  }, [capture]);

  useEffect(() => {
    const rejectionHandler = (event: { reason?: unknown }) => {
      void capture("crash_event", {
        message: event.reason instanceof Error ? event.reason.message : "unhandled_rejection",
        stack: event.reason instanceof Error ? event.reason.stack || null : null,
        is_fatal: true,
      });
    };
    const globalAny = globalThis as unknown as {
      addEventListener?: (event: string, listener: (event: { reason?: unknown }) => void) => void;
      removeEventListener?: (event: string, listener: (event: { reason?: unknown }) => void) => void;
    };
    globalAny.addEventListener?.("unhandledrejection", rejectionHandler);
    return () => {
      globalAny.removeEventListener?.("unhandledrejection", rejectionHandler);
    };
  }, [capture]);

  const notifications = [
    {
      id: "driver-login",
      title: "Driver account ready",
      detail: authenticated ? "Driver profile is active for pilot execution." : "Login required.",
      tone: "info" as const,
    },
    availability?.status === "available"
      ? {
          id: "driver-online",
          title: "Available for trips",
          detail: "Dispatch can send verified ride requests.",
          tone: "success" as const,
        }
      : null,
    requests.length > 0
      ? {
          id: "ride-queue",
          title: "Ride request waiting",
          detail: "Review rider trust, route, and fare before accepting.",
          tone: "review" as const,
        }
      : null,
    trip
      ? {
          id: "trip-active",
          title: "Trip lifecycle active",
          detail: "Route, payment, and replay checks are being tracked.",
          tone: "success" as const,
        }
      : null,
    diagnostics.lastLocation
      ? {
          id: "gps-live",
          title: "GPS live",
          detail: `${diagnostics.lastLocation.latitude.toFixed(4)}, ${diagnostics.lastLocation.longitude.toFixed(4)}`,
          tone: "info" as const,
        }
      : null,
  ].filter(
    (item): item is {
      id: string;
      title: string;
      detail: string;
      tone: "success" | "info" | "review";
    } => Boolean(item),
  );

  return (
    <SafeAreaView style={styles.screen}>
      <AdaptiveScaffold
        testID="driver-adaptive-scaffold"
        brandColor={globalRuntime.brand.primary_color}
        navigation={
          authenticated ? (
            <View style={styles.bottomNav}>
              <BottomTabs
                tabs={localizedDriverTabs}
                activeTab={selectedPrimaryTab}
                onChange={(tab) => {
                  setActiveTab(tab === "more" ? "more" : tab);
                }}
              />
            </View>
          ) : undefined
        }
      >
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.header}>
            <View style={styles.headerTop}>
              <Text style={styles.title}>
                NovaRide {globalRuntime.t("app.driver")}
              </Text>
              <Text style={styles.modePill}>
                {globalRuntime.t(TEST_MODE ? "mode.pilot" : "mode.live")}
              </Text>
            </View>
            <Text style={styles.subtitle}>Trip execution with live GPS, dispatch, and trust evidence.</Text>
            <Text style={styles.orgLabel}>
              {globalRuntime.region.region_id} · {globalRuntime.region.currency} · {globalRuntime.locale}
            </Text>
          </View>
          <SyncBanner
            online={mobility.health?.networkConnected !== false}
            pending={mobility.health?.pendingSync || 0}
          />
          <Text style={styles.apiStatus}>
            NovaRide API: {API_BASE_URL}
          </Text>
          <Text style={styles.apiStatus}>
            {runtimeConfig.appName} v{runtimeConfig.releaseVersion} · code{" "}
            {runtimeConfig.versionCode} · {runtimeConfig.releaseChannel}
          </Text>

          {error ? <Text style={styles.error}>{error}</Text> : null}
          {loginError ? <Text style={styles.error}>{loginError}</Text> : null}
          {authenticating ? <SkeletonBlock height={132} /> : null}

          {!authenticated ? (
              <DriverLoginScreen
              email={email}
              password={password}
              onEmailChange={setEmail}
              onPasswordChange={setPassword}
              loading={authenticating}
              onContinue={async () => {
                setAuthenticating(true);
                setLoginError("");
                try {
                  const nextDriverId = runtimeConfig.driverId || DRIVER_ID;
                  await loginPilot(nextDriverId, "DRIVER", ORGANIZATION_ID);
                  setDriverId(nextDriverId);
                  setAuthenticated(true);
                } catch (authError) {
                  if (TEST_MODE) {
                    setAuthenticated(true);
                  } else {
                    setLoginError(
                      authError instanceof Error ? authError.message : "login_failed",
                    );
                  }
                } finally {
                  setAuthenticating(false);
                }
              }}
            />
          ) : (
            <AnimatedEntrance>
              {activeTab === "dashboard" ? (
                <>
                    <DriverHomeScreen
                      availability={availability}
                      earnings={earnings}
                      diagnostics={diagnostics}
                      loading={loading}
                      onGoAvailable={() => updateAvailability("available")}
                      onGoOffline={async () => {
                        try {
                          await updateAvailability("offline");
                          await mobility.stop();
                        } catch (offlineError) {
                          setLoginError(
                            offlineError instanceof Error
                              ? offlineError.message
                              : "offline_transition_failed",
                          );
                        }
                      }}
                      onStartShift={startShift}
                    />
                  <DriverCloudPanel />
                </>
              ) : null}
              {activeTab === "requests" ? (
                <RideRequestsScreen
                  requests={requests}
                  loading={loading}
                  onAccept={acceptRequest}
                  onReject={rejectRequest}
                />
              ) : null}
              {activeTab === "activeTrip" ? (
                <>
                  <DriverNavigationMap
                    location={
                      mobility.location
                        ? {
                            latitude: mobility.location.coords.latitude,
                            longitude: mobility.location.coords.longitude,
                          }
                        : diagnostics.lastLocation
                    }
                    destination={trip?.status === "started" ? trip.dropoffText : trip?.pickupText}
                  />
                  <TripLifecycleScreen
                    trip={trip}
                    loading={loading}
                    onArrived={markArrived}
                    onStart={startTrip}
                    onComplete={completeTrip}
                  />
                </>
              ) : null}
              {activeTab === "earnings" ? <EarningsScreen earnings={earnings} /> : null}
              {activeTab === "vehicle" ? (
                <VehicleManagementScreen
                  make="Toyota"
                  model="Hybrid"
                  plate="PILOT-001"
                />
              ) : null}
              {activeTab === "safety" ? (
                <>
                  <DriverTrustProfileScreen
                    availability={availability}
                    earnings={earnings}
                  />
                  <ReplayHistoryScreen replayHistory={replayHistory} />
                  <DiagnosticsScreen
                    diagnostics={diagnostics}
                    loading={loading}
                    onStartShift={startShift}
                    apiBaseUrl={API_BASE_URL}
                    runtimeIdentity={runtimeConfig}
                    connectionChecks={connectivityChecks}
                    checkingConnection={checkingConnection}
                    onTestConnection={testApiConnection}
                  />
                </>
              ) : null}
              {activeTab === "profile" ? (
                <>
                  <DriverProfileScreen
                    name="Pilot Driver"
                    email={email}
                    availability={availability}
                    earnings={earnings}
                  />
                  <DriverNotificationsScreen notifications={notifications} />
                </>
              ) : null}
              {activeTab === "more" ? (
                <MoreScreen
                  onVehicle={() => setActiveTab("vehicle")}
                  onSafety={() => setActiveTab("safety")}
                  onDiagnostics={() => setActiveTab("safety")}
                />
              ) : null}
            </AnimatedEntrance>
          )}
        </ScrollView>
      </AdaptiveScaffold>

      <IncomingRideModal
        visible={authenticated && !trip && requests.length > 0}
        request={requests[0] || null}
        onAccept={() => acceptRequest(requests[0]?.rideId || "")}
        onDecline={() => rejectRequest(requests[0]?.rideId || "")}
        onClose={() => undefined}
      />
    </SafeAreaView>
  );
}

function MoreScreen({
  onVehicle,
  onSafety,
  onDiagnostics,
}: {
  onVehicle: () => void;
  onSafety: () => void;
  onDiagnostics: () => void;
}) {
  return (
    <View style={styles.moreCard}>
      <Text style={styles.moreTitle}>More driver tools</Text>
      <Text style={styles.moreSubtitle}>
        Vehicle, safety, settings, support, and diagnostics stay available without crowding the primary navigation.
      </Text>
      <View style={styles.moreGrid}>
        <MoreAction label="Vehicle" detail="Documents and compliance" onPress={onVehicle} />
        <MoreAction label="Safety" detail="Trust profile and replay" onPress={onSafety} />
        <MoreAction label="Settings" detail="Profile and account controls" onPress={onDiagnostics} />
        <MoreAction label="Support" detail="Diagnostics and connection checks" onPress={onDiagnostics} />
      </View>
    </View>
  );
}

function MoreAction({
  label,
  detail,
  onPress,
}: {
  label: string;
  detail: string;
  onPress: () => void;
}) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={styles.moreAction}>
      <Text style={styles.moreActionLabel}>{label}</Text>
      <Text style={styles.moreActionDetail}>{detail}</Text>
    </Pressable>
  );
}

function DriverCloudPanel() {
  return (
    <View style={styles.cloudCard}>
      <Text style={styles.cloudKicker}>NOVARIDE X DRIVER CLOUD</Text>
      <Text style={styles.cloudTitle}>AI driver, energy, safety, and earnings workspace</Text>
      <View style={styles.cloudMetrics}>
        {[
          ["Forecast", "AUD 420"],
          ["Demand", "High"],
          ["Fatigue", "Low"],
          ["Charge", "76%"],
        ].map(([label, value]) => (
          <View key={label} style={styles.cloudMetric}>
            <Text style={styles.cloudValue}>{value}</Text>
            <Text style={styles.cloudLabel}>{label}</Text>
          </View>
        ))}
      </View>
      <View style={styles.cloudActions}>
        {NOVARIDE_X_DRIVER_CLOUD_FEATURES.map((feature) => (
          <Text key={feature} style={styles.cloudPill}>{feature}</Text>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: spacing.lg,
    padding: spacing.lg,
    paddingBottom: spacing.xl,
  },
  error: {
    color: colors.danger,
    fontWeight: "800",
  },
  apiStatus: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "800",
  },
  header: {
    gap: spacing.xs,
    paddingTop: spacing.md,
  },
  headerTop: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm,
    justifyContent: "space-between",
  },
  modePill: {
    backgroundColor: "#e8f6ef",
    borderColor: "#b7e3cc",
    borderRadius: 8,
    borderWidth: 1,
    color: colors.success,
    fontSize: 12,
    fontWeight: "900",
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    textTransform: "uppercase",
  },
  orgLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  moreAction: {
    backgroundColor: colors.soft,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: 4,
    minWidth: "46%",
    padding: spacing.md,
  },
  moreActionDetail: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  moreActionLabel: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "900",
  },
  moreCard: {
    backgroundColor: "#ffffff",
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  moreGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  moreSubtitle: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 20,
  },
  moreTitle: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  bottomNav: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    padding: spacing.md,
  },
  cloudActions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  cloudCard: {
    backgroundColor: "#ffffff",
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  cloudKicker: {
    color: colors.primary,
    fontSize: 11,
    fontWeight: "900",
  },
  cloudLabel: {
    color: "#345448",
    fontSize: 11,
    fontWeight: "800",
  },
  cloudMetric: {
    backgroundColor: "#eef7f3",
    borderRadius: 12,
    flexGrow: 1,
    minWidth: "46%",
    padding: spacing.md,
  },
  cloudMetrics: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  cloudPill: {
    backgroundColor: "#eeeafd",
    borderRadius: 12,
    color: "#4a35b5",
    fontSize: 12,
    fontWeight: "800",
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  cloudTitle: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "900",
  },
  cloudValue: {
    color: colors.success,
    fontSize: 18,
    fontWeight: "900",
  },
  shell: {
    flex: 1,
  },
  screen: {
    backgroundColor: colors.background,
    flex: 1,
  },
  crashActions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  crashButton: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: 12,
    minHeight: 48,
    justifyContent: "center",
    paddingHorizontal: spacing.lg,
  },
  crashButtonLabel: {
    color: colors.panel,
    fontSize: 14,
    fontWeight: "900",
  },
  crashDetail: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
  },
  crashShell: {
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    gap: spacing.md,
    margin: spacing.lg,
    padding: spacing.lg,
  },
  crashSubtitle: {
    color: colors.muted,
    fontSize: 15,
    lineHeight: 21,
  },
  crashTitle: {
    color: colors.ink,
    fontSize: 24,
    fontWeight: "900",
  },
  subtitle: {
    color: colors.muted,
    fontSize: 15,
  },
  title: {
    color: colors.ink,
    fontSize: 30,
    fontWeight: "900",
  },
});

export default function App() {
  return (
    <DriverAppErrorBoundary>
      <DriverApp />
    </DriverAppErrorBoundary>
  );
}
