from __future__ import annotations

import asyncio
import time

from .aggregator import fetch_all_jobs
from .config import CACHE_TTL_SECONDS
from .models import Job


class JobCache:
    """In-process TTL cache shared by every visitor, so we hit upstream APIs once
    per TTL window instead of once per request (good citizenship + speed)."""

    def __init__(self) -> None:
        self._jobs: list[Job] = []
        self._last_refresh: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def age_seconds(self) -> float:
        return time.monotonic() - self._last_refresh

    @property
    def is_stale(self) -> bool:
        return not self._jobs or self.age_seconds > CACHE_TTL_SECONDS

    async def get_jobs(self, force_refresh: bool = False) -> list[Job]:
        if force_refresh or self.is_stale:
            async with self._lock:
                # re-check after acquiring the lock in case another request already refreshed
                if force_refresh or self.is_stale:
                    self._jobs = await fetch_all_jobs()
                    self._last_refresh = time.monotonic()
        return self._jobs


cache = JobCache()
