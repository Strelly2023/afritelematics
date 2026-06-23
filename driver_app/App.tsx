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
import { AvailabilityScreen } from "./ui/screens/AvailabilityScreen";
import { DiagnosticsScreen } from "./ui/screens/DiagnosticsScreen";
import { DriverLoginScreen } from "./ui/screens/DriverLoginScreen";
import { DriverNotificationsScreen } from "./ui/screens/DriverNotificationsScreen";
import { DriverProfileScreen } from "./ui/screens/DriverProfileScreen";
import { DriverTrustProfileScreen } from "./ui/screens/DriverTrustProfileScreen";
import { EarningsScreen } from "./ui/screens/EarningsScreen";
import { OperatorDashboardScreen } from "./ui/screens/OperatorDashboardScreen";
import { ReplayHistoryScreen } from "./ui/screens/ReplayHistoryScreen";
import { RideRequestsScreen } from "./ui/screens/RideRequestsScreen";
import { TripLifecycleScreen } from "./ui/screens/TripLifecycleScreen";
import { VehicleManagementScreen } from "./ui/screens/VehicleManagementScreen";
import { TEST_MODE } from "./core/config/environment";
import { colors } from "./ui/theme/colors";
import { spacing } from "./ui/theme/spacing";
import { ProductTabs } from "./ui/widgets/ProductTabs";

const DRIVER_ID = "driver-demo-001";
type DriverTab = "control" | "trips" | "trust" | "profile" | "alerts";

const driverTabs: Array<{ key: DriverTab; label: string }> = [
  { key: "control", label: "Control" },
  { key: "trips", label: "Trips" },
  { key: "trust", label: "Trust" },
  { key: "profile", label: "Profile" },
  { key: "alerts", label: "Alerts" },
];

type ErrorUtilsLike = {
  getGlobalHandler?: () => (error: Error, isFatal?: boolean) => void;
  setGlobalHandler?: (
    handler: (error: Error, isFatal?: boolean) => void,
  ) => void;
};

export default function App() {
  const [activeTab, setActiveTab] = useState<DriverTab>("control");
  const [authenticated, setAuthenticated] = useState(false);
  const [email, setEmail] = useState("driver@novaride.test");
  const [password, setPassword] = useState("pilot");
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
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <View style={styles.headerTop}>
            <Text style={styles.title}>AfriRide Driver</Text>
            <Text style={styles.modePill}>{TEST_MODE ? "Pilot" : "Live"}</Text>
          </View>
          <Text style={styles.subtitle}>Trip execution with visible trust evidence.</Text>
        </View>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        {!authenticated ? (
          <DriverLoginScreen
            email={email}
            password={password}
            onEmailChange={setEmail}
            onPasswordChange={setPassword}
            onContinue={() => setAuthenticated(true)}
          />
        ) : (
          <>
            <ProductTabs
              tabs={driverTabs}
              activeTab={activeTab}
              onChange={setActiveTab}
            />
            {activeTab === "control" ? (
              <>
                <OperatorDashboardScreen
                  dashboard={operator.dashboard}
                  loading={operator.loading}
                  error={operator.error}
                  onRefresh={operator.refreshDashboard}
                />
                <DiagnosticsScreen
                  diagnostics={diagnostics}
                  loading={loading}
                  onStartShift={startShift}
                />
                <AvailabilityScreen
                  availability={availability}
                  loading={loading}
                  onGoAvailable={() => updateAvailability("available")}
                  onGoOffline={() => updateAvailability("offline")}
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
            {activeTab === "trust" ? (
              <>
                <DriverTrustProfileScreen
                  availability={availability}
                  earnings={earnings}
                />
                <EarningsScreen earnings={earnings} />
                <ReplayHistoryScreen replayHistory={replayHistory} />
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
              </>
            ) : null}
            {activeTab === "alerts" ? (
              <DriverNotificationsScreen notifications={notifications} />
            ) : null}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: spacing.lg,
    padding: spacing.lg,
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
