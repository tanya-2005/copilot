import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { FollowUp, Job } from "../lib/types";

export function FollowUpsPanel() {
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [dueDate, setDueDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [note, setNote] = useState("Follow up on application");
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    const [fu, allJobs] = await Promise.all([api.listFollowUps(), api.listJobs()]);
    setFollowUps(fu);
    setJobs(allJobs);
    setSelectedJobId((current) => current || allJobs[0]?.id || "");
  }

  useEffect(() => {
    refresh();
  }, []);

  async function markDone(id: string) {
    await api.completeFollowUp(id);
    setFollowUps((prev) => prev.filter((f) => f.id !== id));
  }

  async function addFollowUp() {
    if (!selectedJobId) return;
    setSubmitting(true);
    try {
      const created = await api.createFollowUp({ job_id: selectedJobId, due_date: dueDate, note });
      setFollowUps((prev) => [...prev, created]);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        {followUps.length === 0 ? (
          <p className="py-4 text-center text-gray-500">No follow-ups due.</p>
        ) : (
          followUps.map((fu) => (
            <div
              key={fu.id}
              className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3 dark:border-gray-800"
            >
              <div>
                <span className="font-medium">
                  {fu.company} — {fu.title}
                </span>
                : due {fu.due_date} — {fu.note}
              </div>
              <button
                type="button"
                onClick={() => markDone(fu.id)}
                className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900"
              >
                Mark done
              </button>
            </div>
          ))
        )}
      </div>

      <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
        <h3 className="mb-3 text-sm font-semibold uppercase text-gray-500">Add a follow-up reminder</h3>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col text-sm">
            Job
            <select
              className="mt-1 rounded border border-gray-300 bg-white px-2 py-1 dark:border-gray-700 dark:bg-gray-900"
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.company} — {j.title}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col text-sm">
            Due date
            <input
              type="date"
              className="mt-1 rounded border border-gray-300 bg-white px-2 py-1 dark:border-gray-700 dark:bg-gray-900"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </label>
          <label className="flex flex-col text-sm">
            Note
            <input
              type="text"
              className="mt-1 rounded border border-gray-300 bg-white px-2 py-1 dark:border-gray-700 dark:bg-gray-900"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
          <button
            type="button"
            disabled={submitting || !selectedJobId}
            onClick={addFollowUp}
            className="rounded bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
          >
            Add reminder
          </button>
        </div>
      </div>
    </div>
  );
}
