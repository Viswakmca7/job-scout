from __future__ import annotations

import asyncio
import logging

import httpx

from .models import Job
from .sources import ALL_SOURCES

logger = logging.getLogger("jobscout.aggregator")


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

    return _dedupe(jobs)


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
