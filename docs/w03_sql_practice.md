# W03 — SQL esencial II (JOINs + CTEs)

Fecha: 2026-02-18

## Análisis de `dim_host_bad`

```json
{
  "n_fact": 6087,
  "n_join_good": 6087,
  "n_join_bad": 10743,
  "n_join_fixed": 6087
}
```

Explicación: `n_join_good` coincide con `n_fact`, lo que indica cardinalidad many-to-one correcta al unir contra `dim_host_ra` (1 fila por `hostname`). En cambio, `n_join_bad` se infla porque `dim_host_bad` repite `hostname` y multiplica filas en el JOIN. Al deduplicar (`dim_host_fixed`), `n_join_fixed` vuelve a coincidir con el conteo esperado.

## TODO 1 — LEFT JOIN y no-match

```sql
SELECT COUNT(*) AS n_no_match
FROM fact_planet_raw f LEFT JOIN dim_host_ra h ON f.hostname=h.hostname
WHERE h.hostname IS NULL
```

```json
[
  {
    "n_no_match": 0
  }
]
```

## TODO 2 — CTE + ranking (método #1 por año)

```sql
WITH counts AS (
  SELECT disc_year, discoverymethod, COUNT(*) AS n
  FROM fact_planet_raw
  WHERE disc_year IS NOT NULL AND discoverymethod IS NOT NULL
  GROUP BY disc_year, discoverymethod
), ranked AS (
  SELECT disc_year, discoverymethod, n,
         ROW_NUMBER() OVER (PARTITION BY disc_year ORDER BY n DESC, discoverymethod ASC) AS rn
  FROM counts
)
SELECT disc_year, discoverymethod, n
FROM ranked WHERE rn=1
ORDER BY disc_year DESC
LIMIT 20
```

```json
[
  {
    "disc_year": 2026,
    "discoverymethod": "Radial Velocity",
    "n": 3
  },
  {
    "disc_year": 2025,
    "discoverymethod": "Transit",
    "n": 142
  },
  {
    "disc_year": 2024,
    "discoverymethod": "Transit",
    "n": 188
  },
  {
    "disc_year": 2023,
    "discoverymethod": "Transit",
    "n": 226
  },
  {
    "disc_year": 2022,
    "discoverymethod": "Transit",
    "n": 191
  },
  {
    "disc_year": 2021,
    "discoverymethod": "Transit",
    "n": 447
  },
  {
    "disc_year": 2020,
    "discoverymethod": "Transit",
    "n": 166
  },
  {
    "disc_year": 2019,
    "discoverymethod": "Transit",
    "n": 107
  },
  {
    "disc_year": 2018,
    "discoverymethod": "Transit",
    "n": 242
  },
  {
    "disc_year": 2017,
    "discoverymethod": "Transit",
    "n": 87
  },
  {
    "disc_year": 2016,
    "discoverymethod": "Transit",
    "n": 1432
  },
  {
    "disc_year": 2015,
    "discoverymethod": "Transit",
    "n": 99
  },
  {
    "disc_year": 2014,
    "discoverymethod": "Transit",
    "n": 798
  },
  {
    "disc_year": 2013,
    "discoverymethod": "Transit",
    "n": 80
  },
  {
    "disc_year": 2012,
    "discoverymethod": "Transit",
    "n": 93
  },
  {
    "disc_year": 2011,
    "discoverymethod": "Transit",
    "n": 79
  },
  {
    "disc_year": 2010,
    "discoverymethod": "Transit",
    "n": 47
  },
  {
    "disc_year": 2009,
    "discoverymethod": "Radial Velocity",
    "n": 70
  },
  {
    "disc_year": 2008,
    "discoverymethod": "Radial Velocity",
    "n": 36
  },
  {
    "disc_year": 2007,
    "discoverymethod": "Radial Velocity",
    "n": 34
  }
]
```

## TODO 3 — Validación de cardinalidad en dim_discovery

```sql
SELECT discoverymethod, disc_year, COUNT(*) AS cnt
FROM dim_discovery
GROUP BY discoverymethod, disc_year
HAVING COUNT(*)>1
ORDER BY cnt DESC
```

```json
[]
```

## TODO 4 — JOIN + agregación (promedio de RA por método)

