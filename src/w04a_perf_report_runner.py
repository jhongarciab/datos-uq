"""W04A performance runner (SQLite version).

The original docs/w04a_perf_report.md show DuckDB EXPLAIN/EXPLAIN ANALYZE output.
In datos-uq we standardize runners on SQLite (stdlib only), so we reproduce:
- the *results* of the two queries (Q1 and Q2)
- a lightweight timing using time.perf_counter()

We do NOT try to reproduce DuckDB physical plans.

Usage:
  python -m src.w04a_perf_report_runner
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "exoplanets_w06b.sqlite"


def json_rows(cur: sqlite3.Cursor):
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return json.dumps([dict(zip(cols, r)) for r in rows], ensure_ascii=False, indent=2)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing DB {DB_PATH}")

    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()

        print("# W04A — Performance report (repro, sqlite)")

        # Q1
        q1 = """
SELECT discoverymethod, COUNT(*) AS n_planets
FROM raw_ps
WHERE disc_year >= 2015
GROUP BY discoverymethod
ORDER BY n_planets DESC;
""".strip()
        t0 = time.perf_counter()
        cur.execute(q1)
        q1_rows = cur.fetchall()
        t1 = time.perf_counter()
        print("\n## Consulta 1 (agregación con filtro)")
        print(json.dumps([{"discoverymethod": r[0], "n_planets": r[1]} for r in q1_rows], ensure_ascii=False, indent=2))
        print(f"\nTiming(Q1): {t1 - t0:.4f}s")

        # Q2
        # Adapt the CTE query to SQLite using raw_ps as both fact and dim.
        q2 = """
WITH dim_host AS (
  SELECT hostname, MAX(ra) AS ra
  FROM raw_ps
  WHERE hostname IS NOT NULL
  GROUP BY hostname
), fact_planet AS (
  SELECT pl_name, hostname, discoverymethod, disc_year, pl_rade
  FROM raw_ps
  WHERE pl_name IS NOT NULL
)
SELECT f.discoverymethod,
       COUNT(*) AS n_planets,
       AVG(h.ra) AS avg_ra
FROM fact_planet f
JOIN dim_host h
  ON f.hostname = h.hostname
WHERE f.disc_year >= 2015
GROUP BY f.discoverymethod
ORDER BY n_planets DESC;
""".strip()
        t0 = time.perf_counter()
        cur.execute(q2)
        q2_rows = cur.fetchall()
        t1 = time.perf_counter()
        print("\n## Consulta 2 (JOIN + agregación)")
        print(
            json.dumps(
                [
                    {"discoverymethod": r[0], "n_planets": r[1], "avg_ra": r[2]}
                    for r in q2_rows
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        print(f"\nTiming(Q2): {t1 - t0:.4f}s")

        print("\n## Nota")
        print(
            "El documento original usa DuckDB EXPLAIN/EXPLAIN ANALYZE; este runner reproduce resultados y timing en SQLite (stdlib)."
        )

    finally:
        con.close()


if __name__ == "__main__":
    main()
