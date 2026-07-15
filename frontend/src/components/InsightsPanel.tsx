import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { InsightsReport } from "../lib/types";
import { RunsBar } from "./RunsBar";

export function InsightsPanel() {
  const [report, setReport] = useState<InsightsReport | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .latestInsights()
      .then(setReport)
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="py-8 text-center text-gray-500">Loading…</p>;

  if (notFound || !report) {
    return (
      <div className="space-y-3 py-8 text-center text-gray-500">
        <p>No insights generated yet — this runs weekly, or trigger it manually.</p>
        <RunsBar />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
        <p className="text-xs uppercase text-gray-500">
          Last {report.period_days} days · {report.jobs_scored} job(s) scored · generated{" "}
          {new Date(report.generated_at).toLocaleDateString()}
        </p>
        <p className="mt-2">{report.summary}</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <InsightList title="Skills most often missing" items={report.missing_skills} />
        <InsightList title="Frequently requested technologies" items={report.frequent_technologies} />
        <InsightList title="Companies you match well with" items={report.strong_companies} />
        <InsightList title="Resume suggestions" items={report.resume_suggestions} />
      </div>
    </div>
  );
}

function InsightList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
      <h4 className="text-sm font-semibold uppercase text-gray-500">{title}</h4>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-gray-500">Nothing to report.</p>
      ) : (
        <ul className="mt-2 list-inside list-disc space-y-1 text-sm">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
