"""W11 runner: query tuning, EXPLAIN ANALYZE evidence, and gold marts in DuckDB.

Implements the W11 assignment by:
- building a cleaned `silver_planet_v3`
- defining 2 critical analytical queries (before/after)
- measuring baseline and rewritten timings
- saving EXPLAIN ANALYZE outputs
- building gold marts used by the optimized queries
- validating before/after result equivalence

Usage:
  python -m src.w11_perf_runner
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import duckdb


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = REPO_ROOT / "data" / "raw" / "pscomppars.csv"
DB_PATH = REPO_ROOT / "data" / "exoplanets_w11.duckdb"
ART = REPO_ROOT / "artifacts"

EVIDENCE_JSON = ART / "w11_evidence.json"
Q1_BEFORE_TXT = ART / "w11_q1_explain_before.txt"
Q1_AFTER_TXT = ART / "w11_q1_explain_after.txt"
Q2_BEFORE_TXT = ART / "w11_q2_explain_before.txt"
Q2_AFTER_TXT = ART / "w11_q2_explain_after.txt"
Q1_RESULTS_CSV = ART / "w11_q1_results_after.csv"
Q2_RESULTS_CSV = ART / "w11_q2_results_after.csv"
MART_METHOD_ERA_CSV = ART / "w11_gold_mart_method_era.csv"
MART_HOST_ERA_CSV = ART / "w11_gold_mart_host_era.csv"


SYNONYMS = [
    ("transit", "transit"),
    ("radial velocity", "radial_velocity"),
    ("microlensing", "microlensing"),
    ("imaging", "imaging"),
    ("transit timing variations", "transit_timing_variations"),
    ("eclipse timing variations", "eclipse_timing_variations"),
    ("orbital brightness modulation", "orbital_brightness_modulation"),
    ("pulsar timing", "pulsar_timing"),
    ("astrometry", "astrometry"),
    ("pulsation timing variations", "pulsation_timing_variations"),
    ("disk kinematics", "disk_kinematics"),
]


def sql_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def sql_path(p: Path) -> str:
    return sql_quote(p.resolve().as_posix())


def connect() -> duckdb.DuckDBPyConnection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute("PRAGMA threads=4")
    return con


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def rows_from_query(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def digest_rows(rows: list[dict]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_base(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("DROP VIEW IF EXISTS raw_ps")
    con.execute(f"CREATE VIEW raw_ps AS SELECT * FROM read_csv_auto({sql_path(RAW_CSV)})")

    con.execute("DROP TABLE IF EXISTS method_synonyms")
    con.execute("CREATE TABLE method_synonyms(raw_norm VARCHAR, canonical VARCHAR)")
    con.executemany("INSERT INTO method_synonyms VALUES (?, ?)", SYNONYMS)

    con.execute("DROP TABLE IF EXISTS silver_planet_v3")
    con.execute(
        """
CREATE TABLE silver_planet_v3 AS
WITH base AS (
  SELECT
    r.*,
    CASE WHEN hostname IS NULL OR TRIM(hostname) = '' THEN NULL ELSE LOWER(TRIM(hostname)) END AS hostname_canon,
    CASE WHEN discoverymethod IS NULL OR TRIM(discoverymethod) = '' THEN NULL ELSE LOWER(TRIM(discoverymethod)) END AS discoverymethod_norm,
    TRY_CAST(disc_year AS INTEGER) AS disc_year_int
  FROM raw_ps r
)
SELECT
  b.*,
  COALESCE(ms.canonical, b.discoverymethod_norm) AS discoverymethod_canon,
  CASE
    WHEN b.disc_year_int IS NULL THEN TRUE
    WHEN b.disc_year_int < 1980 OR b.disc_year_int > 2026 THEN TRUE
    ELSE FALSE
  END AS disc_year_bad,
  CASE
    WHEN b.disc_year_int BETWEEN 1990 AND 1999 THEN '1990s'
    WHEN b.disc_year_int BETWEEN 2000 AND 2009 THEN '2000s'
    WHEN b.disc_year_int BETWEEN 2010 AND 2019 THEN '2010s'
    WHEN b.disc_year_int BETWEEN 2020 AND 2029 THEN '2020s'
    ELSE 'other'
  END AS disc_era
