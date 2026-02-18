# W02A — SQL practice (W02)

Fecha: 2026-02-18

## 1) Planetas por año (top 15)

```sql
SELECT disc_year, COUNT(*) AS n_planets FROM raw_ps WHERE disc_year IS NOT NULL GROUP BY disc_year ORDER BY n_planets DESC, disc_year DESC LIMIT 15;
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
  },
  {
    "disc_year": 2015,
    "n_planets": 155
  },
  {
    "disc_year": 2017,
    "n_planets": 152
  },
  {
    "disc_year": 2012,
    "n_planets": 139
  },
  {
    "disc_year": 2011,
    "n_planets": 135
  },
  {
    "disc_year": 2013,
    "n_planets": 128
  }
]
```

## 2) Top 10 sistemas (hostname) con más planetas

```sql
SELECT hostname, COUNT(*) AS n_planets FROM raw_ps WHERE hostname IS NOT NULL GROUP BY hostname ORDER BY n_planets DESC, hostname ASC LIMIT 10;
```

```json
[
  {
    "hostname": "KOI-351",
    "n_planets": 8
  },
  {
    "hostname": "TRAPPIST-1",
    "n_planets": 7
  },
  {
    "hostname": "HD 10180",
    "n_planets": 6
  },
  {
    "hostname": "HD 110067",
    "n_planets": 6
  },
  {
    "hostname": "HD 191939",
    "n_planets": 6
  },
  {
    "hostname": "HD 219134",
    "n_planets": 6
  },
  {
    "hostname": "HD 34445",
    "n_planets": 6
  },
  {
    "hostname": "HIP 41378",
    "n_planets": 6
  },
  {
    "hostname": "K2-138",
    "n_planets": 6
  },
  {
    "hostname": "Kepler-11",
    "n_planets": 6
  }
]
```

## 3) Fracción de nulos en pl_bmasse

```sql
SELECT ROUND(100.0*SUM(CASE WHEN pl_bmasse IS NULL THEN 1 ELSE 0 END)/COUNT(*),2) AS pct_null_pl_bmasse FROM raw_ps;
```

```json
[
  {
    "pct_null_pl_bmasse": 0.51
  }
]
```

## 4) Top 10 planetas por radio (pl_rade)

```sql
SELECT pl_name, pl_rade FROM raw_ps WHERE pl_rade IS NOT NULL ORDER BY pl_rade DESC LIMIT 10;
```

```json
[
  {
    "pl_name": "V2376 Ori b",
    "pl_rade": 87.20586985
  },
  {
    "pl_name": "HD 100546 b",
    "pl_rade": 77.3421
  },
  {
    "pl_name": "GQ Lup b",
    "pl_rade": 33.6
  },
  {
    "pl_name": "Kepler-297 d",
    "pl_rade": 32.6
  },
  {
    "pl_name": "PDS 70 b",
    "pl_rade": 30.48848
  },
  {
    "pl_name": "DH Tau b",
    "pl_rade": 30.2643
  },
  {
    "pl_name": "Kepler-1979 b",
    "pl_rade": 29.33
  },
  {
    "pl_name": "TOI-1408 b",
    "pl_rade": 25.0
  },
  {
    "pl_name": "CT Cha b",
    "pl_rade": 24.66
  },
  {
    "pl_name": "TOI-3540 A b",
    "pl_rade": 23.53885947
  }
]
```

## 5) COUNT(*) vs COUNT(disc_year) por método

```sql
SELECT discoverymethod, COUNT(*) AS total_rows, COUNT(disc_year) AS non_null_disc_year FROM raw_ps GROUP BY discoverymethod ORDER BY total_rows DESC;
```

```json
[
  {
    "discoverymethod": "Transit",
    "total_rows": 4488,
    "non_null_disc_year": 4487
  },
  {
    "discoverymethod": "Radial Velocity",
    "total_rows": 1161,
    "non_null_disc_year": 1161
  },
  {
    "discoverymethod": "Microlensing",
    "total_rows": 265,
    "non_null_disc_year": 265
  },
  {
    "discoverymethod": "Imaging",
    "total_rows": 91,
    "non_null_disc_year": 91
  },
  {
    "discoverymethod": "Transit Timing Variations",
    "total_rows": 39,
    "non_null_disc_year": 39
  },
  {
    "discoverymethod": "Eclipse Timing Variations",
    "total_rows": 17,
    "non_null_disc_year": 17
  },
  {
    "discoverymethod": "Orbital Brightness Modulation",
    "total_rows": 9,
    "non_null_disc_year": 9
  },
  {
    "discoverymethod": "Pulsar Timing",
    "total_rows": 8,
    "non_null_disc_year": 8
  },
  {
    "discoverymethod": "Astrometry",
    "total_rows": 6,
    "non_null_disc_year": 6
  },
  {
    "discoverymethod": "Pulsation Timing Variations",
    "total_rows": 2,
    "non_null_disc_year": 2
  },
  {
    "discoverymethod": "Disk Kinematics",
    "total_rows": 1,
    "non_null_disc_year": 1
  }
]
```

