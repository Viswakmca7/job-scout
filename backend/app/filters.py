from __future__ import annotations

from datetime import datetime, timezone

from .models import Job

_EPOCH = datetime.fromtimestamp(0, tz=timezone.utc)


def _sort_key(job: Job) -> datetime:
    """Normalize to an aware UTC datetime — sources occasionally hand back naive
    datetimes, which can't be compared against aware ones during sort."""
    d = job.posted_at
    if d is None:
        return _EPOCH
    if d.tzinfo is None:
        return d.replace(tzinfo=timezone.utc)
    return d


def matches_keyword(job: Job, keyword: str) -> bool:
    """OR-match: any comma/space-separated term found in title, company, tags, or snippet."""
    if not keyword:
        return True
    terms = [t.strip().lower() for t in keyword.replace(",", " ").split() if t.strip()]
    if not terms:
        return True
    haystack = " ".join(
        filter(
            None,
            [job.title, job.company, " ".join(job.tags), job.description_snippet],
        )
    ).lower()
    return any(term in haystack for term in terms)


def filter_jobs(
    jobs: list[Job],
    keyword: str | None = None,
    job_type: str | None = None,
    remote_only: bool = False,
) -> list[Job]:
    result = jobs
    if keyword:
        result = [j for j in result if matches_keyword(j, keyword)]
    if job_type and job_type != "all":
        result = [j for j in result if j.job_type == job_type]
    if remote_only:
        result = [j for j in result if j.remote]
    return result


def sort_jobs(jobs: list[Job], sort_by: str = "latest") -> list[Job]:
    if sort_by == "type":
        return sorted(jobs, key=lambda j: (j.job_type, -_sort_key(j).timestamp()))
    # default: latest first
    return sorted(jobs, key=_sort_key, reverse=True)
