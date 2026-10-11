import { createContext, useContext, useState } from "react";

const AuthContext = createContext(null);

// Placeholder auth: any email/password works until POST /auth/login exists.
export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("lp_user");
    return saved ? JSON.parse(saved) : null;
  });

  const login = (email) => {
    const u = { email };
    localStorage.setItem("lp_user", JSON.stringify(u));
    setUser(u);
  };

  const logout = () => {
    localStorage.removeItem("lp_user");
    localStorage.removeItem("lp_token");
    setUser(null);
  };

  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext);
}