FROM base b
LEFT JOIN method_synonyms ms
  ON b.discoverymethod_norm = ms.raw_norm
WHERE b.hostname_canon IS NOT NULL
  AND COALESCE(ms.canonical, b.discoverymethod_norm) IS NOT NULL
"""
    )


def build_gold_marts(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("DROP TABLE IF EXISTS gold_mart_method_era")
    con.execute(
        """
CREATE TABLE gold_mart_method_era AS
SELECT
  disc_era,
  discoverymethod_canon,
  COUNT(*) AS n_planets,
  ROUND(AVG(pl_rade), 3) AS avg_pl_rade,
  ROUND(AVG(pl_bmasse), 3) AS avg_pl_bmasse
FROM silver_planet_v3
WHERE disc_year_bad = FALSE
  AND disc_era IN ('2010s', '2020s')
GROUP BY disc_era, discoverymethod_canon
"""
    )

    con.execute("DROP TABLE IF EXISTS gold_mart_host_era")
    con.execute(
        """
CREATE TABLE gold_mart_host_era AS
SELECT
  disc_era,
  hostname_canon,
  COUNT(*) AS n_planets,
  ROUND(AVG(pl_rade), 3) AS avg_pl_rade,
  ROUND(AVG(pl_bmasse), 3) AS avg_pl_bmasse
FROM silver_planet_v3
WHERE disc_year_bad = FALSE
  AND disc_era IN ('2010s', '2020s')
GROUP BY disc_era, hostname_canon
"""
    )


def explain_text(con: duckdb.DuckDBPyConnection, sql: str) -> str:
    rows = con.execute(f"EXPLAIN ANALYZE {sql}").fetchall()
    return "\n\n".join(str(r[1]) if len(r) > 1 else str(r[0]) for r in rows)


def extract_total_time(explain: str) -> float | None:
    import re
    m = re.search(r"Total Time: ([0-9.]+)s", explain)
    return float(m.group(1)) if m else None


def main() -> None:
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"Missing raw CSV: {RAW_CSV}")
    ART.mkdir(parents=True, exist_ok=True)
    con = connect()
    try:
        build_base(con)
        build_gold_marts(con)

        q1_before = """
SELECT
  disc_era,
  discoverymethod_canon,
  COUNT(*) AS n_planets,
  ROUND(AVG(pl_rade), 3) AS avg_pl_rade,
  ROUND(AVG(pl_bmasse), 3) AS avg_pl_bmasse
FROM silver_planet_v3
WHERE disc_year_bad = FALSE
  AND disc_era IN ('2010s', '2020s')
GROUP BY disc_era, discoverymethod_canon
ORDER BY disc_era, n_planets DESC, discoverymethod_canon ASC
LIMIT 20
""".strip()

        q1_after = """
SELECT
  disc_era,
  discoverymethod_canon,
  n_planets,
  avg_pl_rade,
  avg_pl_bmasse
FROM gold_mart_method_era
ORDER BY disc_era, n_planets DESC, discoverymethod_canon ASC
LIMIT 20
""".strip()

        q2_before = """
SELECT
  disc_era,
  hostname_canon,
  COUNT(*) AS n_planets,
  ROUND(AVG(pl_rade), 3) AS avg_pl_rade,
  ROUND(AVG(pl_bmasse), 3) AS avg_pl_bmasse
FROM silver_planet_v3
WHERE disc_year_bad = FALSE
  AND disc_era IN ('2010s', '2020s')
GROUP BY disc_era, hostname_canon
HAVING COUNT(*) >= 3
ORDER BY disc_era, n_planets DESC, hostname_canon ASC
LIMIT 20
""".strip()

        q2_after = """
SELECT
  disc_era,
  hostname_canon,
  n_planets,
  avg_pl_rade,
  avg_pl_bmasse
