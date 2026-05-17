# W09 — Quality gates

Fecha: 2026-05-17

Se materializó la tabla `quality_events(ts_utc, check_name, status, metric_value, details)` y se cargaron 4 checks calculados sobre `silver_planet_v3`.

## Resultado de quality gates
```json
[
  {
    "check_name": "disc_year_bad_rows",
    "status": "PASS",
    "metric_value": 1.0,
    "details": "Se tolera 1 fila mala para reflejar el único disc_year nulo del dataset"
  },
  {
    "check_name": "discoverymethod_canon_nulls",
    "status": "PASS",
    "metric_value": 0.0,
    "details": "discoverymethod_canon debe resolverse por synonyms o fallback"
  },
  {
    "check_name": "hostname_canon_nulls",
    "status": "PASS",
    "metric_value": 0.0,
    "details": "hostname_canon debe quedar completo tras LOWER/TRIM"
  },
  {
    "check_name": "method_fallback_rows",
    "status": "PASS",
    "metric_value": 0.0,
    "details": "Con synonyms completos no deberían quedar filas apoyadas solo en fallback"
  }
]
```

## Lectura rápida de cada gate
- `hostname_canon_nulls = 0`: la canonización de hostname quedó completa.
- `discoverymethod_canon_nulls = 0`: no quedaron métodos sin resolver.
- `disc_year_bad_rows = 1`: hay una fila problemática, pero coincide con el único valor faltante ya observado en el historial del proyecto.
- `method_fallback_rows = 0`: la tabla `method_synonyms` cubrió por completo los métodos presentes; no hizo falta depender del fallback en este dataset.

## Umbrales usados
- `hostname_canon_nulls <= 0`
- `discoverymethod_canon_nulls <= 0`
- `disc_year_bad_rows <= 1`
- `method_fallback_rows <= 0`

## Conclusión
Los cuatro quality gates pasaron. El punto más delicado sigue siendo `disc_year`, no porque haya valores fuera de rango, sino porque existe un registro sin año y por eso conviene mantener la bandera `disc_year_bad` en la capa silver.

## Artefactos
- `artifacts/w09_quality_events.csv`
- `artifacts/w09_evidence.json`
- `artifacts/w09_disc_era_counts.csv`
