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
  const hasDriverIdentity = Boolean(driverId);

  useEffect(() => {
    if (!authenticated || !hasDriverIdentity) return;
    let active = true;
    void registerDriverPush(driverId).catch(() => undefined);
    const interval = setInterval(() => {
      if (!active) return;
      void synchronizeDriverQueue().catch(() => undefined);
    }, 30_000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [authenticated, driverId, hasDriverIdentity]);

  useEffect(() => {
    if (!authenticated || !shiftActive || !hasDriverIdentity) return;
    let active = true;
    let subscription: Location.LocationSubscription | null = null;
    void startDriverBackgroundMobility(driverId)
      .then(async () => {
        if (!active) return;
        subscription = await Location.watchPositionAsync(
          { accuracy: Location.Accuracy.High, distanceInterval: 10, timeInterval: 5000 },
          (nextLocation) => {
            if (active) {
              setLocation(nextLocation);
            }
          },
        );
        if (active) {
          setHealth(await getDriverMobilityHealth());
        }
      })
      .catch((reason) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "mobility_failed");
        }
      });
    return () => {
      active = false;
      subscription?.remove();
    };
  }, [authenticated, driverId, hasDriverIdentity, shiftActive]);

  async function stop() {
    try {
      await stopDriverBackgroundMobility();
      setHealth(await getDriverMobilityHealth());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "mobility_stop_failed");
    }
  }

  return { location, health, error, stop };
}
