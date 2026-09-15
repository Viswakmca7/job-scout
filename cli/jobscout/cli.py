from __future__ import annotations

import argparse
import os
import sys
import textwrap

import requests

for _stream in (sys.stdout, sys.stderr):
    # Windows terminals often default to a legacy codepage that can't render
    # em dashes, umlauts, etc. from job listings — force UTF-8 when possible.
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass

DEFAULT_API = os.environ.get("JOBSCOUT_API_URL", "http://localhost:8000")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jobscout",
        description="Search Job Scout listings from your terminal.",
    )
    parser.add_argument("keyword", nargs="?", default="", help="keyword(s) to search for, e.g. 'python remote'")
    parser.add_argument("--type", dest="job_type", default="all", help="full-time | part-time | contract | internship | all")
    parser.add_argument("--remote-only", action="store_true", help="only show remote jobs")
    parser.add_argument("--sort", choices=["latest", "type"], default="latest")
    parser.add_argument("--limit", type=int, default=15, help="max results to print")
    parser.add_argument("--api", default=DEFAULT_API, help=f"Job Scout API base URL (default: {DEFAULT_API})")
    return parser


def fetch_jobs(api_base: str, keyword: str, job_type: str, remote_only: bool, sort: str, limit: int) -> list[dict]:
    resp = requests.get(
        f"{api_base.rstrip('/')}/api/jobs",
        params={
            "keyword": keyword,
            "job_type": job_type,
            "remote_only": remote_only,
            "sort": sort,
            "page": 1,
            "page_size": limit,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["jobs"]


def print_jobs(jobs: list[dict]) -> None:
    if not jobs:
        print("No jobs matched. Try a broader keyword.")
        return
    for job in jobs:
        header = f"{job['title']} — {job['company']} [{job['job_type']}]"
        loc = job.get("location") or ("Remote" if job.get("remote") else "n/a")
        print(header)
        print(f"  location: {loc}    posted: {job.get('posted_at') or 'unknown'}    source: {job['source']}")
        print(f"  {job['url']}")
        if job.get("description_snippet"):
            print(textwrap.indent(textwrap.fill(job["description_snippet"], width=90), "  "))
        print()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        jobs = fetch_jobs(args.api, args.keyword, args.job_type, args.remote_only, args.sort, args.limit)
    except requests.RequestException as exc:
        print(f"Error contacting Job Scout API at {args.api}: {exc}", file=sys.stderr)
        return 1
    print_jobs(jobs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
