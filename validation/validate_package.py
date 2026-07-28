"""Validate that domee.zip contains only exact runtime integration files."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "custom_components" / "domee"
ARCHIVE = ROOT / "domee.zip"
FORBIDDEN = {
    "tests",
    "docs",
    ".github",
    "validation",
    ".storage",
    "__pycache__",
}


def main() -> None:
    """Compare every archive member to its source file."""
    expected = {
        path.relative_to(SOURCE).as_posix(): path.read_bytes()
        for path in SOURCE.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    with ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        if names != sorted(names) or set(names) != set(expected):
            raise SystemExit("Archive content is not the sorted runtime file set")
        if "manifest.json" not in names:
            raise SystemExit("Archive must place manifest.json at its root")
        for name in names:
            parts = set(Path(name).parts)
            if parts & FORBIDDEN or name.endswith((".pyc", ".log", ".db")):
                raise SystemExit(f"Forbidden archive member: {name}")
            if archive.read(name) != expected[name]:
                raise SystemExit(f"Archive content differs from source: {name}")
    print(f"Validated {len(expected)} runtime files")


if __name__ == "__main__":
    main()
