# W04B — Silver report

Fecha: 2026-02-23

## DESCRIBE silver_planet

```json
[
  {
    "cid": 0,
    "name": "pl_name",
    "type": "TEXT",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 1,
    "name": "hostname",
    "type": "TEXT",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 2,
    "name": "discoverymethod",
    "type": "TEXT",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 3,
    "name": "disc_year",
    "type": "INT",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 4,
    "name": "sy_snum",
    "type": "REAL",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 5,
    "name": "sy_pnum",
    "type": "REAL",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 6,
    "name": "sy_dist",
    "type": "REAL",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 7,
    "name": "ra",
    "type": "REAL",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 8,
    "name": "dec",
    "type": "REAL",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 9,
    "name": "pl_orbper",
    "type": "REAL",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 10,
    "name": "pl_rade",
    "type": "REAL",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 11,
    "name": "pl_bmasse",
    "type": "REAL",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 12,
    "name": "pl_eqt",
    "type": "REAL",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 13,
    "name": "st_teff",
    "type": "REAL",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 14,
    "name": "st_rad",
    "type": "REAL",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  },
  {
    "cid": 15,
    "name": "st_mass",
    "type": "REAL",
    "notnull": 0,
    "dflt_value": null,
    "pk": 0
  }
]
```

## Conteos silver

```json
[
  {
    "n_rows": 6081,
    "n_distinct_pl_name": 6081,
    "n_distinct_hostname": 4537
  }
]
```

## dim_host_full: n_rows vs n_keys

```json
[
  {
    "n_rows": 4537,
    "n_keys": 4537
  }
]
```

## JOIN sano (n_fact vs n_join)

```json
[
  {
    "n_fact": 6081,
    "n_join": 6081
  }
]
```

## Vista Gold exportada

- Archivo: `artifacts/gold_by_method_20260223.csv`


## Reflexión (bitácora)
- Evidencia mínima de JOIN sano: verificar `n_fact == n_join` y además `n_rows == n_keys` en la dimensión usada para la llave de JOIN.
- Trade-off: limpiar demasiado reduce cobertura (pierdes filas), limpiar muy poco deja ruido que contamina métricas downstream; por eso se aplicaron reglas mínimas y explícitas.
