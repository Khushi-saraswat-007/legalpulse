import { createContext, useContext, useState } from "react";
import client from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // Only trust a saved user if we also have a token (old demo logins have none)
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("lp_user");
    return saved && localStorage.getItem("lp_token") ? JSON.parse(saved) : null;
  });

  const login = async (email, password) => {
    // the backend expects form fields named "username" and "password"
    const form = new URLSearchParams({ username: email, password });
    const { data } = await client.post("/auth/login", form);
    localStorage.setItem("lp_token", data.access_token);
    const me = await client.get("/auth/me");
    const u = { email: me.data.email, role: me.data.role };
    localStorage.setItem("lp_user", JSON.stringify(u));
    setUser(u);
  };

  const register = async (email, password) => {
    await client.post("/auth/register", { email, password });
    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem("lp_user");
    localStorage.removeItem("lp_token");
    setUser(null);
  };

  return <AuthContext.Provider value={{ user, login, register, logout }}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext);
}