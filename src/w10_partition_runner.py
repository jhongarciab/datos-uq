"""W10 runner: partitioned Parquet + pruning evidence with DuckDB.

Implements the W10 assignment in a reproducible way:
- build a cleaned silver-like dataset with `disc_era`
- write partitioned Parquet by `disc_era`
- collect file counts and partition summaries
- run EXPLAIN ANALYZE with a partition filter to capture pruning evidence
- export artifacts and a compact evidence JSON

Usage:
  python -m src.w10_partition_runner
"""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import duckdb


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = REPO_ROOT / "data" / "raw" / "pscomppars.csv"
DB_PATH = REPO_ROOT / "data" / "exoplanets_w10.duckdb"
ART = REPO_ROOT / "artifacts"
PART_ROOT = REPO_ROOT / "data" / "partitioned" / "w10_disc_era"
EXPLAIN_TXT = ART / "w10b_explain_analyze_pruning.txt"
PART_SUMMARY_CSV = ART / "w10_partition_summary.csv"
FILE_INVENTORY_CSV = ART / "w10_file_inventory.csv"
EVIDENCE_JSON = ART / "w10_evidence.json"


def sql_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def sql_path(p: Path) -> str:
    return sql_quote(p.resolve().as_posix())


def connect() -> duckdb.DuckDBPyConnection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute("PRAGMA threads=4")
    return con


def build_silver_v3(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("DROP VIEW IF EXISTS raw_ps")
    con.execute(f"CREATE VIEW raw_ps AS SELECT * FROM read_csv_auto({sql_path(RAW_CSV)})")

    con.execute("DROP TABLE IF EXISTS method_synonyms")
    con.execute("CREATE TABLE method_synonyms(raw_norm VARCHAR, canonical VARCHAR)")
    con.executemany(
        "INSERT INTO method_synonyms VALUES (?, ?)",
        [
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
        ],
    )

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
    WHEN b.disc_year_int IS NULL THEN 'unknown'
    WHEN b.disc_year_int BETWEEN 1990 AND 1999 THEN '1990s'
    WHEN b.disc_year_int BETWEEN 2000 AND 2009 THEN '2000s'
    WHEN b.disc_year_int BETWEEN 2010 AND 2019 THEN '2010s'
    WHEN b.disc_year_int BETWEEN 2020 AND 2029 THEN '2020s'
    ELSE 'other'
  END AS disc_era
FROM base b
LEFT JOIN method_synonyms ms
  ON b.discoverymethod_norm = ms.raw_norm
"""
    )


def write_partitioned_parquet(con: duckdb.DuckDBPyConnection) -> None:
    if PART_ROOT.exists():
        shutil.rmtree(PART_ROOT)
    PART_ROOT.mkdir(parents=True, exist_ok=True)
    con.execute(
        f"""
COPY (
  SELECT
    pl_name,
    hostname_canon,
    discoverymethod_canon,
    disc_year_int,
    disc_era,
    pl_rade,
    pl_bmasse,
    pl_orbper,
    sy_dist
  FROM silver_planet_v3
  WHERE disc_era <> 'unknown'
) TO {sql_path(PART_ROOT)}
(FORMAT PARQUET, PARTITION_BY (disc_era), OVERWRITE_OR_IGNORE 1)
"""
    )


def collect_files() -> list[dict]:
    rows = []
    for p in sorted(PART_ROOT.rglob("*.parquet")):
        rel = p.relative_to(REPO_ROOT).as_posix()
        partition = p.parent.name.split("=", 1)[1] if "=" in p.parent.name else p.parent.name
        rows.append({
            "path": rel,
            "partition": partition,
            "bytes": p.stat().st_size,
        })
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def collect_evidence(con: duckdb.DuckDBPyConnection) -> dict:
    parquet_glob = PART_ROOT.as_posix() + "/**/*.parquet"

    part_summary = con.execute(
        f"""
SELECT disc_era, COUNT(*) AS n_rows
FROM read_parquet({sql_quote(parquet_glob)}, hive_partitioning=1)
GROUP BY disc_era
ORDER BY disc_era
"""
    ).fetchall()
    part_summary_rows = [{"disc_era": a, "n_rows": b} for a, b in part_summary]

    files = collect_files()
    write_csv(FILE_INVENTORY_CSV, files)
    write_csv(PART_SUMMARY_CSV, part_summary_rows)

    filter_partition = "2010s"
    explain_rows = con.execute(
        f"""
EXPLAIN ANALYZE
SELECT COUNT(*) AS n_rows
FROM read_parquet({sql_quote(parquet_glob)}, hive_partitioning=1)
WHERE disc_era = '{filter_partition}'
"""
    ).fetchall()
    explain_text = "\n\n".join(str(row[1]) if len(row) > 1 else str(row[0]) for row in explain_rows)
    EXPLAIN_TXT.write_text(explain_text + "\n", encoding="utf-8")

    total_files = len(files)
    filtered_files = len([r for r in files if r["partition"] == filter_partition])
    total_bytes = sum(r["bytes"] for r in files)
    filtered_bytes = sum(r["bytes"] for r in files if r["partition"] == filter_partition)

    evidence = {
        "w": "W10",
        "partition_column": "disc_era",
        "filter_used": f"disc_era = '{filter_partition}'",
        "total_files": total_files,
        "filtered_files": filtered_files,
        "total_bytes": total_bytes,
        "filtered_bytes": filtered_bytes,
        "partition_summary": part_summary_rows,
        "files": files,
        "artifacts": {
            "file_inventory": str(FILE_INVENTORY_CSV.relative_to(REPO_ROOT)),
            "partition_summary": str(PART_SUMMARY_CSV.relative_to(REPO_ROOT)),
            "explain_analyze": str(EXPLAIN_TXT.relative_to(REPO_ROOT)),
        },
    }
    EVIDENCE_JSON.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> None:
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"Missing raw CSV: {RAW_CSV}")
    ART.mkdir(parents=True, exist_ok=True)
    con = connect()
    try:
        build_silver_v3(con)
        write_partitioned_parquet(con)
        evidence = collect_evidence(con)
    finally:
        con.close()

    print("# W10 — partition report (repro)")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
