export async function loginUser({ userId, role }) {
  return {
    user: {
      id: userId,
      role,
    },
    authenticated: true,
  };
}

export async function registerUser({ userId, role }) {
  return {
    user: {
      id: userId,
      role,
    },
    authenticated: true,
  };
}

export const login = loginUser;
export const register = registerUser;
