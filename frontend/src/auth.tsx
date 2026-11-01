import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, getToken, setToken } from "./api/client";
import type { User } from "./api/types";

interface AuthState {
  user: User | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
}

const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) { setReady(true); return; }
    api.get<User>("/auth/me").then(setUser).catch(() => setToken(null)).finally(() => setReady(true));
    const onLogout = () => setUser(null);
    window.addEventListener("biotaeditor:logout", onLogout);
    return () => window.removeEventListener("biotaeditor:logout", onLogout);
  }, []);

  const finish = (r: { token: string; user: User }) => { setToken(r.token); setUser(r.user); };
  const login = useCallback(async (email: string, password: string) => {
    finish(await api.post("/auth/login", { email, password }));
  }, []);
  const signup = useCallback(async (email: string, password: string, name?: string) => {
    finish(await api.post("/auth/signup", { email, password, name }));
  }, []);
  const logout = useCallback(() => { setToken(null); setUser(null); }, []);

  return <Ctx.Provider value={{ user, ready, login, signup, logout }}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth outside AuthProvider");
  return v;
}
