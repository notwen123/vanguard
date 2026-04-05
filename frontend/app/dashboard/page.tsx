"use client";
import { useUser } from "@auth0/nextjs-auth0/client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import StatsCards from "@/components/StatsCards";
import AuditTable from "@/components/AuditTable";
import AgentTester from "@/components/AgentTester";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const { user, isLoading } = useUser();
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [accessToken, setAccessToken] = useState<string>("");

  useEffect(() => {
    if (!isLoading && !user) router.push("/");
  }, [user, isLoading, router]);

  useEffect(() => {
    if (!user) return;
    // Get access token for API calls
    fetch("/api/token")
      .then((r) => r.json())
      .then((d) => setAccessToken(d.accessToken || ""))
      .catch(() => {});
  }, [user]);

  useEffect(() => {
    if (!accessToken) return;
    const headers = { Authorization: `Bearer ${accessToken}` };
    fetch(`${API}/audit/stats`, { headers }).then((r) => r.json()).then(setStats).catch(() => {});
    fetch(`${API}/audit/logs?limit=20`, { headers }).then((r) => r.json()).then((d) => setLogs(d.logs || [])).catch(() => {});
  }, [accessToken]);

  if (isLoading || !user) return <div className="flex items-center justify-center h-screen text-gray-400">Loading...</div>;

  return (
    <div className="min-h-screen p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">🛡️ Vanguard Dashboard</h1>
          <p className="text-gray-400 text-sm mt-1">Secure Execution Gateway — {user.email}</p>
        </div>
        <a href="/api/auth/logout" className="text-gray-500 hover:text-gray-300 text-sm">Sign out</a>
      </div>

      {stats && <StatsCards stats={stats} />}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <AgentTester accessToken={accessToken} apiUrl={API} onNewLog={() => {
          const headers = { Authorization: `Bearer ${accessToken}` };
          fetch(`${API}/audit/logs?limit=20`, { headers }).then((r) => r.json()).then((d) => setLogs(d.logs || []));
          fetch(`${API}/audit/stats`, { headers }).then((r) => r.json()).then(setStats);
        }} />
        <AuditTable logs={logs} />
      </div>
    </div>
  );
}
