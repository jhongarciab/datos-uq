#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import platform
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
RAW_CSV = DATA_DIR / 'raw' / 'pscomppars.csv'
DB_PATH = DATA_DIR / 'exoplanets_w06b.sqlite'
ARTIFACTS = PROJECT_ROOT / 'artifacts'


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_float(value: str):
    if value in ('', None):
        return None
    try:
        return float(value)
    except Exception:
        return None


def to_int(value: str):
    if value in ('', None):
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute('PRAGMA journal_mode=WAL;')
    con.execute('PRAGMA synchronous=NORMAL;')
    con.execute('PRAGMA temp_store=MEMORY;')
    return con


def create_raw(con: sqlite3.Connection) -> int:
    con.execute('DROP TABLE IF EXISTS raw_ps')
    con.execute('''
    CREATE TABLE raw_ps (
      pl_name TEXT,
      hostname TEXT,
      discoverymethod TEXT,
      disc_year INTEGER,
      sy_snum REAL,
      sy_pnum REAL,
      sy_dist REAL,
      ra REAL,
      dec REAL,
      pl_orbper REAL,
      pl_rade REAL,
      pl_bmasse REAL,
      pl_eqt REAL,
      st_teff REAL,
      st_rad REAL,
      st_mass REAL
    )
    ''')
    rows = []
    with RAW_CSV.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append((
                r['pl_name'] or None,
                r['hostname'] or None,
                r['discoverymethod'] or None,
                to_int(r['disc_year']),
                to_float(r['sy_snum']),
                to_float(r['sy_pnum']),
                to_float(r['sy_dist']),
                to_float(r['ra']),
                to_float(r['dec']),
                to_float(r['pl_orbper']),
                to_float(r['pl_rade']),
                to_float(r['pl_bmasse']),
                to_float(r['pl_eqt']),
                to_float(r['st_teff']),
                to_float(r['st_rad']),
                to_float(r['st_mass']),
            ))
    con.executemany('INSERT INTO raw_ps VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', rows)
    con.commit()
    return len(rows)


def stage_silver(con: sqlite3.Connection):
    con.execute('DROP TABLE IF EXISTS silver_planet')
    con.execute('''
    CREATE TABLE silver_planet AS
    SELECT *
    FROM raw_ps
    WHERE pl_name IS NOT NULL
      AND hostname IS NOT NULL
      AND (disc_year IS NULL OR (disc_year BETWEEN 1980 AND 2026))
      AND (pl_rade IS NULL OR (pl_rade > 0 AND pl_rade <= 30))
      AND (pl_bmasse IS NULL OR (pl_bmasse > 0))
    ''')
    con.commit()


def stage_dims(con: sqlite3.Connection):
    con.execute('DROP TABLE IF EXISTS dim_host_full')
    con.execute('DROP TABLE IF EXISTS fact_planet')
    con.execute('DROP TABLE IF EXISTS dim_host_sk')
    con.execute('DROP TABLE IF EXISTS fact_planet_sk')

    con.execute('''
    CREATE TABLE dim_host_full AS
    SELECT hostname,
           MAX(sy_dist) AS sy_dist,
           MAX(ra) AS ra,
           MAX(dec) AS dec,
           MAX(st_teff) AS st_teff,
           MAX(st_rad) AS st_rad,
           MAX(st_mass) AS st_mass
    FROM silver_planet
    GROUP BY hostname
    ''')

    con.execute('''
    CREATE TABLE fact_planet AS
    SELECT DISTINCT
      pl_name, hostname, discoverymethod, disc_year, pl_orbper, pl_rade, pl_bmasse, pl_eqt
    FROM silver_planet
    ''')

    con.execute('''
    CREATE TABLE dim_host_sk AS
    SELECT ROW_NUMBER() OVER (ORDER BY hostname) AS host_id,
           hostname, sy_dist, ra, dec, st_teff, st_rad, st_mass
    FROM dim_host_full
    ''')

    con.execute('''
    CREATE TABLE fact_planet_sk AS
    SELECT f.pl_name, d.host_id, f.discoverymethod, f.disc_year,
           f.pl_orbper, f.pl_rade, f.pl_bmasse, f.pl_eqt
    FROM fact_planet f
    JOIN dim_host_sk d ON f.hostname = d.hostname
    ''')
    con.commit()


