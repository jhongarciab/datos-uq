# Data Contract (actualizado W05)

Fecha: 2026-03-03
Versión: 1.1.0

## Datasets
- `silver_planet`
- `dim_host_sk`
- `fact_planet_sk`
- `gold_by_discoverymethod`
- `gold_by_host`

## Grain
- `dim_host_sk`: 1 fila por `hostname`
- `fact_planet_sk`: 1 fila por `pl_name`

## Keys
- `dim_host_sk`: PK lógica `host_id`, `hostname` único
- `fact_planet_sk`: PK lógica `pl_name`
- FK lógica: `fact_planet_sk.host_id -> dim_host_sk.host_id`

## Checks mínimos (con evidencia)
1. Unicidad dimensión: `COUNT(*) == COUNT(DISTINCT hostname)` en `dim_host_sk`
2. Orphans: `orphan_rows == 0` al validar `fact_planet_sk` vs `dim_host_sk`
3. Integridad básica Silver: filtros mínimos en nulos clave y rangos físicos

## Evidencias vinculadas
- `docs/w05a_evidence.md`
- `docs/w05b_gold_report.md`
- `artifacts/gold_by_discoverymethod.csv`
- `artifacts/gold_by_host.csv`
