import { apiRequest } from "./client";
import { setAuthToken } from "./session";
import { ORGANIZATION_ID } from "../config/environment";

type AuthRole = "CUSTOMER" | "DRIVER" | "OPERATOR";

type AuthResponse = {
  token: string;
};

export async function loginPilot(
  userId: string,
  role: AuthRole,
  organizationId: string = ORGANIZATION_ID,
): Promise<string> {
  const result = await apiRequest<AuthResponse>("/v1/auth/token", {
    method: "POST",
    body: {
      user_id: userId,
      role,
      organization_id: organizationId,
    },
  });

  setAuthToken(result.token);
  return result.token;
}
