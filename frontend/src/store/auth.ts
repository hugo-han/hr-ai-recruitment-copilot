import { create } from "zustand";

interface AuthState {
  token: string | null;
  role: string;
  name: string;
  setAuth: (token: string, role: string, name: string) => void;
  logout: () => void;
  isLoggedIn: () => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem("token"),
  role: localStorage.getItem("role") || "",
  name: localStorage.getItem("name") || "",
  setAuth: (token, role, name) => {
    localStorage.setItem("token", token);
    localStorage.setItem("role", role);
    localStorage.setItem("name", name);
    set({ token, role, name });
  },
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("name");
    set({ token: null, role: "", name: "" });
  },
  isLoggedIn: () => !!get().token,
}));
