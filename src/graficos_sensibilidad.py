"""
Figuras del análisis de sensibilidad de hiperparámetros (`src/sensibilidad.py`).

Mismo estilo que las demás figuras del proyecto: 300 DPI, coma decimal, título que dice qué
se compara. Un color por modelo, el mismo en las tres figuras.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.patches import Patch
from optuna.distributions import CategoricalDistribution

from src.diagnostico import numero
from src.graficos_alcance import _leyenda
from src.graficos_diagnostico import ENTRENAMIENTO as AZUL
from src.graficos_diagnostico import NEUTRO, TINTA, TINTA_SUAVE, _ajustar, _estilo, _titulo, guardar
from src.graficos_diagnostico import VALIDACION as ROSA
from src.sensibilidad import ESPACIOS

__all__ = ["figura_importancia", "figura_dependencia", "figura_interacciones", "guardar"]

COLORES = {"Regresión logística": AZUL, "Gradient boosting": "#3C7A6E", "Logística híbrida": ROSA}
ESCALA_LOG = {
    n for espacio in ESPACIOS.values() for n, d in espacio.items() if getattr(d, "log", False)
}
CATEGORICOS = {
    n
    for espacio in ESPACIOS.values()
    for n, d in espacio.items()
    if isinstance(d, CategoricalDistribution)
}
TEXTO = {"True": "Sí", "False": "No", "completo": "completo", "reducido": "reducido"}


def _etiquetas_codigo(nombre: str) -> dict[float, str]:
    """Código 1/0 de una categoría (1 = primera opción del espacio) → texto legible."""
    for espacio in ESPACIOS.values():
        if nombre in espacio:
            a, b = espacio[nombre].choices
            return {1.0: TEXTO.get(str(a), str(a)), 0.0: TEXTO.get(str(b), str(b))}
    return {1.0: "1", 0.0: "0"}


def figura_importancia(importancia: pd.DataFrame) -> Figure:
    """Ranking de importancia de hiperparámetros por modelo (fANOVA e impureza)."""
    modelos = list(dict.fromkeys(importancia["modelo"]))
    fig, ejes = plt.subplots(
        1,
        len(modelos),
        figsize=(12.5, 4.6),
        gridspec_kw={"width_ratios": [4, 8, 2][: len(modelos)]},
    )
    for ax, modelo in zip(np.atleast_1d(ejes), modelos, strict=True):
        datos = importancia[importancia["modelo"] == modelo]
        fan = datos[datos["metodo"] == "fANOVA"].sort_values("importancia")
        imp = datos[datos["metodo"] == "Impureza"].set_index("hiperparametro")
        y = np.arange(len(fan))
        color = COLORES.get(modelo, NEUTRO)
        ax.barh(
            y + 0.2,
            fan["importancia"],
            height=0.38,
            color=color,
            xerr=fan["desviacion"],
            error_kw={"ecolor": TINTA_SUAVE, "lw": 0.8},
        )
        ax.barh(
            y - 0.2,
            imp.loc[fan["hiperparametro"], "importancia"],
            height=0.38,
            color=color,
            alpha=0.35,
        )
        for i, v in enumerate(fan["importancia"]):
            ax.text(
                v + 0.02, i + 0.2, f"{numero(100 * v, 0)} %", va="center", fontsize=8, color=TINTA
            )
        _estilo(ax, modelo, "Importancia (suma 1 por modelo)", "")
        ax.set_yticks(y, fan["hiperparametro"], fontsize=8.5)
        ax.set_xlim(0, 1.15)
        ax.grid(axis="y", visible=False)
    _titulo(
        fig,
        "Qué hiperparámetros explican la PR-AUC de la validación interna",
        "180 pruebas de Optuna (60 por modelo) · validación C2 → C3 · barra de error: "
        "desviación entre 5 semillas",
    )
    _leyenda(
        fig,
        [
            Patch(color=TINTA_SUAVE, label="fANOVA"),
            Patch(color=TINTA_SUAVE, alpha=0.35, label="Disminución de impureza"),
        ],
        2,
    )
    _ajustar(fig)
    return fig


def figura_dependencia(
    dependencia: pd.DataFrame,
    pruebas: dict[str, pd.DataFrame],
    tasa: float | None = None,
    por_modelo: int = 3,
) -> Figure:
    """Dependencia parcial de los hiperparámetros más importantes de cada modelo."""
    modelos = list(dict.fromkeys(dependencia["modelo"]))
    fig, ejes = plt.subplots(
        len(modelos), por_modelo, figsize=(12, 3.2 * len(modelos)), squeeze=False
    )
    for fila, modelo in enumerate(modelos):
        datos = dependencia[dependencia["modelo"] == modelo]
        nombres = list(dict.fromkeys(datos["hiperparametro"]))[:por_modelo]
        color = COLORES.get(modelo, NEUTRO)
        for col in range(por_modelo):
            ax = ejes[fila][col]
            if col >= len(nombres):
                ax.axis("off")
                continue
            nombre = nombres[col]
            curva = datos[datos["hiperparametro"] == nombre]
            observadas = pruebas[modelo]
            _estilo(
                ax,
                f"{modelo} · {nombre}" if col == 0 else nombre,
                nombre,
                "PR-AUC (sustituto)" if col == 0 else "",
            )
            if nombre not in CATEGORICOS:
                x = pd.to_numeric(curva["valor"], errors="coerce")
                ax.plot(x, curva["pr_auc"], color=color, lw=2)
                ax.scatter(
                    observadas[nombre].astype(float),
                    observadas["value"],
                    s=9,
                    color=color,
                    alpha=0.3,
                    lw=0,
                )
                if nombre in ESCALA_LOG:
                    ax.set_xscale("log")
            else:
                etiquetas = _etiquetas_codigo(nombre)
                codigos = pd.to_numeric(curva["valor_codificado"]).tolist()
                ax.bar(range(len(codigos)), curva["pr_auc"], color=color, width=0.55)
                ax.set_xticks(range(len(codigos)), [etiquetas[c] for c in codigos])
                bajo = float(curva["pr_auc"].min())
                ax.set_ylim(bajo * 0.97, float(curva["pr_auc"].max()) * 1.02)
            if tasa and nombre not in CATEGORICOS:
                ax.axhline(tasa, color=NEUTRO, lw=1, ls="--")
    _titulo(
        fig,
        "Dependencia parcial: cómo cambia la PR-AUC con cada hiperparámetro",
        "Línea: efecto promedio estimado con un bosque aleatorio entrenado con las pruebas · "
        "puntos: pruebas observadas · línea discontinua: azar (tasa de C3)",
    )
    _ajustar(fig, abajo=0.15)
    return fig


def figura_interacciones(
    interacciones: pd.DataFrame, mapas: dict[str, pd.DataFrame], pares: dict[str, tuple[str, str]]
) -> Figure:
    """H² de Friedman por par y dependencia parcial 2D del par más fuerte de cada modelo."""
    modelos = list(mapas)
    fig, ejes = plt.subplots(
        1,
        1 + len(modelos),
        figsize=(13, 4.4),
        gridspec_kw={"width_ratios": [1.5] + [1] * len(modelos)},
    )
    ax = ejes[0]
    top = interacciones.groupby("modelo", sort=False).head(3).iloc[::-1]
    y = np.arange(len(top))
    ax.barh(y, top["h2"], color=[COLORES.get(m, NEUTRO) for m in top["modelo"]], height=0.6)
    for i, v in enumerate(top["h2"]):
        ax.text(v + 0.005, i, numero(v, 2), va="center", fontsize=8, color=TINTA)
    _estilo(ax, "Fuerza de las interacciones (H² de Friedman)", "H² (0 = sin interacción)", "")
    ax.set_yticks(y, top["par"], fontsize=8)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, max(0.3, float(top["h2"].max()) * 1.3))
    for ax, modelo in zip(ejes[1:], modelos, strict=True):
        mapa = mapas[modelo]
        a, b = pares[modelo]
        tabla = mapa.pivot(index="b", columns="a", values="pr_auc")
        imagen = ax.imshow(
            tabla.to_numpy(),
            origin="lower",
            aspect="auto",
            cmap="Blues",
            extent=[tabla.columns.min(), tabla.columns.max(), tabla.index.min(), tabla.index.max()],
        )
        sufijo_a = " (log10)" if a in ESCALA_LOG else ""
        sufijo_b = " (log10)" if b in ESCALA_LOG else ""
        _estilo(ax, modelo, f"{a}{sufijo_a}", f"{b}{sufijo_b}")
        ax.grid(False)
        for eje, nombre, valores in ((ax.xaxis, a, tabla.columns), (ax.yaxis, b, tabla.index)):
            if nombre in CATEGORICOS:
                etiquetas = _etiquetas_codigo(nombre)
                bajo, alto = float(min(valores)), float(max(valores))
                paso = (alto - bajo) / len(valores)
                centros = [bajo + paso * (i + 0.5) for i in range(len(valores))]
                eje.set_ticks(centros, [etiquetas[float(v)] for v in sorted(valores)])
        barra = fig.colorbar(imagen, ax=ax, fraction=0.046, pad=0.04)
        barra.ax.tick_params(labelsize=7)
    _leyenda(fig, [Patch(color=c, label=m) for m, c in COLORES.items()], 3)
    _titulo(
        fig,
        "Interacciones entre hiperparámetros",
        "Izquierda: los tres pares más fuertes de cada modelo · derecha: PR-AUC estimada "
        "para el par más fuerte (más oscuro = mejor)",
    )
    _ajustar(fig)
    return fig
