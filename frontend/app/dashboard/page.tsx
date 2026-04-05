"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getStoredToken, clearToken } from "@/lib/auth";
import StatsCards from "@/components/StatsCards";
import AuditTable from "@/components/AuditTable";
import AgentTester from "@/components/AgentTester";
import SecretsManager from "@/components/SecretsManager";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [stats, setStats] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);

  useEffect(() => {
    const t = getStoredToken();
    if (!t) { router.push("/"); return; }
    setToken(t);
  }, [router]);

  const refresh = async (t: string) => {
    const headers = { Authorization: `Bearer ${t}` };
    fetch(`${API}/audit/stats`, { headers }).then((r) => r.json()).then(setStats).catch(() => {});
    fetch(`${API}/audit/logs?limit=20`, { headers }).then((r) => r.json()).then((d) => setLogs(d.logs || [])).catch(() => {});
  };

  useEffect(() => {
    if (token) refresh(token);
    const interval = setInterval(() => { if (token) refresh(token); }, 10000);
    return () => clearInterval(interval);
  }, [token]);

  const signOut = () => { clearToken(); router.push("/"); };

  if (!token) return <div className="flex items-center justify-center h-screen text-gray-400">Loading...</div>;

  return (
    <div className="min-h-screen p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">🛡️ Vanguard Dashboard</h1>
          <p className="text-gray-400 text-sm mt-1">Secure Execution Gateway — live updates every 10s</p>
        </div>
        <button onClick={signOut} className="text-gray-500 hover:text-gray-300 text-sm">Sign out</button>
      </div>

      {stats && <StatsCards stats={stats} />}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <AgentTester accessToken={token} apiUrl={API} onNewLog={() => refresh(token)} />
        <div className="flex flex-col gap-6">
          <AuditTable logs={logs} />
          <SecretsManager accessToken={token} apiUrl={API} />
        </div>
      </div>
    </div>
  );
}
