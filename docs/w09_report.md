# W09 — Report

Fecha: 2026-05-17

## Parte A — Limpieza avanzada

Se construyó `silver_planet_v3` en SQLite a partir de `raw_ps`, agregando cuatro campos operativos pedidos en el assignment:
- `hostname_canon`
- `discoverymethod_canon`
- `disc_year_int`
- `disc_year_bad`

Además se persistió `method_used_fallback` para distinguir cuándo el método quedó resuelto por la tabla de sinónimos y cuándo por fallback normalizado.

## `method_synonyms(raw_norm, canonical)`
Se creó una tabla con 11 filas canónicas, por ejemplo:
- `transit -> transit`
- `radial velocity -> radial_velocity`
- `transit timing variations -> transit_timing_variations`
- `eclipse timing variations -> eclipse_timing_variations`
- `orbital brightness modulation -> orbital_brightness_modulation`
- `disk kinematics -> disk_kinematics`

La idea fue dejar explícita la canonización en tabla, no embebida como `CASE` largo en cada consulta.

## Evidencia mínima de `silver_planet_v3`
- `n_rows = 6087`
- `disc_year_bad = 1`

Interpretación: la transformación no perdió filas y solo marcó una fila problemática en `disc_year`, consistente con el historial del dataset en entregables previos.

## Métodos canónicos más frecuentes
```json
[
  {"discoverymethod_canon": "transit", "n": 4488},
  {"discoverymethod_canon": "radial_velocity", "n": 1161},
  {"discoverymethod_canon": "microlensing", "n": 265},
  {"discoverymethod_canon": "imaging", "n": 91},
  {"discoverymethod_canon": "transit_timing_variations", "n": 39},
  {"discoverymethod_canon": "eclipse_timing_variations", "n": 17},
  {"discoverymethod_canon": "orbital_brightness_modulation", "n": 9},
  {"discoverymethod_canon": "pulsar_timing", "n": 8},
  {"discoverymethod_canon": "astrometry", "n": 6},
  {"discoverymethod_canon": "pulsation_timing_variations", "n": 2}
]
```

CSV exportado: `artifacts/w09_method_canon_counts.csv`.

## Distribución temporal por `disc_era`
```json
[
  {"disc_era": "1990s", "n": 30},
  {"disc_era": "2000s", "n": 380},
  {"disc_era": "2010s", "n": 3683},
  {"disc_era": "2020s", "n": 1993}
]
```

Interpretación breve: la señal temporal sigue dominada por 2010s–2020s, así que la partición por década sí tiene valor analítico para cortes agregados y control de cobertura histórica.

## Sobre `disc_year_bad`
La bandera se definió así:
- `1` si `disc_year_int IS NULL`
- `1` si `disc_year_int < 1980`
- `1` si `disc_year_int > año_actual`
- `0` en caso contrario

Esto deja explícito qué registros requieren revisión antes de usar `disc_year` como dimensión confiable de partición o control temporal.

## Reproducibilidad
Runner:
- `python3 -m src.w09_assignment_runner`

Artifact maestro:
- `artifacts/w09_evidence.json`
