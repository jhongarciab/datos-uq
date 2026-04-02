"""W01 runner (A+B): load raw exoplanets CSV into SQLite and reproduce documented checks.

Goal:
- Reproduce docs/w01a_run.md and docs/w01b_checks.md as closely as possible
  WITHOUT editing the docs.

This script:
1) Loads data/raw/pscomppars.csv into SQLite table raw_ps.
2) Executes the exact queries from docs/w01b_checks.md.
3) Prints results as JSON arrays (same shape as in docs).

Usage:
  python -m src.w01_runner_raw_sqlite

Notes:
- Uses ONLY stdlib (sqlite3, csv, json, pathlib).
- Database file: data/exoplanets_w01.sqlite (created/overwritten).
"""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = REPO_ROOT / "data" / "raw" / "pscomppars.csv"
DB_PATH = REPO_ROOT / "data" / "exoplanets_w01.sqlite"
TABLE = "raw_ps"


def json_rows(cursor: sqlite3.Cursor) -> str:
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    out = [dict(zip(cols, r)) for r in rows]
    return json.dumps(out, ensure_ascii=False)


def infer_type(values: list[str]) -> str:
    # Minimal type inference for SQLite.
    # Prefer INTEGER if all non-empty values are int-like.
    # Else REAL if all non-empty are float-like.
    # Else TEXT.
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

        # Peek first N rows for type inference
        sample = []
        for i, row in enumerate(reader):
            sample.append(row)
            if i >= 200:
                break

    # Re-open to stream insert all rows
    with DATA_RAW.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Infer types from sample
        col_types = {}
        for col in reader.fieldnames or []:
            col_types[col] = infer_type([r.get(col, "") for r in sample])

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


def run_checks(con: sqlite3.Connection) -> None:
    cur = con.cursor()

    # W01A evidence: count(*)
    print("# W01A — Evidencia mínima")
    cur.execute(f"SELECT count(*) AS n_rows FROM {TABLE}")
    print(json_rows(cur))
    print()

    # W01B checks (as documented)
    print("# W01B — Sanity checks")

    print("## Filas totales")
    cur.execute(f"SELECT COUNT(*) AS n_rows FROM {TABLE};")
    print(json_rows(cur))
    print()

    print("## Nulos en variables críticas")
    cur.execute(
        f"""
SELECT
  SUM(CASE WHEN pl_name IS NULL THEN 1 ELSE 0 END) AS null_pl_name,
  SUM(CASE WHEN disc_year IS NULL THEN 1 ELSE 0 END) AS null_disc_year,
  SUM(CASE WHEN discoverymethod IS NULL THEN 1 ELSE 0 END) AS null_discoverymethod
FROM {TABLE};
""".strip()
    )
    print(json_rows(cur))
    print()

    print("## Rango de años de descubrimiento")
    cur.execute(f"SELECT MIN(disc_year) AS min_disc_year, MAX(disc_year) AS max_disc_year FROM {TABLE};")
    print(json_rows(cur))
    print()

    print("## Tarea extra: duplicados por `pl_name`")
    cur.execute(
        f"""
SELECT COUNT(*) AS duplicated_names
FROM (
  SELECT pl_name
  FROM {TABLE}
  GROUP BY pl_name
  HAVING COUNT(*) > 1
) t;
""".strip()
    )
    print(json_rows(cur))


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()  # deterministic rebuild

    con = sqlite3.connect(DB_PATH)
    try:
        load_csv_to_sqlite(con)
        run_checks(con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
