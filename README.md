# Job Scout

A job search engine that aggregates listings from multiple **public, no-auth job APIs**,
lets people filter by keyword, and sort by **latest** or **hiring type** (full-time,
part-time, contract, internship). Ships as a website (FastAPI + static frontend) and a
terminal CLI, both hitting the same backend.

## Why APIs instead of scraping LinkedIn/Indeed

LinkedIn, Indeed, and Glassdoor actively block scrapers and prohibit scraping in their
Terms of Service — doing it anyway risks IP bans and legal exposure, and breaks constantly
as they change their HTML. Instead, this project pulls from job boards that **publish
public APIs for exactly this purpose**:

| Source | Auth required | Coverage |
|---|---|---|
| [RemoteOK](https://remoteok.com/api) | No | Remote tech jobs |
| [Arbeitnow](https://arbeitnow.com/api/job-board-api) | No | Remote + on-site, global |
| [Remotive](https://remotive.com/api/remote-jobs) | No | Remote jobs, all categories |
| [Jobicy](https://jobicy.com/api/v2/remote-jobs) | No | Remote jobs, all categories |
| [Adzuna](https://developer.adzuna.com/) | Free account (optional) | Local + remote, many countries |
| [Jooble](https://jooble.org/api/about) | Free key (optional) | Aggregator with its own broad partnerships |
| [Greenhouse](https://developers.greenhouse.io/job-board.html) | No — per company | Track specific companies' official listings |
| [Lever](https://github.com/lever/postings-api) | No — per company | Track specific companies' official listings |

The "mining" part: results from all sources are normalized into one schema, **deduplicated**
by company+title, and enriched (hiring type is inferred from tags/description when a source
doesn't provide it explicitly).

### Why LinkedIn and Indeed specifically aren't sources here

Neither offers a real API option for this kind of tool, independent of what this project builds:

- **LinkedIn** has no public job-search API. The only job-data API is "Talent Solutions /
  Recruiter System Connect," restricted to approved ATS/HR-tech business partners through a
  formal application — not available to individual developers. There's also no OAuth scope
  that lets a personal account holder say "search jobs on my behalf." Their ToS explicitly
  prohibits scraping, including through third-party scraping services — routing scraping
  through a paid tool doesn't change that it violates the target's ToS.
- **Indeed** had a public Publisher API; it's closed to new applicants. Current Indeed APIs
  are for employers posting jobs, not for job-seeker search.

Jooble is the closest legal substitute for that kind of broad, multi-board coverage — it's
an aggregator with its own legitimate partnerships, and it publishes a free API specifically
for third-party developers. Greenhouse and Lever cover the common case of "I care about these
20 specific companies" — most tech companies' own career pages are powered by one of these two
platforms, and both publish the underlying JSON feed publicly and by design so it can be
embedded elsewhere.

## Project layout

```
job-scout/
  backend/         FastAPI app: aggregation, caching, filtering, REST API, serves the frontend
    app/
      sources/     One module per job API, each normalizes to the shared Job model
      aggregator.py  Fans out to all sources concurrently, dedupes results
      cache.py       Shared 15-minute TTL cache (so we call upstream APIs once for all visitors)
      filters.py     Keyword search + sort by latest/hiring type
      main.py        REST endpoints + static file serving
  frontend/        Static HTML/CSS/JS — no build step, no framework
  cli/             pip-installable `jobscout` terminal command
  render.yaml       One-click Render deploy blueprint
  Procfile          Alternative for Railway/Heroku-style platforms
```

## Run it locally

```bash
cd job-scout/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir .
```

Open http://localhost:8000 — the FastAPI app serves the frontend directly, no separate server needed.

## Run it in VS Code

1. Open the `job-scout/` folder in VS Code (not the whole repo root — that's where `.vscode/` lives).
2. Install the recommended extensions when prompted (Python + the `debugpy` debugger).
3. Run **Terminal → Run Task → "Job Scout: Install backend deps"** once.
4. Press **F5** (or Run → Start Debugging, config "Job Scout: Run backend") — this starts
   uvicorn with `--reload`, breakpoints work in `backend/app/`, and your browser opens to the
   site automatically once the server is ready.
5. Copy [`.env.example`](.env.example) to `job-scout/.env` to enable optional sources
   (Adzuna, Jooble, Greenhouse/Lever boards) or change the cache TTL — it's picked up
   automatically on the next run, no need to export env vars by hand.

Prefer no debugger? **Terminal → Run Task → "Job Scout: Run backend"** does the same thing
without attaching the debugger.

## Deploy it (Render)

1. Push this repo to GitHub.
2. In Render: **New → Blueprint**, point it at your repo. Render reads [`render.yaml`](render.yaml)
   and provisions the web service automatically (free tier works).
3. Wait for the build/deploy to finish — Render gives you a public URL like
   `https://job-scout-xxxx.onrender.com`.
4. Optional: in the Render dashboard, add environment variables from
   [`.env.example`](.env.example) (e.g. `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` for local-job coverage).

Railway/Heroku-style platforms: use the included [`Procfile`](Procfile) instead.

> I can't create hosting or PyPI accounts on your behalf — those steps need your own login,
> so the deploy and CLI-publish instructions above are written for you to run yourself.

## The CLI

```bash
cd job-scout/cli
pip install -e .
export JOBSCOUT_API_URL=https://your-app.onrender.com
jobscout "python remote" --type contract
```

See [`cli/README.md`](cli/README.md) for publishing it to PyPI so anyone can `pip install jobscout-cli`.

## Monetization (what's wired up vs. what's next)

**Wired up now (no payment processing, nothing for you to approve):**
- **Sponsored placements** — set `JOBSCOUT_AFFILIATES` (see `.env.example`) to a JSON map of
  company → your affiliate/apply URL. Matching jobs get a "Sponsored" badge and route through
  your link.
- **Ad slot** — `frontend/index.html` has a ready `#ad-slot` div. Once you're approved for
  [EthicalAds](https://www.ethicalads.io/) (dev-audience friendly) or Google AdSense, drop
  their script tag in; no code changes needed elsewhere.
- **Email capture** — the "Get instant alerts" form posts to `/api/subscribe` and appends to
  `subscribers.jsonl` on the server. This is your seed list for Phase 2.

**Phase 2 (needs your accounts/credentials, so it's not built yet):**
- Wire `subscribers.jsonl` to an actual email sender (e.g. Resend, SendGrid) to deliver
  keyword-match alerts.
- Add a paid tier via Stripe Checkout (instant alerts, resume-match scoring, ad-free) —
  the subscribe endpoint already captures the keyword you'd gate behind it.

## Extending

- Add a new source: create `backend/app/sources/<name>.py` with an async `fetch(client)` that
  returns `list[Job]`, then add it to `ALL_SOURCES` in `backend/app/sources/__init__.py`.
- Change cache freshness: `JOBSCOUT_CACHE_TTL` env var (seconds).
