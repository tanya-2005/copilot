import { useState } from "react";
import { api } from "../lib/api";

export function RunsBar() {
  const [message, setMessage] = useState<string | null>(null);

  async function trigger(kind: "discovery" | "reminders" | "apply" | "insights") {
    setMessage(null);
    await api.triggerRun(kind);
    setMessage(`${kind} run started — check back in a bit.`);
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <button
        type="button"
        onClick={() => trigger("discovery")}
        className="rounded border border-gray-300 px-3 py-1 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900"
      >
        Run discovery now
      </button>
      <button
        type="button"
        onClick={() => trigger("reminders")}
        className="rounded border border-gray-300 px-3 py-1 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900"
      >
        Check reminders
      </button>
      <button
        type="button"
        onClick={() => trigger("apply")}
        title="Submits real applications for anything marked 'ready to apply'"
        className="rounded border border-amber-400 px-3 py-1 text-amber-700 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-950"
      >
        Apply to approved
      </button>
      <button
        type="button"
        onClick={() => trigger("insights")}
        className="rounded border border-gray-300 px-3 py-1 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900"
      >
        Generate insights
      </button>
      {message && <span className="text-gray-500">{message}</span>}
    </div>
  );
}
