type Requester = <T>(
  path: string,
  options: { method: "POST"; body: Record<string, unknown> },
) => Promise<T>;

type TokenProvider = (challenge: {
  platform: "android" | "ios";
  nonce: string;
  cloudProjectNumber?: string;
}) => Promise<string>;

declare global {
  var __AFRIRIDE_DEVICE_ATTESTATION_TOKEN_PROVIDER__: TokenProvider | undefined;
}

export function registerAttestationTokenProvider(provider: TokenProvider): void;
export function attestDevice(options: {
  apiRequest: Requester;
  deviceId: string;
  testMode: boolean;
}): Promise<Record<string, unknown>>;
