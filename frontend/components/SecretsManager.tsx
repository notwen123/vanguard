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
    setMsg(resp.ok ? `✅ ${service} token stored` : "❌ Failed to store");
    setToken("");
    loadServices();
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
    setOtpMsg(resp.ok ? "✅ TOTP verified — step-up approved" : "❌ Invalid code");
    setOtpCode("");
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <h2 className="text-white font-semibold mb-4">Connected Services & Vault</h2>

      {/* Connected services */}
      <div className="mb-4">
        {services.length === 0 ? (
          <p className="text-gray-500 text-sm">No services connected yet</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {services.map((s) => (
              <div key={s.service} className="flex items-center gap-2 bg-green-500/10 border border-green-500/30 rounded-lg px-3 py-1.5">
                <span className="text-green-400 text-sm">{s.service}</span>
                <button onClick={() => deleteService(s.service)} className="text-gray-500 hover:text-red-400 text-xs">✕</button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Store new token */}
      <div className="flex gap-2 mb-2">
        <select
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none"
          value={service}
          onChange={(e) => setService(e.target.value)}
        >
          <option value="slack">Slack</option>
          <option value="github">GitHub</option>
          <option value="gmail">Gmail</option>
        </select>
        <input
          type="password"
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
          placeholder="Paste API token..."
          value={token}
          onChange={(e) => setToken(e.target.value)}
        />
        <button
          onClick={storeToken}
          disabled={!token}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm transition"
        >
          Store
        </button>
      </div>
      {msg && <p className="text-xs text-gray-400 mb-3">{msg}</p>}

      {/* TOTP step-up */}
      <div className="border-t border-gray-800 pt-3 mt-3">
        <p className="text-gray-500 text-xs mb-2">Step-up Auth (TOTP — Google Authenticator)</p>
        <div className="flex gap-2">
          <button onClick={setupTotp} className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded-lg transition">
            Get QR Setup
          </button>
          <input
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200 focus:outline-none"
            placeholder="6-digit OTP code"
            value={otpCode}
            onChange={(e) => setOtpCode(e.target.value)}
            maxLength={6}
          />
          <button onClick={verifyTotp} disabled={otpCode.length !== 6} className="text-xs bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-700 text-white px-3 py-1.5 rounded-lg transition">
            Verify
          </button>
        </div>
        {totpUri && (
          <p className="text-xs text-blue-400 mt-2 break-all">
            Provisioning URI (paste into authenticator app or generate QR):<br />
            <span className="text-gray-400">{totpUri}</span>
          </p>
        )}
        {otpMsg && <p className="text-xs mt-1 text-gray-300">{otpMsg}</p>}
      </div>
    </div>
  );
}
