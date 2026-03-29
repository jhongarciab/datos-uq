# W06B — Run log

Fecha: 2026-03-29

## Comando
```bash
python3 src/w06b_runner_sqlite.py
```

## STDOUT (run 1)
```text
raw_ps rows=6087
silver: 0.0038s
dims: 0.0202s
gold: 0.0001s
export: 0.0168s
```

## STDOUT (run 2)
```text
raw_ps rows=6087
silver: 0.004s
dims: 0.0194s
gold: 0.0001s
export: 0.0154s
```

## Interpretación
- La etapa más lenta en ambas corridas fue **`dims`**.
- Run 1: `dims = 0.0202s`.
- Run 2: `dims = 0.0194s`.
- `export` fue la segunda etapa más costosa (`0.0168s` y `0.0154s`).
- `gold` fue despreciable en tiempo (`0.0001s` en ambas corridas).

## Evidencia adicional
- `silver_planet = 6081`
- `dim_host_sk = 4537`
- `fact_planet_sk = 6081`
- Artifacts generados:
  - `artifacts/w06b_run_report.json`
  - `artifacts/w06b_stage_timings.csv`

## Comparación entre corridas
La segunda corrida fue ligeramente más rápida (`0.0880s` vs `0.2107s` total). La diferencia es consistente con calentamiento de caché del sistema de archivos, reuso del archivo SQLite ya creado y menor costo de arranque al repetir el mismo flujo sobre el mismo dataset.
