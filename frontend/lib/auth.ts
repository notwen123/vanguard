const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const AUTH_MODE = process.env.NEXT_PUBLIC_AUTH_MODE || "local";

export async function localLogin(username: string, password: string): Promise<string> {
  const resp = await fetch(`${API}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!resp.ok) throw new Error("Login failed");
  const data = await resp.json();
  localStorage.setItem("vanguard_token", data.access_token);
  return data.access_token;
}

export function getStoredToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("vanguard_token") || "";
}

export function clearToken() {
  localStorage.removeItem("vanguard_token");
}

export function isLocalMode(): boolean {
  return AUTH_MODE === "local";
}
