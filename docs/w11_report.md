# W11 — Performance tuning y gold marts

Fecha: 2026-05-17

## Queries críticas del proyecto

### Query 1 — Métodos por década reciente
Objetivo: resumir cuántos planetas y qué promedios físicos aparecen por método canónico en `2010s` y `2020s`.

### Query 2 — Hosts con 3+ planetas por década reciente
Objetivo: identificar sistemas con múltiples planetas en décadas recientes y resumir su tamaño/masa promedio.

## Performance budgets
- **Q1 budget:** `0.020s`
- **Q2 budget:** `0.020s`

La idea del budget aquí no es “exprimir” el hardware, sino fijar un umbral operativo razonable para este dataset pequeño y detectar degradaciones futuras.

## Baseline con tiempos
```json
{
  "q1": {
    "baseline_seconds": 0.0037,
    "after_seconds": 0.0011
  },
  "q2": {
    "baseline_seconds": 0.0012,
    "after_seconds": 0.0009
  }
}
```

Ambas queries quedaron por debajo del budget después de la reescritura.

## EXPLAIN ANALYZE guardado
Artefactos:
- `artifacts/w11_q1_explain_before.txt`
- `artifacts/w11_q1_explain_after.txt`
- `artifacts/w11_q2_explain_before.txt`
- `artifacts/w11_q2_explain_after.txt`

## Anti-patrones identificados
1. **Reagrupar desde `silver_planet_v3` en cada consulta crítica** aunque el patrón analítico se repita muchas veces.
2. **Repetir filtros + agregaciones pesadas en caliente** para consumo frecuente, en lugar de publicar marts ya agregadas.

Estos anti-patrones no rompen exactitud, pero sí empeoran costo, latencia y estabilidad de las consultas de consumo.

## Reescrituras justificadas
1. **`gold_mart_method_era`** materializa la agregación por `disc_era + discoverymethod_canon`.
2. **`gold_mart_host_era`** materializa la agregación por `disc_era + hostname_canon`, y luego filtra `n_planets >= 3` sobre la mart en vez de recalcular el `GROUP BY` completo.

## Gold mart propuesto y construido
Se construyeron dos marts:
- `gold_mart_method_era`
- `gold_mart_host_era`

Exports:
- `artifacts/w11_gold_mart_method_era.csv`
- `artifacts/w11_gold_mart_host_era.csv`

## Validación de resultados
Se validó igualdad lógica antes/después con hash SHA-256 de los resultados serializados.

```json
{
  "q1_result_match": true,
  "q2_result_match": true
}
```

Esto asegura que la optimización cambió el plan de ejecución, no el resultado analítico.

## Comparación antes/después
```json
{
  "q1": {
    "before": 0.0037,
    "after": 0.0011,
    "improvement_factor": 3.36
  },
  "q2": {
    "before": 0.0012,
    "after": 0.0009,
    "improvement_factor": 1.33
  }
}
```

Q1 mejora más porque la mart elimina una agregación repetida más costosa. Q2 también mejora, aunque menos, porque el dataset ya es pequeño y el baseline no era malo.

## Decisión técnica final
Para consultas analíticas recurrentes sobre décadas recientes, conviene **publicar marts agregadas** y consumirlas directamente, en lugar de recalcular agregaciones desde silver en cada ejecución. En este repo la estrategia quedó justificada porque:
- preserva exactitud,
- mejora tiempo,
- deja presupuestos y evidencia reproducible,
- reduce riesgo de degradación silenciosa al crecer el flujo.

## Reproducibilidad
Runner:
- `python3 -m src.w11_perf_runner`

Artifact maestro:
- `artifacts/w11_evidence.json`
