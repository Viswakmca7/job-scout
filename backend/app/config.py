import os
from pathlib import Path

from dotenv import load_dotenv

# Load vjobs/.env (repo root of this project, two levels up from backend/app/) so
# `uvicorn app.main:app` picks up local config without exporting env vars by hand.
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


def _env(new_name: str, old_name: str, default: str = "") -> str:
    """Prefer the current VJOBS_* var; fall back to the pre-rename JOBSCOUT_* name
    so an existing deployment that only has the old var set doesn't silently break."""
    return os.getenv(new_name) or os.getenv(old_name) or default


USER_AGENT = "VjobsBot/1.0 (+https://github.com/; contact: vjobs aggregator; respects source rate limits)"
REQUEST_TIMEOUT = 15.0
CACHE_TTL_SECONDS = int(_env("VJOBS_CACHE_TTL", "JOBSCOUT_CACHE_TTL", "900"))  # 15 minutes

# Some sources (RemoteOK, Remotive) keep listings open for weeks, which makes results
# feel out of date. Drop anything older than this many days; jobs with no date at all
# are always kept since we can't tell their age. Set to 0 to disable.
MAX_JOB_AGE_DAYS = int(os.getenv("VJOBS_MAX_JOB_AGE_DAYS", "21"))

# Optional source: Adzuna (free tier, requires a free account at https://developer.adzuna.com/)
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "us")
ADZUNA_QUERY = os.getenv("ADZUNA_QUERY", "software")  # seed query, results are still keyword-filtered client-side

# Affiliate / sponsored placement config: map company name (lowercase) -> affiliate URL override.
# Populate via env var as JSON, e.g. VJOBS_AFFILIATES='{"acme corp": "https://acme.com/apply?ref=vjobs"}'
import json as _json

try:
    AFFILIATE_MAP: dict[str, str] = _json.loads(_env("VJOBS_AFFILIATES", "JOBSCOUT_AFFILIATES", "{}"))
except ValueError:
    AFFILIATE_MAP = {}

SUBSCRIBERS_FILE = _env("VJOBS_SUBSCRIBERS_FILE", "JOBSCOUT_SUBSCRIBERS_FILE", "subscribers.jsonl")

# Optional source: Jooble (free API key at https://jooble.org/api/about)
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY")
JOOBLE_SEED_QUERY = os.getenv("JOOBLE_SEED_QUERY", "software OR developer OR engineer OR analyst OR designer")
JOOBLE_LOCATION = os.getenv("JOOBLE_LOCATION", "")

# Optional sources: Greenhouse / Lever public per-company job boards (no key needed).
# Comma-separated board/company tokens, e.g. "stripe,figma,airbnb".
GREENHOUSE_BOARDS = [
    b.strip() for b in _env("VJOBS_GREENHOUSE_BOARDS", "JOBSCOUT_GREENHOUSE_BOARDS").split(",") if b.strip()
]
LEVER_BOARDS = [b.strip() for b in _env("VJOBS_LEVER_BOARDS", "JOBSCOUT_LEVER_BOARDS").split(",") if b.strip()]
