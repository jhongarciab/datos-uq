# W10 — Partitioning and pruning report

Fecha: 2026-05-17

## Decisión de partición
Se particionó el dataset por **`disc_era`** y se escribió como Parquet particionado con DuckDB en:
- `data/partitioned/w10_disc_era/`

La decisión fue usar `disc_era` porque:
1. es una dimensión temporal natural para este proyecto,
2. genera pocas particiones manejables,
3. tiene suficiente volumen en las décadas principales para evitar fragmentación extrema,
4. permite demostrar pruning con un filtro simple y legible.

## Evidencia de particionamiento
Se generaron **4 archivos Parquet**, uno por partición válida:
- `disc_era=1990s/data_0.parquet`
- `disc_era=2000s/data_0.parquet`
- `disc_era=2010s/data_0.parquet`
- `disc_era=2020s/data_0.parquet`

Número total de archivos: **4**.

## Resumen por partición
```json
[
  {"disc_era": "1990s", "n_rows": 30},
  {"disc_era": "2000s", "n_rows": 380},
  {"disc_era": "2010s", "n_rows": 3683},
  {"disc_era": "2020s", "n_rows": 1993}
]
```

CSV exportado: `artifacts/w10_partition_summary.csv`.

## Evidencia de pruning
Filtro usado:
- `disc_era = '2010s'`

Archivo requerido:
- `artifacts/w10b_explain_analyze_pruning.txt`

Hallazgo clave del `EXPLAIN ANALYZE`:
- `File Filters: (disc_era = '2010s')`
- `Scanning Files: 1/4`
- `Total Files Read: 1`

Esto muestra pruning real: DuckDB evitó leer 3 de los 4 archivos porque el filtro coincide con la columna de partición.

## Texto del número de archivos
- Total de archivos en el dataset particionado: **4**
- Archivos leídos por el filtro de pruning: **1**

## ¿Por qué `disc_era` sí o no?
**Sí la usaría** en este caso porque produce pocas carpetas, fácil interpretación y filtros muy naturales para análisis históricos. No la usaría si el caso de uso principal no filtrara por tiempo o si necesitara granularidad mucho más fina que década.

## ¿Qué otra columna evaluaría?
Evaluaría `discoverymethod_canon`.

Ventaja:
- también tiene valor analítico directo.

Desventaja:
- tiene más categorías y bastante sesgo de distribución (`transit` domina), así que aumenta el riesgo de particiones muy desbalanceadas y archivos pequeños en métodos raros.

## Riesgo de small files encontrado
Sí existe riesgo potencial, aunque en esta corrida fue moderado porque solo salieron 4 archivos. El problema aparece sobre todo en particiones chicas:
- `1990s` → 30 filas
- `2000s` → 380 filas

Si el pipeline escribiera muchas veces o con particiones más finas (por año, método+año, etc.), se multiplicarían archivos diminutos y empeoraría el diseño.

## Reflexión breve
Particionar ayuda cuando la columna coincide con filtros frecuentes y reduce el set físico a leer. Empeora el diseño cuando se particiona por columnas de alta cardinalidad, muy sesgadas o poco usadas en filtros, porque aumenta complejidad y small files sin beneficio real.

## ¿Cuándo particionar ayuda?
- cuando hay consultas repetidas por una dimensión de filtro estable,
- cuando el pruning reduce archivos de forma visible,
- cuando cada partición conserva suficiente volumen.

## ¿Cuándo particionar empeora el diseño?
- cuando la cardinalidad es alta,
- cuando las particiones quedan muy desbalanceadas,
- cuando aparecen muchos archivos pequeños,
- cuando la mayoría de consultas no filtra por la columna de partición.

## Reproducibilidad
Runner:
- `python3 -m src.w10_partition_runner`

Artefactos principales:
- `artifacts/w10_evidence.json`
- `artifacts/w10_file_inventory.csv`
- `artifacts/w10_partition_summary.csv`
- `artifacts/w10b_explain_analyze_pruning.txt`
