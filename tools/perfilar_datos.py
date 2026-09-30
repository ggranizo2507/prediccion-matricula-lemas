"""
Perfil estadístico de la base real para calibrar el dataset sintético.

Se ejecuta DENTRO del entorno autorizado de LEMAS sobre la base ya
seudonimizada. Produce un JSON con estructura y agregados, nunca filas:
- nombre y tipo de cada columna, porcentaje de nulos y cardinalidad;
- percentiles 1-99 para numéricas (no se exportan mínimos ni máximos,
  que podrían señalar a un estudiante atípico);
- frecuencias de categorías, suprimiendo las que tienen menos de 5 casos;
- rango de fechas por cohorte;
- conteos y tasas por cohorte y columna de agrupación, con supresión.
Las columnas que parecen identificadores solo informan que existen.

Revise el JSON antes de compartirlo. Uso:
    python perfilar_datos.py --entrada base_seud.csv --salida perfil.json \
        --col-cohorte periodo --col-objetivo matricula_efectiva \
        --agrupar sede nivel beca --col-familia id_familia_seudonimo
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import warnings
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("perfil")
warnings.filterwarnings("ignore", message="Could not infer format")

MIN_CELDA = 5            # umbral de supresión de celdas pequeñas
MAX_CATEGORIAS = 100     # más categorías que esto se trata como texto libre
UMBRAL_ID = 0.9          # proporción de valores únicos para considerar identificador


def _suprimir(conteos: pd.Series) -> dict:
    """Convierte conteos en dict y reemplaza celdas pequeñas por '<5'."""
    return {str(k): (int(v) if v >= MIN_CELDA else f"<{MIN_CELDA}")
            for k, v in conteos.items()}


def _es_fecha(serie: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(serie):
        return True
    muestra = serie.dropna().astype(str).head(200)
    if muestra.empty:
        return False
    convertida = pd.to_datetime(muestra, errors="coerce", dayfirst=True)
    return convertida.notna().mean() > 0.9 and muestra.str.contains(r"[-/]").mean() > 0.9


def perfilar_columna(serie: pd.Series, cohortes: pd.Series | None) -> dict:
    """Perfil agregado de una columna, sin exponer valores individuales."""
    n = len(serie)
    no_nulos = serie.dropna()
    info = {
        "pct_nulos": round(100 * (1 - len(no_nulos) / n), 2) if n else None,
        "n_unicos": int(no_nulos.nunique()),
    }
    if len(no_nulos) and no_nulos.nunique() / len(no_nulos) > UMBRAL_ID \
            and not pd.api.types.is_numeric_dtype(serie):
        info["tipo"] = "identificador"
        info["ejemplo_formato"] = "".join(
            "9" if c.isdigit() else "A" if c.isalpha() else c
            for c in str(no_nulos.iloc[0]))
        return info

    if _es_fecha(serie):
        fechas = pd.to_datetime(serie, errors="coerce", dayfirst=True)
        info["tipo"] = "fecha"
        grupos = fechas.groupby(cohortes) if cohortes is not None else {"total": fechas}.items()
        info["por_cohorte"] = {}
        for clave, valores in grupos:
            v = valores.dropna()
            if len(v) >= MIN_CELDA:
                info["por_cohorte"][str(clave)] = {
                    "p5": str(v.quantile(0.05).date()),
                    "mediana": str(v.quantile(0.5).date()),
                    "p95": str(v.quantile(0.95).date()),
                    "n": int(len(v)),
                }
        return info

    numerica = pd.to_numeric(serie, errors="coerce")
    if numerica.notna().sum() >= 0.95 * len(no_nulos) and no_nulos.nunique() > MAX_CATEGORIAS:
        v = numerica.dropna()
        info["tipo"] = "numerica"
        info["percentiles"] = {f"p{int(q*100)}": round(float(v.quantile(q)), 3)
                               for q in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)}
        info["media"] = round(float(v.mean()), 3)
        info["desv"] = round(float(v.std()), 3)
        return info

    if no_nulos.nunique() <= MAX_CATEGORIAS:
        info["tipo"] = "categorica"
        info["frecuencias"] = _suprimir(no_nulos.astype(str).value_counts())
        return info

    info["tipo"] = "texto_libre"
    return info


def perfilar(df: pd.DataFrame, col_cohorte: str | None, col_objetivo: str | None,
             agrupar: list[str], col_familia: str | None = None) -> dict:
    cohortes = df[col_cohorte].astype(str) if col_cohorte else None
    perfil = {
        "filas": int(len(df)),
        "columnas": {c: perfilar_columna(df[c], cohortes) for c in df.columns},
        "nota": f"Agregados con supresión de celdas < {MIN_CELDA}. Sin filas individuales.",
    }
    if col_cohorte:
        conteo = df[col_cohorte].astype(str).value_counts().sort_index()
        perfil["filas_por_cohorte"] = _suprimir(conteo)
    if col_familia:
        # Cuántos estudiantes tiene cada familia (estructura de hermanos).
        claves = [col_cohorte, col_familia] if col_cohorte else [col_familia]
        tamanos = df.groupby(claves).size()
        tamanos = tamanos.clip(upper=4)
        dist = (tamanos.groupby(level=0).value_counts().sort_index()
                if col_cohorte else tamanos.value_counts().sort_index())
        perfil["estudiantes_por_familia"] = {
            " | ".join(map(str, k if isinstance(k, tuple) else (k,))).replace("| 4", "| 4+"):
                (int(v) if v >= MIN_CELDA else f"<{MIN_CELDA}") for k, v in dist.items()}
    if col_cohorte and col_objetivo:
        y = pd.to_numeric(df[col_objetivo], errors="coerce")
        tasas = {}
        for dims in [[col_cohorte], *[[col_cohorte, g] for g in agrupar]]:
            tabla = y.groupby([df[d].astype(str) for d in dims]).agg(["count", "mean"])
            clave_tabla = " x ".join(dims)
            tasas[clave_tabla] = {
                " | ".join(map(str, k if isinstance(k, tuple) else (k,))):
                    ({"n": int(r["count"]), "tasa": round(float(r["mean"]), 3)}
                     if r["count"] >= MIN_CELDA else f"<{MIN_CELDA}")
                for k, r in tabla.iterrows()
            }
        perfil["tasas_objetivo"] = tasas
    return perfil


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--entrada", required=True)
    parser.add_argument("--salida", required=True)
    parser.add_argument("--col-cohorte")
    parser.add_argument("--col-objetivo")
    parser.add_argument("--agrupar", nargs="*", default=[])
    parser.add_argument("--col-familia", help="Columna del seudónimo familiar")
    parser.add_argument("--hoja", default=0, help="Hoja de Excel (nombre o índice)")
    args = parser.parse_args(argv)

    ruta = Path(args.entrada)
    try:
        df = (pd.read_excel(ruta, sheet_name=args.hoja, dtype=str)
              if ruta.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(ruta, dtype=str))
        faltan = [c for c in [args.col_cohorte, args.col_objetivo, *args.agrupar]
                  if c and c not in df.columns]
        if faltan:
            raise KeyError(f"Columnas inexistentes: {faltan}")
        perfil = perfilar(df, args.col_cohorte, args.col_objetivo, args.agrupar,
                          args.col_familia)
    except (OSError, ValueError, KeyError) as exc:
        log.error("%s", exc)
        return 1

    Path(args.salida).write_text(json.dumps(perfil, indent=2, ensure_ascii=False),
                                 encoding="utf-8")
    log.info("Perfil guardado en %s. Revíselo antes de compartirlo.", args.salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
