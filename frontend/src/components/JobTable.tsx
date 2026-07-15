import type { Job } from "../lib/types";
import { StatusBadge } from "./StatusBadge";

export function JobTable({ jobs, emptyLabel }: { jobs: Job[]; emptyLabel: string }) {
  if (jobs.length === 0) {
    return <p className="py-8 text-center text-gray-500">{emptyLabel}</p>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-800">
      <table className="w-full text-left text-sm">
        <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-gray-900 dark:text-gray-400">
          <tr>
            <th className="px-4 py-2">Company</th>
            <th className="px-4 py-2">Role</th>
            <th className="px-4 py-2">Location</th>
            <th className="px-4 py-2">Score</th>
            <th className="px-4 py-2">Status</th>
            <th className="px-4 py-2">Link</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
          {jobs.map((job) => (
            <tr key={job.id}>
              <td className="px-4 py-2 font-medium">{job.company}</td>
              <td className="px-4 py-2">{job.title}</td>
              <td className="px-4 py-2 text-gray-500">{job.location ?? "—"}</td>
              <td className="px-4 py-2">{job.score ?? "—"}</td>
              <td className="px-4 py-2">
                <StatusBadge status={job.status} />
              </td>
              <td className="px-4 py-2">
                <a
                  href={job.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  View
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
