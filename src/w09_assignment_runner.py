"""W09 runner: advanced cleaning + quality gates in SQLite.

Implements the W09 assignment in the repo's reproducible style:
- load raw CSV into SQLite
- create `method_synonyms(raw_norm, canonical)`
- create `silver_planet_v3` with canonical hostname/method plus year flags
- create `quality_events` with four computed checks
- export evidence artifacts under `artifacts/`

Usage:
  python -m src.w09_assignment_runner
"""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = REPO_ROOT / "data" / "raw" / "pscomppars.csv"
DB_PATH = REPO_ROOT / "data" / "exoplanets_w09.sqlite"
ART = REPO_ROOT / "artifacts"
TABLE = "raw_ps"
NOW_YEAR = datetime.now(timezone.utc).year

EVIDENCE_JSON = ART / "w09_evidence.json"
QUALITY_CSV = ART / "w09_quality_events.csv"
METHOD_COUNTS_CSV = ART / "w09_method_canon_counts.csv"
DISC_ERA_CSV = ART / "w09_disc_era_counts.csv"

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


def json_rows(cur: sqlite3.Cursor) -> list[dict]:
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def infer_type(values: list[str]) -> str:
    def is_int(s: str) -> bool:
        try:
            int(s)
            return True
        except Exception:
            return False

    def is_float(s: str) -> bool:
        try:
            float(s)
            return True
        except Exception:
            return False

    non_empty = [v for v in values if v not in ("", None)]
    if not non_empty:
        return "TEXT"
    if all(is_int(v) for v in non_empty):
        return "INTEGER"
    if all(is_float(v) for v in non_empty):
        return "REAL"
    return "TEXT"


def load_csv_to_sqlite(con: sqlite3.Connection) -> None:
    if not DATA_RAW.exists():
        raise FileNotFoundError(f"Missing raw CSV: {DATA_RAW}")

    with DATA_RAW.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header")
        sample = []
        for i, row in enumerate(reader):
            sample.append(row)
            if i >= 200:
                break

    with DATA_RAW.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        col_types = {col: infer_type([r.get(col, "") for r in sample]) for col in cols}
        con.execute(f'DROP TABLE IF EXISTS {TABLE}')
        con.execute(
            "CREATE TABLE raw_ps (" + ", ".join([f'"{c}" {col_types[c]}' for c in cols]) + ")"
        )
        insert_sql = (
            f"INSERT INTO {TABLE} (" + ", ".join([f'\"{c}\"' for c in cols]) + ") VALUES (" + ",".join(["?"] * len(cols)) + ")"
        )

        def cast(v: str, t: str):
            if v == "" or v is None:
                return None
            if t == "INTEGER":
                try:
                    return int(v)
                except Exception:
                    return None
            if t == "REAL":
                try:
                    return float(v)
                except Exception:
                    return None
            return v

        batch = []
        for row in reader:
            batch.append([cast(row.get(c, ""), col_types[c]) for c in cols])
            if len(batch) >= 2000:
                con.executemany(insert_sql, batch)
                batch.clear()
        if batch:
            con.executemany(insert_sql, batch)
    con.commit()


def build_method_synonyms(con: sqlite3.Connection) -> None:
    con.execute("DROP TABLE IF EXISTS method_synonyms")
    con.execute("CREATE TABLE method_synonyms(raw_norm TEXT PRIMARY KEY, canonical TEXT NOT NULL)")
    con.executemany("INSERT INTO method_synonyms(raw_norm, canonical) VALUES (?, ?)", SYNONYMS)
    con.commit()


def norm_sql(col: str) -> str:
    return f"LOWER(TRIM(REPLACE(REPLACE(REPLACE({col}, '   ', ' '), '  ', ' '), '  ', ' ')))"


def build_silver_v3(con: sqlite3.Connection) -> None:
    con.execute("DROP TABLE IF EXISTS silver_planet_v3")
    con.execute(
        f"""
CREATE TABLE silver_planet_v3 AS
WITH base AS (
  SELECT
    r.*,
    CASE
      WHEN r.hostname IS NULL OR TRIM(r.hostname) = '' THEN NULL
      ELSE {norm_sql('r.hostname')}
    END AS hostname_canon,
    CASE
      WHEN r.discoverymethod IS NULL OR TRIM(r.discoverymethod) = '' THEN NULL
      ELSE {norm_sql('r.discoverymethod')}
    END AS discoverymethod_norm,
    CASE
      WHEN r.disc_year IS NULL THEN NULL
      ELSE CAST(r.disc_year AS INTEGER)
    END AS disc_year_int
  FROM raw_ps r
)
SELECT
  b.*,
  COALESCE(ms.canonical, b.discoverymethod_norm) AS discoverymethod_canon,
  CASE
    WHEN b.disc_year_int IS NULL THEN 1
    WHEN b.disc_year_int < 1980 OR b.disc_year_int > {NOW_YEAR} THEN 1
    ELSE 0
  END AS disc_year_bad,
  CASE
    WHEN b.disc_year_int IS NULL THEN NULL
    ELSE printf('%ds', CAST(b.disc_year_int / 10 AS INTEGER) * 10)
  END AS disc_era,
  CASE
    WHEN ms.canonical IS NULL AND b.discoverymethod_norm IS NOT NULL THEN 1
    ELSE 0
  END AS method_used_fallback
FROM base b
LEFT JOIN method_synonyms ms
  ON b.discoverymethod_norm = ms.raw_norm
""".strip()
    )
    con.commit()


