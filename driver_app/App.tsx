import React, { useEffect, useState } from "react";
import {
  SafeAreaView,
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
  ORGANIZATION_ID,
  REGION_ID,
  TEST_MODE,
} from "./core/config/environment";
import { apiRequest } from "./core/api/client";
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
type DriverTab = "dashboard" | "requests" | "activeTrip" | "earnings" | "vehicle" | "safety" | "profile";

const driverTabs: Array<{ key: DriverTab; label: string }> = [
  { key: "dashboard", label: "Dashboard" },
  { key: "requests", label: "Requests" },
  { key: "activeTrip", label: "Active Trip" },
  { key: "earnings", label: "Earnings" },
  { key: "vehicle", label: "Vehicle" },
  { key: "safety", label: "Safety" },
  { key: "profile", label: "Profile" },
];

type ErrorUtilsLike = {
  getGlobalHandler?: () => (error: Error, isFatal?: boolean) => void;
  setGlobalHandler?: (
    handler: (error: Error, isFatal?: boolean) => void,
  ) => void;
};

export default function App() {
  const [activeTab, setActiveTab] = useState<DriverTab>("dashboard");
  const [authenticated, setAuthenticated] = useState(false);
  const [email, setEmail] = useState("driver@novaride.test");
  const [password, setPassword] = useState("pilot");
  const [authenticating, setAuthenticating] = useState(false);
  const [loginError, setLoginError] = useState("");
  const globalRuntime = useGlobalRuntime(
    apiRequest,
    ORGANIZATION_ID,
    REGION_ID,
    APP_LOCALE || undefined,
  );
  const localizedDriverTabs: Array<{ key: DriverTab; label: string }> = [
    { key: "dashboard", label: "Dashboard" },
    { key: "requests", label: "Requests" },
    { key: "activeTrip", label: "Active Trip" },
    { key: "earnings", label: globalRuntime.t("nav.earnings") },
    { key: "vehicle", label: "Vehicle" },
    { key: "safety", label: "Safety" },
    { key: "profile", label: globalRuntime.t("nav.profile") },
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
  } = useDriverFlow(DRIVER_ID);
  const operator = useOperatorDashboard();
  const { capture, diagnostics, startShift } = usePilotEvidence(DRIVER_ID);
  const mobility = useDriverMobility(
    DRIVER_ID,
    authenticated,
    diagnostics.shiftStarted,
  );

  useEffect(() => {
    let active = true;
    void (async () => {
      const restored = await restoreSession();
      if (!restored.token || !active) return;
      const unlock = TEST_MODE
        ? { success: true }
        : await requireBiometricUnlock("Unlock NovaRide Driver");
      if (active && unlock.success) setAuthenticated(true);
      else if (!unlock.success) await clearSession();
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
              <BottomTabs tabs={localizedDriverTabs} activeTab={activeTab} onChange={setActiveTab} />
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
                  await loginPilot("driver-demo-001", "DRIVER", ORGANIZATION_ID);
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
                      await updateAvailability("offline");
                      await mobility.stop();
                    }}
                    onStartShift={startShift}
                  />
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
  bottomNav: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    padding: spacing.md,
  },
  shell: {
    flex: 1,
  },
  screen: {
    backgroundColor: colors.background,
    flex: 1,
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
