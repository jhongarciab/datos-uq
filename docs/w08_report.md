# W08 — Report

Fecha: 2026-05-17

## Parte A — Limpieza Raw→Silver v2

Se construyó `silver_planet_v2` en SQLite a partir de `raw_ps`, agregando tres transformaciones explícitas:
- `hostname_clean = LOWER(TRIM(hostname))`
- `discoverymethod_clean` vía `method_map` canónico (11 mapeos) con fallback normalizado
- `disc_era` por década de descubrimiento

### Evidencia mínima
- `raw_ps.n_rows = 6087`
- `silver_planet_v2.n_rows = 6087`
- `hostname_clean` nulo: `0`

Esto muestra que la limpieza normaliza texto sin perder filas del dataset.

## `method_map` canónico
Se versionó una tabla `method_map` con los métodos observados en el dataset, por ejemplo:
- `Transit -> transit`
- `Radial Velocity -> radial_velocity`
- `Microlensing -> microlensing`
- `Imaging -> imaging`
- `Transit Timing Variations -> transit_timing_variations`
- `Eclipse Timing Variations -> eclipse_timing_variations`

La evidencia completa quedó en `artifacts/w08_evidence.json`.

## Métodos canónicos más frecuentes
Top 10 en `silver_planet_v2`:

```json
[
  {"discoverymethod_clean": "transit", "n": 4488},
  {"discoverymethod_clean": "radial_velocity", "n": 1161},
  {"discoverymethod_clean": "microlensing", "n": 265},
  {"discoverymethod_clean": "imaging", "n": 91},
  {"discoverymethod_clean": "transit_timing_variations", "n": 39},
  {"discoverymethod_clean": "eclipse_timing_variations", "n": 17},
  {"discoverymethod_clean": "orbital_brightness_modulation", "n": 9},
  {"discoverymethod_clean": "pulsar_timing", "n": 8},
  {"discoverymethod_clean": "astrometry", "n": 6},
  {"discoverymethod_clean": "pulsation_timing_variations", "n": 2}
]
```

CSV exportado: `artifacts/w08_method_counts.csv`.

## Distribución por década (`disc_era`)
```json
[
  {"disc_era": "1990s", "n": 30},
  {"disc_era": "2000s", "n": 380},
  {"disc_era": "2010s", "n": 3683},
  {"disc_era": "2020s", "n": 1993}
]
```

Interpretación breve: el mayor volumen de descubrimientos quedó concentrado en 2010s y 2020s, consistente con la expansión observacional reciente y el predominio del método de tránsito.

## Parte B — Many-to-Many (toy schema)
Se construyó el esquema pedido con PK/FK explícitas:
- `planet_demo(planet_id PRIMARY KEY, name NOT NULL)`
- `method_demo(method_id PRIMARY KEY, method_name UNIQUE NOT NULL)`
- `planet_method_demo(planet_id, method_id, PRIMARY KEY (planet_id, method_id), FK...)`

DDL exportado: `artifacts/w08_many_to_many_ddl.sql`.

### Q1 — ¿Cuántos planetas hay por método?
```json
[
  {"method_name": "radial_velocity", "n_planets": 2},
  {"method_name": "transit", "n_planets": 2},
  {"method_name": "imaging", "n_planets": 1}
]
```

### Q2 — ¿Cuántos métodos tiene cada planeta?
```json
[
  {"name": "Kepler-10 b", "n_methods": 2},
  {"name": "HR 8799 b", "n_methods": 1},
  {"name": "Proxima Cen b", "n_methods": 1},
  {"name": "TRAPPIST-1 e", "n_methods": 1}
]
```

Interpretación breve: `Kepler-10 b` muestra la relación M:N requerida porque quedó asociada a dos métodos, mientras que el resto mantiene cardinalidad 1:N desde el planeta hacia la tabla puente.

## Evidencia extra requerida (PK/FK + duplicados)
Chequeo `HAVING COUNT(*) > 1` sobre la link table:
- resultado: **0 filas**

Pruebas de integridad ejecutadas:
- duplicado en `(planet_id, method_id)` bloqueado con: `UNIQUE constraint failed: planet_method_demo.planet_id, planet_method_demo.method_id`
- FK inválida bloqueada con: `FOREIGN KEY constraint failed`

Esto confirma que la PK compuesta y las FKs sí están activas y protegen la estructura M:N.

## Artefactos generados
- `artifacts/w08_evidence.json`
- `artifacts/w08_method_counts.csv`
- `artifacts/w08_planets_per_method.csv`
- `artifacts/w08_methods_per_planet.csv`
- `artifacts/w08_many_to_many_ddl.sql`

## Reproducibilidad
Runner:
- `python3 -m src.w08_report_runner`
