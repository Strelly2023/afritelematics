import type { GeoPoint, TripRoute } from "../../novaride-core/src";
export const distanceMeters = (a: GeoPoint, b: GeoPoint) => Math.round(Math.hypot(a.latitude - b.latitude, a.longitude - b.longitude) * 111_000);
export const isRouteComplete = (route: TripRoute) => route.points.length >= 2 && route.distanceMeters > 0;
