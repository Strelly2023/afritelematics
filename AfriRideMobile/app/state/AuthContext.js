import React, { createContext, useContext, useEffect, useState } from "react";
import { loginUser, registerUser } from "../services/authService";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  async function login(credentials) {
    const response = await loginUser(credentials);
    setUser(response.user);
    return response;
  }

  async function register(payload) {
    const response = await registerUser(payload);
    setUser(response.user);
    return response;
  }

  function logout() {
    setUser(null);
  }

  useEffect(() => {
    setLoading(false);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: Boolean(user),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
