export default function StatsCards({ stats }: { stats: any }) {
  const cards = [
    { label: "Requests", value: stats.total_requests, color: "text-blue-400", glow: "bg-blue-400" },
    { label: "Approved", value: stats.approved, color: "text-emerald-400", glow: "bg-emerald-400" },
    { label: "Denied", value: stats.denied, color: "text-rose-400", glow: "bg-rose-400" },
    { label: "Escalated", value: stats.escalated, color: "text-amber-400", glow: "bg-amber-400" },
    { label: "Avg Risk", value: stats.avg_risk_score?.toFixed(2), color: "text-violet-400", glow: "bg-violet-400" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
      {cards.map((c) => (
        <div key={c.label} className="glass p-6 glass-hover group transition-all duration-500">
          <div className="flex items-center justify-between mb-3">
            <p className="text-gray-500 text-[10px] uppercase tracking-[0.2em] font-bold">{c.label}</p>
            <div className={`w-1.5 h-1.5 rounded-full ${c.glow} opacity-30 group-hover:opacity-100 transition-opacity`} />
          </div>
          <p className={`text-4xl font-black tracking-tighter ${c.color}`}>{c.value ?? "—"}</p>
        </div>
      ))}
    </div>
  );
}
