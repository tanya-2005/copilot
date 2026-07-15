# AI Internship Copilot

Personal-use system that discovers internships daily, scores them against
your resume, generates tailored application documents for strong matches,
finds public recruiter contacts, tracks everything in a dashboard, and
submits applications automatically only where that's genuinely safe —
everywhere else, it hands you a ready-to-go package for a one-click manual
submit.

**Read this before anything else:** [`ARCHITECTURE.md`](ARCHITECTURE.md) has
the full design (schema, modules, data flow). This file is the practical
"how do I actually run this" guide.

---

## How you'll actually use this, day to day

Two very different phases:

**One-time setup (this guide, ~45–60 min):** you'll use VS Code's terminal a
handful of times to install things, create accounts, and push code to
GitHub. This is the only part that feels "technical."

**Daily use, forever after:** you open a **dashboard** in your browser and
click buttons. That's it. The discovery/matching/document-generation runs
automatically in GitHub's cloud (GitHub Actions) every morning — your
computer doesn't need to be on. You never touch the terminal again unless
you want to add a company or change a setting.

---

## Part 1 — One-time setup

### 1.1 Create a Supabase account (the database)

1. https://supabase.com → sign up → **New project**.
2. Pick a name + strong password (save the password) + a region near you.
3. Wait ~2 min for provisioning.
4. **Project Settings → Database → Connection string → URI** → copy the
   **Session pooler** version. It looks like:
   `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres`

### 1.2 Get an OpenRouter API key (free)

https://openrouter.ai/keys → sign in → **Create Key**. No card required for
the free-model pool. This powers matching, tailoring, document generation,
and weekly insights — see "AI provider" below for how it works and how to
swap providers later if you ever want to.

### 1.2b Get a Tavily API key (free)

https://tavily.com → sign up → copy your API key. No card required (1,000
free searches/month). This powers the two web-search features: broader-web
job discovery and the recruiter contact finder. Skip this only if you set
`web_discovery.enabled: false` in `config/sources.yaml` and never call
`find_and_persist_contact` — otherwise those calls will fail without it.

### 1.3 Local setup (VS Code)

```bash
# Open this folder in VS Code, then in its terminal:
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# open .env in the editor, paste in DATABASE_URL, OPENROUTER_API_KEY, and TAVILY_API_KEY
```

### 1.4 Create the database tables

```bash
alembic upgrade head
python src/storage/test_connection.py
```

Should end with: `All expected tables are present.`

### 1.5 Load your resume

Edit `resume/master_resume.txt` if you want to update it (already pre-filled
with your current resume). Then:

```bash
python scripts/load_resume.py resume/master_resume.txt
```

Also replace `resume/master_resume.pdf` with your latest PDF export — it's
used if/when the Lever auto-apply path fires.

### 1.6 Test one full run locally

```bash
python src/scheduler/daily_discovery.py
```

Watch the output. It should search the configured companies, find/score
jobs, and (if any strong matches exist) generate documents and try to find
contacts. If `SMTP_*` isn't set in `.env` yet, it'll print the digest
instead of emailing it — that's fine for this test.

### 1.7 Try the dashboard locally

```bash
streamlit run dashboard/app.py
```

Opens in your browser at `localhost:8501`. Browse the tabs, confirm jobs
show up.

