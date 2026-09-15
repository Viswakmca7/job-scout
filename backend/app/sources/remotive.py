from __future__ import annotations

from datetime import datetime

import httpx

from ..config import REQUEST_TIMEOUT, USER_AGENT
from ..models import Job
from ..textutils import clean_snippet, infer_job_type

API_URL = "https://remotive.com/api/remote-jobs"

_TYPE_MAP = {
    "full_time": "full-time",
    "part_time": "part-time",
    "contract": "contract",
    "freelance": "contract",
    "internship": "internship",
}


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
    for item in data.get("jobs", []):
        title = item.get("title") or ""
        company = item.get("company_name") or "Unknown"
        url = item.get("url") or ""
        if not url:
            continue
        tags = item.get("tags") or []
        posted_at = None
        if item.get("publication_date"):
            try:
                posted_at = datetime.fromisoformat(item["publication_date"].replace("Z", "+00:00"))
            except ValueError:
                posted_at = None

        raw_type = (item.get("job_type") or "").lower()
        job_type = _TYPE_MAP.get(raw_type) or infer_job_type(title, raw_type, " ".join(tags))

        jobs.append(
            Job(
                id=Job.make_id("remotive", url),
                title=title,
                company=company,
                location=item.get("candidate_required_location") or "Remote",
                remote=True,
                job_type=job_type,
                url=url,
                source="remotive",
                posted_at=posted_at,
                tags=[str(t) for t in tags],
                salary=item.get("salary") or None,
                description_snippet=clean_snippet(item.get("description")),
            )
        )
    return jobs
