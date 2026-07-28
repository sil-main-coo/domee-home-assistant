"""Validate preparation metadata and optionally enforce release readiness."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "custom_components" / "domee" / "manifest.json"
HACS = ROOT / "hacs.json"


def main() -> None:
    """Validate fixed metadata and report human-owned release blockers."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hacs = json.loads(HACS.read_text(encoding="utf-8"))
    expected = {
        "domain": "domee",
        "name": "Domee",
        "version": "0.1.0",
        "integration_type": "hub",
        "iot_class": "cloud_polling",
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise SystemExit(f"manifest {key} must be {value!r}")
    if not re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"]):
        raise SystemExit("manifest version must be SemVer")
    expected_hacs = {
        "name": "Domee",
        "homeassistant": "2024.3.3",
        "zip_release": True,
        "filename": "domee.zip",
        "hide_default_branch": True,
    }
    if hacs != expected_hacs:
        raise SystemExit("hacs.json differs from the distribution contract")
    components = [path.name for path in (ROOT / "custom_components").iterdir()]
    if components != ["domee"]:
        raise SystemExit("Exactly one Domee integration is allowed")
    blockers = []
    if "OWNER" in manifest.get("documentation", ""):
        blockers.append("public repository URL")
    if "OWNER" in manifest.get("issue_tracker", ""):
        blockers.append("public issue tracker URL")
    if not manifest.get("codeowners"):
        blockers.append("GitHub code owner")
    if (ROOT / "LICENSE").read_text(encoding="utf-8").startswith(
        "LICENSE NOT YET SELECTED"
    ):
        blockers.append("approved license")
    if not (ROOT / "custom_components" / "domee" / "brand" / "icon.png").is_file():
        blockers.append("official Domee brand icon")
    if blockers:
        message = "Release blockers: " + ", ".join(blockers)
        if args.release:
            raise SystemExit(message)
        print(message)
    print("Preparation metadata is internally consistent")


if __name__ == "__main__":
    main()