### 1.8 Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<you>/internship-copilot.git
git push -u origin main
```

Make the repo **private** — it'll reference your resume and applications.

### 1.9 Add GitHub Actions secrets

Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Required? | Value |
|---|---|---|
| `DATABASE_URL` | Yes | Same as your `.env` |
| `OPENROUTER_API_KEY` | Yes | Same as your `.env` |
| `TAVILY_API_KEY` | Yes | Same as your `.env` — needed since `web_discovery` is enabled by default |
| `CANDIDATE_NAME` | Yes | Your full name |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `DIGEST_TO` | Optional | For email digests — Gmail: use an [app password](https://myaccount.google.com/apppasswords), not your real password |
| `CANDIDATE_EMAIL`, `CANDIDATE_PHONE` | Optional | Only needed for Lever auto-apply |

### 1.10 Test the workflow manually

Repo → **Actions** tab → **Daily Discovery** → **Run workflow**. Check the
log, then check your Supabase Table Editor to confirm jobs landed there.

### 1.11 (Optional) Deploy the dashboard so it's not just local

Easiest free option: https://share.streamlit.io → connect your GitHub repo
→ point it at `dashboard/app.py` → add `DATABASE_URL`, `OPENROUTER_API_KEY`,
and `TAVILY_API_KEY` as secrets there too. Now the dashboard is a real URL you can open from your
phone.

If you'd rather not deploy it anywhere, that's fine too — just run
`streamlit run dashboard/app.py` locally whenever you want to check in.

---

## Part 2 — Daily use, once it's live

1. Every morning, **Daily Discovery** runs automatically: searches sources,
   dedupes, scores against your resume, generates tailored resume/cover
   letter/recruiter email for strong matches, looks up a public contact,
   and emails you a digest.
2. **Reminder Check** runs shortly after, emailing you any follow-ups due.
3. You open the dashboard (locally or the deployed URL):
   - **New** tab: everything discovered, unscored/unreviewed status.
   - **Recommended** tab: strong matches — expand one to see why it
     matched, download the tailored resume/cover letter, see the recruiter
     email draft and any contact found. Change its status to
     `ready_to_apply` when you want to move forward.
   - **Applied / Interview** tabs: track progress; add follow-up reminders.
   - **Response stats** tab: your funnel at a glance.
4. When you're ready to actually submit: for postings the system can
   auto-submit (currently just simple Lever postings), go to the **Actions**
   tab → **Apply to Approved Applications** → **Run workflow** — this is
   deliberately a manual button, not automatic, since it can send real
   applications. For everything else, use the downloaded resume/cover
   letter and the direct job link to apply yourself — should take under a
   minute per application since everything's pre-written.
5. Mark status `applied` (auto-set for successful auto-submissions, or set
   it yourself after a manual submit).

---

## Adding more companies

Edit `config/sources.yaml`. Find a company's ATS by checking their careers
page URL pattern:

- `boards.greenhouse.io/<token>` → `ats: greenhouse`
- `jobs.lever.co/<token>` → `ats: lever`
- `jobs.ashbyhq.com/<token>` → `ats: ashby`
- `jobs.smartrecruiters.com/<token>` → `ats: smartrecruiters`
- `<tenant>.wdN.myworkdayjobs.com/en-US/<site>` → `ats: workday`,
  `board_token: "<tenant>/wdN/<site>"` (all three pieces come from that URL —
  see the comment in `config/sources.yaml` for a worked example)

Add an entry, commit, push — next scheduled run picks it up.

## Updating your resume

```bash
# after editing resume/master_resume.txt and replacing master_resume.pdf:
python scripts/load_resume.py resume/master_resume.txt
git add resume/ && git commit -m "Update resume" && git push
```

## Adjusting match sensitivity

`config/matching.yaml`: `strong_match_threshold` (default 70) controls what
triggers document generation + notification. `min_log_threshold` (default
40) controls what's even stored at all.

## Project structure

```
internship-copilot/
├── ARCHITECTURE.md          — full design doc
├── README.md                 — this file
├── requirements.txt
├── alembic.ini
├── .env.example
├── config/                   — settings, sources.yaml, matching.yaml
├── resume/                   — master_resume.txt / .pdf
├── generated/                — scratch space during a run (not persisted — see note below)
├── scripts/
│   └── load_resume.py
├── src/
│   ├── storage/               — models, db connection, Alembic migrations
│   ├── discovery/              — Greenhouse/Lever/Ashby/web-search sources
│   ├── dedup/                   — dedup against the database
│   ├── matching/                 — AI scoring
│   ├── documents/                 — resume tailoring, cover letter, recruiter email
│   ├── contacts/                   — public recruiter/HM search
│   ├── notifications/               — email digests
│   └── scheduler/                    — daily_discovery.py, reminder_check.py, apply_approved.py
├── dashboard/
│   └── app.py                — Streamlit dashboard
├── backend/                  — FastAPI API for the React frontend
├── frontend/                 — React + TypeScript + Tailwind dashboard (WIP)
└── .github/workflows/        — the four GitHub Actions
```

## AI Insights

`src/insights/generator.py` produces a periodic report — skills you're most
often missing, technologies that show up frequently in postings, companies
you match well with, and concrete resume suggestions, plus a short weekly
summary. It runs over the trailing week's `job_matches` with a single AI
call (kept cheap by aggregating rather than analyzing job-by-job).

Runs automatically via the **Weekly Insights** GitHub Action (Mondays), or
manually: `python src/scheduler/weekly_insights.py`. Results are stored in
the `insights` table and show up in the dashboard's **Insights** tab (both
Streamlit and, once built, React) and at `GET /api/insights/latest`.

## AI provider

Every AI call in this project (scoring, resume/cover-letter/email writing,
web-search discovery, contact-finding, weekly insights) goes through one
file: `src/ai/client.py`. It calls the OpenRouter API
(openrouter.ai), which fronts many providers' models behind one key — no
card required to use the free-model pool, get a key at openrouter.ai/keys.

This project previously called Google's Gemini API directly, but its free
tier regularly returned "model overloaded" errors under normal, low-volume
use. The default model here, `openrouter/free`, is OpenRouter's own router
that spreads each request across its pool of ~20 free models instead of
hammering one, which is much more reliable in practice.

Two things to know:

- **Web search goes through Tavily, not OpenRouter, to stay free.**
  OpenRouter's own web-search plugin charges a small per-call fee even on
  free models. Instead, `web_search_source.py` and `contact_finder.py` call
  `AIClient.generate(..., use_search=True)`, which fetches real results
  from Tavily's free tier (1,000 searches/month, no card, get a key at
  tavily.com) and stitches them into the prompt as context before the free
  OpenRouter model writes the answer. Both API calls stay on free tiers at
  this project's volume (a few dozen searches a day).
- **Change the model** — set `OPENROUTER_MODEL` in `.env` to a specific
  slug (e.g. `meta-llama/llama-3.3-70b-instruct:free`) if you want
  consistent behavior instead of the pooled router. Browse current options,
  including paid ones, at openrouter.ai/models.

To switch providers entirely, every call in this project goes through
`AIClient.generate(prompt, max_tokens, use_search=...)` in
`src/ai/client.py`. Rewriting that one file's internals (to call a
different provider's API) is the only place you'd need to touch — every
other module (`matching/scorer.py`, `documents/*.py`, `insights/generator.py`,
etc.) is written against that same simple interface and wouldn't need to
change.

**Note on `generated/`:** GitHub Actions runners are thrown away after each
run, so files written there don't persist. The database is the durable
store — every generated document's full content lives in the
`generated_documents` table, and the dashboard rebuilds the actual `.docx`
file on the fly when you click download. `generated/` is only useful for
local testing.

## Backend API (for the React dashboard)

`backend/` is a FastAPI app that exposes the same data/actions as the
Streamlit dashboard over REST, for the upcoming React + TypeScript +
Tailwind frontend. It wraps `src/` directly — no logic is duplicated.

```bash
cd internship-copilot
uvicorn backend.main:app --reload --port 8000
```

Docs at `localhost:8000/docs`. Set `CORS_ORIGINS` in `.env` if the frontend
runs somewhere other than `localhost:5173`. The Streamlit dashboard keeps
working independently — this doesn't replace it yet.

Key routes: `GET /api/jobs` (filter by `status`, `min_score`, `search`),
`GET /api/jobs/{id}`, `GET /api/jobs/{id}/documents`,
`GET /api/jobs/{id}/documents/{doc_type}/download`, `GET /api/jobs/{id}/contact`,
`PATCH /api/applications/{job_id}`, `GET|POST /api/followups`,
`PATCH /api/followups/{id}/complete`, `GET /api/stats`, and
`POST /api/runs/{discovery|reminders|apply}` to trigger the same jobs
GitHub Actions runs on a schedule. `/runs/apply` can submit a real
application — treat it with the same care as the Actions button.

## Troubleshooting

- **Workflow fails with a missing secret error**: check step 1.9 — the
  secret name must match exactly (case-sensitive).
- **No jobs found**: check the Actions log — a company's `board_token`
  might be wrong, or there genuinely are no open matching internships right
  now. Try adding more companies.
- **Dashboard shows nothing**: confirm `DATABASE_URL` is set wherever you're
  running the dashboard (local `.env`, or Streamlit Cloud secrets).
- **Lever auto-apply always falls back to manual**: check `CANDIDATE_NAME`/
  `CANDIDATE_EMAIL` secrets are set, and that `resume/master_resume.pdf`
  exists in the repo (not gitignored).
