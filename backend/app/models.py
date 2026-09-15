from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

JOB_TYPES = ("full-time", "part-time", "contract", "internship", "unknown")


class Job(BaseModel):
    id: str
    title: str
    company: str
    location: Optional[str] = None
    remote: bool = False
    job_type: str = "unknown"
    url: str
    source: str
    posted_at: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    salary: Optional[str] = None
    description_snippet: Optional[str] = None
    sponsored: bool = False

    @staticmethod
    def make_id(source: str, url: str) -> str:
        return hashlib.sha1(f"{source}:{url}".encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def dedupe_key(title: str, company: str) -> str:
        norm = lambda s: "".join(ch.lower() for ch in s if ch.isalnum())
        return f"{norm(company)}::{norm(title)}"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
