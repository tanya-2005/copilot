import { useState } from "react";
import type { ApplicationStatus, Contact, GeneratedDocument, Job, RecruiterEmail } from "../lib/types";
import { api } from "../lib/api";
import { StatusSelect } from "./StatusSelect";

function isRecruiterEmail(content: GeneratedDocument["content"]): content is RecruiterEmail {
  return typeof content === "object" && content !== null && !Array.isArray(content) && "subject" in content;
}

export function RecommendedCard({ job, onStatusChanged }: { job: Job; onStatusChanged: (next: ApplicationStatus) => void }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState<GeneratedDocument[] | null>(null);
  const [contact, setContact] = useState<Contact | null>(null);

  async function handleToggle() {
    const next = !open;
    setOpen(next);
    if (next && documents === null) {
      setLoading(true);
      try {
        const [docs, c] = await Promise.all([api.listDocuments(job.id), api.getContact(job.id)]);
        setDocuments(docs);
        setContact(c);
      } finally {
        setLoading(false);
      }
    }
  }

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-800">
      <button
        type="button"
        onClick={handleToggle}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span>
          <span className="font-medium">{job.company}</span> — {job.title}{" "}
          <span className="text-gray-500">(score: {job.score ?? "—"})</span>
        </span>
        <span className="text-gray-400">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="space-y-4 border-t border-gray-200 px-4 py-4 dark:border-gray-800">
          {job.reason && (
            <p>
              <span className="font-medium">Why it matched: </span>
              {job.reason}
            </p>
          )}
          <p>
            <a href={job.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline dark:text-blue-400">
              Open job posting
            </a>
          </p>

          {loading && <p className="text-sm text-gray-500">Loading documents & contact…</p>}

          {documents && documents.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold uppercase text-gray-500">Generated documents</h4>
              {documents.map((d) =>
                d.doc_type === "recruiter_email" && isRecruiterEmail(d.content) ? (
                  <div key={d.id} className="rounded border border-gray-200 p-3 dark:border-gray-800">
                    <p className="text-sm font-medium">Recruiter email — {d.content.subject}</p>
                    <p className="mt-1 whitespace-pre-wrap text-sm text-gray-600 dark:text-gray-400">{d.content.body}</p>
                  </div>
                ) : (
                  <a
                    key={d.id}
                    href={api.documentDownloadUrl(job.id, d.doc_type)}
                    className="inline-block rounded border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900"
                  >
                    Download {d.doc_type.replace("_", " ")} (.docx)
                  </a>
                ),
              )}
            </div>
          )}

          {contact && (
            <div className="text-sm">
              <h4 className="text-sm font-semibold uppercase text-gray-500">Possible contact</h4>
              <p>
                {contact.name ?? "?"} — {contact.title ?? "?"} ({contact.confidence ?? "?"} confidence) via{" "}
                {contact.source ?? "?"}
              </p>
              {contact.email && <p>Email: {contact.email}</p>}
              {contact.linkedin_url && (
                <p>
                  <a href={contact.linkedin_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline dark:text-blue-400">
                    LinkedIn
                  </a>
                </p>
              )}
            </div>
          )}

          <StatusSelect jobId={job.id} status={job.status} onChanged={onStatusChanged} />
        </div>
      )}
    </div>
  );
}
