import { apiRequest } from "./client";
import { setAuthSession } from "./session";
import { DEVICE_ID, DRIVER_ID, ORGANIZATION_ID, TEST_MODE } from "../config/environment";
import { attestDevice } from "../../../afriride_system/mobile/shared/deviceAttestation";

type AuthRole = "CUSTOMER" | "DRIVER" | "OPERATOR";

type AuthResponse = {
  token: string;
};

export async function loginPilot(
  userId: string,
  role: AuthRole,
  organizationId: string = ORGANIZATION_ID,
): Promise<string> {
  await attestDevice({ apiRequest, deviceId: DEVICE_ID, testMode: TEST_MODE });
  const result = await apiRequest<AuthResponse>("/v1/auth/token", {
    method: "POST",
    body: {
      user_id: userId,
      role,
      organization_id: organizationId,
    },
  });

  const driverId = DRIVER_ID || (TEST_MODE ? userId : "");
  await setAuthSession(result.token, { driverId, role, organizationId });
  return result.token;
}
