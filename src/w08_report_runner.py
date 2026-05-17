"""W08 runner: raw->silver v2 cleaning + toy many-to-many evidence in SQLite.

Reproduces the W08 assignment in a repo-consistent way:
- load `data/raw/pscomppars.csv` into SQLite table `raw_ps`
- create `method_map` with canonical discovery-method mappings
- create `silver_planet_v2` with cleaned hostname/method and `disc_era`
- create a toy many-to-many schema with PK/FK evidence
- export reproducible artifacts under `artifacts/`

Usage:
  python -m src.w08_report_runner
"""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = REPO_ROOT / "data" / "raw" / "pscomppars.csv"
DB_PATH = REPO_ROOT / "data" / "exoplanets_w08.sqlite"
ART = REPO_ROOT / "artifacts"
EVIDENCE_JSON = ART / "w08_evidence.json"
METHOD_COUNTS_CSV = ART / "w08_method_counts.csv"
PLANETS_PER_METHOD_CSV = ART / "w08_planets_per_method.csv"
METHODS_PER_PLANET_CSV = ART / "w08_methods_per_planet.csv"
DDL_SQL = ART / "w08_many_to_many_ddl.sql"

TABLE = "raw_ps"

METHOD_MAP_ROWS = [
    ("Transit", "transit"),
    ("Radial Velocity", "radial_velocity"),
    ("Microlensing", "microlensing"),
    ("Imaging", "imaging"),
    ("Transit Timing Variations", "transit_timing_variations"),
    ("Eclipse Timing Variations", "eclipse_timing_variations"),
    ("Orbital Brightness Modulation", "orbital_brightness_modulation"),
    ("Pulsar Timing", "pulsar_timing"),
    ("Astrometry", "astrometry"),
    ("Pulsation Timing Variations", "pulsation_timing_variations"),
    ("Disk Kinematics", "disk_kinematics"),
]

DDL_PLANET = """
CREATE TABLE planet_demo(
  planet_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL
)
""".strip()

DDL_METHOD = """
CREATE TABLE method_demo(
  method_id INTEGER PRIMARY KEY,
  method_name TEXT NOT NULL UNIQUE
)
""".strip()

DDL_LINK = """
CREATE TABLE planet_method_demo(
  planet_id INTEGER NOT NULL,
  method_id INTEGER NOT NULL,
  PRIMARY KEY (planet_id, method_id),
  FOREIGN KEY (planet_id) REFERENCES planet_demo(planet_id),
  FOREIGN KEY (method_id) REFERENCES method_demo(method_id)
)
""".strip()


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
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError("CSV has no header")
        sample = []
        for i, row in enumerate(reader):
            sample.append(row)
            if i >= 200:
                break

    with DATA_RAW.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        col_types = {col: infer_type([r.get(col, "") for r in sample]) for col in (reader.fieldnames or [])}
        cols_sql = ", ".join([f'"{c}" {t}' for c, t in col_types.items()])
        con.execute(f'DROP TABLE IF EXISTS {TABLE}')
        con.execute(f'CREATE TABLE {TABLE} ({cols_sql})')

        cols = reader.fieldnames or []
        placeholders = ",".join(["?"] * len(cols))
        cols_quoted = ", ".join([f'"{c}"' for c in cols])
        insert_sql = f"INSERT INTO {TABLE} ({cols_quoted}) VALUES ({placeholders})"

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


def build_method_map(con: sqlite3.Connection) -> None:
    con.execute("DROP TABLE IF EXISTS method_map")
    con.execute(
        "CREATE TABLE method_map(raw_method TEXT PRIMARY KEY, canonical_method TEXT NOT NULL)"
    )
    con.executemany("INSERT INTO method_map(raw_method, canonical_method) VALUES (?, ?)", METHOD_MAP_ROWS)
    con.commit()


def build_silver_v2(con: sqlite3.Connection) -> None:
    con.execute("DROP TABLE IF EXISTS silver_planet_v2")
    con.execute(
        """
CREATE TABLE silver_planet_v2 AS
SELECT
  r.*,
  CASE
    WHEN r.hostname IS NULL OR TRIM(r.hostname) = '' THEN NULL
    ELSE LOWER(TRIM(r.hostname))
  END AS hostname_clean,
  CASE
    WHEN r.discoverymethod IS NULL OR TRIM(r.discoverymethod) = '' THEN NULL
    ELSE LOWER(TRIM(r.discoverymethod))
  END AS discoverymethod_norm,
  COALESCE(
    mm.canonical_method,
    CASE
      WHEN r.discoverymethod IS NULL OR TRIM(r.discoverymethod) = '' THEN NULL
      ELSE LOWER(TRIM(r.discoverymethod))
    END
  ) AS discoverymethod_clean,
  CASE
    WHEN r.disc_year IS NULL THEN NULL
    ELSE printf('%ds', CAST(r.disc_year / 10 AS INTEGER) * 10)
  END AS disc_era
FROM raw_ps r
LEFT JOIN method_map mm
  ON r.discoverymethod = mm.raw_method
""".strip()
    )
    con.commit()


