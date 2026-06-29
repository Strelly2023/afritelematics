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
import { ORGANIZATION_ID, TEST_MODE } from "./core/config/environment";
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
import { OperatorDashboardScreen } from "./ui/screens/OperatorDashboardScreen";
import { ReplayHistoryScreen } from "./ui/screens/ReplayHistoryScreen";
import { RideRequestsScreen } from "./ui/screens/RideRequestsScreen";
import { TripLifecycleScreen } from "./ui/screens/TripLifecycleScreen";
import { VehicleManagementScreen } from "./ui/screens/VehicleManagementScreen";
import { colors } from "./ui/theme/colors";
import { spacing } from "./ui/theme/spacing";
import { ProductTabs } from "./ui/widgets/ProductTabs";

const DRIVER_ID = "driver-demo-001";
type DriverTab = "home" | "trips" | "earnings" | "trust" | "profile";

const driverTabs: Array<{ key: DriverTab; label: string }> = [
  { key: "home", label: "Home" },
  { key: "trips", label: "Trips" },
  { key: "earnings", label: "Earnings" },
  { key: "trust", label: "Trust" },
  { key: "profile", label: "Profile" },
];

type ErrorUtilsLike = {
  getGlobalHandler?: () => (error: Error, isFatal?: boolean) => void;
  setGlobalHandler?: (
    handler: (error: Error, isFatal?: boolean) => void,
  ) => void;
};

export default function App() {
  const [activeTab, setActiveTab] = useState<DriverTab>("home");
  const [authenticated, setAuthenticated] = useState(false);
  const [email, setEmail] = useState("driver@novaride.test");
  const [password, setPassword] = useState("pilot");
  const [authenticating, setAuthenticating] = useState(false);
  const [loginError, setLoginError] = useState("");
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
      <View style={styles.shell}>
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.header}>
            <View style={styles.headerTop}>
              <Text style={styles.title}>AfriRide Driver</Text>
              <Text style={styles.modePill}>{TEST_MODE ? "Pilot" : "Live"}</Text>
            </View>
            <Text style={styles.subtitle}>Trip execution with live GPS, dispatch, and trust evidence.</Text>
            <Text style={styles.orgLabel}>Org: {ORGANIZATION_ID}</Text>
          </View>

          {error ? <Text style={styles.error}>{error}</Text> : null}
          {loginError ? <Text style={styles.error}>{loginError}</Text> : null}

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
            <>
              {activeTab === "home" ? (
                <>
                  <DriverHomeScreen
                    availability={availability}
                    earnings={earnings}
                    diagnostics={diagnostics}
                    loading={loading}
                    onGoAvailable={() => updateAvailability("available")}
                    onGoOffline={() => updateAvailability("offline")}
                    onStartShift={startShift}
                  />
                </>
              ) : null}
              {activeTab === "trips" ? (
                <>
                  <RideRequestsScreen
                    requests={requests}
                    loading={loading}
                    onAccept={acceptRequest}
                    onReject={rejectRequest}
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
              {activeTab === "trust" ? (
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
                  <VehicleManagementScreen
                    make="Toyota"
                    model="Hybrid"
                    plate="PILOT-001"
                  />
                  <DriverNotificationsScreen notifications={notifications} />
                </>
              ) : null}
            </>
          )}
        </ScrollView>

        {authenticated ? (
          <View style={styles.bottomNav}>
            <BottomTabs tabs={driverTabs} activeTab={activeTab} onChange={setActiveTab} />
          </View>
        ) : null}
      </View>

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
