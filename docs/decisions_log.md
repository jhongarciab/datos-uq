# Decisions Log

- Fecha: 2026-02-18
- Decisión: Guardar el SHA-256 y dimensiones del CSV raw en `artifacts/` por cada ejecución de W01B.
- Razón: Garantizar trazabilidad y detectar cambios silenciosos del dato.
- Evidencia: `artifacts/w01b_raw_evidence_20260218_073442.json` con `n_rows=6087` y `n_cols=16`.

- Fecha: 2026-02-18
- Decisión: En W02 usar validaciones explícitas de completitud (`COUNT(*)` vs `COUNT(col)`) antes de interpretar resultados científicos.
- Razón: Evitar conclusiones sesgadas por nulos silenciosos en atributos clave.
- Evidencia: `docs/w02a_sql_practice.md`, sección 5.
