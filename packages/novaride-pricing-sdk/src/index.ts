import type { FareEstimate } from "../../novaride-core/src";
export const estimateFare = (distanceKm: number, minutes: number, surge = 1): FareEstimate => {
  const base = 3.5, distance = distanceKm * 1.7, time = minutes * 0.35, fees = 1.25;
  return { currency: "AUD", base, distance, time, fees, total: Number(((base + distance + time + fees) * surge).toFixed(2)) };
};
