# W04A — Performance report

Fecha: 2026-02-27

## Consulta 1 (agregación con filtro)
```sql
SELECT discoverymethod, COUNT(*) AS n_planets
FROM raw_ps
WHERE disc_year >= 2015
GROUP BY discoverymethod
ORDER BY n_planets DESC;
```

### Nota sobre engine
Este repo estandariza los runners en **SQLite (stdlib)** usando la BD local:

- `data/exoplanets_w06b.sqlite`

Por eso, en lugar de `EXPLAIN`/`EXPLAIN ANALYZE` de DuckDB, el entregable reproduce:
- el **resultado** de la consulta (en JSON)
- un **timing** simple (segundos) medido desde Python

(El plan físico específico de DuckDB no se reproduce aquí.)

## Consulta 2 (JOIN + agregación)
```sql
WITH dim_host AS (
  SELECT hostname, MAX(ra) AS ra
  FROM raw_ps
  WHERE hostname IS NOT NULL
  GROUP BY hostname
), fact_planet AS (
  SELECT pl_name, hostname, discoverymethod, disc_year, pl_rade
  FROM raw_ps
  WHERE pl_name IS NOT NULL
)
SELECT f.discoverymethod,
       COUNT(*) AS n_planets,
       AVG(h.ra) AS avg_ra
FROM fact_planet f
JOIN dim_host h
  ON f.hostname = h.hostname
WHERE f.disc_year >= 2015
GROUP BY f.discoverymethod
ORDER BY n_planets DESC;
```

### Nota (Q2)
De nuevo: el plan físico de DuckDB (`READ_CSV_AUTO`, `HASH_JOIN`, etc.) no aplica en SQLite.
En este entregable se reporta el **resultado** y un **timing** medido desde Python.

## Conclusiones
1) El costo principal está en el **SCAN** inicial sobre `raw_ps`: aunque el filtro de año ayuda, la lectura base sigue siendo el paso dominante. Mejora directa: proyectar menos columnas y materializar una tabla silver compacta para consultas repetidas.
2) En la consulta con JOIN, la cardinalidad se mantiene controlada porque `dim_host` se fuerza a una fila por `hostname` (`GROUP BY hostname`). Para bajar costo, conviene filtrar por `disc_year` antes del JOIN y evitar columnas que no se usan en el resultado.

## Timing (Q1)
El runner `src/w04a_perf_report_runner.py` imprime `Timing(Q1)` medido con `time.perf_counter()`.
Ese valor reemplaza el `Total Time` que antes venía de `EXPLAIN ANALYZE` en DuckDB.

## Reflexión (bitácora)
- Lo más difícil de interpretar fue mapear rápidamente dónde termina el SCAN y empieza el costo real de agregación.
- Si el dataset crece 100×, normalmente empeora primero el **SCAN** (I/O y cardinalidad de entrada), y en segundo lugar el `GROUP BY` por el volumen que debe agregar.
