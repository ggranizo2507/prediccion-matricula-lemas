"""
Figura del análisis de costo esperado (`src/costo.py`).

Mismo estilo que las figuras del diagnóstico y del alcance: 300 DPI, coma decimal, título
que dice qué se compara y leyenda. Azul para la regla D2, gris para el azar y rosa oscuro
para la segunda llamada a quienes siguen sin pagar.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from src.diagnostico import numero
from src.graficos_alcance import CLARO, PORCENTAJE, _leyenda
from src.graficos_diagnostico import ENTRENAMIENTO as REGLA_COLOR
from src.graficos_diagnostico import NEUTRO, TINTA, TINTA_SUAVE, _ajustar, _estilo, _titulo, guardar
from src.graficos_diagnostico import VALIDACION as SEGUNDO_COLOR

__all__ = ["figura_costo", "guardar"]

ETIQUETAS = {
    "azar": "Al azar (k)",
    "primera_mitad": "Lista D2: primera mitad",
    "lista_k": "Lista D2 completa (k)",
    "tramo_k_2k": "Alargar la lista de k a 2k",
    "lista_k_c5": "Lista D2 (k) · prueba C5",
    "azar_c5": "Al azar (k) · prueba C5",
}
GROSORES = {50: 1.0, 100: 1.6, 200: 2.4}


def _color(escenario: str) -> str:
    if escenario.startswith("azar"):
        return NEUTRO
    if escenario.startswith("pendientes"):
        return SEGUNDO_COLOR
    return REGLA_COLOR


def figura_costo(
    equilibrio: pd.DataFrame, curva: pd.DataFrame, cohorte: str = "C4", eficacia: float = 0.10
) -> Figure:
    """Razón de equilibrio por escenario y beneficio neto según el tamaño de la lista."""
    col = f"razon_equilibrio_e{int(round(100 * eficacia))}"
    fig, (ax_e, ax_b) = plt.subplots(
        1, 2, figsize=(11.5, 4.6), gridspec_kw={"width_ratios": [1.05, 1]}
    )

    tabla = equilibrio.iloc[::-1].reset_index(drop=True)
    etiquetas, valores, colores = [], [], []
    for _, fila in tabla.iterrows():
        esc = str(fila["escenario"])
        if esc.startswith("pendientes_semana_"):
            etiqueta = f"Pendientes en la semana {esc.rsplit('_', 1)[1]}"
        else:
            etiqueta = ETIQUETAS.get(esc, esc)
        etiquetas.append(etiqueta)
        valores.append(float(fila[col]))
        es_c5 = str(fila["cohorte"]) == "C5"
        colores.append(CLARO[_color(esc)] if es_c5 else _color(esc))
    y = np.arange(len(valores))
    ax_e.barh(y, valores, color=colores, height=0.62)
    for i, v in enumerate(valores):
        if np.isfinite(v):
            ax_e.text(
                v + max(valores) * 0.015, i, numero(v, 0), va="center", fontsize=8.5, color=TINTA
            )
    _estilo(
        ax_e,
        "Cuánto debe valer un caso para que llamar compense",
        "Razón de equilibrio cFN / cFP (en llamadas; menor es mejor)",
        "",
    )
    ax_e.set_yticks(y, etiquetas, fontsize=8.5)
    ax_e.set_xlim(0, max(valores) * 1.15)
    ax_e.grid(axis="y", visible=False)

    datos = curva[(np.isclose(curva["eficacia"], eficacia)) & (curva["cohorte"] == cohorte)]
    ax_b.axhline(0, color=TINTA_SUAVE, lw=0.8)
    for razon, grupo in datos.groupby("razon"):
        grupo = grupo.sort_values("pct_familias")
        grosor = GROSORES.get(int(razon), 1.4)
        ax_b.plot(
            grupo["pct_familias"],
            grupo["beneficio_lista"],
            color=REGLA_COLOR,
            lw=grosor,
            marker="o",
            ms=3.5,
            markeredgecolor="white",
        )
        ax_b.plot(grupo["pct_familias"], grupo["beneficio_azar"], color=NEUTRO, lw=grosor, ls="--")
        ultimo = grupo.iloc[-1]
        ax_b.annotate(
            f"R = {int(razon)}",
            xy=(ultimo["pct_familias"], ultimo["beneficio_lista"]),
            xytext=(4, 0),
            textcoords="offset points",
            fontsize=8,
            color=TINTA_SUAVE,
            va="center",
        )
    k = datos[datos["multiplicador"].astype(str).isin({"1.0", "1"})]
    if not k.empty:
        ax_b.axvline(float(k.iloc[0]["pct_familias"]), color=NEUTRO, lw=0.8, ls=":")
        ax_b.annotate(
            "k aprobado",
            xy=(float(k.iloc[0]["pct_familias"]), ax_b.get_ylim()[1]),
            xytext=(4, -10),
            textcoords="offset points",
            fontsize=8,
            color=TINTA_SUAVE,
        )
    _estilo(
        ax_b,
        "Beneficio neto según el tamaño de la lista",
        "Familias contactadas",
        "Beneficio neto (en llamadas)",
    )
    ax_b.xaxis.set_major_formatter(PORCENTAJE)
    ax_b.set_xlim(0, 1.12)

    _titulo(
        fig,
        "Costo esperado: cuándo compensa llamar y cuántas llamadas hacer",
        f"Una llamada rescata al {numero(100 * eficacia, 0)} % de los casos (supuesto) · "
        f"R = cuántas llamadas vale un caso rescatado · cohorte {cohorte}; "
        "tonos claros: prueba C5 ya publicada",
    )
    _leyenda(
        fig,
        [
            Line2D(
                [],
                [],
                color=REGLA_COLOR,
                lw=2,
                marker="o",
                ms=4,
                markeredgecolor="white",
                label="Lista D2",
            ),
            Line2D([], [], color=NEUTRO, lw=1.6, ls="--", label="Al azar"),
            Line2D([], [], color=SEGUNDO_COLOR, lw=6, label="Segunda llamada a pendientes (C2–C4)"),
        ],
        3,
    )
    _ajustar(fig)
    return fig
