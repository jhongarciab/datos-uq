"""W02A runner: reproduce the SQL practice results documented in docs/w02a_sql_practice.md.

Approach
- Uses the same raw table (raw_ps) built from data/raw/pscomppars.csv.
- Executes the exact SQL queries as in the doc.
- Prints results as JSON arrays (same shape) in the same order.

Usage
  python -m src.w02a_sql_practice_runner

Notes
- Creates/overwrites data/exoplanets_w02.sqlite (gitignored).
- Stdlib only.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = REPO_ROOT / "data" / "raw" / "pscomppars.csv"
DB_PATH = REPO_ROOT / "data" / "exoplanets_w02.sqlite"
TABLE = "raw_ps"


def json_rows(cursor: sqlite3.Cursor) -> str:
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    out = [dict(zip(cols, r)) for r in rows]
    return json.dumps(out, ensure_ascii=False, indent=2)


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


def load_raw(con: sqlite3.Connection) -> None:
    if not DATA_RAW.exists():
        raise FileNotFoundError(f"Missing raw CSV: {DATA_RAW}")

    # sample for types
    with DATA_RAW.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        sample = []
        for i, row in enumerate(reader):
            sample.append(row)
            if i >= 200:
                break

    with DATA_RAW.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        if not cols:
            raise ValueError("CSV has no header")

        col_types = {c: infer_type([r.get(c, "") for r in sample]) for c in cols}
        cols_sql = ", ".join([f'"{c}" {t}' for c, t in col_types.items()])

        con.execute(f"DROP TABLE IF EXISTS {TABLE}")
        con.execute(f"CREATE TABLE {TABLE} ({cols_sql})")

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


def q(con: sqlite3.Connection, sql: str) -> str:
    cur = con.cursor()
    cur.execute(sql)
    return json_rows(cur)


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    con = sqlite3.connect(DB_PATH)
    try:
        load_raw(con)

        print("# W02A — SQL practice (repro)")

        print("\n## 1) Planetas por año (top 15)")
        print(
            q(
                con,
                "SELECT disc_year, COUNT(*) AS n_planets FROM raw_ps WHERE disc_year IS NOT NULL GROUP BY disc_year ORDER BY n_planets DESC, disc_year DESC LIMIT 15;",
            )
        )

        print("\n## 2) Top 10 sistemas (hostname) con más planetas")
        print(
            q(
                con,
                "SELECT hostname, COUNT(*) AS n_planets FROM raw_ps WHERE hostname IS NOT NULL GROUP BY hostname ORDER BY n_planets DESC, hostname ASC LIMIT 10;",
            )
        )

        print("\n## 3) Fracción de nulos en pl_bmasse")
        print(
            q(
                con,
                "SELECT ROUND(100.0*SUM(CASE WHEN pl_bmasse IS NULL THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_null_pl_bmasse FROM raw_ps;",
            )
        )

        print("\n## 4) Top 10 planetas por radio (pl_rade)")
        print(
            q(
                con,
                "SELECT pl_name, pl_rade FROM raw_ps WHERE pl_rade IS NOT NULL ORDER BY pl_rade DESC LIMIT 10;",
            )
        )

        print("\n## 5) COUNT(*) vs COUNT(disc_year) por método")
        print(
            q(
                con,
                "SELECT discoverymethod, COUNT(*) AS total_rows, COUNT(disc_year) AS non_null_disc_year FROM raw_ps GROUP BY discoverymethod ORDER BY total_rows DESC;",
            )
        )

        print("\n## 6) Resumen por método (n_planets y promedio de periodo orbital)")
        print(
            q(
                con,
                "SELECT discoverymethod, COUNT(*) AS n_planets, ROUND(AVG(pl_orbper),2) AS avg_orbper_days FROM raw_ps WHERE pl_orbper IS NOT NULL GROUP BY discoverymethod ORDER BY n_planets DESC;",
            )
        )

        print("\n## 4 consultas adicionales (tarea)")

        print("\n### Calidad 1 — Duplicados por pl_name")
        print(
            q(
                con,
                "SELECT COUNT(*) AS duplicated_pl_name_groups FROM (SELECT pl_name FROM raw_ps WHERE pl_name IS NOT NULL GROUP BY pl_name HAVING COUNT(*)>1) t;",
            )
        )

        print("\n### Calidad 2 — Años fuera de rango")
        print(
            q(
                con,
                "SELECT COUNT(*) AS invalid_disc_year_rows FROM raw_ps WHERE disc_year IS NOT NULL AND (disc_year<1980 OR disc_year>CAST(strftime('%Y','now') AS INTEGER));",
            )
        )

        print("\n### Científica 1 — Métodos de descubrimiento más frecuentes")
        print(
            q(
                con,
                "SELECT discoverymethod, COUNT(*) AS n_planets FROM raw_ps GROUP BY discoverymethod ORDER BY n_planets DESC LIMIT 5;",
            )
        )

        print("\n### Científica 2 — Promedio de radio y masa (filas con ambos datos)")
        print(
            q(
                con,
                "SELECT ROUND(AVG(pl_rade),2) AS avg_radius_earth, ROUND(AVG(pl_bmasse),2) AS avg_mass_earth FROM raw_ps WHERE pl_rade IS NOT NULL AND pl_bmasse IS NOT NULL;",
            )
        )

    finally:
        con.close()


if __name__ == "__main__":
    main()
