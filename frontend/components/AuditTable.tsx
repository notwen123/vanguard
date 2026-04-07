const DECISION_COLORS: Record<string, string> = {
  APPROVED: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
  DENIED: "text-rose-400 border-rose-500/20 bg-rose-500/5",
  ESCALATED: "text-amber-400 border-amber-500/20 bg-amber-500/5",
  FAILED: "text-orange-400 border-orange-500/20 bg-orange-500/5",
};

export default function AuditTable({ logs }: { logs: any[] }) {
  return (
    <div className="glass overflow-hidden flex flex-col h-full border-white/5">
      <div className="p-6 border-b border-white/5 flex items-center justify-between">
        <h2 className="text-white font-bold text-lg tracking-tight uppercase">Audit Ledger</h2>
        <p className="text-[10px] text-gray-500 uppercase tracking-widest font-mono">Real-time Stream</p>
      </div>
      <div className="overflow-auto max-h-[600px] flex-grow">
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3 grayscale opacity-50">
            <span className="text-4xl">📄</span>
            <p className="text-gray-500 text-xs uppercase tracking-widest">No activity recorded</p>
          </div>
        ) : (
          <table className="w-full text-sm border-separate border-spacing-0">
            <thead>
              <tr className="text-gray-500 text-[10px] uppercase tracking-widest bg-white/[0.02]">
                <th className="text-left py-3 px-6 font-bold">Intent & Purpose</th>
                <th className="text-left py-3 px-6 font-bold">Vector</th>
                <th className="text-left py-3 px-6 font-bold">Decision</th>
                <th className="text-right py-3 px-6 font-bold">Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {logs.map((log) => (
                <tr key={log.id} className="group hover:bg-white/[0.02] transition-colors">
                  <td className="py-4 px-6">
                    <p className="text-white font-medium mb-0.5 truncate max-w-[200px]" title={log.intent}>
                        {log.intent}
                    </p>
                    <p className="text-[10px] text-gray-500 mono uppercase">{new Date().toLocaleTimeString()}</p>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex flex-col">
                        <span className="text-blue-400 text-xs font-bold uppercase">{log.service}</span>
                        <span className="text-gray-500 text-[10px] mono uppercase">{log.action}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <span className={`px-2 py-1 rounded-md text-[10px] font-black tracking-tighter border ${DECISION_COLORS[log.decision] || "text-gray-400"}`}>
                      {log.decision}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-right">
                    <span className={`text-xs font-mono font-bold ${log.risk_score > 0.6 ? 'text-rose-400' : 'text-gray-400'}`}>
                        {(log.risk_score || 0).toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
