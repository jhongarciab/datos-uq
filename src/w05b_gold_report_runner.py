"""W05B runner: reproduce the Gold report numbers documented in docs/w05b_gold_report.md.

This runner reads the already-exported artifact CSVs:
- artifacts/gold_by_discoverymethod.csv
- artifacts/gold_by_host.csv

and prints the Top 10 rows as JSON arrays (matching docs).

Rationale
- The Gold outputs are already materialized as artifacts in this repo.
- Recomputing gold from scratch would require re-implementing the full pipeline.
  For W05B, the documented deliverable is the interpretation + top-10 snapshots.

Usage:
  python -m src.w05b_gold_report_runner
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ART = REPO_ROOT / "artifacts"
BY_METHOD = ART / "gold_by_discoverymethod.csv"
BY_HOST = ART / "gold_by_host.csv"


def read_csv(path: Path, limit: int = 10):
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        out = []
        for i, row in enumerate(r):
            if i >= limit:
                break
            # cast numeric fields where possible
            casted = {}
            for k, v in row.items():
                if v is None or v == "":
                    casted[k] = None
                    continue
                # try int then float
                try:
                    casted[k] = int(v)
                    continue
                except Exception:
                    pass
                try:
                    casted[k] = float(v)
                    continue
                except Exception:
                    pass
                casted[k] = v
            out.append(casted)
        return out


def main() -> None:
    if not BY_METHOD.exists():
        raise FileNotFoundError(f"Missing artifact: {BY_METHOD}")
    if not BY_HOST.exists():
        raise FileNotFoundError(f"Missing artifact: {BY_HOST}")

    print("# W05B — Gold report (repro)")

    print("\n## Top 10 `gold_by_discoverymethod`")
    print(json.dumps(read_csv(BY_METHOD, 10), ensure_ascii=False, indent=2))

    print("\n## Top 10 `gold_by_host`")
    print(json.dumps(read_csv(BY_HOST, 10), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
