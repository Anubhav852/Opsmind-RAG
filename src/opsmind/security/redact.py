import re

PATTERNS = [
    ("AWS_KEY", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GH_TOKEN", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("BEARER", re.compile(r"(?i)bearer\s+[a-z0-9\-_.=]{20,}")),
    ("PASSWORD", re.compile(r"(?i)(password|passwd|secret)\s*[=:]\s*\S+")),
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
]


def redact(text: str) -> tuple[str, list[str]]:
    found = []
    for name, rx in PATTERNS:
        if rx.search(text):
            found.append(name)
            text = rx.sub(f"[REDACTED:{name}]", text)
    return text, found
