# Clearline Grant Dashboard

A private-source funding intelligence dashboard for Clearline Technologies' Canadian entity. It tracks official Canadian opportunities related to recycled-rubber manufacturing, recycling and circular economy initiatives, R&D and new products, AI adoption, and manufacturing automation.

## What it does

- Displays opportunities in a clean, searchable and filterable dashboard.
- Scores every program from 0–100 for its fit with Clearline.
- Links only to official government or program-administrator pages.
- Runs a daily scan and merges verified changes into `data/grants.json`.
- Sends a concise email digest on the 1st and 15th of each month containing only opportunities that have never been emailed before. If there are no new grants, it sends nothing.

## Required GitHub secrets

Add these under **Settings → Secrets and variables → Actions**:

- `OPENAI_API_KEY`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `EMAIL_FROM`, `EMAIL_TO`
- `DASHBOARD_URL` once hosting is configured

The dashboard works without these secrets using the included sample data. The automated research and email workflows require them.

## Matching scope

Edit `config/company.json` to change the company profile, funding priorities, official source domains, or geographic scope. The current scope is Canada only.

## Local preview

Run `python -m http.server 8000`, then open `http://localhost:8000`.

## Important

Automated results are leads, not guaranteed eligibility. Confirm all requirements with the official program administrator before applying.
