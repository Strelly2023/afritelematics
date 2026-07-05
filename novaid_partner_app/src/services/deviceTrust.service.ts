import { TrustedDevice } from "../models";

const now = () => new Date().toISOString();

export async function manageTrustedDevice(
  device: TrustedDevice,
  trusted: boolean,
): Promise<TrustedDevice> {
  return {
    ...device,
    trusted,
    lastSeenAt: now(),
    deviceTrustScore: trusted ? Math.min(device.deviceTrustScore + 1, 100) : Math.max(device.deviceTrustScore - 10, 0),
  };
}
