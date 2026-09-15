from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ..config import REQUEST_TIMEOUT, USER_AGENT
from ..models import Job
from ..textutils import clean_snippet, infer_job_type

API_URL = "https://arbeitnow.com/api/job-board-api"


async def fetch(client: httpx.AsyncClient) -> list[Job]:
    try:
        resp = await client.get(
            API_URL, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT, follow_redirects=True
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    jobs: list[Job] = []
    for item in data.get("data", []):
        title = item.get("title") or ""
        company = item.get("company_name") or "Unknown"
        url = item.get("url") or ""
        if not url:
            continue
        tags = item.get("tags") or []
        job_types = item.get("job_types") or []
        posted_at = None
        if item.get("created_at"):
            try:
                posted_at = datetime.fromtimestamp(int(item["created_at"]), tz=timezone.utc)
            except (ValueError, TypeError):
                posted_at = None

        jobs.append(
            Job(
                id=Job.make_id("arbeitnow", url),
                title=title,
                company=company,
                location=item.get("location") or ("Remote" if item.get("remote") else None),
                remote=bool(item.get("remote")),
                job_type=infer_job_type(title, " ".join(job_types), " ".join(tags)),
                url=url,
                source="arbeitnow",
                posted_at=posted_at,
                tags=[str(t) for t in tags],
                salary=None,
                description_snippet=clean_snippet(item.get("description")),
            )
        )
    return jobs
