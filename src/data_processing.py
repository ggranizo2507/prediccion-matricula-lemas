"""
Procesamiento de la base de LEMAS: de las hojas por ciclo lectivo a una tabla
de modelado por cohorte, con la foto de información en t0 y la etiqueta en H.

Reglas (ver config.yaml y docs/analisis_datos.md):
- Unidad de análisis: estudiante antiguo con reserva aprobada para el ciclo siguiente.
- Predictores: solo información del ciclo de origen, conocida antes de t0 (20-feb).
- Etiqueta y_no_matricula: 1 si NO pagó matrícula del ciclo destino en [t0, H].
- El pago del ciclo destino se usa únicamente para construir la etiqueta.
"""

from __future__ import annotations

import logging
import re

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.utils import Cohorte, cohortes_desde_config

log = logging.getLogger("lemas.datos")

NUMERICAS = [
    "promedio",
    "conducta",
    "anios_permanencia",
    "atrasos_pension",
    "hermanos_lemas",
    "beca",
    "reserva_extraordinaria",
]
CATEGORICAS = ["sede", "subnivel", "curso", "pago_origen"]
VALORES_SI = {"SI", "SÍ", "S", "1", "TRUE", "VERDADERO"}
VALORES_NO = {"NO", "N", "0", "FALSE", "FALSO"}


# --------------------------------------------------------------------------- #
# Limpieza
# --------------------------------------------------------------------------- #
def _a_binario(serie: pd.Series) -> pd.Series:
    """SI/NO, 1/0 → 1/0; cualquier otro valor queda como NaN."""
    texto = serie.astype(str).str.strip().str.upper()
    return texto.map(lambda v: 1 if v in VALORES_SI else 0 if v in VALORES_NO else np.nan)


def _a_fecha(serie: pd.Series) -> pd.Series:
    """Fechas ISO ('2021-11-09 14:53') o dd/mm/aaaa; lo ilegible queda NaT."""
    texto = serie.astype(str).str.strip()
    iso = pd.to_datetime(texto, errors="coerce", format="ISO8601")
    dmy = pd.to_datetime(texto, errors="coerce", dayfirst=True, format="mixed")
    return iso.fillna(dmy).dt.normalize()


def separar_nivel(nivel: str, paralelo: str | None = None) -> tuple[str, str]:
    """'Inicial 1 A - Inicial' → ('Inicial 1', 'Inicial').

    La parte izquierda es curso + paralelo; la derecha, el subnivel.
    """
    if not isinstance(nivel, str) or not nivel.strip():
        return ("SIN_DATO", "SIN_DATO")
    izquierda, _, derecha = nivel.partition(" - ")
    izquierda = izquierda.strip()
    if paralelo and isinstance(paralelo, str) and paralelo.strip():
        izquierda = re.sub(rf"\s+{re.escape(paralelo.strip())}$", "", izquierda)
    return (izquierda or "SIN_DATO", derecha.strip() or "SIN_DATO")


