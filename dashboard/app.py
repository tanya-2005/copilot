"""
app.py — Streamlit dashboard for the Internship Copilot.

Run locally:   streamlit run dashboard/app.py
Or deploy free on Streamlit Community Cloud pointing at this file, with
DATABASE_URL set as a secret there too.

Views: New jobs, Recommended (strong matches), Applied, Interview, Response
stats, follow-up reminders, and AI insights. Status changes here are what
apply_approved.py and the discovery run act on.
"""
import sys
import os
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "storage"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "documents"))

import json

import streamlit as st
import pandas as pd

try:
    # Streamlit Community Cloud only exposes secrets via st.secrets, not
    # os.environ — but every other module in this project (including ones
    # reused here, like settings.py) reads config through os.environ so it
    # works the same locally (.env) and in GitHub Actions (real env vars).
    # Bridge the two here, before settings.py is imported, so nothing else
    # needs to know it's running on Community Cloud.
    for _key, _value in st.secrets.items():
        os.environ.setdefault(_key, str(_value))
except Exception:
    pass  # no secrets.toml locally — settings.py falls back to .env via dotenv

from settings import settings
from db import get_session
from models import Job, Company, JobMatch, Application, ApplicationStatus, Contact, FollowUp, GeneratedDocument, Insight
from exporters import build_docx_bytes

st.set_page_config(page_title="Internship Copilot", layout="wide")
st.title("Internship copilot")


def load_jobs_df(session, status_filter=None):
    q = (
        session.query(Job, Company, JobMatch, Application)
        .outerjoin(Company, Job.company_id == Company.id)
        .outerjoin(JobMatch, JobMatch.job_id == Job.id)
        .outerjoin(Application, Application.job_id == Job.id)
    )
    rows = q.all()
    data = []
    for job, company, match, app in rows:
        status = app.status.value if app else "not_applied"
        if status_filter and status not in status_filter:
            continue
        data.append({
            "job_id": str(job.id),
            "company": company.name if company else "?",
            "title": job.title,
            "location": job.location,
            "score": match.match_score if match else None,
            "reason": match.match_reason if match else "",
            "status": status,
            "url": job.url,
            "source": job.source.value,
            "date_discovered": job.date_discovered,
        })
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values(by=["score"], ascending=False, na_position="last")
    return df


def status_update_widget(session, job_id: str, current_status: str, key_suffix: str):
    options = [s.value for s in ApplicationStatus]
    new_status = st.selectbox("Status", options, index=options.index(current_status),
                               key=f"status_{job_id}_{key_suffix}")
    if new_status != current_status:
        if st.button("Save", key=f"save_{job_id}_{key_suffix}"):
            app = session.query(Application).filter_by(job_id=job_id).first()
            if not app:
                app = Application(job_id=job_id, status=ApplicationStatus(new_status))
                session.add(app)
            else:
                app.status = ApplicationStatus(new_status)
                if new_status == "applied" and not app.applied_at:
                    app.applied_at = datetime.datetime.now(datetime.timezone.utc)
            session.commit()
            st.rerun()


tab_new, tab_recommended, tab_applied, tab_interview, tab_stats, tab_followups, tab_insights = st.tabs(
    ["New", "Recommended", "Applied", "Interview", "Response stats", "Follow-ups", "Insights"]
)

