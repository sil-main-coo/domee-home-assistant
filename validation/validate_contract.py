"""Parse a synthetic backend snapshot using the public integration parser."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from custom_components.domee.snapshot import parse_snapshot


def main() -> None:
    """Validate one snapshot fixture without backend source imports."""
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    raw = json.loads(args.snapshot.read_text(encoding="utf-8"))
    snapshot = parse_snapshot(raw)
    print(
        json.dumps(
            {
                "schemaVersion": snapshot.schema_version,
                "accountId": snapshot.account_id,
            }
        )
    )


if __name__ == "__main__":
    main()
