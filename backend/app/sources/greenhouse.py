from __future__ import annotations

"""Optional source: Greenhouse job boards (https://developers.greenhouse.io/job-board.html).

Greenhouse publishes a public, no-auth JSON API per company specifically so career
pages and third-party aggregators can embed a company's live job list. Fully public
and intended for exactly this use — no partnership or key required, just the
company's board token (the slug in boards.greenhouse.io/<token>).

Configure via VJOBS_GREENHOUSE_BOARDS, a comma-separated list of board tokens,
e.g. "stripe,figma,airbnb". Empty by default (no boards tracked).
"""

import asyncio
from datetime import datetime

import httpx

from ..config import GREENHOUSE_BOARDS, REQUEST_TIMEOUT, USER_AGENT
from ..models import Job
from ..textutils import clean_snippet, infer_job_type

API_URL = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs"


async def _fetch_board(client: httpx.AsyncClient, board: str) -> list[Job]:
    try:
        resp = await client.get(
            API_URL.format(board=board),
            params={"content": "true"},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    company_display = board.replace("-", " ").title()
    jobs: list[Job] = []
    for item in data.get("jobs", []):
        title = item.get("title") or ""
        url = item.get("absolute_url") or ""
        if not url:
            continue
        posted_at = None
        if item.get("updated_at"):
            try:
                posted_at = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
            except ValueError:
                posted_at = None

        location = (item.get("location") or {}).get("name")
        content = clean_snippet(item.get("content"), max_len=400)
        departments = [d.get("name") for d in item.get("departments", []) if d.get("name")]

        jobs.append(
            Job(
                id=Job.make_id("greenhouse", url),
                title=title,
                company=company_display,
                location=location,
                remote=bool(location and "remote" in location.lower()),
                job_type=infer_job_type(title, content),
                url=url,
                source="greenhouse",
                posted_at=posted_at,
                tags=departments,
                salary=None,
                description_snippet=content,
            )
        )
    return jobs


async def fetch(client: httpx.AsyncClient) -> list[Job]:
    if not GREENHOUSE_BOARDS:
        return []
    results = await asyncio.gather(*(_fetch_board(client, b) for b in GREENHOUSE_BOARDS), return_exceptions=True)
    jobs: list[Job] = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)
    return jobs