```sql
SELECT f.discoverymethod,
       COUNT(*) AS n_planets,
       ROUND(AVG(h.ra),4) AS avg_host_ra
FROM fact_planet_raw f
JOIN dim_host_ra h ON f.hostname=h.hostname
WHERE f.discoverymethod IS NOT NULL AND h.ra IS NOT NULL
GROUP BY f.discoverymethod
ORDER BY n_planets DESC
```

```json
[
  {
    "discoverymethod": "Transit",
    "n_planets": 4488,
    "avg_host_ra": 247.0115
  },
  {
    "discoverymethod": "Radial Velocity",
    "n_planets": 1161,
    "avg_host_ra": 175.6753
  },
  {
    "discoverymethod": "Microlensing",
    "n_planets": 265,
    "avg_host_ra": 267.303
  },
  {
    "discoverymethod": "Imaging",
    "n_planets": 91,
    "avg_host_ra": 184.1132
  },
  {
    "discoverymethod": "Transit Timing Variations",
    "n_planets": 39,
    "avg_host_ra": 250.0828
  },
  {
    "discoverymethod": "Eclipse Timing Variations",
    "n_planets": 17,
    "avg_host_ra": 223.4642
  },
  {
    "discoverymethod": "Orbital Brightness Modulation",
    "n_planets": 9,
    "avg_host_ra": 292.9125
  },
  {
    "discoverymethod": "Pulsar Timing",
    "n_planets": 8,
    "avg_host_ra": 218.7431
  },
  {
    "discoverymethod": "Astrometry",
    "n_planets": 6,
    "avg_host_ra": 235.4218
  },
  {
    "discoverymethod": "Pulsation Timing Variations",
    "n_planets": 2,
    "avg_host_ra": 315.2425
  },
  {
    "discoverymethod": "Disk Kinematics",
    "n_planets": 1,
    "avg_host_ra": 167.0133
  }
]
```

## Consulta extra (JOIN)

```sql
SELECT f.disc_year, COUNT(*) AS n_planets
FROM fact_planet_raw f
JOIN dim_host_ra h ON f.hostname=h.hostname
WHERE f.disc_year IS NOT NULL
GROUP BY f.disc_year
ORDER BY n_planets DESC, f.disc_year DESC
LIMIT 10
```

```json
[
  {
    "disc_year": 2016,
    "n_planets": 1496
  },
  {
    "disc_year": 2014,
    "n_planets": 869
  },
  {
    "disc_year": 2021,
    "n_planets": 554
  },
  {
    "disc_year": 2022,
    "n_planets": 369
  },
  {
    "disc_year": 2023,
    "n_planets": 326
  },
  {
    "disc_year": 2018,
    "n_planets": 315
  },
  {
    "disc_year": 2024,
    "n_planets": 260
  },
  {
    "disc_year": 2025,
    "n_planets": 241
  },
  {
    "disc_year": 2020,
    "n_planets": 235
  },
  {
    "disc_year": 2019,
    "n_planets": 196
  }
]
```

## Consulta extra (CTE)

```sql
WITH m AS (
  SELECT discoverymethod, AVG(pl_rade) AS avg_radius
  FROM fact_planet_raw
  WHERE discoverymethod IS NOT NULL AND pl_rade IS NOT NULL
  GROUP BY discoverymethod
)
SELECT discoverymethod, ROUND(avg_radius,3) AS avg_radius
FROM m
ORDER BY avg_radius DESC
LIMIT 10
```

```json
[
  {
    "discoverymethod": "Imaging",
    "avg_radius": 15.649
  },
  {
    "discoverymethod": "Disk Kinematics",
    "avg_radius": 13.3
  },
  {
    "discoverymethod": "Eclipse Timing Variations",
    "avg_radius": 12.893
  },
  {
    "discoverymethod": "Pulsation Timing Variations",
    "avg_radius": 12.75
  },
  {
    "discoverymethod": "Astrometry",
    "avg_radius": 12.45
  },
  {
    "discoverymethod": "Microlensing",
    "avg_radius": 9.86
  },
  {
    "discoverymethod": "Radial Velocity",
    "avg_radius": 9.792
  },
  {
    "discoverymethod": "Orbital Brightness Modulation",
    "avg_radius": 9.645
  },
  {
    "discoverymethod": "Transit Timing Variations",
    "avg_radius": 6.493
  },
  {
    "discoverymethod": "Pulsar Timing",
    "avg_radius": 5.411
  }
]
```
