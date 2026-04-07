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
    try {
      const sResp = await fetch(`${API}/audit/stats`, { headers });
      const sData = await sResp.json();
      setStats(sData);

      const lResp = await fetch(`${API}/audit/logs?limit=20`, { headers });
      const lData = await lResp.json();
      setLogs(lData.logs || []);
    } catch (e) {
      console.error("Failed to refresh dashboard:", e);
    }
  };

  useEffect(() => {
    if (token) {
      refresh(token);
      const interval = setInterval(() => refresh(token), 10000);
      return () => clearInterval(interval);
    }
  }, [token]);

  const signOut = () => { clearToken(); router.push("/"); };

  if (!token) return (
    <div className="flex flex-col items-center justify-center h-screen gap-4">
      <div className="glow-point scale-150" />
      <p className="text-gray-500 animate-pulse uppercase tracking-widest text-[10px]">Verifying Session...</p>
    </div>
  );

  return (
    <div className="min-h-screen p-6 lg:p-12 max-w-[1600px] mx-auto relative">
      {/* Subtle background glow */}
      <div className="absolute top-0 right-0 w-1/2 h-1/2 bg-blue-500/5 blur-[120px] pointer-events-none" />
      
      <header className="flex flex-col md:flex-row items-start md:items-center justify-between mb-12 gap-6 relative z-10">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-2xl">🛡️</span>
            <h1 className="text-4xl font-black text-white tracking-tight">
              <span className="text-gradient">VANGUARD</span> CONTROL
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <p className="text-gray-500 text-sm font-medium uppercase tracking-wider flex items-center">
              <span className="glow-point" /> Gateway Active
            </p>
            <span className="text-white/10">|</span>
            <p className="text-gray-600 text-xs">Infrastructure Node: US-EAST-1</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
            <div className="glass px-4 py-2 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-bold text-xs">
                    JD
                </div>
                <div className="hidden sm:block">
                    <p className="text-white text-xs font-bold">Admin User</p>
                    <p className="text-gray-500 text-[10px] uppercase">Superuser</p>
                </div>
            </div>
            <button 
                onClick={signOut} 
                className="btn-secondary text-xs h-10 px-4 flex items-center gap-2 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/20"
            >
                Terminate Session
            </button>
        </div>
      </header>

      <main className="relative z-10">
        {stats && <StatsCards stats={stats} />}

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 mt-12">
            <div className="xl:col-span-12">
                <AgentTester accessToken={token} apiUrl={API} onNewLog={() => refresh(token)} />
            </div>
            
            <div className="xl:col-span-8">
                <AuditTable logs={logs} />
            </div>
            
            <div className="xl:col-span-4">
                <SecretsManager accessToken={token} apiUrl={API} />
            </div>
        </div>
      </main>

      <footer className="mt-24 pb-8 border-t border-white/5 pt-8 flex items-center justify-between">
        <p className="text-[10px] text-gray-600 uppercase tracking-widest">
            Vanguard Secure Gateway v1.0.0
        </p>
        <div className="flex gap-6">
            <span className="text-[10px] text-gray-500 uppercase cursor-pointer hover:text-white transition">Docs</span>
            <span className="text-[10px] text-gray-500 uppercase cursor-pointer hover:text-white transition">Network Status</span>
            <span className="text-[10px] text-gray-500 uppercase cursor-pointer hover:text-white transition">Support</span>
        </div>
      </footer>
    </div>
  );
}
