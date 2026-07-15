import { useEffect, useState } from "react";
import { api } from "./lib/api";
import type { ApplicationStatus, Job } from "./lib/types";
import { JobTable } from "./components/JobTable";
import { RecommendedCard } from "./components/RecommendedCard";
import { InterviewList } from "./components/InterviewList";
import { StatsPanel } from "./components/StatsPanel";
import { FollowUpsPanel } from "./components/FollowUpsPanel";
import { InsightsPanel } from "./components/InsightsPanel";
import { RunsBar } from "./components/RunsBar";

const TABS = ["New", "Recommended", "Applied", "Interview", "Stats", "Follow-ups", "Insights"] as const;
type Tab = (typeof TABS)[number];

function App() {
  const [tab, setTab] = useState<Tab>("New");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadJobs() {
    setLoading(true);
    setError(null);
    try {
      setJobs(await api.listJobs());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadJobs();
  }, []);

  function applyStatusChange(jobId: string, next: ApplicationStatus) {
    setJobs((prev) => prev.map((j) => (j.id === jobId ? { ...j, status: next } : j)));
  }

  const newJobs = jobs.filter((j) => j.status === "not_applied");
  const recommendedJobs = jobs.filter((j) => j.status === "recommended" || j.status === "ready_to_apply");
  const appliedJobs = jobs.filter((j) => j.status === "applied");
  const interviewJobs = jobs.filter((j) => ["interview", "offer", "rejected"].includes(j.status));

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Internship Copilot</h1>
        <RunsBar />
      </header>

      <nav className="mb-6 flex gap-1 border-b border-gray-200 dark:border-gray-800">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium ${
              tab === t
                ? "border-b-2 border-blue-600 text-blue-600 dark:text-blue-400"
                : "text-gray-500 hover:text-gray-800 dark:hover:text-gray-200"
            }`}
          >
            {t}
          </button>
        ))}
      </nav>

      {error && <p className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">{error}</p>}
      {loading && !["Stats", "Follow-ups", "Insights"].includes(tab) ? (
        <p className="py-8 text-center text-gray-500">Loading…</p>
      ) : (
        <>
          {tab === "New" && <JobTable jobs={newJobs} emptyLabel="No newly discovered jobs yet." />}

          {tab === "Recommended" && (
            <div className="space-y-3">
              {recommendedJobs.length === 0 ? (
                <p className="py-8 text-center text-gray-500">No recommended jobs yet.</p>
              ) : (
                recommendedJobs.map((job) => (
                  <RecommendedCard key={job.id} job={job} onStatusChanged={(next) => applyStatusChange(job.id, next)} />
                ))
              )}
            </div>
          )}

          {tab === "Applied" && <JobTable jobs={appliedJobs} emptyLabel="Nothing applied to yet." />}

          {tab === "Interview" && (
            <InterviewList jobs={interviewJobs} onStatusChanged={applyStatusChange} />
          )}

          {tab === "Stats" && <StatsPanel />}

          {tab === "Follow-ups" && <FollowUpsPanel />}

          {tab === "Insights" && <InsightsPanel />}
        </>
      )}
    </div>
  );
}

export default App;
