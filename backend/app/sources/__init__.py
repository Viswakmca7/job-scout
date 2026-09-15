from .remoteok import fetch as fetch_remoteok
from .arbeitnow import fetch as fetch_arbeitnow
from .remotive import fetch as fetch_remotive
from .jobicy import fetch as fetch_jobicy
from .adzuna import fetch as fetch_adzuna
from .jooble import fetch as fetch_jooble
from .greenhouse import fetch as fetch_greenhouse
from .lever import fetch as fetch_lever

ALL_SOURCES = [
    fetch_remoteok,
    fetch_arbeitnow,
    fetch_remotive,
    fetch_jobicy,
    fetch_adzuna,
    fetch_jooble,
    fetch_greenhouse,
    fetch_lever,
]