def build_many_to_many(con: sqlite3.Connection) -> dict:
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("DROP TABLE IF EXISTS planet_method_demo")
    con.execute("DROP TABLE IF EXISTS method_demo")
    con.execute("DROP TABLE IF EXISTS planet_demo")
    con.execute(DDL_PLANET)
    con.execute(DDL_METHOD)
    con.execute(DDL_LINK)

    con.executemany(
        "INSERT INTO planet_demo(planet_id, name) VALUES (?, ?)",
        [
            (1, "Kepler-10 b"),
            (2, "TRAPPIST-1 e"),
            (3, "Proxima Cen b"),
            (4, "HR 8799 b"),
        ],
    )
    con.executemany(
        "INSERT INTO method_demo(method_id, method_name) VALUES (?, ?)",
        [
            (10, "transit"),
            (20, "radial_velocity"),
            (30, "imaging"),
        ],
    )
    con.executemany(
        "INSERT INTO planet_method_demo(planet_id, method_id) VALUES (?, ?)",
        [
            (1, 10),
            (1, 20),
            (2, 10),
            (3, 20),
            (4, 30),
        ],
    )
    con.commit()

    cur = con.cursor()
    cur.execute(
        """
SELECT m.method_name, COUNT(DISTINCT pm.planet_id) AS n_planets
FROM method_demo m
LEFT JOIN planet_method_demo pm ON pm.method_id = m.method_id
GROUP BY m.method_id, m.method_name
ORDER BY n_planets DESC, m.method_name ASC
""".strip()
    )
    q1 = json_rows(cur)

    cur.execute(
        """
SELECT p.name, COUNT(pm.method_id) AS n_methods
FROM planet_demo p
LEFT JOIN planet_method_demo pm ON pm.planet_id = p.planet_id
GROUP BY p.planet_id, p.name
ORDER BY n_methods DESC, p.name ASC
""".strip()
    )
    q2 = json_rows(cur)

    cur.execute(
        """
SELECT planet_id, method_id, COUNT(*) AS c
FROM planet_method_demo
GROUP BY planet_id, method_id
HAVING COUNT(*) > 1
""".strip()
    )
    dup_check = json_rows(cur)

    duplicate_insert_error = None
    try:
        con.execute("INSERT INTO planet_method_demo(planet_id, method_id) VALUES (1, 10)")
        con.commit()
    except sqlite3.IntegrityError as e:
        duplicate_insert_error = str(e)
        con.rollback()

    fk_insert_error = None
    try:
        con.execute("INSERT INTO planet_method_demo(planet_id, method_id) VALUES (99, 10)")
        con.commit()
    except sqlite3.IntegrityError as e:
        fk_insert_error = str(e)
        con.rollback()

    return {
        "planets_per_method": q1,
        "methods_per_planet": q2,
        "duplicate_check": dup_check,
        "duplicate_insert_error": duplicate_insert_error,
        "fk_insert_error": fk_insert_error,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def collect_evidence(con: sqlite3.Connection, many_to_many: dict) -> dict:
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) AS n_rows FROM raw_ps")
    raw_count = json_rows(cur)[0]

    cur.execute("SELECT COUNT(*) AS n_rows FROM silver_planet_v2")
    silver_count = json_rows(cur)[0]

    cur.execute("SELECT COUNT(*) AS n_null_hosts FROM silver_planet_v2 WHERE hostname_clean IS NULL")
    null_hosts = json_rows(cur)[0]

    cur.execute(
        """
SELECT discoverymethod_clean, COUNT(*) AS n
FROM silver_planet_v2
WHERE discoverymethod_clean IS NOT NULL
GROUP BY discoverymethod_clean
ORDER BY n DESC, discoverymethod_clean ASC
""".strip()
    )
    method_counts = json_rows(cur)

    cur.execute(
        """
SELECT disc_era, COUNT(*) AS n
FROM silver_planet_v2
WHERE disc_era IS NOT NULL
GROUP BY disc_era
ORDER BY disc_era ASC
""".strip()
    )
    disc_era_counts = json_rows(cur)

    cur.execute("SELECT raw_method, canonical_method FROM method_map ORDER BY raw_method")
    method_map = json_rows(cur)

    write_csv(METHOD_COUNTS_CSV, method_counts)
    write_csv(PLANETS_PER_METHOD_CSV, many_to_many["planets_per_method"])
    write_csv(METHODS_PER_PLANET_CSV, many_to_many["methods_per_planet"])
    DDL_SQL.write_text("\n\n".join([DDL_PLANET + ";", DDL_METHOD + ";", DDL_LINK + ";"]) + "\n", encoding="utf-8")

    evidence = {
        "w": "W08",
        "raw_count": raw_count,
        "silver_count": silver_count,
        "null_hosts": null_hosts,
        "method_map": method_map,
        "method_counts_top10": method_counts[:10],
        "disc_era_counts": disc_era_counts,
        "many_to_many": many_to_many,
        "artifacts": {
            "method_counts_csv": str(METHOD_COUNTS_CSV.relative_to(REPO_ROOT)),
            "planets_per_method_csv": str(PLANETS_PER_METHOD_CSV.relative_to(REPO_ROOT)),
            "methods_per_planet_csv": str(METHODS_PER_PLANET_CSV.relative_to(REPO_ROOT)),
            "ddl_sql": str(DDL_SQL.relative_to(REPO_ROOT)),
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
        build_method_map(con)
        build_silver_v2(con)
        many_to_many = build_many_to_many(con)
        evidence = collect_evidence(con, many_to_many)
    finally:
        con.close()

    print("# W08 — report (repro)")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
