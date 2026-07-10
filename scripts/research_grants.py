#!/usr/bin/env python3
"""Research Canadian funding programs and merge verified results into the dashboard."""
from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "company.json"
DATA_PATH = ROOT / "data" / "grants.json"

SCHEMA = {
    "type": "object",
    "properties": {
        "grants": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "program": {"type": "string"},
                    "organization": {"type": "string"},
                    "description": {"type": "string"},
                    "category": {"type": "string", "enum": [
                        "Recycling & Circular Economy", "Research & Development",
                        "AI Adoption", "Automation & Robotics", "Workforce & Training",
                        "Capital Equipment", "Energy & Sustainability", "Business Growth",
                        "Export Development", "Tax Credits", "Other Funding"
                    ]},
                    "funding_amount": {"type": "string"},
                    "funding_max": {"type": ["number", "null"]},
                    "funding_type": {"type": "string"},
                    "deadline": {"type": ["string", "null"]},
                    "province": {"type": "string"},
                    "status": {"type": "string", "enum": ["Open", "Upcoming", "Closed"]},
                    "match_score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "fit_reason": {"type": "string"},
                    "official_url": {"type": "string"},
                    "source_domain": {"type": "string"}
                },
                "required": ["program", "organization", "description", "category", "funding_amount",
                             "funding_max", "funding_type", "deadline", "province", "status",
                             "match_score", "fit_reason", "official_url", "source_domain"],
                "additionalProperties": False
            }
        }
    },
    "required": ["grants"],
    "additionalProperties": False
}

def normalized_domain(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")

def allowed_url(url: str, allowed_domains: list[str]) -> bool:
    domain = normalized_domain(url)
    if not url.startswith("https://") or not domain:
        return False
    return any(domain == d or domain.endswith("." + d) for d in allowed_domains)

def reachable(url: str) -> bool:
    try:
        response = requests.get(url, timeout=20, allow_redirects=True,
                                headers={"User-Agent": "ClearlineFundingMonitor/1.0"})
        return response.status_code < 400
    except requests.RequestException:
        return False

def stable_id(program: str, organization: str) -> str:
    raw = f"{organization}-{program}".lower()
    return re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:100]

def research(config: dict) -> list[dict]:
    allowed = config["official_domains"]
    prompt = f"""
Research funding opportunities that are currently open or formally announced in Canada.

Company: {config['company_name']}
Profile: {config['company_description']}
Geographic scope: Canada only. Do not include United States programs.
Search broadly for any grant, non-repayable contribution, repayable contribution, tax credit,
wage subsidy, training subsidy, or government-backed funding program that this company could
realistically use. These are known priorities, but do not exclude a legitimate opportunity merely
because it falls outside them:
{json.dumps(config['priority_categories'], indent=2)}

STRICT SOURCE RULES:
- Each official_url must be the government's or program administrator's official program, eligibility, or application page.
- Never return a blog, news article, search page, consultant page, funding directory, or third-party summary.
- Use only the allowed official domains supplied to the web search tool.
- If the official program page cannot be located, omit the opportunity.
- Do not invent deadlines, amounts, eligibility, or URLs. Use null or 'Not listed' where appropriate.
- Score 80-100 for direct alignment with recycled rubber, recycling, R&D, products, AI or automation.
- Score 60-79 for useful company-wide funding such as workforce, equipment, energy, growth or exports.
- Use below 60 for opportunities that may be eligible but have a weak or conditional business case.
- Keep descriptions and fit reasons plain-language and concise.
- Return up to 20 verified opportunities, prioritizing strong matches.
"""
    client = OpenAI()
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.5"),
        reasoning={"effort": "medium"},
        tools=[{"type": "web_search", "filters": {"allowed_domains": allowed}}],
        tool_choice="required",
        input=prompt,
        text={"format": {"type": "json_schema", "name": "grant_results", "strict": True, "schema": SCHEMA}}
    )
    return json.loads(response.output_text)["grants"]

def merge(found: list[dict], existing: dict, config: dict) -> dict:
    today = date.today().isoformat()
    old = {g["id"]: g for g in existing.get("grants", [])}
    merged = {}
    for grant in found:
        url = grant["official_url"].strip()
        if not allowed_url(url, config["official_domains"]) or not reachable(url):
            continue
        grant_id = stable_id(grant["program"], grant["organization"])
        prior = old.get(grant_id)
        grant.update({
            "id": grant_id,
            "source_domain": normalized_domain(url),
            "is_new": prior is None,
            "first_found": prior.get("first_found", today) if prior else today,
            "last_checked": today,
            "last_updated": today if prior != grant else prior.get("last_updated", today),
            "change_notes": "New opportunity found." if prior is None else "Verified during daily scan."
        })
        merged[grant_id] = grant
    for grant_id, grant in old.items():
        if grant_id.startswith("sample-") and merged:
            continue
        if grant_id not in merged:
            grant["is_new"] = False
            merged[grant_id] = grant
    return {"last_checked": today, "grants": sorted(merged.values(), key=lambda g: -g["match_score"])}

def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    existing = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    DATA_PATH.write_text(json.dumps(merge(research(config), existing, config), indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
