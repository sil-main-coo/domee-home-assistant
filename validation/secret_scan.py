"""Fail on common secret material and exported runtime artifacts."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache"}
FORBIDDEN_SUFFIXES = {".db", ".sqlite", ".log", ".pem", ".key", ".env"}
FORBIDDEN_NAMES = {".storage", "secrets.yaml"}
TEXT_PATTERNS = {
    "private key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "capture SSID": re.compile(r"Lap12345", re.IGNORECASE),
    "capture IP": re.compile(r"\b192\.168\.1\.21\b"),
    "legacy private repository": re.compile(r"sil-main-coo/ivoice_server", re.I),
}


def main() -> None:
    """Scan actual export contents rather than relying on .gitignore."""
    findings = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if set(relative.parts) & SKIP_DIRS:
            continue
        if path.is_dir():
            if path.name in FORBIDDEN_NAMES:
                findings.append(f"runtime directory: {relative}")
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES or path.name in FORBIDDEN_NAMES:
            findings.append(f"forbidden file: {relative}")
            continue
        if path.name == Path(__file__).name:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in TEXT_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{label}: {relative}")
    if findings:
        raise SystemExit("\n".join(findings))
    print("No known secrets, captures, or runtime artifacts found")


if __name__ == "__main__":
    main()
