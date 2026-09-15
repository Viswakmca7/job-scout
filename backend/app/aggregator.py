from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from .config import MAX_JOB_AGE_DAYS
from .models import Job
from .sources import ALL_SOURCES

logger = logging.getLogger("vjobs.aggregator")


async def fetch_all_jobs() -> list[Job]:
    """Fan out to every source concurrently, tolerating individual failures."""
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *(source(client) for source in ALL_SOURCES),
            return_exceptions=True,
        )

    jobs: list[Job] = []
    for source, result in zip(ALL_SOURCES, results):
        if isinstance(result, Exception):
            logger.warning("source %s failed: %s", getattr(source, "__module__", source), result)
            continue
        jobs.extend(result)

    before = len(jobs)
    jobs = _drop_stale(jobs)
    dropped = before - len(jobs)
    if dropped:
        logger.info("dropped %d jobs older than %d days", dropped, MAX_JOB_AGE_DAYS)

    return _dedupe(jobs)


def _drop_stale(jobs: list[Job]) -> list[Job]:
    """Some sources (RemoteOK, Remotive) keep long-open listings around for weeks —
    their date is real but stale enough to make results feel out of date. Jobs with
    no date at all are kept since we can't tell their age."""
    if MAX_JOB_AGE_DAYS <= 0:
        return jobs
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_JOB_AGE_DAYS)
    return [j for j in jobs if j.posted_at is None or _as_aware(j.posted_at) >= cutoff]


def _as_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _dedupe(jobs: list[Job]) -> list[Job]:
    seen: dict[str, Job] = {}
    for job in jobs:
        key = Job.dedupe_key(job.title, job.company)
        existing = seen.get(key)
        if existing is None:
            seen[key] = job
            continue
        # Prefer whichever posting has a real timestamp; break ties by keeping the first seen.
        if job.posted_at and (not existing.posted_at or job.posted_at > existing.posted_at):
            seen[key] = job
    return list(seen.values())
