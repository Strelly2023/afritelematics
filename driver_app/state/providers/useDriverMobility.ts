import { useEffect, useState } from "react";
import * as Location from "expo-location";
import {
  getDriverMobilityHealth,
  registerDriverPush,
  startDriverBackgroundMobility,
  stopDriverBackgroundMobility,
  synchronizeDriverQueue,
  type DriverMobilityHealth,
} from "../../core/services/mobility.service";

export function useDriverMobility(driverId: string, authenticated: boolean, shiftActive: boolean) {
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [health, setHealth] = useState<DriverMobilityHealth | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authenticated) return;
    void registerDriverPush(driverId).catch(() => undefined);
    const interval = setInterval(() => void synchronizeDriverQueue(), 30_000);
    return () => clearInterval(interval);
  }, [authenticated, driverId]);

  useEffect(() => {
    if (!authenticated || !shiftActive) return;
    let subscription: Location.LocationSubscription | null = null;
    void startDriverBackgroundMobility(driverId)
      .then(async () => {
        subscription = await Location.watchPositionAsync(
          { accuracy: Location.Accuracy.High, distanceInterval: 10, timeInterval: 5000 },
          setLocation,
        );
        setHealth(await getDriverMobilityHealth());
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "mobility_failed"));
    return () => subscription?.remove();
  }, [authenticated, driverId, shiftActive]);

  async function stop() {
    await stopDriverBackgroundMobility();
    setHealth(await getDriverMobilityHealth());
  }

  return { location, health, error, stop };
}