FROM gold_mart_host_era
WHERE n_planets >= 3
ORDER BY disc_era, n_planets DESC, hostname_canon ASC
LIMIT 20
""".strip()

        q1_before_rows = rows_from_query(con, q1_before)
        q1_after_rows = rows_from_query(con, q1_after)
        q2_before_rows = rows_from_query(con, q2_before)
        q2_after_rows = rows_from_query(con, q2_after)

        write_csv(Q1_RESULTS_CSV, q1_after_rows)
        write_csv(Q2_RESULTS_CSV, q2_after_rows)
        write_csv(MART_METHOD_ERA_CSV, rows_from_query(con, "SELECT * FROM gold_mart_method_era ORDER BY disc_era, n_planets DESC, discoverymethod_canon ASC"))
        write_csv(MART_HOST_ERA_CSV, rows_from_query(con, "SELECT * FROM gold_mart_host_era ORDER BY disc_era, n_planets DESC, hostname_canon ASC"))

        q1_before_exp = explain_text(con, q1_before)
        q1_after_exp = explain_text(con, q1_after)
        q2_before_exp = explain_text(con, q2_before)
        q2_after_exp = explain_text(con, q2_after)
        Q1_BEFORE_TXT.write_text(q1_before_exp + "\n", encoding="utf-8")
        Q1_AFTER_TXT.write_text(q1_after_exp + "\n", encoding="utf-8")
        Q2_BEFORE_TXT.write_text(q2_before_exp + "\n", encoding="utf-8")
        Q2_AFTER_TXT.write_text(q2_after_exp + "\n", encoding="utf-8")

        q1_before_t = extract_total_time(q1_before_exp)
        q1_after_t = extract_total_time(q1_after_exp)
        q2_before_t = extract_total_time(q2_before_exp)
        q2_after_t = extract_total_time(q2_after_exp)

        q1_budget = 0.020
        q2_budget = 0.020

        evidence = {
            "w": "W11",
            "queries": {
                "q1": {
                    "name": "Métodos por década reciente",
                    "budget_seconds": q1_budget,
                    "baseline_seconds": q1_before_t,
                    "after_seconds": q1_after_t,
                    "within_budget_after": q1_after_t is not None and q1_after_t <= q1_budget,
                    "result_match": digest_rows(q1_before_rows) == digest_rows(q1_after_rows),
                    "before_rows_sha256": digest_rows(q1_before_rows),
                    "after_rows_sha256": digest_rows(q1_after_rows),
                },
                "q2": {
                    "name": "Hosts con 3+ planetas por década reciente",
                    "budget_seconds": q2_budget,
                    "baseline_seconds": q2_before_t,
                    "after_seconds": q2_after_t,
                    "within_budget_after": q2_after_t is not None and q2_after_t <= q2_budget,
                    "result_match": digest_rows(q2_before_rows) == digest_rows(q2_after_rows),
                    "before_rows_sha256": digest_rows(q2_before_rows),
                    "after_rows_sha256": digest_rows(q2_after_rows),
                },
            },
            "anti_patterns": [
                "Reagrupar desde silver_planet_v3 en cada consulta crítica en lugar de consumir una mart agregada persistente.",
                "Repetir filtros y agregaciones pesadas en caliente para dashboards/consultas frecuentes, aumentando costo y variabilidad de tiempo.",
            ],
            "rewrites": [
                "Materializar gold_mart_method_era para desacoplar la agregación por método+década del consumo analítico.",
                "Materializar gold_mart_host_era y filtrar `n_planets >= 3` sobre la mart en vez de recalcular el GROUP BY completo cada vez.",
            ],
            "gold_marts": {
                "method_era": "artifacts/w11_gold_mart_method_era.csv",
                "host_era": "artifacts/w11_gold_mart_host_era.csv",
            },
            "artifacts": {
                "q1_before": str(Q1_BEFORE_TXT.relative_to(REPO_ROOT)),
                "q1_after": str(Q1_AFTER_TXT.relative_to(REPO_ROOT)),
                "q2_before": str(Q2_BEFORE_TXT.relative_to(REPO_ROOT)),
                "q2_after": str(Q2_AFTER_TXT.relative_to(REPO_ROOT)),
            },
        }
        EVIDENCE_JSON.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    finally:
        con.close()

    print("# W11 — performance report (repro)")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
