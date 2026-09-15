from __future__ import annotations

"""Optional source: Adzuna (https://developer.adzuna.com/).

Disabled unless ADZUNA_APP_ID and ADZUNA_APP_KEY are set (free account required).
Adds non-remote / local job coverage on top of the always-on remote-job sources.
"""

from datetime import datetime

import httpx

from ..config import (
    ADZUNA_APP_ID,
    ADZUNA_APP_KEY,
    ADZUNA_COUNTRY,
    ADZUNA_QUERY,
    REQUEST_TIMEOUT,
    USER_AGENT,
)
from ..models import Job
from ..textutils import clean_snippet, infer_job_type

API_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"

_TYPE_MAP = {
    "full_time": "full-time",
    "part_time": "part-time",
}


async def fetch(client: httpx.AsyncClient) -> list[Job]:
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        return []

    try:
        resp = await client.get(
            API_URL.format(country=ADZUNA_COUNTRY),
            params={
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_APP_KEY,
                "results_per_page": 50,
                "what": ADZUNA_QUERY,
                "content-type": "application/json",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    jobs: list[Job] = []
    for item in data.get("results", []):
        title = item.get("title") or ""
        company = (item.get("company") or {}).get("display_name") or "Unknown"
        url = item.get("redirect_url") or ""
        if not url:
            continue
        location = (item.get("location") or {}).get("display_name")
        posted_at = None
        if item.get("created"):
            try:
                posted_at = datetime.fromisoformat(item["created"].replace("Z", "+00:00"))
            except ValueError:
                posted_at = None

        raw_type = (item.get("contract_time") or "").lower()
        job_type = _TYPE_MAP.get(raw_type) or infer_job_type(title, item.get("contract_type"), raw_type)

        salary = None
        if item.get("salary_min") or item.get("salary_max"):
            salary = f"${item.get('salary_min', '?'):.0f} - ${item.get('salary_max', '?'):.0f}" if isinstance(
                item.get("salary_min"), (int, float)
            ) else None

        jobs.append(
            Job(
                id=Job.make_id("adzuna", url),
                title=title,
                company=company,
                location=location,
                remote=False,
                job_type=job_type,
                url=url,
                source="adzuna",
                posted_at=posted_at,
                tags=[item.get("category", {}).get("label")] if item.get("category") else [],
                salary=salary,
                description_snippet=clean_snippet(item.get("description")),
            )
        )
    return jobs
