"""Extract and inspect a built Domee release artifact."""

from __future__ import annotations

import tempfile
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "domee.zip"
REQUIRED = {
    "__init__.py",
    "api.py",
    "binary_sensor.py",
    "button.py",
    "config_flow.py",
    "const.py",
    "coordinator.py",
    "entity.py",
    "identity.py",
    "manifest.json",
    "sensor.py",
    "snapshot.py",
    "strings.json",
    "switch.py",
    "translations/en.json",
    "brand/icon.png",
}
FORBIDDEN_PARTS = {
    ".github",
    ".storage",
    "__pycache__",
    "docs",
    "tests",
    "validation",
}


def main() -> None:
    """Extract the archive and verify its installable runtime layout."""
    with tempfile.TemporaryDirectory(prefix="domee-release-") as temp:
        destination = Path(temp)
        with ZipFile(ARCHIVE) as archive:
            archive.extractall(destination)
        files = {
            path.relative_to(destination).as_posix()
            for path in destination.rglob("*")
            if path.is_file()
        }
        missing = REQUIRED - files
        if missing:
            raise SystemExit(f"Missing required release files: {sorted(missing)}")
        for file in files:
            path = Path(file)
            if set(path.parts) & FORBIDDEN_PARTS:
                raise SystemExit(f"Forbidden extracted path: {file}")
            if path.suffix.lower() in {".db", ".log", ".pyc", ".pyo"}:
                raise SystemExit(f"Forbidden extracted file: {file}")
    print(f"Extracted artifact inspection passed ({len(files)} files)")


if __name__ == "__main__":
    main()