## 6) Resumen por método (n_planets y promedio de periodo orbital)

```sql
SELECT discoverymethod, COUNT(*) AS n_planets, ROUND(AVG(pl_orbper),2) AS avg_orbper_days FROM raw_ps WHERE pl_orbper IS NOT NULL GROUP BY discoverymethod ORDER BY n_planets DESC;
```

```json
[
  {
    "discoverymethod": "Transit",
    "n_planets": 4488,
    "avg_orbper_days": 23.99
  },
  {
    "discoverymethod": "Radial Velocity",
    "n_planets": 1161,
    "avg_orbper_days": 1761.71
  },
  {
    "discoverymethod": "Transit Timing Variations",
    "n_planets": 39,
    "avg_orbper_days": 347.89
  },
  {
    "discoverymethod": "Imaging",
    "n_planets": 25,
    "avg_orbper_days": 17028014.9
  },
  {
    "discoverymethod": "Eclipse Timing Variations",
    "n_planets": 17,
    "avg_orbper_days": 3596.2
  },
  {
    "discoverymethod": "Microlensing",
    "n_planets": 12,
    "avg_orbper_days": 4175.56
  },
  {
    "discoverymethod": "Orbital Brightness Modulation",
    "n_planets": 9,
    "avg_orbper_days": 1.17
  },
  {
    "discoverymethod": "Pulsar Timing",
    "n_planets": 7,
    "avg_orbper_days": 1475.79
  },
  {
    "discoverymethod": "Astrometry",
    "n_planets": 6,
    "avg_orbper_days": 865.26
  },
  {
    "discoverymethod": "Pulsation Timing Variations",
    "n_planets": 2,
    "avg_orbper_days": 1005.0
  }
]
```

## 4 consultas adicionales (tarea)

### Calidad 1 — Duplicados por pl_name

```sql
SELECT COUNT(*) AS duplicated_pl_name_groups FROM (SELECT pl_name FROM raw_ps WHERE pl_name IS NOT NULL GROUP BY pl_name HAVING COUNT(*)>1) t;
```

```json
[
  {
    "duplicated_pl_name_groups": 0
  }
]
```

Interpretación: No aparecen grupos duplicados por nombre de planeta en este corte.

### Calidad 2 — Años fuera de rango

```sql
SELECT COUNT(*) AS invalid_disc_year_rows FROM raw_ps WHERE disc_year IS NOT NULL AND (disc_year<1980 OR disc_year>CAST(strftime('%Y','now') AS INTEGER));
```

```json
[
  {
    "invalid_disc_year_rows": 0
  }
]
```

Interpretación: No se detectan años fuera del rango [1980, año actual].

### Científica 1 — Métodos de descubrimiento más frecuentes

```sql
SELECT discoverymethod, COUNT(*) AS n_planets FROM raw_ps GROUP BY discoverymethod ORDER BY n_planets DESC LIMIT 5;
```

```json
[
  {
    "discoverymethod": "Transit",
    "n_planets": 4488
  },
  {
    "discoverymethod": "Radial Velocity",
    "n_planets": 1161
  },
  {
    "discoverymethod": "Microlensing",
    "n_planets": 265
  },
  {
    "discoverymethod": "Imaging",
    "n_planets": 91
  },
  {
    "discoverymethod": "Transit Timing Variations",
    "n_planets": 39
  }
]
```

Interpretación: La detección está fuertemente concentrada en pocos métodos, liderados por transit y radial velocity.

### Científica 2 — Promedio de radio y masa (filas con ambos datos)

```sql
SELECT ROUND(AVG(pl_rade),2) AS avg_radius_earth, ROUND(AVG(pl_bmasse),2) AS avg_mass_earth FROM raw_ps WHERE pl_rade IS NOT NULL AND pl_bmasse IS NOT NULL;
```

```json
[
  {
    "avg_radius_earth": 5.8,
    "avg_mass_earth": 394.46
  }
]
```

Interpretación: El promedio conjunto de radio y masa sugiere sesgo hacia objetos grandes/fáciles de detectar.

## Reflexión (bitácora)

- Consulta más difícil: la comparación COUNT(*) vs COUNT(col) por método, porque obliga a distinguir claramente total de filas vs presencia real del atributo.

- Si el dataset crece 100×, empeorarían más los `GROUP BY` amplios y los `ORDER BY ... LIMIT` sobre columnas no indexadas/materializadas.
