"""Build a deterministic HACS zip from the runtime integration."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "custom_components" / "domee"
OUTPUT = ROOT / "domee.zip"
FORBIDDEN_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".storage",
    "tests",
    "docs",
    ".github",
    "validation",
}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".log", ".db"}


def runtime_files() -> list[Path]:
    """Return the allowlisted runtime files or fail on unsafe content."""
    files = []
    for path in sorted(SOURCE.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(SOURCE)
        if set(relative.parts) & FORBIDDEN_PARTS:
            raise SystemExit(f"Forbidden release path: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise SystemExit(f"Forbidden release file: {relative}")
        files.append(path)
    if SOURCE / "manifest.json" not in files:
        raise SystemExit("manifest.json is required")
    return files


def main() -> None:
    """Build a byte-reproducible archive with files at the HACS zip root."""
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for path in runtime_files():
            relative = path.relative_to(SOURCE).as_posix()
            info = ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    print(f"Built {OUTPUT.name}")


if __name__ == "__main__":
    main()
