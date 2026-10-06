import re

_RULES = {
    "override": r"ignore (all |any )?(the )?(previous|prior|above|earlier) (instructions|prompts|rules)",
    "disregard": r"disregard .{0,40}(instructions|rules|guidelines)",
    "role_swap": r"\byou are now\b|\bact as\b.{0,30}\b(admin|root|system)\b",
    "prompt_leak": r"(print|reveal|show|repeat).{0,30}(system prompt|instructions|api key|secret)",
    "fake_tags": r"<\s*/?\s*(system|assistant|tool)\s*>",
    "exec": r"\b(run|execute)\b.{0,20}\b(command|shell|script)\b",
}
_COMPILED = {k: re.compile(v, re.I | re.S) for k, v in _RULES.items()}
WITHHELD = "[content withheld: possible prompt injection]"


def scan(text: str) -> list[str]:
    return [name for name, rx in _COMPILED.items() if rx.search(text)]


def safe_for_llm(text: str, limit: int = 600) -> str:
    return WITHHELD if scan(text) else text[:limit]


def looks_like_injection(text: str) -> bool:
    """Return True when the supplied text matches a prompt-injection rule."""
    return bool(scan(text))


def looks_like_injection(text: str) -> bool:
    """Return True when the supplied text matches a prompt-injection rule."""
    return bool(scan(text))
