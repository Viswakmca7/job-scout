from __future__ import annotations

from datetime import datetime

import httpx

from ..config import REQUEST_TIMEOUT, USER_AGENT
from ..models import Job
from ..textutils import clean_snippet, infer_job_type

API_URL = "https://remoteok.com/api"


async def fetch(client: httpx.AsyncClient) -> list[Job]:
    try:
        resp = await client.get(
            API_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    jobs: list[Job] = []
    for item in data:
        if not isinstance(item, dict) or "id" not in item or "position" not in item:
            continue  # first element is a legal-notice record, not a job
        title = item.get("position") or ""
        company = item.get("company") or "Unknown"
        url = item.get("url") or f"https://remoteok.com/remote-jobs/{item.get('id')}"
        tags = item.get("tags") or []
        posted_at = None
        if item.get("date"):
            try:
                posted_at = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
            except ValueError:
                posted_at = None
        salary = None
        if item.get("salary_min") or item.get("salary_max"):
            salary = f"${item.get('salary_min', '?')} - ${item.get('salary_max', '?')}"

        jobs.append(
            Job(
                id=Job.make_id("remoteok", url),
                title=title,
                company=company,
                location=item.get("location") or "Remote",
                remote=True,
                job_type=infer_job_type(title, " ".join(tags)),
                url=url,
                source="remoteok",
                posted_at=posted_at,
                tags=[str(t) for t in tags],
                salary=salary,
                description_snippet=clean_snippet(item.get("description")),
            )
        )
    return jobs