def limpiar_base(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Renombra a nombres internos, tipa columnas y elimina duplicados."""
    mapa = {origen: interno for interno, origen in config["columnas"].items()}
    faltantes = [c for c in mapa if c not in df.columns]
    if faltantes:
        raise KeyError(f"Faltan columnas en la base: {faltantes}")

    base = df.rename(columns=mapa)[list(mapa.values())].copy()
    for col in ("sede", "nivel", "paralelo", "reserva", "estado_reserva", "tipo_reserva"):
        base[col] = base[col].astype("string").str.strip()

    base["anio_origen"] = pd.to_numeric(base["anio_origen"], errors="coerce").astype("Int64")
    base["anio_ingreso"] = pd.to_numeric(base["anio_ingreso"], errors="coerce").astype("Int64")
    base["promedio"] = pd.to_numeric(base["promedio"], errors="coerce")
    base["atrasos"] = pd.to_numeric(base["atrasos"], errors="coerce")
    base["beca"] = _a_binario(base["beca"])
    base["fecha_pago"] = _a_fecha(base["fecha_pago"])
    base["fecha_reserva"] = _a_fecha(base["fecha_reserva"])

    if config["conducta"]["formato"] == "letras":
        mapa_letras = config["conducta"]["letras_a_ordinal"]
        letras = base["conducta"].astype("string").str.strip().str.upper()
        base["conducta"] = letras.map(mapa_letras).astype(float)
        invalidas = letras.notna() & base["conducta"].isna()
        if invalidas.any():
            log.warning("%d notas de conducta fuera de A-E quedan como vacías.", invalidas.sum())
    else:
        base["conducta"] = pd.to_numeric(base["conducta"], errors="coerce")

    partes = [separar_nivel(n, p) for n, p in zip(base["nivel"], base["paralelo"], strict=False)]
    base["curso"] = [p[0] for p in partes]
    base["subnivel"] = [p[1] for p in partes]

    duplicados = base.duplicated(["anio_origen", "id_estudiante"], keep="first")
    if duplicados.any():
        log.warning("Se eliminan %d filas duplicadas (mismo estudiante y año).", duplicados.sum())
        base = base[~duplicados]

    sin_id = base["id_estudiante"].isna() | base["anio_origen"].isna()
    if sin_id.any():
        log.warning("Se eliminan %d filas sin identificador o sin año.", sin_id.sum())
        base = base[~sin_id]
    return base.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Predictores (todos conocidos antes de t0)
# --------------------------------------------------------------------------- #
def _estado_pago_origen(fila: pd.Series, mes_dia_t0: tuple, mes_dia_h: tuple) -> str:
    """Puntualidad del pago que confirmó el propio ciclo de origen."""
    if pd.notna(fila["anio_ingreso"]) and fila["anio_ingreso"] == fila["anio_origen"]:
        return "nuevo"
    if pd.isna(fila["fecha_pago"]):
        return "sin_dato"
    anio = int(fila["anio_origen"])
    inicio = pd.Timestamp(year=anio, month=mes_dia_t0[0], day=mes_dia_t0[1])
    cierre = pd.Timestamp(year=anio, month=mes_dia_h[0], day=mes_dia_h[1])
    if fila["fecha_pago"] < inicio:
        return "anticipado"
    return "en_plazo" if fila["fecha_pago"] <= cierre else "tardio"


def agregar_predictores(origen: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Deriva las variables del modelo a partir de la hoja del ciclo de origen."""
    datos = origen.copy()
    hermanos = datos.groupby("id_familia")["id_estudiante"].transform("count") - 1
    datos["hermanos_lemas"] = hermanos.where(datos["id_familia"].notna(), 0)
    datos["anios_permanencia"] = (datos["anio_origen"] - datos["anio_ingreso"]).astype("Float64")
    datos["atrasos_pension"] = datos["atrasos"]
    datos["reserva_extraordinaria"] = (
        datos["tipo_reserva"].str.upper().str.contains("EXTRA", na=False).astype(int)
    )
    t0, h = config["calendario"]["t0_mes_dia"], config["calendario"]["h_mes_dia"]
    datos["pago_origen"] = datos.apply(_estado_pago_origen, axis=1, args=(t0, h))
    return datos


# --------------------------------------------------------------------------- #
# Cohorte: población elegible + etiqueta
# --------------------------------------------------------------------------- #
def construir_cohorte(
    base: pd.DataFrame,
    cohorte: Cohorte,
    config: dict,
    estados_aprobados: list[str] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Devuelve (tabla de modelado, reporte de conteos) para una cohorte."""
    reglas = config["elegibilidad"]
    estados = estados_aprobados or reglas["estados_aprobados"]
    origen = base[base["anio_origen"] == cohorte.anio_origen]
    destino = base[base["anio_origen"] == cohorte.anio_destino]
    reporte = {"cohorte": cohorte.nombre, "origen_total": len(origen)}

    if destino.empty:
        log.warning("%s: no existe la hoja %d; la etiqueta no puede construirse.",
                    cohorte.nombre, cohorte.anio_destino)
        return pd.DataFrame(), {**reporte, "estado": "sin_destino"}

    origen = agregar_predictores(origen, config)
    paso = origen[origen["reserva"].str.upper().isin(reglas["reserva_si"])]
    reporte["reserva_si"] = len(paso)
    en_proceso = paso["estado_reserva"].str.contains("proceso", case=False, na=False)
    reporte["en_proceso"] = int(en_proceso.sum())
    paso = paso[paso["estado_reserva"].isin(estados)]
    reporte["aprobados"] = len(paso)

    reserva_tardia = paso["fecha_reserva"].notna() & (paso["fecha_reserva"] >= cohorte.t0)
    reporte["reserva_despues_t0"] = int(reserva_tardia.sum())
    paso = paso[~reserva_tardia]

    terminal = paso["nivel"].str.contains(reglas["cursos_terminales_regex"], regex=True, na=False)
    reporte["terminales_excluidos"] = int(terminal.sum())
    paso = paso[~terminal].copy()

    pagos = destino.set_index("id_estudiante")["fecha_pago"]
    paso["fecha_pago_destino"] = paso["id_estudiante"].map(pagos)
    confirmado = paso["fecha_pago_destino"] < cohorte.t0
    reporte["confirmados_antes_t0"] = int(confirmado.sum())
    paso = paso[~confirmado].copy()

    en_plazo = paso["fecha_pago_destino"].between(cohorte.t0, cohorte.h)
    paso["y_no_matricula"] = (~en_plazo).astype(int)
    paso["matricula_tardia"] = (paso["fecha_pago_destino"] > cohorte.h).astype(int)
    paso["cohorte"] = cohorte.nombre
    paso["rol"] = cohorte.rol

    evento_familiar = paso.groupby("id_familia")["y_no_matricula"].max()
    reporte.update(
        modelables=len(paso),
        no_matricula=int(paso["y_no_matricula"].sum()),
        tardias=int(paso["matricula_tardia"].sum()),
        familias=int(paso["id_familia"].nunique()),
        familias_no_matricula=int(evento_familiar.sum()),
        estado="ok",
    )
    columnas = ["cohorte", "rol", "id_estudiante", "id_familia", *CATEGORICAS, *NUMERICAS,
                "fecha_pago_destino", "y_no_matricula", "matricula_tardia"]
    return paso[columnas].reset_index(drop=True), reporte


def construir_dataset(
    base: pd.DataFrame, config: dict, estados_aprobados: list[str] | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Une todas las cohortes configuradas. Devuelve (dataset, reporte por cohorte)."""
    tablas, reportes = [], []
    for cohorte in cohortes_desde_config(config):
        tabla, reporte = construir_cohorte(base, cohorte, config, estados_aprobados)
        reportes.append(reporte)
        if not tabla.empty:
            tablas.append(tabla)
            log.info("%s: %d modelables, %d no matrícula (%.1f%%).", cohorte.nombre,
                     reporte["modelables"], reporte["no_matricula"],
                     100 * reporte["no_matricula"] / max(reporte["modelables"], 1))
    dataset = pd.concat(tablas, ignore_index=True) if tablas else pd.DataFrame()
    return dataset, pd.DataFrame(reportes)


# --------------------------------------------------------------------------- #
# Guardas anti-fuga
# --------------------------------------------------------------------------- #
def construir_matriz_x(dataset: pd.DataFrame) -> pd.DataFrame:
    """Solo las columnas predictoras permitidas, con tipos simples para scikit-learn."""
    X = dataset[CATEGORICAS + NUMERICAS].copy()
    for col in CATEGORICAS:
        X[col] = X[col].astype("object").where(X[col].notna(), "SIN_DATO").astype(str)
    for col in NUMERICAS:
        X[col] = pd.to_numeric(X[col], errors="coerce").astype(float)
    return X


def construir_preprocesador(escalar: bool = True, min_frecuencia: int = 10) -> ColumnTransformer:
    """Imputación + escalado (numéricas) y one-hot (categóricas).

    Se ajusta SOLO con las cohortes de entrenamiento dentro del pipeline del modelo.
    Las categorías con menos de `min_frecuencia` casos se agrupan como "infrecuentes"
    (estabilidad y privacidad); las categorías nuevas en C4/C5 se tratan igual.
    """
    pasos_num = [("imputar", SimpleImputer(strategy="median"))]
    if escalar:
        pasos_num.append(("escalar", StandardScaler()))
    categoricas = Pipeline([
        ("imputar", SimpleImputer(strategy="constant", fill_value="SIN_DATO")),
        ("onehot", OneHotEncoder(handle_unknown="infrequent_if_exist",
                                 min_frequency=min_frecuencia, sparse_output=False)),
    ])
    return ColumnTransformer(
        [("num", Pipeline(pasos_num), NUMERICAS), ("cat", categoricas, CATEGORICAS)],
        verbose_feature_names_out=False,
    )


def verificar_sin_fuga(X: pd.DataFrame, config: dict) -> None:
    """Falla si X contiene columnas prohibidas o columnas fuera de la lista blanca."""
    prohibidas = set(config["prohibidas_en_X"]) & set(X.columns)
    if prohibidas:
        raise ValueError(f"Fuga de información: X contiene {sorted(prohibidas)}")
    desconocidas = set(X.columns) - set(CATEGORICAS + NUMERICAS)
    if desconocidas:
        raise ValueError(f"Columnas no autorizadas en X: {sorted(desconocidas)}")


# --------------------------------------------------------------------------- #
# Ejecución: python -m src.data_processing [--fuente real|sintetica]
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    import argparse

    from src.utils import RAIZ, cargar_config, configurar_logging

    configurar_logging()
    config = cargar_config()
    parser = argparse.ArgumentParser(description="Construye la tabla de modelado")
    parser.add_argument("--fuente", choices=["real", "sintetica"], default=config["fuente_datos"])
    args = parser.parse_args(argv)

    ruta = RAIZ / config["rutas"]["base_real" if args.fuente == "real" else "base_sintetica"]
    base = limpiar_base(pd.read_csv(ruta, dtype=str), config)
    dataset, reporte = construir_dataset(base, config)
    verificar_sin_fuga(construir_matriz_x(dataset), config)

    sufijo = "real" if args.fuente == "real" else "sintetico"
    salida = RAIZ / config["rutas"]["procesados"] / f"dataset_modelado_{sufijo}.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(salida, index=False)
    ruta_reporte = RAIZ / config["rutas"]["metricas"] / f"reporte_cohortes_{sufijo}.csv"
    ruta_reporte.parent.mkdir(parents=True, exist_ok=True)
    reporte.to_csv(ruta_reporte, index=False)
    log.info("Dataset: %s | Reporte por cohorte: %s", salida, ruta_reporte)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