def build_quality_events(con: sqlite3.Connection) -> list[dict]:
    con.execute("DROP TABLE IF EXISTS quality_events")
    con.execute(
        """
CREATE TABLE quality_events(
  ts_utc TEXT NOT NULL,
  check_name TEXT NOT NULL,
  status TEXT NOT NULL,
  metric_value REAL NOT NULL,
  details TEXT
)
""".strip()
    )

    cur = con.cursor()
    checks_sql = {
        "hostname_canon_nulls": "SELECT COUNT(*) FROM silver_planet_v3 WHERE hostname_canon IS NULL",
        "discoverymethod_canon_nulls": "SELECT COUNT(*) FROM silver_planet_v3 WHERE discoverymethod_canon IS NULL",
        "disc_year_bad_rows": "SELECT COUNT(*) FROM silver_planet_v3 WHERE disc_year_bad = 1",
        "method_fallback_rows": "SELECT COUNT(*) FROM silver_planet_v3 WHERE method_used_fallback = 1",
    }
    thresholds = {
        "hostname_canon_nulls": 0,
        "discoverymethod_canon_nulls": 0,
        "disc_year_bad_rows": 1,
        "method_fallback_rows": 0,
    }
    details = {
        "hostname_canon_nulls": "hostname_canon debe quedar completo tras LOWER/TRIM",
        "discoverymethod_canon_nulls": "discoverymethod_canon debe resolverse por synonyms o fallback",
        "disc_year_bad_rows": "Se tolera 1 fila mala para reflejar el único disc_year nulo del dataset",
        "method_fallback_rows": "Con synonyms completos no deberían quedar filas apoyadas solo en fallback",
    }

    ts = datetime.now(timezone.utc).isoformat()
    rows = []
    for name, sql in checks_sql.items():
        cur.execute(sql)
        metric = float(cur.fetchone()[0])
        status = "PASS" if metric <= thresholds[name] else "FAIL"
        row = {
            "ts_utc": ts,
            "check_name": name,
            "status": status,
            "metric_value": metric,
            "details": details[name],
        }
        rows.append(row)
        con.execute(
            "INSERT INTO quality_events(ts_utc, check_name, status, metric_value, details) VALUES (?, ?, ?, ?, ?)",
            (row["ts_utc"], row["check_name"], row["status"], row["metric_value"], row["details"]),
        )
    con.commit()
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def collect_evidence(con: sqlite3.Connection, quality_rows: list[dict]) -> dict:
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) AS n_rows FROM silver_planet_v3")
    silver_count = json_rows(cur)[0]
    cur.execute("SELECT COUNT(*) AS disc_year_bad FROM silver_planet_v3 WHERE disc_year_bad = 1")
    disc_year_bad = json_rows(cur)[0]
    cur.execute(
        """
SELECT discoverymethod_canon, COUNT(*) AS n
FROM silver_planet_v3
WHERE discoverymethod_canon IS NOT NULL
GROUP BY discoverymethod_canon
ORDER BY n DESC, discoverymethod_canon ASC
""".strip()
    )
    method_counts = json_rows(cur)
    cur.execute(
        """
SELECT disc_era, COUNT(*) AS n
FROM silver_planet_v3
WHERE disc_era IS NOT NULL
GROUP BY disc_era
ORDER BY disc_era ASC
""".strip()
    )
    disc_era_counts = json_rows(cur)
    cur.execute("SELECT raw_norm, canonical FROM method_synonyms ORDER BY raw_norm")
    method_synonyms = json_rows(cur)
    cur.execute("SELECT check_name, status, metric_value, details FROM quality_events ORDER BY check_name")
    quality_table = json_rows(cur)

    write_csv(QUALITY_CSV, quality_table)
    write_csv(METHOD_COUNTS_CSV, method_counts)
    write_csv(DISC_ERA_CSV, disc_era_counts)

    evidence = {
        "w": "W09",
        "silver_count": silver_count,
        "disc_year_bad": disc_year_bad,
        "method_synonyms": method_synonyms,
        "method_counts_top10": method_counts[:10],
        "disc_era_counts": disc_era_counts,
        "quality_events": quality_rows,
        "artifacts": {
            "quality_csv": str(QUALITY_CSV.relative_to(REPO_ROOT)),
            "method_counts_csv": str(METHOD_COUNTS_CSV.relative_to(REPO_ROOT)),
            "disc_era_csv": str(DISC_ERA_CSV.relative_to(REPO_ROOT)),
        },
    }
    EVIDENCE_JSON.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    con = sqlite3.connect(DB_PATH)
    try:
        load_csv_to_sqlite(con)
        build_method_synonyms(con)
        build_silver_v3(con)
        quality_rows = build_quality_events(con)
        evidence = collect_evidence(con, quality_rows)
    finally:
        con.close()

    print("# W09 — assignment (repro)")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
