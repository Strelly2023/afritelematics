import { useCallback, useEffect, useState } from "react";
import {
  getRiderLocation,
  getRiderMobilityHealth,
  registerRiderPush,
  synchronizeRiderQueue,
  type MobilityHealth,
} from "../../core/services/mobility.service";

export function useRiderMobility(riderId: string, enabled: boolean) {
  const [location, setLocation] = useState<{ latitude: number; longitude: number } | null>(null);
  const [health, setHealth] = useState<MobilityHealth | null>(null);

  const refresh = useCallback(async () => {
    const [position, snapshot] = await Promise.all([
      getRiderLocation(),
      getRiderMobilityHealth(),
    ]);
    if (position) {
      setLocation({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
      });
    }
    setHealth(snapshot);
  }, []);

  useEffect(() => {
    if (!enabled) return;
    void registerRiderPush(riderId).catch(() => undefined);
    void synchronizeRiderQueue().then(() => refresh());
    const interval = setInterval(() => {
      void synchronizeRiderQueue().then(() => refresh());
    }, 30_000);
    void refresh();
    return () => clearInterval(interval);
  }, [enabled, refresh, riderId]);

  return { location, health, refresh };
}
