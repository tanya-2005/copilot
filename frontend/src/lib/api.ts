import type {
  ApplicationStatus,
  Contact,
  FollowUp,
  GeneratedDocument,
  InsightsReport,
  Job,
  JobDetail,
  RunLogEntry,
  Stats,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export interface ListJobsParams {
  status?: ApplicationStatus[];
  minScore?: number;
  search?: string;
}

function buildQuery(params: ListJobsParams): string {
  const q = new URLSearchParams();
  params.status?.forEach((s) => q.append("status", s));
  if (params.minScore !== undefined) q.set("min_score", String(params.minScore));
  if (params.search) q.set("search", params.search);
  const qs = q.toString();
  return qs ? `?${qs}` : "";
}

export const api = {
  listJobs: (params: ListJobsParams = {}) => request<Job[]>(`/api/jobs${buildQuery(params)}`),

  getJob: (jobId: string) => request<JobDetail>(`/api/jobs/${jobId}`),

  listDocuments: (jobId: string) => request<GeneratedDocument[]>(`/api/jobs/${jobId}/documents`),

  documentDownloadUrl: (jobId: string, docType: string) =>
    `${API_BASE}/api/jobs/${jobId}/documents/${docType}/download`,

  getContact: (jobId: string) => request<Contact | null>(`/api/jobs/${jobId}/contact`),

  updateApplication: (jobId: string, body: { status?: string; notes?: string }) =>
    request<{ status: string; notes: string | null }>(`/api/applications/${jobId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  listFollowUps: (includeCompleted = false) =>
    request<FollowUp[]>(`/api/followups?include_completed=${includeCompleted}`),

  createFollowUp: (body: { job_id: string; due_date: string; note: string }) =>
    request<FollowUp>("/api/followups", { method: "POST", body: JSON.stringify(body) }),

  completeFollowUp: (id: string) =>
    request<{ completed: boolean }>(`/api/followups/${id}/complete`, { method: "PATCH" }),

  getStats: () => request<Stats>("/api/stats"),

  triggerRun: (kind: "discovery" | "reminders" | "apply" | "insights") =>
    request<{ status: string; run: string }>(`/api/runs/${kind}`, { method: "POST" }),

  listRuns: (limit = 10) => request<RunLogEntry[]>(`/api/runs?limit=${limit}`),

  latestInsights: () => request<InsightsReport>("/api/insights/latest"),
};
