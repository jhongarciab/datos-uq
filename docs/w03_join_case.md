# W03 — Caso real de JOIN malo

## Caso
Al unir `fact_planet_raw` con `dim_host_bad` por `hostname`, el resultado se multiplicó por violación de cardinalidad (la supuesta dimensión tenía múltiples filas por llave).

## Evidencia (conteos)
- `n_fact`: 6087
- `n_join_bad`: 10743
- `n_join_good`: 6087
- `n_join_fixed`: 6087

## Diagnóstico
La clave `hostname` **no era única** en `dim_host_bad`.

## Fix aplicado
Antes del JOIN se deduplicó la dimensión:

```sql
WITH dim_host_fixed AS (
  SELECT DISTINCT hostname
  FROM dim_host_bad
)
SELECT COUNT(*)
FROM fact_planet_raw f
JOIN dim_host_fixed h
  ON f.hostname = h.hostname;
```

Resultado: se recupera cardinalidad correcta (`n_join_fixed = n_fact`).
