"""
Figuras de la simulación de escenarios críticos (`src/escenarios.py`, D57).

Mismo estilo que las figuras del diagnóstico: 300 DPI, coma decimal, título que dice qué
se compara y leyenda. Azul = regla D2, rosa = logística híbrida. La línea discontinua gris
es el azar (Lift = 1) y la punteada, el umbral de utilidad (Lift = 1,20). Las bandas van
del percentil 5 al 95 de las repeticiones.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from src.diagnostico import numero
from src.escenarios import HIBRIDO, REGLA, SENALES, UMBRAL_UTIL
from src.graficos_alcance import PORCENTAJE, _leyenda
from src.graficos_diagnostico import ENTRENAMIENTO as AZUL
from src.graficos_diagnostico import NEUTRO, TINTA, TINTA_SUAVE, _ajustar, _estilo, _titulo, guardar
from src.graficos_diagnostico import VALIDACION as ROSA

__all__ = ["figura_degradacion", "figura_cambio", "guardar"]

COLORES = {REGLA: AZUL, HIBRIDO: ROSA}
# Panel de faltantes: solo la regla D2, así que sus tres señales van en tonos de azul y con
# otro trazo, para no confundirlas con la logística híbrida (rosa).
COLOR_SENAL = {"pago_tardio": "#1B3F66", "reserva_extraordinaria": AZUL,
               "atrasos_pension": "#7FA8CF", "promedio": NEUTRO}
TRAZO_SENAL = {"pago_tardio": "-", "reserva_extraordinaria": "--", "atrasos_pension": ":"}
CORTOS = {"pago_tardio": "Pago tardío", "reserva_extraordinaria": "Reserva extraordinaria",
          "atrasos_pension": "Pensiones tarde", "promedio": "Promedio",
          "todas_d2": "Las tres de D2", "ninguna": "Sin perturbar"}


def _referencias(ax, umbral: float = UMBRAL_UTIL) -> None:
    ax.axhline(1.0, color=NEUTRO, lw=1.1, ls="--")
    ax.axhline(umbral, color=TINTA_SUAVE, lw=0.9, ls=":")


def _num(serie: pd.Series) -> np.ndarray:
    return pd.to_numeric(serie, errors="coerce").to_numpy(dtype=float)


def _curva(ax, tabla: pd.DataFrame, color: str, etiqueta: str | None = None,
           x_col: str = "nivel", trazo: str = "-") -> None:
    tabla = tabla.assign(_x=pd.to_numeric(tabla[x_col], errors="coerce")).sort_values("_x")
    x = tabla["_x"].to_numpy(dtype=float)
    ax.plot(x, _num(tabla["lift_k"]), color=color, lw=2, ls=trazo, marker="o", ms=4,
            markeredgecolor="white", label=etiqueta)
    if "lift_k_p05" in tabla:
        ax.fill_between(x, _num(tabla["lift_k_p05"]), _num(tabla["lift_k_p95"]), color=color,
                        alpha=0.13, lw=0)


def figura_degradacion(resultados: pd.DataFrame, cohorte: str = "C4",
                       umbral: float = UMBRAL_UTIL) -> Figure:
    """Lift@k de la lista según el tipo y el nivel de perturbación (cuatro paneles)."""
    fig, ejes = plt.subplots(2, 2, figsize=(11.5, 8.2))
    (ax_r, ax_f), (ax_d, ax_c) = ejes

    ruido = resultados[(resultados["escenario"] == "ruido")
                       & (resultados["variable"] == "errores_registro")]
    for sistema, grupo in ruido.groupby("sistema", sort=False):
        _curva(ax_r, grupo, COLORES.get(sistema, NEUTRO))
    _referencias(ax_r, umbral)
    _estilo(ax_r, "1 · Errores de registro en las tres señales",
            "Probabilidad de error por señal y estudiante", "Lift@k")
    ax_r.xaxis.set_major_formatter(PORCENTAJE)

    falt = resultados[(resultados["escenario"] == "faltantes")
                      & (resultados["sistema"] == REGLA)]
    for senal, grupo in falt.groupby("variable", sort=False):
        _curva(ax_f, grupo, COLOR_SENAL.get(senal, NEUTRO), CORTOS.get(senal, senal),
               trazo=TRAZO_SENAL.get(senal, "-"))
    _referencias(ax_f, umbral)
    _estilo(ax_f, "2 · Datos faltantes en una señal (regla D2)", "Fracción de la señal vacía",
            "Lift@k")
    ax_f.xaxis.set_major_formatter(PORCENTAJE)
    ax_f.legend(frameon=False, fontsize=8, labelcolor=TINTA, loc="lower left")

    desb = resultados[resultados["escenario"] == "desbalance"].copy()
    if not desb.empty:
        desb["nivel"] = desb["tasa_real"]
        for sistema, grupo in desb.groupby("sistema", sort=False):
            _curva(ax_d, grupo, COLORES.get(sistema, NEUTRO))
        ax_d.invert_xaxis()
    _referencias(ax_d, umbral)
    _estilo(ax_d, "3 · Desbalance extremo: menos familias con caso",
            "Tasa familiar del evento (a la derecha, más extremo)", "Lift@k")
    ax_d.xaxis.set_major_formatter(PORCENTAJE)

    caida = resultados[resultados["escenario"] == "senal_caida"]
    orden = ["ninguna", *SENALES, "todas_d2"]
    variables = [v for v in orden if v in set(caida["variable"])]
    y = np.arange(len(variables))
    alto = 0.38
    for desplazamiento, sistema in ((-alto / 2, REGLA), (alto / 2, HIBRIDO)):
        sub = caida[caida["sistema"] == sistema].set_index("variable")
        valores = [float(sub.loc[v, "lift_k"]) if v in sub.index else np.nan for v in variables]
        ax_c.barh(y + desplazamiento, valores, height=alto, color=COLORES[sistema])
        for i, v in enumerate(valores):
            if np.isfinite(v):
                ax_c.text(v + 0.02, i + desplazamiento, numero(v, 2), va="center", fontsize=7.5,
                          color=TINTA)
    ax_c.axvline(1.0, color=NEUTRO, lw=1.1, ls="--")
    ax_c.axvline(umbral, color=TINTA_SUAVE, lw=0.9, ls=":")
    _estilo(ax_c, "4 · Una señal llega constante", "Lift@k", "")
    ax_c.set_yticks(y, [CORTOS.get(v, v) for v in variables], fontsize=8.5)
    ax_c.invert_yaxis()
    ax_c.grid(axis="y", visible=False)

    _titulo(fig, "Escenarios críticos: hasta dónde la lista sigue siendo útil",
            f"Perturbaciones sobre la cohorte {cohorte} con el sistema ya elegido · C5 no "
            "interviene · banda: percentiles 5 a 95 de las repeticiones")
    _leyenda(fig, [Line2D([], [], color=AZUL, lw=2, marker="o", ms=4, markeredgecolor="white",
                          label="Regla D2"),
                   Line2D([], [], color=ROSA, lw=2, marker="o", ms=4, markeredgecolor="white",
                          label="Logística híbrida"),
                   Line2D([], [], color=NEUTRO, lw=1.1, ls="--", label="Azar (Lift = 1)"),
                   Line2D([], [], color=TINTA_SUAVE, lw=0.9, ls=":",
                          label=f"Umbral de utilidad ({numero(umbral, 2)})")], 4)
    _ajustar(fig)
    return fig


def figura_cambio(cambio: pd.DataFrame) -> Figure:
    """Entrenar con un subgrupo y probar con otro: discriminación y calibración."""
    fig, (ax_p, ax_o) = plt.subplots(1, 2, figsize=(11.5, 4.4))
    etiqueta = {"0": "no becados", "1": "becados"}
    direcciones = cambio[["corte", "origen", "destino"]].drop_duplicates().to_records(index=False)
    nombres = [f"{etiqueta.get(o, o)} → {etiqueta.get(d, d)}" for _, o, d in direcciones]
    y = np.arange(len(direcciones))
    modelos = (("transferido", ROSA), ("referencia (todos)", "#EBCBD5"),
               ("regla D2 (sin aprendizaje)", AZUL))
    alto = 0.26
    for i, (modelo, color) in enumerate(modelos):
        valores, razones = [], []
        for corte, o, d in direcciones:
            fila = cambio[(cambio["corte"] == corte) & (cambio["origen"] == o)
                          & (cambio["destino"] == d) & (cambio["modelo"] == modelo)]
            valores.append(float(fila["pr_auc"].iloc[0]) if not fila.empty else np.nan)
            razones.append(float(fila["observados_sobre_esperados"].iloc[0])
                           if not fila.empty else np.nan)
        desplazamiento = (i - 1) * alto
        ax_p.barh(y + desplazamiento, valores, height=alto, color=color)
        if modelo != "regla D2 (sin aprendizaje)":
            ax_o.barh(y + desplazamiento + alto / 2, razones, height=alto, color=color)
    ax_o.axvline(1.0, color=NEUTRO, lw=1.1, ls="--")
    _estilo(ax_p, "Discriminación en el grupo de destino", "PR-AUC (mayor es mejor)", "")
    _estilo(ax_o, "Calibración en el grupo de destino",
            "Observados / esperados (1 = bien calibrado)", "")
    for ax in (ax_p, ax_o):
        ax.set_yticks(y, nombres, fontsize=8.5)
        ax.invert_yaxis()
        ax.grid(axis="y", visible=False)
    _titulo(fig, "Cambio de distribución: entrenar con un grupo y probar con otro",
            "Logística híbrida en C4 · origen → destino · los grupos con menos de 5 casos "
            "no se muestran")
    _leyenda(fig, [Patch(color=ROSA, label="Entrenada con el grupo de origen"),
                   Patch(color="#EBCBD5", label="Entrenada con todos (Fase 2)"),
                   Patch(color=AZUL, label="Regla D2 (no aprende)")], 3)
    _ajustar(fig)
    return fig