with get_session() as session:

    with tab_new:
        st.subheader("Newly discovered (not yet reviewed)")
        df = load_jobs_df(session, status_filter=["not_applied"])
        st.dataframe(df[["company", "title", "location", "score", "status", "url"]] if not df.empty else df,
                     use_container_width=True)

    with tab_recommended:
        st.subheader("Recommended (strong matches, ready for your review)")
        df = load_jobs_df(session, status_filter=["recommended", "ready_to_apply"])
        if df.empty:
            st.info("No recommended jobs yet.")
        for _, row in df.iterrows():
            with st.expander(f"{row['company']} — {row['title']}  (score: {row['score']})"):
                st.write(f"**Why it matched:** {row['reason']}")
                st.write(f"**Link:** {row['url']}")

                docs = session.query(GeneratedDocument).filter_by(job_id=row["job_id"]).all()
                for d in docs:
                    if d.doc_type.value == "recruiter_email":
                        try:
                            email = json.loads(d.content_text)
                            st.text_area("Recruiter email — subject", email.get("subject", ""),
                                         height=60, key=f"subj_{d.id}")
                            st.text_area("Recruiter email — body", email.get("body", ""),
                                         height=150, key=f"body_{d.id}")
                        except Exception:
                            st.text_area("Recruiter email", d.content_text, height=150, key=f"email_raw_{d.id}")
                    elif d.content_text:
                        docx_bytes = build_docx_bytes(d.doc_type.value, d.content_text, row["company"], row["title"])
                        st.download_button(
                            f"Download {d.doc_type.value.replace('_', ' ')} (.docx)",
                            docx_bytes,
                            file_name=f"{d.doc_type.value}_{row['company']}_{row['title']}.docx".replace(" ", "_"),
                            key=f"dl_{d.id}",
                        )

                contact = session.query(Contact).filter_by(job_id=row["job_id"]).first()
                if contact:
                    st.write(f"**Possible contact:** {contact.name or '?'} — {contact.title or '?'} "
                              f"({contact.confidence.value if contact.confidence else '?'} confidence) "
                              f"via {contact.source}")
                    if contact.email:
                        st.write(f"Email: {contact.email}")
                    if contact.linkedin_url:
                        st.write(f"LinkedIn: {contact.linkedin_url}")

                status_update_widget(session, row["job_id"], row["status"], "rec")

    with tab_applied:
        st.subheader("Applied")
        df = load_jobs_df(session, status_filter=["applied"])
        st.dataframe(df[["company", "title", "score", "url"]] if not df.empty else df, use_container_width=True)

    with tab_interview:
        st.subheader("Interview / offer / rejected")
        df = load_jobs_df(session, status_filter=["interview", "offer", "rejected"])
        for _, row in df.iterrows():
            with st.expander(f"{row['company']} — {row['title']} ({row['status']})"):
                status_update_widget(session, row["job_id"], row["status"], "int")

    with tab_stats:
        st.subheader("Response statistics")
        all_df = load_jobs_df(session)
        if all_df.empty:
            st.info("No data yet.")
        else:
            counts = all_df["status"].value_counts()
            st.bar_chart(counts)
            total_applied = counts.get("applied", 0) + counts.get("interview", 0) + \
                counts.get("offer", 0) + counts.get("rejected", 0)
            interview_rate = (counts.get("interview", 0) + counts.get("offer", 0)) / total_applied * 100 \
                if total_applied else 0
            st.metric("Total applied", total_applied)
            st.metric("Interview rate", f"{interview_rate:.1f}%")

    with tab_followups:
        st.subheader("Follow-up reminders")
        followups = (
            session.query(FollowUp, Application, Job, Company)
            .join(Application, FollowUp.application_id == Application.id)
            .join(Job, Application.job_id == Job.id)
            .outerjoin(Company, Job.company_id == Company.id)
            .filter(FollowUp.completed == False)  # noqa: E712
            .all()
        )
        for fu, app, job, company in followups:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{company.name if company else '?'} — {job.title}**: due {fu.due_date} — {fu.note}")
            with col2:
                if st.button("Mark done", key=f"fu_{fu.id}"):
                    fu.completed = True
                    session.commit()
                    st.rerun()

        st.divider()
        st.write("Add a follow-up reminder")
        job_options = {f"{c.name if c else '?'} — {j.title}": str(j.id)
                        for j, c in session.query(Job, Company).outerjoin(Company, Job.company_id == Company.id).all()}
        if job_options:
            selected = st.selectbox("Job", list(job_options.keys()))
            due = st.date_input("Due date", datetime.date.today())
            note = st.text_input("Note", "Follow up on application")
            if st.button("Add reminder"):
                job_id = job_options[selected]
                app = session.query(Application).filter_by(job_id=job_id).first()
                if not app:
                    app = Application(job_id=job_id, status=ApplicationStatus.applied)
                    session.add(app)
                    session.flush()
                session.add(FollowUp(application_id=app.id, due_date=due, note=note))
                session.commit()
                st.success("Reminder added.")
                st.rerun()

    with tab_insights:
        st.subheader("AI insights")
        latest = session.query(Insight).order_by(Insight.generated_at.desc()).first()
        if not latest:
            st.info(
                "No insights generated yet — this runs weekly via the 'Weekly Insights' "
                "GitHub Action, or run `python src/scheduler/weekly_insights.py` locally."
            )
        else:
            content = json.loads(latest.content)
            st.caption(
                f"Last {latest.period_days} days · {latest.jobs_scored} job(s) scored · "
                f"generated {latest.generated_at.strftime('%Y-%m-%d')}"
            )
            st.write(content.get("summary", ""))

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Skills most often missing**")
                for s in content.get("missing_skills", []) or ["(none)"]:
                    st.write(f"- {s}")
                st.write("**Companies you match well with**")
                for c in content.get("strong_companies", []) or ["(none)"]:
                    st.write(f"- {c}")
            with col2:
                st.write("**Frequently requested technologies**")
                for t in content.get("frequent_technologies", []) or ["(none)"]:
                    st.write(f"- {t}")
                st.write("**Resume suggestions**")
                for r in content.get("resume_suggestions", []) or ["(none)"]:
                    st.write(f"- {r}")
