"""W05A runner: reproduce PK/FK evidence checks documented in docs/w05a_evidence.md.

Uses the W06B SQLite warehouse:
  data/exoplanets_w06b.sqlite

Reproduces:
1) Uniqueness in dim_host_sk (n_rows vs n_keys)
2) Orphan rows in fact_planet_sk (FK integrity)

Usage:
  python -m src.w05a_pk_fk_checks_runner
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "exoplanets_w06b.sqlite"


def json_rows(cur: sqlite3.Cursor) -> str:
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return json.dumps([dict(zip(cols, r)) for r in rows], ensure_ascii=False, indent=2)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing DB {DB_PATH}")

    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        print("# W05A — Evidencia PK/FK y checks (repro)")

        print("\n## 1) Conteo de unicidad en `dim_host_sk`")
        cur.execute(
            """
SELECT
  COUNT(*) AS n_rows,
  COUNT(DISTINCT hostname) AS n_keys
FROM dim_host_sk;
""".strip()
        )
        print(json_rows(cur))

        print("\n## 2) Orphan rows en `fact_planet_sk`")
        cur.execute(
            """
SELECT COUNT(*) AS orphan_rows
FROM fact_planet_sk f
LEFT JOIN dim_host_sk d ON f.host_id = d.host_id
WHERE d.host_id IS NULL;
""".strip()
        )
        print(json_rows(cur))

    finally:
        con.close()


if __name__ == "__main__":
    main()
