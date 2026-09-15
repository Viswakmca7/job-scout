from __future__ import annotations

from datetime import datetime

import httpx

from ..config import REQUEST_TIMEOUT, USER_AGENT
from ..models import Job
from ..textutils import clean_snippet, infer_job_type

API_URL = "https://jobicy.com/api/v2/remote-jobs"


async def fetch(client: httpx.AsyncClient) -> list[Job]:
    try:
        resp = await client.get(
            API_URL,
            params={"count": 100},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    jobs: list[Job] = []
    for item in data.get("jobs", []):
        title = item.get("jobTitle") or ""
        company = item.get("companyName") or "Unknown"
        url = item.get("url") or ""
        if not url:
            continue
        job_types = item.get("jobType") or []
        if isinstance(job_types, str):
            job_types = [job_types]
        posted_at = None
        if item.get("pubDate"):
            try:
                posted_at = datetime.fromisoformat(item["pubDate"].replace("Z", "+00:00"))
            except ValueError:
                posted_at = None

        salary = None
        if item.get("annualSalaryMin") or item.get("annualSalaryMax"):
            salary = f"${item.get('annualSalaryMin', '?')} - ${item.get('annualSalaryMax', '?')} / yr"

        industry = item.get("jobIndustry")
        if isinstance(industry, list):
            tags = [str(i) for i in industry]
        elif industry:
            tags = [str(industry)]
        else:
            tags = []

        jobs.append(
            Job(
                id=Job.make_id("jobicy", url),
                title=title,
                company=company,
                location=item.get("jobGeo") or "Remote",
                remote=True,
                job_type=infer_job_type(title, " ".join(job_types)),
                url=url,
                source="jobicy",
                posted_at=posted_at,
                tags=tags,
                salary=salary,
                description_snippet=clean_snippet(item.get("jobExcerpt")),
            )
        )
    return jobs
