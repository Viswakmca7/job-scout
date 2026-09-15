from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr

from . import auth
from .cache import cache
from .config import AFFILIATE_MAP, APP_BASE_URL, SESSION_COOKIE_NAME, SESSION_TTL_DAYS, SUBSCRIBERS_FILE
from .db import init_db
from .email_service import send_magic_link_email
from .filters import filter_jobs, sort_jobs
from .models import Job

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Vjobs API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _apply_affiliates(jobs: list[Job]) -> list[Job]:
    if not AFFILIATE_MAP:
        return jobs
    out = []
    for job in jobs:
        override = AFFILIATE_MAP.get(job.company.lower())
        if override:
            job = job.model_copy(update={"url": override, "sponsored": True})
        out.append(job)
    return out


@app.get("/api/health")
async def health():
    return {"status": "ok", "cached_jobs": len(cache._jobs), "cache_age_seconds": round(cache.age_seconds, 1)}


@app.get("/api/jobs")
async def list_jobs(
    keyword: str | None = Query(None, description="Space/comma separated keywords, OR-matched"),
    job_type: str | None = Query(None, description="full-time | part-time | contract | internship | unknown | all"),
    remote_only: bool = Query(False),
    sort: str = Query("latest", pattern="^(latest|type)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    jobs = await cache.get_jobs()
    jobs = filter_jobs(jobs, keyword=keyword, job_type=job_type, remote_only=remote_only)
    jobs = sort_jobs(jobs, sort_by=sort)
    jobs = _apply_affiliates(jobs)

    total = len(jobs)
    start = (page - 1) * page_size
    page_jobs = jobs[start : start + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "cache_age_seconds": round(cache.age_seconds, 1),
        "jobs": [j.model_dump(mode="json") for j in page_jobs],
    }


@app.post("/api/refresh")
async def refresh_jobs():
    jobs = await cache.get_jobs(force_refresh=True)
    return {"status": "refreshed", "total_jobs": len(jobs)}


@app.get("/api/job-types")
async def job_types():
    jobs = await cache.get_jobs()
    counts: dict[str, int] = {}
    for j in jobs:
        counts[j.job_type] = counts.get(j.job_type, 0) + 1
    return counts


class SubscribeRequest(BaseModel):
    email: EmailStr
    keyword: str = ""


_EMAIL_SAFE = re.compile(r"^[^\s]+@[^\s]+\.[^\s]+$")


@app.post("/api/subscribe")
async def subscribe(req: SubscribeRequest):
    """Seed list for the future paid alerts tier (Phase 2). No payment is processed here."""
    if not _EMAIL_SAFE.match(req.email):
        raise HTTPException(status_code=400, detail="invalid email")

    record = {
        "email": req.email,
        "keyword": req.keyword.strip()[:200],
        "subscribed_at": datetime.now(timezone.utc).isoformat(),
    }
    path = Path(SUBSCRIBERS_FILE)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return {"status": "subscribed"}


class RequestLinkRequest(BaseModel):
    email: EmailStr


def _accounts_unavailable() -> HTTPException:
    return HTTPException(status_code=503, detail="Accounts aren't configured on this deployment")


@app.post("/api/auth/request-link")
async def request_link(req: RequestLinkRequest):
    try:
        token = await auth.create_magic_link(req.email)
    except RuntimeError:
        raise _accounts_unavailable()

    link_url = f"{APP_BASE_URL}/api/auth/verify?token={token}"
    await send_magic_link_email(req.email, link_url)
    return {"status": "sent"}


@app.get("/api/auth/verify")
async def verify_link(token: str):
    try:
        session_token = await auth.verify_magic_link(token)
    except RuntimeError:
        raise _accounts_unavailable()

    if session_token is None:
        return RedirectResponse(url="/?auth=invalid")

    response = RedirectResponse(url="/?auth=success")
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_token,
        max_age=SESSION_TTL_DAYS * 86400,
        httponly=True,
        samesite="lax",
        secure=APP_BASE_URL.startswith("https://"),
    )
    return response


@app.get("/api/auth/me")
async def me(vjobs_session: str | None = Cookie(default=None)):
    try:
        email = await auth.get_user_email_from_session(vjobs_session)
    except RuntimeError:
        raise _accounts_unavailable()
    if not email:
        raise HTTPException(status_code=401, detail="not signed in")
    return {"email": email}


@app.post("/api/auth/logout")
async def logout(response: Response, vjobs_session: str | None = Cookie(default=None)):
    try:
        await auth.delete_session(vjobs_session)
    except RuntimeError:
        pass
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup():
    import asyncio

    asyncio.create_task(cache.get_jobs())  # slow (calls external APIs) — don't block startup on it
    await init_db()  # fast (schema DDL) — must finish before auth endpoints can be trusted


frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
