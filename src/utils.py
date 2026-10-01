"""Funciones auxiliares compartidas: configuración, logging, semillas y calendario."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

RAIZ = Path(__file__).resolve().parents[1]


def cargar_config(ruta: str | Path | None = None) -> dict:
    """Lee config.yaml (por defecto el de la raíz del repositorio)."""
    ruta = Path(ruta) if ruta else RAIZ / "config.yaml"
    with open(ruta, encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


def configurar_logging(nivel: int = logging.INFO) -> logging.Logger:
    """Logger único del proyecto con formato legible."""
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger("lemas")


def fijar_semilla(semilla: int) -> None:
    """Reproducibilidad en random y numpy."""
    random.seed(semilla)
    np.random.seed(semilla)


@dataclass(frozen=True)
class Cohorte:
    """Transición de un ciclo de origen al ciclo siguiente."""

    nombre: str
    anio_origen: int
    rol: str
    t0: pd.Timestamp
    h: pd.Timestamp

    @property
    def anio_destino(self) -> int:
        return self.anio_origen + 1


def cohortes_desde_config(config: dict) -> list[Cohorte]:
    """Construye las cohortes con sus fechas t0 y H a partir de config.yaml."""
    mes_t0, dia_t0 = config["calendario"]["t0_mes_dia"]
    mes_h, dia_h = config["calendario"]["h_mes_dia"]
    cohortes = []
    for nombre, datos in config["cohortes"].items():
        destino = int(datos["anio_origen"]) + 1
        cohortes.append(
            Cohorte(
                nombre=nombre,
                anio_origen=int(datos["anio_origen"]),
                rol=datos["rol"],
                t0=pd.Timestamp(year=destino, month=mes_t0, day=dia_t0),
                h=pd.Timestamp(year=destino, month=mes_h, day=dia_h),
            )
        )
    return cohortes


def tasa_por_grupo(
    datos: pd.DataFrame, grupo: str, objetivo: str = "y_no_matricula", minimo: int = 5
) -> pd.DataFrame:
    """Tasa del evento por grupo con n; oculta los grupos con menos de `minimo` casos."""
    tabla = datos.groupby(grupo, dropna=False, observed=True)[objetivo].agg(n="count", tasa="mean")
    tabla["tasa"] = tabla["tasa"].round(4)
    return tabla[tabla["n"] >= minimo].reset_index()


def suprimir_celdas(conteos: pd.Series, minimo: int = 5) -> pd.Series:
    """Reemplaza conteos menores al mínimo por '<minimo' para reportes públicos."""
    return conteos.astype(object).where(conteos >= minimo, f"<{minimo}")


COLUMNAS_BASE_SEUD = ("anoa", "fecha_pago", "id_seudonimo", "id_familia_seudonimo")


def leer_base_seud(ruta: str | Path) -> pd.DataFrame:
    """Lee base_seud.csv y verifica que sea la salida de 00a (columnas mínimas)."""
    ruta = Path(ruta)
    try:
        df = pd.read_csv(ruta, dtype=str)
    except Exception as error:  # archivo binario, Excel renombrado, etc.
        raise ValueError(f"{ruta.name} no es un CSV legible: {error}") from error
    faltan = [c for c in COLUMNAS_BASE_SEUD if c not in df.columns]
    if faltan:
        raise ValueError(f"{ruta.name} no parece base_seud.csv: faltan columnas {faltan}")
    return completar_anoa_desde_hoja(unificar_alias(df, cargar_config().get("alias_columnas", {})))


def unificar_alias(df: pd.DataFrame, alias: dict[str, str]) -> pd.DataFrame:
    """Rellena cada columna oficial con su alias (encabezado distinto en otras hojas)."""
    df = df.copy()
    for viejo, oficial in alias.items():
        if viejo not in df.columns:
            continue
        if oficial in df.columns:
            vacio = df[oficial].isna() | (df[oficial].astype("string").str.strip() == "")
            df.loc[vacio, oficial] = df.loc[vacio, viejo]
        else:
            df[oficial] = df[viejo]
        df = df.drop(columns=viejo)
        logging.getLogger("lemas.datos").info("Columna '%s' unificada en '%s'.", viejo, oficial)
    return df


def completar_anoa_desde_hoja(df: pd.DataFrame) -> pd.DataFrame:
    """Si `anoa` está vacío en alguna hoja, lo toma del nombre de la hoja (p. ej. '2023')."""
    if "hoja" not in df.columns:
        return df
    vacio = df["anoa"].isna() | (df["anoa"].astype("string").str.strip() == "")
    anio_hoja = df["hoja"].astype("string").str.extract(r"(20\d{2})", expand=False)
    completables = vacio & anio_hoja.notna()
    if completables.any():
        df = df.copy()
        df.loc[completables, "anoa"] = anio_hoja[completables]
        por_hoja = df.loc[completables, "hoja"].value_counts().sort_index().to_dict()
        logging.getLogger("lemas.datos").warning(
            "anoa vacío en %d filas; se completó con el nombre de la hoja: %s",
            int(completables.sum()), por_hoja)
    return df


def obtener_base_seud(
    ruta: str | Path, en_colab: bool, subir_de_nuevo: bool = False
) -> pd.DataFrame:
    """Devuelve la base seudonimizada; en Colab la pide si falta o si se pide reemplazarla.

    Si el archivo subido no es válido, se borra para que la siguiente ejecución vuelva
    a pedirlo (evita quedar atrapado con un archivo equivocado).
    """
    ruta = Path(ruta)
    if subir_de_nuevo and ruta.exists():
        ruta.unlink()
    if not ruta.exists():
        if not en_colab:
            raise FileNotFoundError(f"Copie base_seud.csv en {ruta}")
        from google.colab import files  # type: ignore[import-not-found]

        print("Suba base_seud.csv (generado por 00a_seudonimizacion)")
        subidos = files.upload()
        nombre = next(iter(subidos))
        ruta.parent.mkdir(parents=True, exist_ok=True)
        Path(nombre).replace(ruta)
        for otro in subidos:  # no dejar copias sueltas de otros archivos subidos
            Path(otro).unlink(missing_ok=True)
    try:
        return leer_base_seud(ruta)
    except ValueError:
        ruta.unlink(missing_ok=True)
        raise
