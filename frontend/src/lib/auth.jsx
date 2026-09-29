import React, { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

const AuthContext = React.createContext({ user: null, setUser: () => {}, checking: true, logout: async () => {} });

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  useEffect(() => {
    api.get("/auth/me").then((r) => setUser(r.data)).catch(() => setUser(false)).finally(() => setChecking(false));
  }, []);
  const logout = useCallback(async () => {
    try { await api.post("/auth/logout"); } catch (e) {}
    setUser(false);
  }, []);
  return <AuthContext.Provider value={{ user, setUser, checking, logout }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => React.useContext(AuthContext);
