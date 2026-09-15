from __future__ import annotations

"""Optional source: Jooble (https://jooble.org/api/about).

Jooble is a job aggregator with its own legitimate partnerships across many boards
(including some Indeed-sourced listings) and a free API key for developers. Unlike
LinkedIn/Indeed, this is an API they actually publish for third-party use.

Disabled unless JOOBLE_API_KEY is set. Jooble's API is query-based (it has no
"list everything" endpoint), so we fetch once per cache refresh using a broad seed
query and then apply Vjobs's normal keyword filter on top of that pool — same
pattern the site already uses for every other source.
"""

from datetime import datetime

import httpx

from ..config import JOOBLE_API_KEY, JOOBLE_LOCATION, JOOBLE_SEED_QUERY, REQUEST_TIMEOUT, USER_AGENT
from ..models import Job
from ..textutils import clean_snippet, infer_job_type

API_URL = "https://jooble.org/api/{key}"


async def fetch(client: httpx.AsyncClient) -> list[Job]:
    if not JOOBLE_API_KEY:
        return []

    try:
        resp = await client.post(
            API_URL.format(key=JOOBLE_API_KEY),
            json={"keywords": JOOBLE_SEED_QUERY, "location": JOOBLE_LOCATION},
            headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    jobs: list[Job] = []
    for item in data.get("jobs", []):
        title = item.get("title") or ""
        company = item.get("company") or "Unknown"
        url = item.get("link") or ""
        if not url:
            continue
        posted_at = None
        if item.get("updated"):
            try:
                posted_at = datetime.strptime(item["updated"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                posted_at = None

        jobs.append(
            Job(
                id=Job.make_id("jooble", url),
                title=title,
                company=company,
                location=item.get("location"),
                remote="remote" in (item.get("location") or "").lower(),
                job_type=infer_job_type(title, item.get("type"), item.get("snippet")),
                url=url,
                source="jooble",
                posted_at=posted_at,
                tags=[item.get("source")] if item.get("source") else [],
                salary=item.get("salary") or None,
                description_snippet=clean_snippet(item.get("snippet")),
            )
        )
    return jobs
