"""
notifier.py — sends email notifications for strong new matches and due
follow-ups. If SMTP isn't configured, falls back to printing (so nothing
is silently lost — you just read it in the GitHub Actions log instead).
"""
import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "config"))
from settings import settings


def _safe_print(text: str) -> None:
    """Windows consoles default to a legacy codepage (e.g. cp1252) that can't
    display every Unicode character an AI-generated digest might contain
    (em-dashes, smart quotes, etc). Fall back to replacing those characters
    rather than crashing the whole run over a print statement."""
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "ascii"
        print(text.encode(encoding, errors="replace").decode(encoding))


def _send(subject: str, html_body: str) -> bool:
    if not all([settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USER,
                settings.SMTP_PASS, settings.DIGEST_TO]):
        _safe_print(f"[notify] SMTP not configured — printing instead.\nSubject: {subject}\n{html_body}")
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = settings.DIGEST_TO
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP(settings.SMTP_HOST, int(settings.SMTP_PORT)) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_USER, [settings.DIGEST_TO], msg.as_string())
        _safe_print(f"[notify] email sent to {settings.DIGEST_TO}")
        return True
    except Exception as e:
        _safe_print(f"[notify] send failed: {e}\n{html_body}")
        return False


def notify_strong_matches(strong_matches: list) -> None:
    """strong_matches: list of dicts {job, score, reason}"""
    if not strong_matches:
        return
    rows = "".join(
        f"<tr><td>{m['job'].company.name if m['job'].company else ''}</td>"
        f"<td>{m['job'].title}</td><td>{m['score']}</td>"
        f"<td>{m['reason']}</td>"
        f"<td><a href='{m['job'].url}'>Link</a></td></tr>"
        for m in strong_matches
    )
    html = (
        f"<h2>Internship Copilot — {len(strong_matches)} strong new match(es)</h2>"
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>Company</th><th>Role</th><th>Score</th><th>Why</th><th>Link</th></tr>"
        f"{rows}</table>"
        "<p>Tailored resume, cover letter, and recruiter email have been generated for each. "
        "Open the dashboard to review and mark them 'ready_to_apply'.</p>"
    )
    _send(f"Internship Copilot — {len(strong_matches)} strong match(es)", html)


def notify_weekly_insights(insights: dict) -> None:
    """insights: the dict returned by src/insights/generator.generate_insights()."""
    if not insights.get("jobs_scored"):
        return

    def _list_items(values: list) -> str:
        return "".join(f"<li>{v}</li>" for v in values) or "<li>(none)</li>"

    html = (
        f"<h2>Internship Copilot — weekly insights ({insights['jobs_scored']} jobs scored "
        f"in the last {insights['period_days']} days)</h2>"
        f"<p>{insights.get('summary', '')}</p>"
        "<h3>Skills most often missing</h3><ul>" + _list_items(insights.get("missing_skills", [])) + "</ul>"
        "<h3>Frequently requested technologies</h3><ul>" + _list_items(insights.get("frequent_technologies", [])) + "</ul>"
        "<h3>Companies you match well with</h3><ul>" + _list_items(insights.get("strong_companies", [])) + "</ul>"
        "<h3>Resume suggestions</h3><ul>" + _list_items(insights.get("resume_suggestions", [])) + "</ul>"
    )
    _send("Internship Copilot — weekly insights", html)


def notify_due_followups(followups: list) -> None:
    """followups: list of dicts {company, role, due_date, note}"""
    if not followups:
        return
    rows = "".join(
        f"<tr><td>{f['company']}</td><td>{f['role']}</td><td>{f['due_date']}</td><td>{f['note']}</td></tr>"
        for f in followups
    )
    html = (
        f"<h2>Internship Copilot — {len(followups)} follow-up(s) due</h2>"
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>Company</th><th>Role</th><th>Due</th><th>Note</th></tr>"
        f"{rows}</table>"
    )
    _send(f"Internship Copilot — {len(followups)} follow-up(s) due today", html)
