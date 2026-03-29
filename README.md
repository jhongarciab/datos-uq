# Física Computacional: Ingeniería de Datos I

### Estudiante:
- Jhon García
---

## Resumen de la evolución

W01 → Control de trazabilidad del dataset raw  
W02 → Validación explícita de completitud y nulos  
W03 → Control de cardinalidad y JOINs seguros  
W04 → Reglas mínimas Silver y control de calidad  
W04A → Optimización de consultas (EXPLAIN y performance)  
W05 → Modelo dimensional + salidas Gold  
W06B → Runner secuencial con métricas por etapa, run log y comparación entre corridas

Ver: [Decision Log](docs/decisions_log.md)

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
│   └── w06b_stage_timings.csv     # Tiempos por etapa y por corrida
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
│   └── w06b_run_log.md
│
├── .gitignore
└── README.md     
```