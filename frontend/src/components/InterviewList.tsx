import type { ApplicationStatus, Job } from "../lib/types";
import { StatusSelect } from "./StatusSelect";

export function InterviewList({
  jobs,
  onStatusChanged,
}: {
  jobs: Job[];
  onStatusChanged: (jobId: string, next: ApplicationStatus) => void;
}) {
  if (jobs.length === 0) {
    return <p className="py-8 text-center text-gray-500">Nothing in interview, offer, or rejected yet.</p>;
  }

  return (
    <div className="space-y-2">
      {jobs.map((job) => (
        <div
          key={job.id}
          className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3 dark:border-gray-800"
        >
          <div>
            <span className="font-medium">{job.company}</span> — {job.title}
          </div>
          <StatusSelect jobId={job.id} status={job.status} onChanged={(next) => onStatusChanged(job.id, next)} />
        </div>
      ))}
    </div>
  );
}
