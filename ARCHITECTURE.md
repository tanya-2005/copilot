# AI Internship Copilot — Architecture Design

Personal-use system. Goal: maximize automation in discovery, matching, and
document prep, while keeping every real submission a deliberate, reviewed,
manual (or explicitly-safe-automated) action. Built module-by-module, each
one independently testable before the next is wired in.

---

## 1. Design principles

1. **No ToS violations, no login-scraping.** Every discovery source is either
   a documented public API (Greenhouse/Lever/Ashby), an RSS/official feed, or
   an Apify actor that itself operates within the target site's terms (Apify
   marketplace actors vary — vet each one individually; default to "read public
   listing pages only," never "log in and scrape.")
2. **Submission is opt-in and source-aware.** The system never guesses at a
   form. It auto-submits only where a documented, stable API exists (this will
   likely end up being a short list — maybe just Lever, maybe none at first).
   Everywhere else, it prepares a complete, ready-to-submit package and stops.
3. **One source of truth.** Every job, match, document, and application status
   lives in one database, not scattered CSVs or emails.
4. **Modular.** Each stage (discovery, dedup, storage, matching, document
   generation, contact-finding, notification, dashboard) is a separate service
   with a narrow interface, so new sources or AI features can be added without
   touching the rest.
5. **Idempotent and dedup-safe.** Running discovery twice in a row, or on
   overlapping data from two sources, never creates duplicate jobs or
   duplicate applications.
6. **Cheap to run, cheap to maintain.** Free-tier infrastructure throughout
   (GitHub Actions for scheduling, Supabase free tier for Postgres, Streamlit
   Community Cloud or local for the dashboard). No servers to babysit.

---

## 2. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11 | Best library support for scraping, AI SDKs, data wrangling |
| Database | Supabase (managed Postgres) | Free tier, accessible from both GitHub Actions and the dashboard, real relational schema (unlike a CSV), built-in row-level auth if ever needed |
| ORM | SQLAlchemy + Alembic | Type-safe models, versioned migrations as schema evolves |
| Scheduling | GitHub Actions (cron) | Free, no server to maintain, already used for the earlier tracker version |
| AI | OpenRouter API (free-model pool) | Matching, scoring, resume tailoring, cover letters, recruiter-email drafting. All calls go through one wrapper (`src/ai/client.py`) so the provider can be swapped later without touching every module. |
| Discovery — ATS | Direct REST calls | Greenhouse/Lever/Ashby/Workday/SmartRecruiters all have public, unauthenticated job-board JSON APIs |
| Discovery — broader web | Tavily search (free tier) + OpenRouter free model, optional Apify actors | Search-based fallback for company career pages and boards not on a known ATS |
| Document generation | python-docx / reportlab | ATS-optimized resume + cover letter as real .docx/.pdf files |
| Dashboard | Streamlit | Fastest to build and maintain for a single-user internal tool; reads/writes Supabase directly |
| Notifications | Email (SMTP) to start; Telegram bot optional later | Simple, reliable, no new infra |

Why not FastAPI + React: for a single user, that's two extra services to
deploy, auth, and maintain for no real benefit. Streamlit gives you a live,
filterable, editable dashboard in one file.

---

## 3. High-level data flow

Sources → Discovery/Dedup → Database → AI Matching → (above threshold) →
Document Generation + Contact Finder → Dashboard/Notifications → You approve →
Application submitted (auto where safe, else manual) → status tracked back
into the database.

Scheduler (GitHub Actions cron) triggers discovery + matching daily, and a
separate lightweight job checks for due follow-up reminders.

---

## 4. Database schema

```
companies
  id                pk
  name              text
  ats_type          enum(greenhouse, lever, ashby, rss, web_search, manual)
  board_token       text null          -- identifier in the ATS's URL
  career_page_url   text null
  apify_actor_id    text null
  enabled           boolean default true
  created_at        timestamptz

jobs
  id                pk
  company_id        fk -> companies
  source            enum(greenhouse, lever, ashby, apify, rss, web_search)
  external_id       text null          -- ATS's own job id, when available
  title             text
  location          text
  remote_type       enum(remote, onsite, hybrid, unknown)
  url               text unique        -- primary dedup key
  description_raw   text
  description_hash  text               -- secondary dedup key (catches reposts with new ids)
  date_posted       date null
  date_discovered   timestamptz
  last_seen_at      timestamptz        -- updated each run the job still appears; stale jobs can be auto-archived
  is_active         boolean default true
  UNIQUE (company_id, external_id)

resumes
  id                pk
  version_label     text               -- e.g. "master-2026-07"
  file_path         text
  text_content      text
  is_master         boolean default false
  created_at        timestamptz

job_matches
  id                pk
  job_id            fk -> jobs
  resume_id         fk -> resumes
  match_score       int                -- 0-100
  match_reason      text               -- AI-generated explanation
  matched_at        timestamptz
  ai_model_used     text
  UNIQUE (job_id, resume_id)

generated_documents
  id                pk
  job_id            fk -> jobs
  doc_type          enum(resume, cover_letter, recruiter_email)
  file_path         text null
  content_text      text
  version           int default 1
  generated_at      timestamptz

contacts
  id                pk
  job_id            fk -> jobs
  name              text null
  title             text null
  email             text null
  linkedin_url      text null
  source            text               -- where it was found (company site, public search, etc.)
  confidence        enum(high, medium, low)
  found_at          timestamptz

applications
  id                pk
  job_id            fk -> jobs unique
  status            enum(not_applied, recommended, ready_to_apply, applied,
                          interview, offer, rejected, withdrawn)
  applied_at        timestamptz null
  applied_via       enum(auto, manual) null
  notes             text
  updated_at        timestamptz

follow_ups
  id                pk
  application_id    fk -> applications
  due_date          date
  note              text
  completed         boolean default false

notifications_log
  id                pk
  job_id            fk -> jobs
  channel           enum(email, telegram)
  sent_at           timestamptz

run_log
  id                pk
  run_type          enum(discovery, matching, apply_check, reminder_check)
  started_at        timestamptz
  finished_at       timestamptz
  jobs_found        int
  jobs_new          int
  errors            text null
```

