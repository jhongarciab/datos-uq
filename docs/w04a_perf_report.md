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

### EXPLAIN (Q1)
```text
physical_plan | 
┌───────────────────────────┐
│          ORDER_BY         │
│    ────────────────────   │
│     count_star() DESC     │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│       HASH_GROUP_BY       │
│    ────────────────────   │
│         Groups: #0        │
│                           │
│        Aggregates:        │
│        count_star()       │
│                           │
│        ~2,094 rows        │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│      discoverymethod      │
│                           │
│        ~2,311 rows        │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             #0            │
│                           │
│        ~2,311 rows        │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│           FILTER          │
│    ────────────────────   │
│    (disc_year >= 2015)    │
│                           │
│        ~2,311 rows        │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│       READ_CSV_AUTO       │
│    ────────────────────   │
│         Function:         │
│       READ_CSV_AUTO       │
│                           │
│        Projections:       │
│      discoverymethod      │
│         disc_year         │
│                           │
│        ~11,555 rows       │
└───────────────────────────┘

```

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

### EXPLAIN (Q2)
```text
physical_plan |
┌───────────────────────────┐
│          ORDER_BY         │
│    ────────────────────   │
│     count_star() DESC     │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│       HASH_GROUP_BY       │
│    ────────────────────   │
│         Groups: #0        │
│                           │
│        Aggregates:        │
│        count_star()       │
│          avg(#1)          │
│                           │
│         ~410 rows         │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│      discoverymethod      │
│             ra            │
│                           │
│         ~418 rows         │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         HASH_JOIN         │
│    ────────────────────   │
│      Join Type: INNER     │
│                           │
│        Conditions:        ├──────────────┐
│    hostname = hostname    │              │
│                           │              │
│         ~418 rows         │              │
└─────────────┬─────────────┘              │
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│         PROJECTION        ││       HASH_GROUP_BY       │
│    ────────────────────   ││    ────────────────────   │
│             #1            ││         Groups: #0        │
│             #2            ││    Aggregates: max(#1)    │
│                           ││                           │
│        ~2,311 rows        ││        ~2,094 rows        │
└─────────────┬─────────────┘└─────────────┬─────────────┘
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│           FILTER          ││         PROJECTION        │
│    ────────────────────   ││    ────────────────────   │
│ ((disc_year >= 2015) AND  ││          hostname         │
│   (pl_name IS NOT NULL))  ││             ra            │
│                           ││                           │
│        ~2,311 rows        ││        ~2,311 rows        │
└─────────────┬─────────────┘└─────────────┬─────────────┘
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│       READ_CSV_AUTO       ││           FILTER          │
│    ────────────────────   ││    ────────────────────   │
│         Function:         ││   (hostname IS NOT NULL)  │
│       READ_CSV_AUTO       ││                           │
│                           ││                           │
│        Projections:       ││                           │
│          pl_name          ││                           │
│          hostname         ││                           │
│      discoverymethod      ││                           │
│         disc_year         ││                           │
│                           ││                           │
│        ~11,555 rows       ││        ~2,311 rows        │
└───────────────────────────┘└─────────────┬─────────────┘
                             ┌─────────────┴─────────────┐
                             │       READ_CSV_AUTO       │
                             │    ────────────────────   │
                             │         Function:         │
                             │       READ_CSV_AUTO       │
                             │                           │
                             │        Projections:       │
                             │          hostname         │
                             │             ra            │
                             │                           │
                             │        ~11,555 rows       │
                             └───────────────────────────┘

```

## Conclusiones
1) El costo principal está en el **SCAN** inicial sobre `raw_ps`: aunque el filtro de año ayuda, la lectura base sigue siendo el paso dominante. Mejora directa: proyectar menos columnas y materializar una tabla silver compacta para consultas repetidas.
2) En la consulta con JOIN, la cardinalidad se mantiene controlada porque `dim_host` se fuerza a una fila por `hostname` (`GROUP BY hostname`). Para bajar costo, conviene filtrar por `disc_year` antes del JOIN y evitar columnas que no se usan en el resultado.

## EXPLAIN ANALYZE (Q1)
```text
analyzed_plan | 
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││    Query Profiling Information    ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
EXPLAIN ANALYZE  SELECT discoverymethod, COUNT(*) AS n_planets FROM raw_ps WHERE disc_year >= 2015 GROUP BY discoverymethod ORDER BY n_planets DESC; 
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││              Total Time: 0.0303s             ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│           0 rows          │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│          ORDER_BY         │
│    ────────────────────   │
│     count_star() DESC     │
│                           │
│          11 rows          │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│       HASH_GROUP_BY       │
│    ────────────────────   │
│         Groups: #0        │
│                           │
│        Aggregates:        │
│        count_star()       │
│                           │
│          11 rows          │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│      discoverymethod      │
│                           │
│         4,307 rows        │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             #0            │
│                           │
│         4,307 rows        │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│           FILTER          │
│    ────────────────────   │
│    (disc_year >= 2015)    │
│                           │
│         4,307 rows        │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         TABLE_SCAN        │
│    ────────────────────   │
│         Function:         │
│       READ_CSV_AUTO       │
│                           │
│        Projections:       │
│      discoverymethod      │
│         disc_year         │
│                           │
│    Total Files Read: 1    │
│                           │
│         6,087 rows        │
│          (0.00s)          │
└───────────────────────────┘

```

## Reflexión (bitácora)
- Lo más difícil de interpretar fue mapear rápidamente dónde termina el SCAN y empieza el costo real de agregación.
- Si el dataset crece 100×, normalmente empeora primero el **SCAN** (I/O y cardinalidad de entrada), y en segundo lugar el `GROUP BY` por el volumen que debe agregar.
