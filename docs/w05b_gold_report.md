# W05B — Gold report

Fecha: 2026-03-03

## Qué significa cada output Gold
- **`gold_by_discoverymethod`**: resume descubrimientos por método (volumen y promedios físicos), útil para comparar sesgos observacionales entre técnicas.
- **`gold_by_host`**: resume sistemas (hosts) por número de planetas y características promedio, útil para priorizar análisis por arquitectura de sistemas.

## Top 10 `gold_by_discoverymethod`
```json
[
  {
    "discoverymethod": "Transit",
    "n_planets": 4487,
    "avg_pl_rade": 4.365,
    "avg_pl_bmasse": 123.769,
    "first_disc_year": 2002,
    "last_disc_year": 2026
  },
  {
    "discoverymethod": "Radial Velocity",
    "n_planets": 1161,
    "avg_pl_rade": 9.792,
    "avg_pl_bmasse": 1039.835,
    "first_disc_year": 1995,
    "last_disc_year": 2026
  },
  {
    "discoverymethod": "Microlensing",
    "n_planets": 265,
    "avg_pl_rade": 9.86,
    "avg_pl_bmasse": 800.545,
    "first_disc_year": 2004,
    "last_disc_year": 2026
  },
  {
    "discoverymethod": "Imaging",
    "n_planets": 86,
    "avg_pl_rade": 13.446,
    "avg_pl_bmasse": 4498.628,
    "first_disc_year": 2004,
    "last_disc_year": 2026
  },
  {
    "discoverymethod": "Transit Timing Variations",
    "n_planets": 39,
    "avg_pl_rade": 6.493,
    "avg_pl_bmasse": 484.399,
    "first_disc_year": 2011,
    "last_disc_year": 2025
  },
  {
    "discoverymethod": "Eclipse Timing Variations",
    "n_planets": 17,
    "avg_pl_rade": 12.893,
    "avg_pl_bmasse": 2102.722,
    "first_disc_year": 2009,
    "last_disc_year": 2023
  },
  {
    "discoverymethod": "Orbital Brightness Modulation",
    "n_planets": 9,
    "avg_pl_rade": 9.645,
    "avg_pl_bmasse": 350.324,
    "first_disc_year": 2011,
    "last_disc_year": 2021
  },
  {
    "discoverymethod": "Pulsar Timing",
    "n_planets": 8,
    "avg_pl_rade": 5.411,
    "avg_pl_bmasse": 278.156,
    "first_disc_year": 1992,
    "last_disc_year": 2024
  },
  {
    "discoverymethod": "Astrometry",
    "n_planets": 6,
    "avg_pl_rade": 12.45,
    "avg_pl_bmasse": 4673.61,
    "first_disc_year": 2013,
    "last_disc_year": 2025
  },
  {
    "discoverymethod": "Pulsation Timing Variations",
    "n_planets": 2,
    "avg_pl_rade": 12.75,
    "avg_pl_bmasse": 2383.725,
    "first_disc_year": 2007,
    "last_disc_year": 2016
  }
]
```

## Top 10 `gold_by_host`
```json
[
  {
    "hostname": "KOI-351",
    "n_planets": 8,
    "avg_pl_rade": 3.9,
    "first_disc_year": 2013,
    "last_disc_year": 2017
  },
  {
    "hostname": "TRAPPIST-1",
    "n_planets": 7,
    "avg_pl_rade": 0.979,
    "first_disc_year": 2016,
    "last_disc_year": 2017
  },
  {
    "hostname": "HD 10180",
    "n_planets": 6,
    "avg_pl_rade": 6.677,
    "first_disc_year": 2010,
    "last_disc_year": 2010
  },
  {
    "hostname": "HD 110067",
    "n_planets": 6,
    "avg_pl_rade": 2.431,
    "first_disc_year": 2023,
    "last_disc_year": 2023
  },
  {
    "hostname": "HD 191939",
    "n_planets": 6,
    "avg_pl_rade": 6.59,
    "first_disc_year": 2020,
    "last_disc_year": 2022
  },
  {
    "hostname": "HD 219134",
    "n_planets": 6,
    "avg_pl_rade": 3.669,
    "first_disc_year": 2015,
    "last_disc_year": 2015
  },
  {
    "hostname": "HD 34445",
    "n_planets": 6,
    "avg_pl_rade": 8.855,
    "first_disc_year": 2009,
    "last_disc_year": 2017
  },
  {
    "hostname": "HIP 41378",
    "n_planets": 6,
    "avg_pl_rade": 4.254,
    "first_disc_year": 2016,
    "last_disc_year": 2025
  },
  {
    "hostname": "K2-138",
    "n_planets": 6,
    "avg_pl_rade": 2.584,
    "first_disc_year": 2017,
    "last_disc_year": 2021
  },
  {
    "hostname": "Kepler-11",
    "n_planets": 6,
    "avg_pl_rade": 2.967,
    "first_disc_year": 2010,
    "last_disc_year": 2010
  }
]
```

## Interpretación científica simple
La distribución por método sugiere dominio de técnicas como **Transit** y **Radial Velocity**, coherente con sus ventajas instrumentales para detectar grandes volúmenes de exoplanetas. A nivel de host, los sistemas con mayor número de planetas concentrados permiten estudiar formación y estabilidad orbital de arquitecturas múltiples.
