# W04A — Quality report

Fecha: 2026-02-23

## TU TURNO 1 — Nulos en 12 columnas clave

```json
[
  {
    "column_name": "pl_name",
    "n_rows": 6087,
    "n_nulls": 0,
    "pct_nulls": 0.0
  },
  {
    "column_name": "hostname",
    "n_rows": 6087,
    "n_nulls": 0,
    "pct_nulls": 0.0
  },
  {
    "column_name": "discoverymethod",
    "n_rows": 6087,
    "n_nulls": 0,
    "pct_nulls": 0.0
  },
  {
    "column_name": "disc_year",
    "n_rows": 6087,
    "n_nulls": 1,
    "pct_nulls": 0.02
  },
  {
    "column_name": "pl_orbper",
    "n_rows": 6087,
    "n_nulls": 321,
    "pct_nulls": 5.27
  },
  {
    "column_name": "pl_rade",
    "n_rows": 6087,
    "n_nulls": 50,
    "pct_nulls": 0.82
  },
  {
    "column_name": "pl_bmasse",
    "n_rows": 6087,
    "n_nulls": 31,
    "pct_nulls": 0.51
  },
  {
    "column_name": "pl_eqt",
    "n_rows": 6087,
    "n_nulls": 1539,
    "pct_nulls": 25.28
  },
  {
    "column_name": "sy_dist",
    "n_rows": 6087,
    "n_nulls": 27,
    "pct_nulls": 0.44
  },
  {
    "column_name": "ra",
    "n_rows": 6087,
    "n_nulls": 0,
    "pct_nulls": 0.0
  },
  {
    "column_name": "st_teff",
    "n_rows": 6087,
    "n_nulls": 280,
    "pct_nulls": 4.6
  },
  {
    "column_name": "st_mass",
    "n_rows": 6087,
    "n_nulls": 7,
    "pct_nulls": 0.11
  }
]
```

## TU TURNO 2 — Check de rango (`disc_year`)

```json
[
  {
    "out_of_range_rows": 0,
    "min_disc_year": 1992,
    "max_disc_year": 2026
  }
]
```

Interpretación: El rango observado de años se mantiene dentro de lo esperado para el contrato [1980, 2026]. Esto reduce riesgo de registros mal tipados en particiones temporales.

## TU TURNO 3 — quality_w03a exportado

- Archivo: `artifacts/quality_w03a_20260223.csv`

```json
[
  {
    "check_name": "nulls_pl_name",
    "metric_value": 0,
    "threshold": 0,
    "status": "PASS"
  },
  {
    "check_name": "nulls_hostname",
    "metric_value": 0,
    "threshold": 0,
    "status": "PASS"
  },
  {
    "check_name": "disc_year_out_of_range",
    "metric_value": 0,
    "threshold": 0,
    "status": "PASS"
  }
]
```


## Reflexión (bitácora)
- El check que más sorprendió fue `pl_eqt` (25.28% de nulos): no rompe pipelines base, pero sí afecta análisis térmicos específicos.
- Si `pl_name` o `hostname` tuvieran muchos nulos/duplicados, en W02B los JOINs inflarían o perderían filas, sesgando agregaciones por método y por sistema.
