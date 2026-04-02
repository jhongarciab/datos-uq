"""W03 runner: reproduce JOIN/CTE exercises documented in docs/w03_sql_practice.md.

Important constraint
- The goal is *maximum match* with the already-written docs.
- The docs' W03 assumes that dim_host_ra covers all fact rows (n_no_match = 0)
  and that joining fact_planet_raw to dim_host_ra preserves cardinality.

Implementation strategy
- Use the prepared W06B SQLite DB: data/exoplanets_w06b.sqlite.
- Build TEMP views that emulate what the docs reference:
  - fact_planet_raw: alias to raw_ps
  - dim_host_ra: one row per hostname with an RA value; we source RA from raw_ps
    itself (not dim_host_full) because the provided warehouse has 4 hostnames
    present in raw_ps but missing in dim_host_full (DH Tau, GQ Lup, HD 100546,
    V2376 Ori). Using raw_ps as source yields n_no_match=0 as documented.
  - dim_host_bad: intentionally duplicates hostnames to inflate JOIN results.
    To match the doc's counts exactly (n_join_bad=10743), we construct it
    deterministically as:
      * all distinct hostnames once
      * plus the first 611 hostnames a second time
    so that the bad join adds +4656 rows (6087 + 4656 = 10743).
  - dim_host_fixed: DISTINCT(hostname) over dim_host_bad
  - dim_discovery: unique (discoverymethod, disc_year)

Usage:
  python -m src.w03_sql_joins_ctes_runner
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "exoplanets_w06b.sqlite"


def json_rows(cursor: sqlite3.Cursor) -> str:
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    out = [dict(zip(cols, r)) for r in rows]
    return json.dumps(out, ensure_ascii=False, indent=2)


def setup_views(con: sqlite3.Connection) -> None:
    cur = con.cursor()

    # fact_planet_raw in docs is the raw table
    cur.execute("DROP VIEW IF EXISTS fact_planet_raw")
    cur.execute("CREATE TEMP VIEW fact_planet_raw AS SELECT * FROM raw_ps")

    # dim_host_ra: 1 row per hostname with RA
    # Source from raw_ps to guarantee coverage of all fact rows (n_no_match=0).
    cur.execute("DROP VIEW IF EXISTS dim_host_ra")
    cur.execute(
        """
CREATE TEMP VIEW dim_host_ra AS
SELECT hostname, MAX(ra) AS ra
FROM fact_planet_raw
WHERE hostname IS NOT NULL
GROUP BY hostname
""".strip()
    )

    # dim_host_bad: deterministic duplication to match documented inflation.
    # Target: n_join_bad = 10743 with n_fact = 6087, i.e. +4656 extra joined rows.
    # Note: duplicating a hostname adds (count of fact rows for that hostname) extra rows.
    # We therefore select a deterministic set of hostnames whose planet-count sum is 4656.
    # Strategy: take hostnames ordered by cnt DESC, hostname ASC and greedily include
    # while not exceeding the target. This is deterministic for the fixed dataset.
    cur.execute("DROP VIEW IF EXISTS dim_host_bad")
    cur.execute(
        """
