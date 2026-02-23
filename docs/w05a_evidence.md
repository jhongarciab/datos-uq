# W05A — Evidencia PK/FK y checks

Fecha: 2026-03-03

## 1) Conteo de unicidad en `dim_host_sk`
```sql
SELECT COUNT(*) , COUNT(DISTINCT hostname)
FROM dim_host_sk;
```
```json
[
  {
    "n_rows": 4537,
    "n_keys": 4537
  }
]
```

## 2) Orphan rows en `fact_planet_sk`
```sql
SELECT COUNT(*) AS orphan_rows
FROM fact_planet_sk f
LEFT JOIN dim_host_sk d ON f.host_id = d.host_id
WHERE d.host_id IS NULL;
```
```json
[
  {
    "orphan_rows": 0
  }
]
```
