import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Stats } from "../lib/types";
import { STATUS_LABELS } from "../lib/statuses";
import type { ApplicationStatus } from "../lib/types";

export function StatsPanel() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    api.getStats().then(setStats);
  }, []);

  if (!stats) return <p className="py-8 text-center text-gray-500">Loading…</p>;

  const maxCount = Math.max(1, ...Object.values(stats.status_counts));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Total jobs" value={stats.total_jobs} />
        <StatCard label="Total applied" value={stats.total_applied} />
        <StatCard label="Interview rate" value={`${stats.interview_rate}%`} />
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold uppercase text-gray-500">Status breakdown</h3>
        {Object.entries(stats.status_counts).map(([status, count]) => (
          <div key={status} className="flex items-center gap-3">
            <span className="w-32 shrink-0 text-sm">{STATUS_LABELS[status as ApplicationStatus] ?? status}</span>
            <div className="h-3 flex-1 rounded bg-gray-100 dark:bg-gray-800">
              <div
                className="h-3 rounded bg-blue-500"
                style={{ width: `${(count / maxCount) * 100}%` }}
              />
            </div>
            <span className="w-8 shrink-0 text-right text-sm text-gray-500">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
      <p className="text-xs uppercase text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}
