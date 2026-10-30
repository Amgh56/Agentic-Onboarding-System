import { api, setToken } from "@/shared/lib/api-client";
import type { LoginForm, SignupForm, User } from "./auth.model";

type TokenResponse = { access_token: string };

export async function login(values: LoginForm) {
  const data = await api<TokenResponse>("/auth/login", { method: "POST", body: values });
  setToken(data.access_token);
}

export async function signup(values: SignupForm) {
  const data = await api<TokenResponse>("/auth/signup", { method: "POST", body: values });
  setToken(data.access_token);
}

export const getMe = () => api<User>("/auth/me");
