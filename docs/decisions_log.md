# Decisions Log


- Fecha: 2026-02-18
- Decisión: Guardar el SHA-256 y dimensiones del CSV raw en `artifacts/` por cada ejecución de W01B.
- Razón: Garantizar trazabilidad y detectar cambios silenciosos del dato.
- Evidencia: `artifacts/w01b_raw_evidence_20260218_073442.json` con `n_rows=6087` y `n_cols=16`.
---

- Fecha: 2026-02-18
- Decisión: En W02 usar validaciones explícitas de completitud (`COUNT(*)` vs `COUNT(col)`) antes de interpretar resultados científicos.
- Razón: Evitar conclusiones sesgadas por nulos silenciosos en atributos clave.
- Evidencia: `docs/w02a_sql_practice.md`, sección 5.
---

- Fecha: 2026-02-20
- Decisión: Validar cardinalidad (`COUNT(*)` antes/después del JOIN y chequeo de llaves duplicadas) antes de promover una tabla como dimensión.
- Razón: Evitar inflación silenciosa de filas al unir facts con dimensiones mal construidas.
- Evidencia: `docs/w03_sql_practice.md` (análisis `dim_host_bad`) y `docs/w03_join_case.md`.
---

- Fecha: 2026-02-23
- Decisión: Para W04A seleccioné 12 columnas que cubren identificación, temporalidad, orbitales y parámetros estelares para el control de nulos.
- Razón: Esta combinación captura los campos más usados en agregaciones y JOINs de W02–W04 sin inflar el costo de chequeo.
- Evidencia: `docs/w03a_quality_report.md` (tabla de nulos en 12 columnas).
---

- Fecha: 2026-02-23
- Decisión: En Silver apliqué reglas mínimas (`pl_name`/`hostname` no nulos, rango de `disc_year`, límites físicos básicos en `pl_rade` y `pl_bmasse`) antes de construir fact y dimensiones.
- Razón: Evitar inconsistencias tempranas y asegurar JOINs sanos (`n_fact ≈ n_join`).
- Evidencia: `docs/w03b_silver_report.md` y `docs/data_contract_silver_v1.json`.
---

- Fecha: 2026-02-23
- Decisión: Reescribí consultas de performance para filtrar por `disc_year` antes de agrupar y evitar columnas innecesarias en la proyección.
- Razón: Reducir cardinalidad de entrada al `GROUP BY` y minimizar costo de scan en analítica.
- Evidencia: `docs/w04a_perf_report.md` (EXPLAIN Q1/Q2) y `artifacts/w04a_explain_q1.txt`.
---
