# W01B — Sanity checks

## Filas totales
```sql
SELECT COUNT(*) AS n_rows FROM raw_ps;
```
Resultado:
```json
[{"n_rows": 6087}]
```

## Nulos en variables críticas
```sql
SELECT
  SUM(CASE WHEN pl_name IS NULL THEN 1 ELSE 0 END) AS null_pl_name,
  SUM(CASE WHEN disc_year IS NULL THEN 1 ELSE 0 END) AS null_disc_year,
  SUM(CASE WHEN discoverymethod IS NULL THEN 1 ELSE 0 END) AS null_discoverymethod
FROM raw_ps;
```
Resultado:
```json
[{"null_pl_name": 0, "null_disc_year": 1, "null_discoverymethod": 0}]
```

## Rango de años de descubrimiento
```sql
SELECT MIN(disc_year) AS min_disc_year, MAX(disc_year) AS max_disc_year FROM raw_ps;
```
Resultado:
```json
[{"min_disc_year": 1992, "max_disc_year": 2026}]
```

## Tarea extra: duplicados por `pl_name`
```sql
SELECT COUNT(*) AS duplicated_names
FROM (
  SELECT pl_name
  FROM raw_ps
  GROUP BY pl_name
  HAVING COUNT(*) > 1
) t;
```
Resultado:
```json
[{"duplicated_names": 0}]
```
