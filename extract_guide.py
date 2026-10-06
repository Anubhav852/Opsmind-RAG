"""Writes every '### `path`' + code block in the guide to disk. Skips files that already exist."""
import re, sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text().splitlines()
i = 0
while i < len(lines):
    m = re.match(r"^###\s+`([^`]+)`", lines[i])
    if m and ("/" in m.group(1) or "." in m.group(1)):
        path = Path(m.group(1))
        j = i + 1
        while j < len(lines) and not lines[j].startswith("```") and not lines[j].startswith("#"):
            j += 1
        if j < len(lines) and lines[j].startswith("```"):
            k, buf = j + 1, []
            while k < len(lines) and not lines[k].startswith("```"):
                buf.append(lines[k]); k += 1
            if path.exists():
                print("skip (exists):", path)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("\n".join(buf) + "\n")
                print("wrote:", path)
            i = k
    i += 1
