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
    if (getStoredToken()) router.push("/dashboard");
    
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    if (code && AUTH_MODE === "auth0") {
      exchangeAuth0Code(code);
    }
  }, [router]);

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
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="relative flex flex-col items-center justify-center min-h-screen p-6 overflow-hidden">
      {/* Background Decorative Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/10 rounded-full blur-[120px]" />

      <div className="z-10 w-full max-w-md">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass border-white/5 text-xs font-medium text-blue-400 mb-6 mx-auto">
            <span className="glow-point" /> Authorized to Act — Secure AI Gateway
          </div>
          <h1 className="text-6xl font-extrabold tracking-tight text-white mb-4">
            🛡️ <span className="text-gradient">Vanguard</span>
          </h1>
          <p className="text-gray-400 text-lg leading-relaxed max-w-sm mx-auto">
            The intelligent control plane for sovereign AI agents. 
            Secure. Private. Authorized.
          </p>
        </div>

        <div className="glass p-8 border-white/5 shadow-2xl relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
          
          <div className="relative z-10">
            <h2 className="text-xl font-semibold text-white mb-6">Access Gateway</h2>
            
            {AUTH_MODE === "auth0" ? (
              <button
                onClick={handleAuth0Login}
                className="btn-primary w-full flex items-center justify-center gap-2 h-12"
              >
                Sign in with Auth0 
              </button>
            ) : (
              <form onSubmit={handleLocalLogin} className="flex flex-col gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5 ml-1">IDENTITY</label>
                  <input
                    className="input-field w-full h-12"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5 ml-1">KEY</label>
                  <input
                    type="password"
                    className="input-field w-full h-12"
                    placeholder="Enter passphrase"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
                {error && <p className="text-red-400 text-xs text-center mt-2">{error}</p>}
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary w-full h-12 mt-4"
                >
                  {loading ? "Authenticating..." : "Initialize Session"}
                </button>
                <div className="mt-6 flex flex-col gap-2">
                  <div className="h-px bg-white/5 w-full" />
                  <p className="text-gray-500 text-[10px] text-center uppercase tracking-widest leading-relaxed">
                    Local mode active • uses mock validation<br/>
                    Auth0 Token Vault protection initialized
                  </p>
                </div>
              </form>
            )}
          </div>
        </div>
        
        <div className="mt-12 grid grid-cols-3 gap-4 text-center">
            <div>
                <p className="text-white font-bold text-sm">Zero Trust</p>
                <p className="text-gray-500 text-[10px] uppercase">Architecture</p>
            </div>
            <div className="border-x border-white/5">
                <p className="text-white font-bold text-sm">FIPS 140-2</p>
                <p className="text-gray-500 text-[10px] uppercase">Compliance</p>
            </div>
            <div>
                <p className="text-white font-bold text-sm">Auth0</p>
                <p className="text-gray-500 text-[10px] uppercase">Token Vault</p>
            </div>
        </div>
      </div>

      <footer className="absolute bottom-8 text-gray-600 text-xs tracking-tighter">
        © 2026 VANGUARD SECURITY SYSTEMS • BUILT FOR AUTHORIZED TO ACT HACKATHON
      </footer>
    </main>
  );
}
