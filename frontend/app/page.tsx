"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { localLogin, getStoredToken } from "@/lib/auth";

const AUTH_MODE = process.env.NEXT_PUBLIC_AUTH_MODE || "local";
const AUTH0_DOMAIN = process.env.NEXT_PUBLIC_AUTH0_DOMAIN || "";
const AUTH0_CLIENT_ID = process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID || "";
const AUTH0_AUDIENCE = process.env.NEXT_PUBLIC_AUTH0_AUDIENCE || "vanguard-api";
const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";

export default function Home() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Handle Auth0 callback — exchange code for token
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    if (code && AUTH_MODE === "auth0") {
      exchangeAuth0Code(code);
    }
    // Already logged in
    if (getStoredToken()) router.push("/dashboard");
  }, []);

  const exchangeAuth0Code = async (code: string) => {
    try {
      const resp = await fetch(`https://${AUTH0_DOMAIN}/oauth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          grant_type: "authorization_code",
          client_id: AUTH0_CLIENT_ID,
          code,
          redirect_uri: `${BASE_URL}/`,
        }),
      });
      const data = await resp.json();
      if (data.access_token) {
        localStorage.setItem("vanguard_token", data.access_token);
        router.push("/dashboard");
      }
    } catch {
      setError("Auth0 login failed");
    }
  };

  const handleAuth0Login = () => {
    const params = new URLSearchParams({
      response_type: "code",
      client_id: AUTH0_CLIENT_ID,
      redirect_uri: `${BASE_URL}/`,
      scope: "openid profile email",
      audience: AUTH0_AUDIENCE,
    });
    window.location.href = `https://${AUTH0_DOMAIN}/authorize?${params}`;
  };

  const handleLocalLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await localLogin(username, password);
      router.push("/dashboard");
    } catch {
      setError("Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex flex-col items-center justify-center min-h-screen gap-8 p-8">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-white mb-2">🛡️ Vanguard</h1>
        <p className="text-gray-400 text-xl">Secure Execution Gateway for AI Agents</p>
        <p className="text-gray-500 mt-1 text-sm">Zero Trust · Intent-Based Authorization · Auth0 Token Vault</p>
      </div>

      {AUTH_MODE === "auth0" ? (
        <button
          onClick={handleAuth0Login}
          className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition"
        >
          Sign in with Auth0 →
        </button>
      ) : (
        <form onSubmit={handleLocalLogin} className="w-full max-w-sm flex flex-col gap-3">
          <input
            className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            type="password"
            className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            placeholder="Password (any value in local mode)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white py-3 rounded-lg font-semibold transition"
          >
            {loading ? "Signing in..." : "Sign in →"}
          </button>
          <p className="text-gray-600 text-xs text-center">
            Local mode — any username/password works. Set NEXT_PUBLIC_AUTH_MODE=auth0 for production.
          </p>
        </form>
      )}
    </main>
  );
}
