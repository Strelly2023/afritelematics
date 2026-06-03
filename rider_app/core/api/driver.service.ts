import { apiRequest } from "./client";

export type DriverRideSummary = {
  rideId: string;
  status: string;
};

export async function getDriverRides(driverId: string): Promise<DriverRideSummary[]> {
  const result = await apiRequest<{ rides: Array<{ ride_id: string; status: string }> }>(
    `/driver/rides?driver_id=${encodeURIComponent(driverId)}`,
  );

  return result.rides.map((ride) => ({
    rideId: ride.ride_id,
    status: ride.status,
  }));
}
