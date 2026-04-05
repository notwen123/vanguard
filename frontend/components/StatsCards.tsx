export default function StatsCards({ stats }: { stats: any }) {
  const cards = [
    { label: "Total Requests", value: stats.total_requests, color: "text-blue-400" },
    { label: "Approved", value: stats.approved, color: "text-green-400" },
    { label: "Denied", value: stats.denied, color: "text-red-400" },
    { label: "Escalated", value: stats.escalated, color: "text-yellow-400" },
    { label: "Avg Risk Score", value: stats.avg_risk_score?.toFixed(2), color: "text-purple-400" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {cards.map((c) => (
        <div key={c.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-gray-500 text-xs uppercase tracking-wide">{c.label}</p>
          <p className={`text-3xl font-bold mt-1 ${c.color}`}>{c.value ?? "—"}</p>
        </div>
      ))}
    </div>
  );
}
