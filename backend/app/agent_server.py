from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from .cache import cache
from .filters import filter_jobs, sort_jobs

mcp_server = MCPServer(
    name="vjobs",
    title="Vjobs",
    description=(
        "Search live job postings aggregated from RemoteOK, Arbeitnow, Remotive, Jobicy "
        "(plus Adzuna/Jooble/Greenhouse/Lever when configured). Listings older than the "
        "configured freshness window are already excluded, so everything returned is current."
    ),
    website_url="https://job-scout-726z.onrender.com",
)


@mcp_server.tool()
async def search_jobs(
    keyword: str = "",
    job_type: str = "all",
    remote_only: bool = False,
    sort: str = "latest",
    limit: int = 10,
) -> list[dict]:
    """Search current job listings by keyword.

    Args:
        keyword: Space/comma separated terms, OR-matched against title, company, tags,
            and description (e.g. "python django" or "react, vue"). Empty returns all jobs.
        job_type: One of "full-time", "part-time", "contract", "internship", "unknown", or "all".
        remote_only: If true, only return remote-eligible positions.
        sort: "latest" (most recently posted first) or "type" (grouped by hiring type).
        limit: Max results to return (1-25).
    """
    limit = max(1, min(limit, 25))
    jobs = await cache.get_jobs()
    jobs = filter_jobs(jobs, keyword=keyword, job_type=job_type, remote_only=remote_only)
    jobs = sort_jobs(jobs, sort_by=sort)
    return [j.model_dump(mode="json") for j in jobs[:limit]]


@mcp_server.tool()
async def hiring_type_counts() -> dict[str, int]:
    """Count currently cached jobs by hiring type (full-time/part-time/contract/internship/unknown)."""
    jobs = await cache.get_jobs()
    counts: dict[str, int] = {}
    for j in jobs:
        counts[j.job_type] = counts.get(j.job_type, 0) + 1
    return counts


def build_mcp_app():
    # Disable DNS-rebinding protection: it's meant to protect a *local* dev server from
    # malicious browser requests, and defaults to allowing only localhost/127.0.0.1 hosts —
    # which would reject every real request once this is deployed behind a public domain.
    return mcp_server.streamable_http_app(
        streamable_http_path="/",
        stateless_http=True,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
