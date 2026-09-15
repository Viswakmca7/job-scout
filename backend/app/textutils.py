import html
import re

_TYPE_PATTERNS = [
    ("internship", re.compile(r"\bintern(ship)?\b", re.I)),
    ("contract", re.compile(r"\bcontract(or)?\b|\bfreelance\b|\btemp(orary)?\b", re.I)),
    ("part-time", re.compile(r"\bpart[\s-]?time\b", re.I)),
    ("full-time", re.compile(r"\bfull[\s-]?time\b", re.I)),
]


def infer_job_type(*texts: str | None) -> str:
    blob = " ".join(t for t in texts if t)
    for label, pattern in _TYPE_PATTERNS:
        if pattern.search(blob):
            return label
    return "unknown"


def clean_snippet(text: str | None, max_len: int = 220) -> str | None:
    if not text:
        return None
    unescaped = html.unescape(text)
    stripped = re.sub(r"<[^>]+>", " ", unescaped)
    stripped = html.unescape(stripped)  # entities can appear outside tags too
    stripped = re.sub(r"\s+", " ", stripped).strip()
    if not stripped:
        return None
    return stripped[:max_len].rstrip() + ("…" if len(stripped) > max_len else "")
