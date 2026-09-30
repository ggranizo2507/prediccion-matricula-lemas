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
