"""W04B runner: reproduce the silver report documented in docs/w03b_silver_report.md.

Reproduces:
- PRAGMA table_info(silver_planet) (DESCRIBE)
- Counts for silver_planet
- dim_host_full: n_rows vs n_keys
- Healthy join check: n_fact vs n_join
- (Doc mentions gold export already present in artifacts/)

Usage:
  python -m src.w04b_silver_report_runner

Notes:
- Uses the existing DB: data/exoplanets_w06b.sqlite
- Stdlib only.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "exoplanets_w06b.sqlite"


def json_rows_from_cursor(cur: sqlite3.Cursor) -> str:
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    out = [dict(zip(cols, r)) for r in rows]
    return json.dumps(out, ensure_ascii=False, indent=2)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing DB {DB_PATH}")

    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()

        print("# W04B — Silver report (repro)")

        print("\n## DESCRIBE silver_planet")
        cur.execute("PRAGMA table_info(silver_planet)")
        print(json_rows_from_cursor(cur))

        print("\n## Conteos silver")
        cur.execute(
            """
SELECT
  COUNT(*) AS n_rows,
  COUNT(DISTINCT pl_name) AS n_distinct_pl_name,
  COUNT(DISTINCT hostname) AS n_distinct_hostname
FROM silver_planet
""".strip()
        )
        print(json_rows_from_cursor(cur))

        print("\n## dim_host_full: n_rows vs n_keys")
        cur.execute(
            """
SELECT
  COUNT(*) AS n_rows,
  COUNT(DISTINCT hostname) AS n_keys
FROM dim_host_full
""".strip()
        )
        print(json_rows_from_cursor(cur))

        print("\n## JOIN sano (n_fact vs n_join)")
        cur.execute(
            """
SELECT
  (SELECT COUNT(*) FROM fact_planet) AS n_fact,
  (SELECT COUNT(*) FROM fact_planet f JOIN dim_host_full h ON f.hostname=h.hostname) AS n_join
""".strip()
        )
        print(json_rows_from_cursor(cur))

        print("\n## Vista Gold exportada")
        print("- Archivo: artifacts/gold_by_method_20260223.csv")

    finally:
        con.close()


if __name__ == "__main__":
    main()