Dedup logic: a job is "new" only if its `url` is not already in `jobs`, **and**
its `description_hash` (normalized title+company+description, hashed) doesn't
match an existing active job — this catches the same posting re-listed under a
new ATS id.

---

## 5. Services / modules

```
discovery/
  base.py              — common interface: fetch() -> list[RawJob]
  ats_greenhouse.py
  ats_lever.py
  ats_ashby.py
  apify_source.py      — wraps specific, vetted Apify actors
  rss_source.py
  web_search_source.py — Tavily search + OpenRouter free model, structured JSON output
  runner.py            — iterates all enabled sources, merges results

dedup/
  dedup_engine.py       — url + description_hash matching against DB

storage/
  models.py             — SQLAlchemy models (mirrors schema above)
  db.py                  — session/connection management (Supabase)
  migrations/            — Alembic

matching/
  scorer.py              — score_job(resume, job) -> {score, reason}
  batch_matcher.py        — runs scoring over all unscored jobs, tiered (cheap score-only pass, then full pass only above threshold)

documents/
  resume_tailor.py        — ATS-optimized resume generation from master resume + JD
  cover_letter_generator.py
  recruiter_email_generator.py
  exporters.py             — renders to .docx / .pdf

contacts/
  contact_finder.py        — searches company site + public sources for recruiter/HM info; never scrapes LinkedIn logins, uses public search only

notifications/
  notifier.py               — sends email (and later Telegram) for strong new matches and due follow-ups

dashboard/
  app.py                     — Streamlit app: New / Recommended / Applied / Interview views, filters, inline status editing, response stats

scheduler/
  daily_discovery.py          — orchestrates discovery → dedup → store → match → notify
  reminder_check.py            — checks follow_ups due today, notifies

config/
  settings.py                  — env var loading
  sources.yaml                  — companies + ATS tokens + Apify actor ids + RSS feeds
  matching.yaml                  — thresholds, keyword filters
```

---

## 6. Folder structure

```
internship-copilot/
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   ├── settings.py
│   ├── sources.yaml
│   └── matching.yaml
├── src/
│   ├── discovery/
│   ├── dedup/
│   ├── storage/
│   │   └── migrations/
│   ├── matching/
│   ├── documents/
│   ├── contacts/
│   ├── notifications/
│   └── scheduler/
├── dashboard/
│   └── app.py
├── resume/
│   ├── master_resume.txt
│   └── master_resume.docx
├── generated/               (gitignored — output docs land here before upload to Supabase storage or attach to job record)
├── tests/
│   ├── test_discovery.py
│   ├── test_dedup.py
│   ├── test_matching.py
│   └── test_documents.py
└── .github/
    └── workflows/
        ├── daily_discovery.yml
        └── reminder_check.yml
```

---

## 7. Notes on specific sources

- **Greenhouse / Lever / Ashby**: documented, public, unauthenticated JSON
  APIs. No ToS concern. This should be the backbone — build and prove this
  module first.
- **Wellfound (AngelList)**: no public jobs API. Options, in order of
  preference: (a) their own RSS/email alerts if available, (b) a vetted Apify
  actor that reads public listing pages without login, (c) skip it and rely on
  web-search discovery instead. Decide this when we build that module — I'd
  suggest starting without it and only adding Apify if the coverage gap is
  real after a few weeks of data.
- **LinkedIn / Indeed**: no automated discovery or application via login or
  scraping — both explicitly prohibit this. The AI client's web search
  grounding can surface public posting URLs for the dashboard, but nothing
  gets scraped or auto-submitted there.
- **Apify**: used narrowly and only where it "genuinely improves discovery,"
  per your instruction — meaning: only for sources with no public API, only
  actors that read public pages (not authenticated scraping), and only after
  the ATS + web-search sources prove insufficient on their own.

---

## 8. Implementation plan (build order)

| Phase | Module | Deliverable |
|---|---|---|
| 1 | `storage/` | Supabase schema live, models + migrations, connection tested |
| 2 | `discovery/ats_*` + `dedup/` | Greenhouse/Lever/Ashby pulling real jobs into the DB, verified no duplicates on repeat runs |
| 3 | `matching/` | Every stored job gets scored against your resume; threshold filtering works |
| 4 | `documents/` | Tailored resume + recruiter email + cover letter generated for a strong match, exported as real files |
| 5 | `contacts/` | Best-effort recruiter/HM lookup attached to strong matches |
| 6 | `notifications/` | Email fires on new strong match and on due follow-ups |
| 7 | `dashboard/` | Streamlit views: New, Recommended, Applied, Interview, stats, editable status |
| 8 | `scheduler/` + GitHub Actions | Daily automated run end-to-end, unattended |
| 9 | Optional expansion | Wellfound/Apify source, Telegram notifications, more AI features (e.g. interview prep generator) |

Each phase ships something you can actually run and inspect before the next
one starts — nothing is built two layers ahead of what's tested.

---

## 9. Open decisions for you before we start building

1. **Apify**: do you already have an Apify account/budget, or should we treat
   it as optional/phase-9?
2. **Contact-finding sources**: comfortable with company-website + public
   search only, or do you want to integrate a paid tool like Hunter.io later
   for better email-finding accuracy?
3. **Notification channel**: email only for now, or set up Telegram from the
   start?
