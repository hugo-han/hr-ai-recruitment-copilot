import { api } from "./client";

export interface LoginResult {
  access_token: string;
  refresh_token: string;
  token_type: string;
  role: string;
  name: string;
}

export interface MeResult {
  id: number;
  username: string;
  name: string;
  role: string;
}

export async function login(username: string, password: string): Promise<LoginResult> {
  const resp = await api.post<LoginResult>("/auth/login", { username, password });
  return resp.data;
}

export async function refreshToken(refresh_token: string) {
  const resp = await api.post("/auth/refresh", { refresh_token });
  return resp.data;
}

export async function getMe(): Promise<MeResult> {
  const resp = await api.get<MeResult>("/auth/me");
  return resp.data;
}
