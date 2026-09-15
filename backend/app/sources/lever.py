from __future__ import annotations

"""Optional source: Lever job postings (https://github.com/lever/postings-api).

Like Greenhouse, Lever publishes a public no-auth JSON API per company so career
pages and aggregators can embed live postings. No key required — just the
company's Lever site token (the slug in jobs.lever.co/<token>).

Configure via JOBSCOUT_LEVER_BOARDS, a comma-separated list of company tokens,
e.g. "netflix,palantir". Empty by default (no boards tracked).
"""

import asyncio
from datetime import datetime, timezone

import httpx

from ..config import LEVER_BOARDS, REQUEST_TIMEOUT, USER_AGENT
from ..models import Job
from ..textutils import clean_snippet, infer_job_type

API_URL = "https://api.lever.co/v0/postings/{company}"

_COMMITMENT_MAP = {
    "full-time": "full-time",
    "part-time": "part-time",
    "contract": "contract",
    "intern": "internship",
    "internship": "internship",
}


async def _fetch_board(client: httpx.AsyncClient, company: str) -> list[Job]:
    try:
        resp = await client.get(
            API_URL.format(company=company),
            params={"mode": "json"},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    company_display = company.replace("-", " ").title()
    jobs: list[Job] = []
    for item in data:
        title = item.get("text") or ""
        url = item.get("hostedUrl") or ""
        if not url:
            continue
        categories = item.get("categories") or {}
        location = categories.get("location")
        commitment = (categories.get("commitment") or "").lower()
        job_type = _COMMITMENT_MAP.get(commitment) or infer_job_type(title, commitment)

        posted_at = None
        if item.get("createdAt"):
            try:
                posted_at = datetime.fromtimestamp(int(item["createdAt"]) / 1000, tz=timezone.utc)
            except (ValueError, TypeError):
                posted_at = None

        jobs.append(
            Job(
                id=Job.make_id("lever", url),
                title=title,
                company=company_display,
                location=location,
                remote=bool(location and "remote" in location.lower()),
                job_type=job_type,
                url=url,
                source="lever",
                posted_at=posted_at,
                tags=[categories.get("team")] if categories.get("team") else [],
                salary=None,
                description_snippet=clean_snippet(item.get("descriptionPlain")),
            )
        )
    return jobs


async def fetch(client: httpx.AsyncClient) -> list[Job]:
    if not LEVER_BOARDS:
        return []
    results = await asyncio.gather(*(_fetch_board(client, c) for c in LEVER_BOARDS), return_exceptions=True)
    jobs: list[Job] = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)
    return jobs
