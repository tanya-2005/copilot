import { useState } from "react";
import type { ApplicationStatus } from "../lib/types";
import { STATUS_LABELS, STATUS_OPTIONS } from "../lib/statuses";
import { api } from "../lib/api";

export function StatusSelect({
  jobId,
  status,
  onChanged,
}: {
  jobId: string;
  status: ApplicationStatus;
  onChanged: (next: ApplicationStatus) => void;
}) {
  const [saving, setSaving] = useState(false);

  async function handleChange(next: ApplicationStatus) {
    setSaving(true);
    try {
      await api.updateApplication(jobId, { status: next });
      onChanged(next);
    } finally {
      setSaving(false);
    }
  }

  return (
    <select
      className="rounded border border-gray-300 bg-white px-2 py-1 text-sm dark:border-gray-700 dark:bg-gray-900"
      value={status}
      disabled={saving}
      onChange={(e) => handleChange(e.target.value as ApplicationStatus)}
    >
      {STATUS_OPTIONS.map((s) => (
        <option key={s} value={s}>
          {STATUS_LABELS[s]}
        </option>
      ))}
    </select>
  );
}
