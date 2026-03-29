#!/usr/bin/env python
"""
W07B — Orquestación ligera + métricas de ejecución (cross-platform)

Idea: un "scheduler" mínimo hace 3 cosas:
1) ejecuta etapas (silver/dims/gold/export) en orden
2) mide tiempos por etapa
3) deja evidencia (run report) en artifacts/

Ejecutar desde raíz:
- python -m src.pipeline.w07b_runner
o
- python src/pipeline/w07b_runner.py
"""

from __future__ import annotations

from pathlib import Path
import json
import platform
import sys
import time
from datetime import datetime, timezone

import duckdb

# Import pipeline runner from W07A
from src.pipeline import w07_pipeline


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(db_path))
    con.execute("PRAGMA threads=4")
    return con


def safe_count(con: duckdb.DuckDBPyConnection, obj: str) -> int | None:
    # return None if missing
    q = """
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema='main' AND table_name=?
    """
    exists = con.execute(q, [obj]).fetchone()[0] == 1
    if not exists:
        return None
    return con.execute(f"SELECT COUNT(*) FROM {obj}").fetchone()[0]


def file_info(p: Path) -> dict:
    if not p.exists():
        return {"exists": False, "bytes": None}
    return {"exists": True, "bytes": p.stat().st_size}


def run_stage(mode: str, project_root: Path, db_path: Path, raw_csv: Path) -> dict:
    t0 = time.perf_counter()
    rc = w07_pipeline.main([
        "--project-root", str(project_root),
        "--db-path", str(db_path.relative_to(project_root)),
        "--raw-csv", str(raw_csv.relative_to(project_root)),
        "--mode", mode
    ])
    dt = time.perf_counter() - t0
    return {"mode": mode, "return_code": rc, "seconds": round(dt, 4)}


def main() -> int:
    project_root = Path(".").resolve()
    db_path = project_root / "data" / "exoplanets.duckdb"
    raw_csv = project_root / "data" / "raw" / "pscomppars.csv"
    artifacts = project_root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    # 1) Run stages (explicit schedule)
    stages = ["silver", "dims", "gold", "export"]
    results = []
    for s in stages:
        print(f"\n== Running stage: {s} ==")
        r = run_stage(s, project_root, db_path, raw_csv)
        print("Result:", r)
        if r["return_code"] != 0:
            print("[ERROR] stopping because a stage failed.", file=sys.stderr)
            results.append(r)
            break
        results.append(r)

    # 2) Collect evidence (counts + artifacts)
    con = connect(db_path)
    counts = {
        "silver_planet": safe_count(con, "silver_planet"),
        "dim_host_sk": safe_count(con, "dim_host_sk"),
        "fact_planet_sk": safe_count(con, "fact_planet_sk"),
    }
    con.close()

    art1 = artifacts / "gold_by_discoverymethod.csv"
    art2 = artifacts / "gold_by_host.csv"

    report = {
        "w": "W07B",
        "timestamp_utc": utc_now(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "project_root": str(project_root),
        "db_path": str(db_path),
        "raw_csv": str(raw_csv),
        "stages": results,
        "counts": counts,
        "artifacts": {
            "gold_by_discoverymethod": file_info(art1),
            "gold_by_host": file_info(art2),
        },
    }

    # 3) Write run report
    out_json = artifacts / "w07b_run_report.json"
    out_csv = artifacts / "w07b_stage_timings.csv"

    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # simple CSV without pandas
    lines = ["stage,seconds,return_code"]
    for r in results:
        lines.append(f'{r["mode"]},{r["seconds"]},{r["return_code"]}')
    out_csv.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\nWrote:", out_json)
    print("Wrote:", out_csv)
    return 0 if all(r["return_code"] == 0 for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
