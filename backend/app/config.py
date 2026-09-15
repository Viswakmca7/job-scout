import os
from pathlib import Path

from dotenv import load_dotenv

# Load job-scout/.env (repo root of this project, two levels up from backend/app/) so
# `uvicorn app.main:app` picks up local config without exporting env vars by hand.
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

USER_AGENT = "JobScoutBot/1.0 (+https://github.com/; contact: job-scout aggregator; respects source rate limits)"
REQUEST_TIMEOUT = 15.0
CACHE_TTL_SECONDS = int(os.getenv("JOBSCOUT_CACHE_TTL", "900"))  # 15 minutes

# Optional source: Adzuna (free tier, requires a free account at https://developer.adzuna.com/)
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "us")
ADZUNA_QUERY = os.getenv("ADZUNA_QUERY", "software")  # seed query, results are still keyword-filtered client-side

# Affiliate / sponsored placement config: map company name (lowercase) -> affiliate URL override.
# Populate via env var as JSON, e.g. JOBSCOUT_AFFILIATES='{"acme corp": "https://acme.com/apply?ref=jobscout"}'
import json as _json

try:
    AFFILIATE_MAP: dict[str, str] = _json.loads(os.getenv("JOBSCOUT_AFFILIATES", "{}"))
except ValueError:
    AFFILIATE_MAP = {}

SUBSCRIBERS_FILE = os.getenv("JOBSCOUT_SUBSCRIBERS_FILE", "subscribers.jsonl")

# Optional source: Jooble (free API key at https://jooble.org/api/about)
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY")
JOOBLE_SEED_QUERY = os.getenv("JOOBLE_SEED_QUERY", "software OR developer OR engineer OR analyst OR designer")
JOOBLE_LOCATION = os.getenv("JOOBLE_LOCATION", "")

# Optional sources: Greenhouse / Lever public per-company job boards (no key needed).
# Comma-separated board/company tokens, e.g. "stripe,figma,airbnb".
GREENHOUSE_BOARDS = [b.strip() for b in os.getenv("JOBSCOUT_GREENHOUSE_BOARDS", "").split(",") if b.strip()]
LEVER_BOARDS = [b.strip() for b in os.getenv("JOBSCOUT_LEVER_BOARDS", "").split(",") if b.strip()]
