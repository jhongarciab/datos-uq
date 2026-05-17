# Física Computacional: Ingeniería de Datos I

### Estudiante:
- Jhon García
---

## Resumen de la evolución

W01 → Control de trazabilidad del dataset raw  
W02 → Validación explícita de completitud y nulos  
W03 → Control de cardinalidad y JOINs seguros  
W04 → Reglas mínimas Silver y control de calidad  
W04A → Performance/timing de consultas en SQLite  
W05 → Modelo dimensional + salidas Gold  
W06B → Runner secuencial con métricas por etapa, run log y comparación entre corridas  
W08 → Limpieza Raw→Silver v2 + ejemplo Many-to-Many con evidencia de PK/FK

Ver: [Decision Log](docs/decisions_log.md)

## Runners (reproducibilidad)
Ejecuta con `python3 -m ...` desde la raíz del repo:
- W01: `src.w01_runner_raw_sqlite`
- W02A: `src.w02a_sql_practice_runner`
- W03: `src.w03_sql_joins_ctes_runner`
- W04A (quality): `src.w04a_quality_report_runner`
- W04B (silver): `src.w04b_silver_report_runner`
- W04A (perf/timing): `src.w04a_perf_report_runner`
- W05A: `src.w05a_pk_fk_checks_runner`
- W05B: `src.w05b_gold_report_runner`
- W06B (pipeline): `src.w06b_runner_sqlite`
- W08: `src.w08_report_runner`

## Estructura del repositorio
```text
datos-uq/
├── artifacts/                     # Evidencia reproducible generada en cada entrega
│   ├── w01b_raw_evidence_*.json   # Hash + dimensiones del dataset raw
│   ├── quality_w03a_*.csv         # Control de nulos y calidad
│   ├── w04a_explain_q1.txt        # Análisis de performance
│   ├── gold_by_discoverymethod.csv
│   ├── gold_by_host.csv
│   ├── gold_by_method_*.csv
│   ├── w06b_run_report.json       # Reporte de ejecución del runner por etapas
│   ├── w06b_stage_timings.csv     # Tiempos por etapa y por corrida
│   ├── w08_evidence.json          # Evidencia integrada del entregable W08
│   ├── w08_method_counts.csv      # Frecuencias por método canónico
│   ├── w08_planets_per_method.csv # Respuesta Q1 del esquema M:N
│   ├── w08_methods_per_planet.csv # Respuesta Q2 del esquema M:N
│   └── w08_many_to_many_ddl.sql   # DDL con PK/FK del esquema toy
│
├── data/
│   └── raw/
│       └── pscomppars.csv         # Dataset
│
├── docs/                          # Documentación y evolución del modelo
│   ├── decisions_log.md           # Registro cronológico de decisiones
│   ├── glossary.md
│   ├── data_contract.md
│   ├── data_contract_silver_v1.json
│   ├── w01a_run.md
│   ├── w01b_checks.md
│   ├── w02a_sql_practice.md
│   ├── w03_join_case.md
│   ├── w03_sql_practice.md
│   ├── w03a_quality_report.md
│   ├── w03b_silver_report.md
│   ├── w04a_perf_report.md
│   ├── w05a_evidence.md
│   ├── w05b_gold_report.md
│   ├── w06b_run_log.md
│   └── w08_report.md
│
├── .gitignore
└── README.md     
```