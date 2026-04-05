const DECISION_COLORS: Record<string, string> = {
  APPROVED: "text-green-400 bg-green-400/10",
  DENIED: "text-red-400 bg-red-400/10",
  ESCALATED: "text-yellow-400 bg-yellow-400/10",
  FAILED: "text-orange-400 bg-orange-400/10",
};

export default function AuditTable({ logs }: { logs: any[] }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <h2 className="text-white font-semibold mb-4">Recent Decisions</h2>
      <div className="overflow-auto max-h-96">
        {logs.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-8">No requests yet</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 text-xs uppercase border-b border-gray-800">
                <th className="text-left pb-2">Intent</th>
                <th className="text-left pb-2">Service/Action</th>
                <th className="text-left pb-2">Decision</th>
                <th className="text-left pb-2">Risk</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="py-2 pr-2 text-gray-300 max-w-[150px] truncate" title={log.intent}>
                    {log.intent}
                  </td>
                  <td className="py-2 pr-2 text-gray-400 text-xs">
                    {log.service}/{log.action}
                  </td>
                  <td className="py-2 pr-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${DECISION_COLORS[log.decision] || "text-gray-400"}`}>
                      {log.decision}
                    </span>
                  </td>
                  <td className="py-2 text-gray-400 text-xs">{log.risk_score?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