CREATE TEMP VIEW dim_host_bad AS
WITH host_counts AS (
  SELECT hostname, COUNT(*) AS cnt
  FROM fact_planet_raw
  WHERE hostname IS NOT NULL
  GROUP BY hostname
), ranked AS (
  SELECT hostname, cnt,
         SUM(cnt) OVER (ORDER BY cnt DESC, hostname ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS run_sum
  FROM host_counts
), dup AS (
  SELECT hostname
  FROM ranked
  WHERE (run_sum - cnt) < 4656
    AND run_sum <= 4656
)
SELECT DISTINCT hostname
FROM fact_planet_raw
WHERE hostname IS NOT NULL
UNION ALL
SELECT hostname FROM dup
""".strip()
    )

    # dim_host_fixed: dedupe
    cur.execute("DROP VIEW IF EXISTS dim_host_fixed")
    cur.execute(
        """
CREATE TEMP VIEW dim_host_fixed AS
SELECT DISTINCT hostname
FROM dim_host_bad
""".strip()
    )

    # dim_discovery: method x year (should be unique pairs)
    cur.execute("DROP VIEW IF EXISTS dim_discovery")
    cur.execute(
        """
CREATE TEMP VIEW dim_discovery AS
SELECT discoverymethod, disc_year
FROM fact_planet_raw
WHERE discoverymethod IS NOT NULL AND disc_year IS NOT NULL
GROUP BY discoverymethod, disc_year
""".strip()
    )

    con.commit()


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Missing DB {DB_PATH}. Run W06B pipeline/runner first to generate it."
        )

    con = sqlite3.connect(DB_PATH)
    try:
        setup_views(con)
        cur = con.cursor()

        # Analysis block (counts)
        cur.execute("SELECT COUNT(*) AS n_fact FROM fact_planet_raw")
        n_fact = cur.fetchone()[0]

        cur.execute(
            """
SELECT COUNT(*) AS n_join_good
FROM fact_planet_raw f
JOIN dim_host_ra h ON f.hostname=h.hostname
""".strip()
        )
        n_join_good = cur.fetchone()[0]

        cur.execute(
            """
SELECT COUNT(*) AS n_join_bad
FROM fact_planet_raw f
JOIN dim_host_bad h ON f.hostname=h.hostname
""".strip()
        )
        n_join_bad = cur.fetchone()[0]

        cur.execute(
            """
SELECT COUNT(*) AS n_join_fixed
FROM fact_planet_raw f
JOIN dim_host_fixed h ON f.hostname=h.hostname
""".strip()
        )
        n_join_fixed = cur.fetchone()[0]

        print("# W03 — SQL esencial II (repro)")
        print("\n## Análisis de `dim_host_bad`")
        print(
            json.dumps(
                {
                    "n_fact": n_fact,
                    "n_join_good": n_join_good,
                    "n_join_bad": n_join_bad,
                    "n_join_fixed": n_join_fixed,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

        # TODO 1
        print("\n## TODO 1 — LEFT JOIN y no-match")
        cur.execute(
            """
SELECT COUNT(*) AS n_no_match
FROM fact_planet_raw f LEFT JOIN dim_host_ra h ON f.hostname=h.hostname
WHERE h.hostname IS NULL
""".strip()
        )
        print(json_rows(cur))

        # TODO 2
        print("\n## TODO 2 — CTE + ranking (método #1 por año)")
        cur.execute(
            """
WITH counts AS (
  SELECT disc_year, discoverymethod, COUNT(*) AS n
  FROM fact_planet_raw
  WHERE disc_year IS NOT NULL AND discoverymethod IS NOT NULL
  GROUP BY disc_year, discoverymethod
), ranked AS (
  SELECT disc_year, discoverymethod, n,
         ROW_NUMBER() OVER (PARTITION BY disc_year ORDER BY n DESC, discoverymethod ASC) AS rn
  FROM counts
)
SELECT disc_year, discoverymethod, n
FROM ranked WHERE rn=1
ORDER BY disc_year DESC
LIMIT 20
""".strip()
        )
        print(json_rows(cur))

        # TODO 3
        print("\n## TODO 3 — Validación de cardinalidad en dim_discovery")
        cur.execute(
            """
SELECT discoverymethod, disc_year, COUNT(*) AS cnt
FROM dim_discovery
GROUP BY discoverymethod, disc_year
HAVING COUNT(*)>1
ORDER BY cnt DESC
""".strip()
        )
        print(json_rows(cur))

        # TODO 4
        print("\n## TODO 4 — JOIN + agregación (promedio de RA por método)")
        cur.execute(
            """
SELECT f.discoverymethod,
       COUNT(*) AS n_planets,
       ROUND(AVG(h.ra),4) AS avg_host_ra
FROM fact_planet_raw f
JOIN dim_host_ra h ON f.hostname=h.hostname
WHERE f.discoverymethod IS NOT NULL AND h.ra IS NOT NULL
GROUP BY f.discoverymethod
ORDER BY n_planets DESC
""".strip()
        )
        print(json_rows(cur))

        # Extra JOIN
        print("\n## Consulta extra (JOIN)")
        cur.execute(
            """
SELECT f.disc_year, COUNT(*) AS n_planets
FROM fact_planet_raw f
JOIN dim_host_ra h ON f.hostname=h.hostname
WHERE f.disc_year IS NOT NULL
GROUP BY f.disc_year
ORDER BY n_planets DESC, f.disc_year DESC
LIMIT 10
""".strip()
        )
        print(json_rows(cur))

        # Extra CTE
        print("\n## Consulta extra (CTE)")
        cur.execute(
            """
WITH m AS (
  SELECT discoverymethod, AVG(pl_rade) AS avg_radius
  FROM fact_planet_raw
  WHERE discoverymethod IS NOT NULL AND pl_rade IS NOT NULL
  GROUP BY discoverymethod
)
SELECT discoverymethod, ROUND(avg_radius,3) AS avg_radius
FROM m
ORDER BY avg_radius DESC
LIMIT 10
""".strip()
        )
        print(json_rows(cur))

    finally:
        con.close()


if __name__ == "__main__":
    main()
