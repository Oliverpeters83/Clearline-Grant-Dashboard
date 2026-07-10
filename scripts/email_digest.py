#!/usr/bin/env python3
"""Send a concise funding digest through a configured SMTP account."""
import json
import os
import smtplib
from datetime import date
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "email-state.json"

def main():
    data = json.loads((ROOT / "data" / "grants.json").read_text(encoding="utf-8"))
    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {"sent_grant_ids": [], "last_sent": null}
    sent_ids = set(state.get("sent_grant_ids", []))
    grants = [g for g in data["grants"] if g["status"] in ("Open", "Upcoming") and g["id"] not in sent_ids]
    grants.sort(key=lambda g: -g["match_score"])
    if not grants:
        print("No new grants to email; digest skipped.")
        return
    rows = "".join(f"<tr><td><b>{g['program']}</b><br><small>{g['organization']}</small></td><td>{g['category']}</td><td><b>{g['match_score']}%</b></td><td>{g['funding_amount']}</td><td><a href=\"{g['official_url']}\">Official page</a></td></tr>" for g in grants)
    html = f"<h2>Clearline Funding Update</h2><p>{len(grants)} new or updated opportunities from the last two weeks.</p><table cellpadding='8' cellspacing='0' border='1' style='border-collapse:collapse;border-color:#dfe7e2'><tr><th>Program</th><th>Category</th><th>Match</th><th>Funding</th><th>Link</th></tr>{rows}</table><p><a href='{os.getenv('DASHBOARD_URL','#')}'>Open the full dashboard</a></p>"
    msg = EmailMessage();msg["Subject"] = f"Clearline funding update — {date.today():%B %d, %Y}";msg["From"] = os.environ["EMAIL_FROM"];msg["To"] = os.environ["EMAIL_TO"];msg.set_content("Open this email in HTML format to view the funding digest.");msg.add_alternative(html, subtype="html")
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT", "587"))) as server:
        server.starttls();server.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"]);server.send_message(msg)
    state["sent_grant_ids"] = sorted(sent_ids | {g["id"] for g in grants})
    state["last_sent"] = date.today().isoformat()
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__": main()
