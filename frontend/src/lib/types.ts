export type ApplicationStatus =
  | "not_applied"
  | "recommended"
  | "ready_to_apply"
  | "applied"
  | "interview"
  | "offer"
  | "rejected"
  | "withdrawn";

export interface Job {
  id: string;
  company: string;
  title: string;
  location: string | null;
  remote_type: string;
  url: string;
  source: string;
  date_discovered: string;
  date_posted: string | null;
  score: number | null;
  reason: string | null;
  status: ApplicationStatus;
}

export interface JobDetail extends Job {
  description_raw: string | null;
}

export interface TailoredResume {
  summary_line?: string;
  bullets?: string[];
  ats_keywords?: string[];
}

export interface RecruiterEmail {
  subject?: string;
  body?: string;
}

export interface GeneratedDocument {
  id: string;
  doc_type: "resume" | "cover_letter" | "recruiter_email";
  content: TailoredResume | RecruiterEmail | string;
  generated_at: string;
}

export interface Contact {
  name: string | null;
  title: string | null;
  email: string | null;
  linkedin_url: string | null;
  source: string | null;
  confidence: "high" | "medium" | "low" | null;
}

export interface FollowUp {
  id: string;
  company: string;
  title: string;
  due_date: string;
  note: string | null;
  completed: boolean;
}

export interface Stats {
  status_counts: Record<string, number>;
  total_jobs: number;
  total_applied: number;
  interview_rate: number;
}

export interface RunLogEntry {
  id: string;
  run_type: string;
  started_at: string;
  finished_at: string | null;
  jobs_found: number;
  jobs_new: number;
  errors: string | null;
}

export interface InsightsReport {
  id: string;
  period_days: number;
  jobs_scored: number;
  generated_at: string;
  summary: string;
  missing_skills: string[];
  frequent_technologies: string[];
  strong_companies: string[];
  resume_suggestions: string[];
  application_counts: Record<string, number>;
}