def stage_gold(con: sqlite3.Connection):
    con.execute('DROP VIEW IF EXISTS gold_by_discoverymethod')
    con.execute('DROP VIEW IF EXISTS gold_by_host')
    con.execute('''
    CREATE VIEW gold_by_discoverymethod AS
    SELECT discoverymethod,
           COUNT(*) AS n_planets,
           ROUND(AVG(pl_rade), 3) AS avg_pl_rade,
           ROUND(AVG(pl_bmasse), 3) AS avg_pl_bmasse,
           MIN(disc_year) AS first_disc_year,
           MAX(disc_year) AS last_disc_year
    FROM fact_planet_sk
    WHERE discoverymethod IS NOT NULL
    GROUP BY discoverymethod
    ORDER BY n_planets DESC
    ''')
    con.execute('''
    CREATE VIEW gold_by_host AS
    SELECT d.hostname,
           COUNT(*) AS n_planets,
           ROUND(AVG(f.pl_rade), 3) AS avg_pl_rade,
           MIN(f.disc_year) AS first_disc_year,
           MAX(f.disc_year) AS last_disc_year
    FROM fact_planet_sk f
    JOIN dim_host_sk d ON f.host_id = d.host_id
    GROUP BY d.hostname
    ORDER BY n_planets DESC, avg_pl_rade DESC
    ''')
    con.commit()


def export_csv(con: sqlite3.Connection, query: str, out_path: Path):
    cur = con.execute(query)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    with out_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)


def stage_export(con: sqlite3.Connection):
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    export_csv(con, 'SELECT * FROM gold_by_discoverymethod', ARTIFACTS / 'gold_by_discoverymethod.csv')
    export_csv(con, 'SELECT * FROM gold_by_host', ARTIFACTS / 'gold_by_host.csv')


def safe_count(con, table):
    cur = con.execute(f'SELECT COUNT(*) FROM {table}')
    return cur.fetchone()[0]


def run_once(run_label: str) -> tuple[dict, str]:
    t0_total = time.perf_counter()
    stdout = []
    con = connect()
    raw_rows = create_raw(con)
    stdout.append(f'raw_ps rows={raw_rows}')
    stages = []
    for mode, fn in [('silver', stage_silver), ('dims', stage_dims), ('gold', stage_gold), ('export', stage_export)]:
        t0 = time.perf_counter()
        fn(con)
        dt = round(time.perf_counter() - t0, 4)
        stages.append({'mode': mode, 'seconds': dt, 'return_code': 0})
        stdout.append(f'{mode}: {dt}s')
    counts = {
        'silver_planet': safe_count(con, 'silver_planet'),
        'dim_host_sk': safe_count(con, 'dim_host_sk'),
        'fact_planet_sk': safe_count(con, 'fact_planet_sk'),
    }
    report = {
        'w': 'W06B',
        'run_label': run_label,
        'timestamp_utc': utc_now(),
        'python': sys.version.split()[0],
        'platform': platform.platform(),
        'project_root': str(PROJECT_ROOT),
        'db_path': str(DB_PATH),
        'raw_csv': str(RAW_CSV),
        'stages': stages,
        'counts': counts,
        'artifacts': {
            'gold_by_discoverymethod': {'exists': (ARTIFACTS / 'gold_by_discoverymethod.csv').exists(), 'bytes': (ARTIFACTS / 'gold_by_discoverymethod.csv').stat().st_size if (ARTIFACTS / 'gold_by_discoverymethod.csv').exists() else None},
            'gold_by_host': {'exists': (ARTIFACTS / 'gold_by_host.csv').exists(), 'bytes': (ARTIFACTS / 'gold_by_host.csv').stat().st_size if (ARTIFACTS / 'gold_by_host.csv').exists() else None},
        },
        'total_seconds': round(time.perf_counter() - t0_total, 4),
    }
    con.close()
    return report, '\n'.join(stdout)


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    reports = []
    stdouts = []
    for label in ('run1', 'run2'):
        report, stdout = run_once(label)
        reports.append(report)
        stdouts.append({'run_label': label, 'stdout': stdout})

    final = reports[-1]
    (ARTIFACTS / 'w06b_run_report.json').write_text(json.dumps(final, indent=2), encoding='utf-8')
    with (ARTIFACTS / 'w06b_stage_timings.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['run_label', 'stage', 'seconds', 'return_code'])
        for rep in reports:
            for s in rep['stages']:
                w.writerow([rep['run_label'], s['mode'], s['seconds'], s['return_code']])
    (ARTIFACTS / 'w06b_run_history.json').write_text(json.dumps({'runs': reports, 'stdouts': stdouts}, indent=2), encoding='utf-8')
    print(json.dumps({'runs': reports, 'stdouts': stdouts}, indent=2))


if __name__ == '__main__':
    main()
