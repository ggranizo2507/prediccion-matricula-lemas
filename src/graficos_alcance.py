"""
Figuras del análisis de alcance de la lista de contactos (`src/alcance.py`).

Mismo estilo que las figuras del diagnóstico: 300 DPI, coma decimal, título que dice qué
se compara y leyenda. Azul para la regla D2, gris para el azar y rosa oscuro para la
proporción de casos (colores ya comprobados con un validador de paletas). El tono claro de
cada color es el total y el tono fuerte, la parte que interesa.

Las celdas ocultas por privacidad («<5», «oculto») se dibujan como dato ausente.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

from src.alcance import TIPOS, TODAS
from src.diagnostico import numero
from src.graficos_diagnostico import ENTRENAMIENTO as REGLA_COLOR
from src.graficos_diagnostico import (
    NEUTRO,
    REJILLA,
    TINTA,
    TINTA_SUAVE,
    _ajustar,
    _estilo,
    _titulo,
    guardar,
)
from src.graficos_diagnostico import VALIDACION as SEGUNDO_COLOR

__all__ = ["figura_desglose", "figura_por_k", "figura_semanal", "figura_campana", "guardar"]

CLARO = {REGLA_COLOR: "#C9DDEF", SEGUNDO_COLOR: "#EBCBD5", NEUTRO: "#DDE1E5"}


def _pct(valor: float, decimales: int = 0) -> str:
    return f"{numero(100 * valor, decimales)} %"


def _marca_pct(valor: float, _posicion=None) -> str:
    """Marca de eje en porcentaje: sin decimales si es entero, con uno si no."""
    cien = 100 * valor
    return _pct(valor, 0 if abs(cien - round(cien)) < 1e-6 else 1)


PORCENTAJE = FuncFormatter(_marca_pct)


def _numerica(serie: pd.Series) -> pd.Series:
    """Convierte a número; las celdas ocultas («<5», «oculto») quedan como NaN."""
    return pd.to_numeric(serie, errors="coerce")


def _numero(valor) -> float:
    return float(_numerica(pd.Series([valor])).iloc[0])


def _leyenda(fig: Figure, claves: list, columnas: int = 4) -> None:
    fig.legend(handles=claves, loc="lower center", ncol=columnas, frameon=False, fontsize=9,
               labelcolor=TINTA, bbox_to_anchor=(0.5, 0.0))


# --------------------------------------------------------------------------- #
# 1. Qué hay dentro del evento
# --------------------------------------------------------------------------- #
def figura_desglose(desglose: pd.DataFrame, cohortes: str) -> Figure:
    """Familias que no pagaron en plazo, por tipo, y cuántas de cada tipo están en la lista."""
    total = desglose[desglose["cohorte"] == TODAS].iloc[0]
    fig, ax = plt.subplots(figsize=(9.5, 4))
    casos = {tipo: _numero(total[tipo]) for tipo in TIPOS}
    if any(np.isnan(v) for v in casos.values()):
        ax.text(0.5, 0.5, "Alguna celda tiene menos casos que el mínimo publicable:\n"
                "el desglose no se muestra.", ha="center", va="center", fontsize=10,
                color=TINTA_SUAVE, transform=ax.transAxes)
        ax.set_axis_off()
    else:
        _estilo(ax, "", "Familias que no pagaron la matrícula en plazo", "")
        for fila, tipo in enumerate(TIPOS):
            aciertos = _numero(total[f"aciertos_{tipo}"])
            ax.barh(fila, casos[tipo], color=CLARO[REGLA_COLOR], height=0.55)
            ax.barh(fila, aciertos, color=REGLA_COLOR, height=0.55)
            nota = f"  {int(aciertos)} de {int(casos[tipo])} en la lista"
            if casos[tipo]:
                nota += f" ({_pct(aciertos / casos[tipo])})"
            ax.text(casos[tipo], fila, nota, va="center", fontsize=9, color=TINTA)
        ax.set_yticks(range(len(TIPOS)), list(TIPOS.values()))
        ax.invert_yaxis()
        ax.set_xlim(0, max(max(casos.values()), 1) * 1.5)
        ax.tick_params(axis="y", labelsize=9, colors=TINTA)
        ax.grid(axis="y", visible=False)
    _titulo(fig, "¿A quién encuentra la lista?",
            f"Regla D2 con el k aprobado · cohortes {cohortes} · C5 no interviene")
    _leyenda(fig, [Patch(color=CLARO[REGLA_COLOR], label="Casos de cada tipo"),
                   Patch(color=REGLA_COLOR, label="Casos que están en la lista")], 2)
    _ajustar(fig)
    return fig


# --------------------------------------------------------------------------- #
# 2. Alcance según el número de contactos
# --------------------------------------------------------------------------- #
def figura_por_k(por_k: pd.DataFrame, cohortes: str) -> Figure:
    """Recall y precisión de la lista D2 según el porcentaje de familias contactadas."""
    fig, (ax_r, ax_p) = plt.subplots(1, 2, figsize=(11, 4.4))
    maximo = 0.0
    for nombre, grupo in por_k.groupby("cohorte"):
        if nombre == TODAS:
            continue
        for ax, columna in ((ax_r, "recall"), (ax_p, "precision")):
            ax.plot(grupo["pct_familias"], _numerica(grupo[columna]), color=REGLA_COLOR,
                    lw=0.9, alpha=0.35)
        maximo = max(maximo, float(_numerica(grupo["precision"]).max()))
    total = por_k[por_k["cohorte"] == TODAS]
    x = total["pct_familias"].to_numpy()
    recall, precision = _numerica(total["recall"]), _numerica(total["precision"])
    ax_r.plot([0, 1], [0, 1], color=NEUTRO, lw=1.2, ls="--")
    ax_r.plot(x, recall, color=REGLA_COLOR, lw=2, marker="o", ms=5, markeredgecolor="white")
    tasa = float(precision.iloc[-1])                      # contactar a todas = tasa de casos
    ax_p.axhline(tasa, color=NEUTRO, lw=1.2, ls="--")
    ax_p.plot(x, precision, color=REGLA_COLOR, lw=2, marker="o", ms=5, markeredgecolor="white")

    actual = total[total["multiplicador"].astype(str).isin({"1.0", "1"})].iloc[0]
    _estilo(ax_r, "Casos alcanzados", "Familias contactadas", "Recall (casos en la lista)")
    _estilo(ax_p, "Aciertos por contacto", "Familias contactadas",
            "Precisión (casos entre los contactados)")
    for ax, columna in ((ax_r, "recall"), (ax_p, "precision")):
        valor = _numero(actual[columna])
        if not np.isnan(valor):
            ax.annotate("k aprobado", xy=(actual["pct_familias"], valor),
                        xytext=(16, -24 if columna == "recall" else 24),
                        textcoords="offset points", fontsize=8, color=TINTA_SUAVE,
                        arrowprops={"arrowstyle": "-", "color": NEUTRO, "lw": 0.8})
        ax.xaxis.set_major_formatter(PORCENTAJE)
        ax.yaxis.set_major_formatter(PORCENTAJE)
        ax.set_xlim(0, 1.02)
    ax_r.set_ylim(0, 1.03)
    tope = np.nanmax([maximo, float(precision.max()), tasa, 0.0])
    ax_p.set_ylim(0, tope * 1.15 if tope > 0 else 1)
    _titulo(fig, "Qué se alcanza con más o con menos contactos",
            f"Regla D2 · cohortes {cohortes} · línea fina: cada cohorte · C5 no interviene")
    _leyenda(fig, [Line2D([], [], color=REGLA_COLOR, lw=2, marker="o", ms=5,
                          markeredgecolor="white", label="Regla D2 (todas las cohortes)"),
                   Line2D([], [], color=NEUTRO, lw=1.2, ls="--", label="Selección al azar")], 2)
    _ajustar(fig)
    return fig


# --------------------------------------------------------------------------- #
# 3. Lista actualizada durante la campaña
# --------------------------------------------------------------------------- #
def figura_semanal(semanal: pd.DataFrame, cohortes: str) -> Figure:
    """Cómo cambian el grupo pendiente y el alcance de la lista semana a semana."""
    total = semanal[semanal["cohorte"] == TODAS]
    semanas = total["semana"].to_numpy()
    fig, (ax_g, ax_r) = plt.subplots(1, 2, figsize=(11, 4.4))

    ax_g.bar(semanas, _numerica(total["pct_pendientes"]), color=CLARO[NEUTRO], width=0.7)
    ax_g.plot(semanas, _numerica(total["tasa_base"]), color=SEGUNDO_COLOR, lw=2, marker="o",
              ms=5, markeredgecolor="white")
    _estilo(ax_g, "El grupo se achica y los casos se concentran", "Semana de la campaña",
            "Porcentaje")
    ax_r.plot(semanas, _numerica(total["recall_azar"]), color=NEUTRO, lw=1.6, ls="--",
              marker="s", ms=4, markeredgecolor="white")
    ax_r.plot(semanas, _numerica(total["recall"]), color=REGLA_COLOR, lw=2, marker="o", ms=5,
              markeredgecolor="white")
    _estilo(ax_r, "Casos que contendría una lista de k familias hecha esa semana",
            "Semana de la campaña", "Recall (casos en la lista)")
    for ax in (ax_g, ax_r):
        ax.yaxis.set_major_formatter(PORCENTAJE)
        ax.set_xticks(semanas)
        ax.set_ylim(0, 1.05)
    _titulo(fig, "Esperar concentra los casos, pero deja menos tiempo para ayudar",
            f"Familias que siguen sin pagar cada semana · cohortes {cohortes} · C5 no interviene")
    _leyenda(fig, [
        Patch(color=CLARO[NEUTRO], label="Familias que aún no pagan"),
        Line2D([], [], color=SEGUNDO_COLOR, lw=2, marker="o", ms=5, markeredgecolor="white",
               label="Casos entre las pendientes"),
        Line2D([], [], color=REGLA_COLOR, lw=2, marker="o", ms=5, markeredgecolor="white",
               label="Lista con la regla D2"),
        Line2D([], [], color=NEUTRO, lw=1.6, ls="--", marker="s", ms=4,
               markeredgecolor="white", label="Lista al azar entre pendientes")])
    _ajustar(fig)
    return fig


def figura_campana(estrategias: pd.DataFrame, cohortes: str) -> Figure:
    """Tres formas de usar los mismos k contactos, con regla y al azar."""
    total = estrategias[estrategias["cohorte"] == TODAS].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11, 4.6))
    _estilo(ax, "", "Casos alcanzados (recall)", "")
    posiciones = np.arange(len(total))
    for y, fila in zip(posiciones, total.itertuples(), strict=True):
        color = REGLA_COLOR if fila.estrategia.endswith("d2") else NEUTRO
        recall, pronto = _numero(fila.recall), _numero(fila.recall_primera_mitad)
        sin_usar, margen = _numero(fila.cupos_sin_usar), _numero(fila.margen_medio_dias)
        if np.isnan(recall):
            ax.text(0.01, y, "no publicable", va="center", fontsize=8.5, color=TINTA_SUAVE)
            continue
        ax.barh(y, recall, color=CLARO[color], height=0.6)
        partes = [f"{_pct(recall)} en total"]
        if not np.isnan(pronto):
            ax.barh(y, pronto, color=color, height=0.6)
            partes.append(f"{_pct(pronto)} en la primera mitad")
        if not np.isnan(margen):
            partes.append(f"margen medio {numero(margen, 0)} días")
        if not np.isnan(sin_usar) and sin_usar >= 0.5 and fila.cupos:
            partes.append(f"{_pct(sin_usar / fila.cupos)} de cupos sin usar")
        ax.text(recall, y, "  " + " · ".join(partes), va="center", fontsize=8.3, color=TINTA)
    ax.set_yticks(posiciones, total["descripcion"])
    ax.invert_yaxis()
    ax.set_xlim(0, 2.25)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.xaxis.set_major_formatter(PORCENTAJE)
    ax.tick_params(axis="y", labelsize=9, colors=TINTA)
    ax.grid(axis="y", visible=False)
    ax.axvline(1.0, color=REJILLA, lw=1)
    _titulo(fig, "Tres formas de usar los mismos contactos",
            f"Simulación con las fechas de pago históricas · cohortes {cohortes} · "
            "C5 no interviene")
    _leyenda(fig, [Patch(color=CLARO[REGLA_COLOR], label="Casos alcanzados en toda la campaña"),
                   Patch(color=REGLA_COLOR, label="Alcanzados en la primera mitad"),
                   Patch(color=NEUTRO, label="Sin regla (al azar)")], 3)
    _ajustar(fig)
    return fig
