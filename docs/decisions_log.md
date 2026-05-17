# Decisions Log

### W01
- Fecha: 2026-02-18
- Decisión: Guardar el SHA-256 y dimensiones del CSV raw en `artifacts/` por cada ejecución de W01B.
- Razón: Garantizar trazabilidad y detectar cambios silenciosos del dato.
- Evidencia: `artifacts/w01b_raw_evidence_20260218_073442.json` con `n_rows=6087` y `n_cols=16`.
---

### W02
- Fecha: 2026-02-18
- Decisión: En W02 usar validaciones explícitas de completitud (`COUNT(*)` vs `COUNT(col)`) antes de interpretar resultados científicos.
- Razón: Evitar conclusiones sesgadas por nulos silenciosos en atributos clave.
- Evidencia: `docs/w02a_sql_practice.md`, sección 5.
---

### W03
- Fecha: 2026-02-20
- Decisión: Validar cardinalidad (`COUNT(*)` antes/después del JOIN y chequeo de llaves duplicadas) antes de promover una tabla como dimensión.
- Razón: Evitar inflación silenciosa de filas al unir facts con dimensiones mal construidas.
- Evidencia: `docs/w03_sql_practice.md` (análisis `dim_host_bad`) y `docs/w03_join_case.md`.
---

### W04
- Fecha: 2026-02-23
- Decisión: Para W04A seleccioné 12 columnas que cubren identificación, temporalidad, orbitales y parámetros estelares para el control de nulos.
- Razón: Esta combinación captura los campos más usados en agregaciones y JOINs de W02–W04 sin inflar el costo de chequeo.
- Evidencia: `docs/w03a_quality_report.md` (tabla de nulos en 12 columnas).
- Decisión: En Silver apliqué reglas mínimas (`pl_name`/`hostname` no nulos, rango de `disc_year`, límites físicos básicos en `pl_rade` y `pl_bmasse`) antes de construir fact y dimensiones.
- Razón: Evitar inconsistencias tempranas y asegurar JOINs sanos (`n_fact ≈ n_join`).
- Evidencia: `docs/w03b_silver_report.md` y `docs/data_contract_silver_v1.json`.
---

### W04A
- Fecha: 2026-02-23
- Decisión: Reescribí consultas de performance para filtrar por `disc_year` antes de agrupar y evitar columnas innecesarias en la proyección.
- Razón: Reducir cardinalidad de entrada al `GROUP BY` y minimizar costo de scan en analítica.
- Evidencia: `docs/w04a_perf_report.md` (EXPLAIN Q1/Q2) y `artifacts/w04a_explain_q1.txt`.
---

### W05
- Fecha: 2026-02-23
- Decisión: Implementar `host_id` como surrogate key en `dim_host_sk` y mapear `fact_planet_sk` por FK lógica (`host_id`).
- Razón: Estabilizar joins, desacoplar fact del texto de `hostname` y facilitar evolución del modelo.
- Evidencia: `docs/w05a_evidence.md` (unicidad y orphan_rows=0).
- Decisión: Publicar dos salidas Gold (`gold_by_discoverymethod` y `gold_by_host`) como productos mínimos de consumo analítico.
- Razón: Cubrir vistas complementarias (método de descubrimiento y arquitectura por sistema) para análisis rápido y reproducible.
- Evidencia: `docs/w05b_gold_report.md` + CSV en `artifacts/`.---

### W06B
- Fecha: 2026-03-29
- Decisión: Mantener un runner secuencial en cuatro etapas (`silver`, `dims`, `gold`, `export`) y usar como umbral operativo que la etapa `dims` permanezca por debajo de `0.03s` en este dataset.
- Razón: `dims` concentra el mayor costo del flujo porque reconstruye dimensiones, facts y la tabla con surrogate key; fijar un umbral simple permite detectar rápido degradaciones de performance sin complicar el entregable.
- Evidencia: `artifacts/w06b_stage_timings.csv` (run1 `dims=0.0202s`, run2 `dims=0.0194s`) y `docs/w06b_run_log.md`.

### W08
- Fecha: 2026-05-17
- Decisión: Canonizar `discoverymethod` mediante una tabla `method_map` explícita y persistir además una columna `disc_era` en `silver_planet_v2`.
- Razón: La tabla de mapeo evita depender de normalizaciones implícitas dispersas en queries, mientras `disc_era` deja lista una segmentación temporal reproducible para análisis posteriores.
- Evidencia: `docs/w08_report.md`, `artifacts/w08_evidence.json` y `artifacts/w08_method_counts.csv`.
- Decisión: Modelar el ejemplo many-to-many con tabla puente y restricciones reales (PK compuesta + FK activadas), no solo como diagrama.
- Razón: El entregable pide evidencia de integridad; ejecutar inserciones inválidas y el chequeo `HAVING COUNT(*)>1` demuestra que la cardinalidad queda protegida de verdad.
- Evidencia: `artifacts/w08_many_to_many_ddl.sql` y `artifacts/w08_evidence.json`.

### W09
- Fecha: 2026-05-17
- Decisión: Separar la canonización avanzada de `discoverymethod` en una tabla `method_synonyms(raw_norm, canonical)` y propagar el resultado como `discoverymethod_canon` en `silver_planet_v3`.
- Razón: Esto vuelve auditable la limpieza, permite extender sinónimos sin reescribir SQL analítico y deja visible cuándo una fila cae en fallback.
- Evidencia: `docs/w09_report.md`, `artifacts/w09_evidence.json` y `artifacts/w09_method_canon_counts.csv`.
- Decisión: Materializar `quality_events` como tabla persistente con umbrales explícitos en vez de dejar checks sueltos en notebooks.
- Razón: Un registro tabular de gates facilita reruns, comparación entre corridas y automatización posterior de alertas o validaciones en pipeline.
- Evidencia: `docs/w09_quality.md` y `artifacts/w09_quality_events.csv`.
