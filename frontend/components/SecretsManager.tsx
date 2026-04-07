"use client";
import { useState, useEffect } from "react";

export default function SecretsManager({ accessToken, apiUrl }: { accessToken: string; apiUrl: string }) {
  const [services, setServices] = useState<any[]>([]);
  const [service, setService] = useState("slack");
  const [token, setToken] = useState("");
  const [msg, setMsg] = useState("");
  const [totpUri, setTotpUri] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [otpMsg, setOtpMsg] = useState("");

  const headers = { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" };

  const loadServices = () => {
    fetch(`${apiUrl}/secrets/list`, { headers })
      .then((r) => r.json())
      .then((d) => setServices(d.connected_services || []))
      .catch(() => {});
  };

  useEffect(() => { loadServices(); }, [accessToken]);

  const storeToken = async () => {
    const resp = await fetch(`${apiUrl}/secrets/store`, {
      method: "POST", headers,
      body: JSON.stringify({ service, token, scopes: [] }),
    });
    setMsg(resp.ok ? `SUCCESS: ${service} credential encrypted and vaulted` : "ERROR: Encryption failed");
    setToken("");
    loadServices();
    setTimeout(() => setMsg(""), 5000);
  };

  const deleteService = async (svc: string) => {
    await fetch(`${apiUrl}/secrets/${svc}`, { method: "DELETE", headers });
    loadServices();
  };

  const setupTotp = async () => {
    const resp = await fetch(`${apiUrl}/secrets/totp/setup`, { headers });
    const data = await resp.json();
    setTotpUri(data.provisioning_uri || "");
  };

  const verifyTotp = async () => {
    const resp = await fetch(`${apiUrl}/secrets/totp/verify`, {
      method: "POST", headers,
      body: JSON.stringify({ otp_code: otpCode }),
    });
    setOtpMsg(resp.ok ? "AUTH_SUCCESS: Step-up authorization confirmed" : "AUTH_ERROR: Invalid code sequence");
    setOtpCode("");
    setTimeout(() => setOtpMsg(""), 5000);
  };

  return (
    <div className="glass overflow-hidden border-white/5 h-full flex flex-col">
      <div className="p-6 border-b border-white/5 flex items-center justify-between">
        <h2 className="text-white font-bold text-lg tracking-tight uppercase">Identity Vault</h2>
        <div className="flex items-center gap-2">
            <span className="glow-point bg-emerald-500 shadow-emerald-500" />
            <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-widest">Encrypted</span>
        </div>
      </div>

      <div className="p-6 space-y-8">
        {/* Connected Services */}
        <div>
          <label className="block text-[10px] font-bold text-gray-500 mb-4 uppercase tracking-[0.2em]">Authorized Vectors</label>
          {services.length === 0 ? (
            <div className="p-4 border border-dashed border-white/10 rounded-lg text-center">
                <p className="text-gray-600 text-xs uppercase tracking-widest italic">No active connections</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {services.map((s) => (
                <div key={s.service} className="flex items-center justify-between bg-white/[0.03] border border-white/5 hover:border-emerald-500/20 rounded-lg px-4 py-3 group transition-all">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
                    <span className="text-white text-xs font-bold uppercase tracking-widest">{s.service}</span>
                  </div>
                  <button onClick={() => deleteService(s.service)} className="text-gray-600 hover:text-rose-400 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="text-xs font-bold uppercase tracking-tighter">revoke</span>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Store Token */}
        <div className="space-y-4">
          <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-[0.2em]">Add Credential</label>
          <div className="flex flex-col gap-3">
            <div className="flex gap-2">
                <select
                className="bg-black/30 border border-white/5 text-white rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-500 flex-none w-28 h-10"
                value={service}
                onChange={(e) => setService(e.target.value)}
                >
                <option value="slack">Slack</option>
                <option value="github">GitHub</option>
                <option value="gmail">Gmail</option>
                </select>
                <input
                type="password"
                className="flex-1 input-field h-10 text-xs"
                placeholder="Paste Scoped API Token"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                />
            </div>
            <button
              onClick={storeToken}
              disabled={!token}
              className="btn-primary w-full h-10 text-xs"
            >
              COMMIT TO VAULT
            </button>
          </div>
          {msg && <p className={`text-[10px] font-mono text-center uppercase tracking-widest ${msg.includes('SUCCESS') ? 'text-emerald-400' : 'text-rose-400'}`}>{msg}</p>}
        </div>

        {/* Step-up MFA */}
        <div className="pt-6 border-t border-white/5 space-y-4">
          <div className="flex items-center justify-between">
              <label className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.2em]">Step-up Authentication</label>
              <span className="text-amber-500 text-[8px] font-black uppercase bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">Required for Escalate</span>
          </div>
          <p className="text-gray-500 text-[10px] uppercase tracking-wide leading-relaxed">
            Link a TOTP authenticator (Google/Authy) for high-risk manual authorizations.
          </p>
          
          <div className="flex flex-col gap-3">
            <button onClick={setupTotp} className="btn-secondary w-full h-10 text-[10px] flex items-center justify-center gap-2">
               INITIATE TOTP HANDSHAKE
            </button>
            
            <div className="flex gap-2">
                <input
                    className="flex-1 input-field h-10 text-sm tracking-[0.5em] text-center font-mono"
                    placeholder="000000"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    maxLength={6}
                />
                <button onClick={verifyTotp} disabled={otpCode.length !== 6} className="bg-amber-500 hover:bg-amber-600 disabled:bg-gray-700 text-black px-4 py-2 rounded-lg text-[10px] font-bold uppercase transition w-24">
                    VERIFY
                </button>
            </div>
          </div>

          {totpUri && (
            <div className="p-4 bg-black/40 border border-blue-500/20 rounded-lg space-y-3">
                <p className="text-[10px] text-blue-400 font-bold uppercase tracking-widest">Provisioning Configuration</p>
                <div className="p-3 bg-white/5 rounded text-[10px] font-mono text-gray-400 break-all select-all border border-white/5">
                    {totpUri}
                </div>
                <p className="text-[8px] text-gray-500 uppercase italic">Scan the URI above with your TOTP app.</p>
            </div>
          )}
          {otpMsg && <p className={`text-[10px] font-mono text-center uppercase tracking-widest ${otpMsg.includes('SUCCESS') ? 'text-emerald-400' : 'text-rose-400'}`}>{otpMsg}</p>}
        </div>
      </div>
      
      <div className="mt-auto p-4 bg-white/[0.01] border-t border-white/5">
        <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-500 pulse" />
            <p className="text-gray-600 text-[8px] uppercase tracking-[0.3em]">Vault Status: Synchronized (AES-256-GCM)</p>
        </div>
      </div>
    </div>
  );
}
