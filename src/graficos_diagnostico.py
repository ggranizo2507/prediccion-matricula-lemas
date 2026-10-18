"""
Figuras del diagnóstico de sobreajuste y subajuste (actividad de la semana 3).

Requisitos de la actividad que cumple cada figura: 300 DPI (config.yaml), título
descriptivo, ejes rotulados, leyenda, colores contrastantes para entrenamiento y
validación, cuadrícula y anotaciones en los puntos críticos.

Colores: azul para entrenamiento y rosa oscuro para validación. El par se comprobó con
un validador de paletas: la diferencia de color mínima entre ambos es ΔE 13 con
protanopía (el objetivo es 8 o más) y los dos superan el contraste 3:1 sobre blanco.
La validación lleva además marcadores redondos, para que la identidad no dependa solo
del color.

Las notas se colocan de forma automática en la zona del panel más alejada de las
curvas (`_mejor_posicion`), para que no tapen los datos.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, ScalarFormatter

from src.diagnostico import numero

ENTRENAMIENTO = "#2F6FA7"
VALIDACION = "#B03A5B"
TINTA = "#1F2933"          # texto principal
TINTA_SUAVE = "#5B6670"    # texto secundario y anotaciones
REJILLA = "#E3E6EA"
NEUTRO = "#8A939C"         # referencias (azar, valor de la Fase 2, «antes»)
ETIQUETAS_HIPERPARAMETRO = {"C": ("C (menos regularización →)", "C"),
                            "learning_rate": ("Tasa de aprendizaje (más ajuste →)", "tasa")}


# --------------------------------------------------------------------------- #
# Piezas comunes
# --------------------------------------------------------------------------- #
class _ConComa(ScalarFormatter):
    """Marcas de los ejes con coma decimal, como en el resto de la documentación."""

    def __call__(self, x, pos=None):
        return super().__call__(x, pos).replace(".", ",")


def _estilo(ax, titulo: str, xlabel: str, ylabel: str) -> None:
    for eje in (ax.xaxis, ax.yaxis):
        if eje.get_scale() == "linear":
            eje.set_major_formatter(_ConComa())
    ax.set_title(titulo, fontsize=10, color=TINTA, loc="left", pad=8)
    ax.set_xlabel(xlabel, fontsize=9, color=TINTA_SUAVE)
    ax.set_ylabel(ylabel, fontsize=9, color=TINTA_SUAVE)
    ax.grid(True, color=REJILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(REJILLA)
    ax.tick_params(colors=TINTA_SUAVE, labelsize=8, length=0)


def _leyenda(fig: Figure, extra: list | None = None) -> None:
    claves = [Line2D([], [], color=ENTRENAMIENTO, lw=2, label="Entrenamiento"),
              Line2D([], [], color=VALIDACION, lw=2, marker="o", ms=5,
                     markeredgecolor="white", label="Validación")]
    fig.legend(handles=claves + (extra or []), loc="lower center", ncol=4, frameon=False,
               fontsize=9, labelcolor=TINTA, bbox_to_anchor=(0.5, 0.0))


def _titulo(fig: Figure, titulo: str, subtitulo: str) -> None:
    """Título y subtítulo arriba a la izquierda, a distancia fija del borde."""
    alto = fig.get_figheight()
    fig.text(0.01, 1 - 0.12 / alto, titulo, fontsize=13, color=TINTA, ha="left", va="top",
             fontweight="bold")
    fig.text(0.01, 1 - 0.42 / alto, subtitulo, fontsize=9.5, color=TINTA_SUAVE, ha="left",
             va="top")


def _ajustar(fig: Figure) -> None:
    alto = fig.get_figheight()
    fig.tight_layout(rect=(0, 0.42 / alto, 1, 1 - 0.72 / alto))


def _en_ejes(ax, x, y) -> np.ndarray:
    """Convierte puntos de datos a fracción de los ejes (0–1), también en escala log."""
    puntos = np.column_stack([np.asarray(x, dtype=float), np.asarray(y, dtype=float)])
    return ax.transAxes.inverted().transform(ax.transData.transform(puntos))


def _mejor_posicion(ax, curvas: list[tuple], ancla: tuple, ancho: float = 0.40,
                    alto: float = 0.17) -> tuple[float, float]:
    """Centro (en fracción de ejes) de la caja de texto que queda más lejos de las curvas.

    Recorre una rejilla de posiciones dentro del panel y elige la que maximiza la
    distancia a todas las curvas, con una pequeña preferencia por quedar cerca del punto
    anotado. `curvas` es una lista de (x, y) en coordenadas de datos.
    """
    tramos = []
    for x, y in curvas:
        vertices = _en_ejes(ax, x, y)
        tramos.append(vertices)
        for t in (0.2, 0.4, 0.6, 0.8):        # puntos intermedios entre vértices
            tramos.append(vertices[:-1] + t * (vertices[1:] - vertices[:-1]))
    obstaculos = np.vstack(tramos)
    punto = _en_ejes(ax, [ancla[0]], [ancla[1]])[0]
    mejor, mejor_valor = (0.5, 0.5), -np.inf
    for cx in np.linspace(ancho / 2 + 0.03, 1 - ancho / 2 - 0.03, 9):
        for cy in np.linspace(alto / 2 + 0.05, 1 - alto / 2 - 0.09, 9):
            dx = np.maximum(np.abs(obstaculos[:, 0] - cx) - ancho / 2, 0)
            dy = np.maximum(np.abs(obstaculos[:, 1] - cy) - alto / 2, 0)
            libre = float(np.hypot(dx, dy).min())           # 0 si alguna curva cruza la caja
            cercania = float(np.hypot(cx - punto[0], cy - punto[1]))
            valor = min(libre, 0.12) - 0.08 * cercania
            if valor > mejor_valor:
                mejor, mejor_valor = (cx, cy), valor
    return mejor


def _nota(ax, texto: str, ancla: tuple, curvas: list[tuple]) -> None:
    """Nota con una línea guía hasta el punto, colocada donde no tapa las curvas."""
    lineas = texto.count("\n") + 1
    centro = _mejor_posicion(ax, curvas, ancla, alto=0.075 * lineas + 0.03)
    ax.annotate(texto, xy=ancla, xycoords="data", xytext=centro, textcoords="axes fraction",
                fontsize=8, color=TINTA_SUAVE, ha="center", va="center",
                arrowprops={"arrowstyle": "-", "color": NEUTRO, "lw": 0.8,
                            "shrinkA": 2, "shrinkB": 5})


def _azar(ax, tasa: float | None, validacion: np.ndarray | None = None) -> None:
    """Línea del azar. La etiqueta va en el lado donde la validación está más lejos."""
    if tasa is None:
        return
    ax.axhline(tasa, color=NEUTRO, lw=1)
    a_la_derecha = True
    if validacion is not None and len(validacion):
        a_la_derecha = abs(validacion[-1] - tasa) >= abs(validacion[0] - tasa)
    ax.text(0.99 if a_la_derecha else 0.01, tasa, f" azar = {numero(tasa)} ", fontsize=8,
            color=TINTA_SUAVE, va="top", ha="right" if a_la_derecha else "left",
            transform=ax.get_yaxis_transform())


def _brecha(ax, x: float, y_tr: float, y_val: float) -> None:
    """Flecha doble entre entrenamiento y validación; se omite si la brecha no se ve."""
    bajo, alto = ax.get_ylim()
    if abs(y_tr - y_val) >= 0.08 * (alto - bajo):
        ax.annotate("", xy=(x, y_tr), xytext=(x, y_val),
                    arrowprops={"arrowstyle": "<->", "color": NEUTRO, "lw": 1})


def guardar(fig: Figure, ruta: Path, dpi: int = 300) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=dpi, bbox_inches="tight", facecolor="white")
    return ruta


# --------------------------------------------------------------------------- #
# A y B. Curvas durante el entrenamiento
# --------------------------------------------------------------------------- #
def _referencia_perdida(ax, valor: float | None) -> None:
    """Pérdida de un modelo sin variables (predice a todos la tasa del entrenamiento)."""
    if valor is None:
        return
    ax.axhline(valor, color=NEUTRO, lw=1, ls=":")     # el valor va en la leyenda


def _limites_comunes(seguimientos: dict[str, pd.DataFrame], nombres: list[str],
                     metrica: str, referencia: float | None) -> tuple[float, float]:
    valores = [v for nombre in nombres for conjunto in ("entrenamiento", "validacion")
               for v in seguimientos[nombre][f"{metrica}_{conjunto}"].to_numpy()]
    if referencia is not None:
        valores.append(referencia)
    bajo, alto = float(np.nanmin(valores)), float(np.nanmax(valores))
    margen = 0.22 * ((alto - bajo) or 0.01)
    return bajo - margen, alto + margen


def _panel_iteraciones(ax, s: pd.DataFrame, metrica: str, nombre: str, ylabel: str,
                       tasa: float | None, ylim: tuple[float, float] | None = None,
                       referencia: float | None = None, nota: str = "") -> None:
    x = s["iteracion"].to_numpy(dtype=float)
    tr = s[f"{metrica}_entrenamiento"].to_numpy()
    val = s[f"{metrica}_validacion"].to_numpy()
    pocos = len(x) <= 30
    ax.plot(x, tr, color=ENTRENAMIENTO, lw=2, marker="s" if pocos else None, ms=3.5)
    ax.plot(x, val, color=VALIDACION, lw=2, marker="o", ms=4.5, markeredgecolor="white",
            markevery=1 if pocos else max(1, len(x) // 12))
    unidad = s["unidad"].iloc[0] if "unidad" in s else "iteración"
    if unidad.startswith("iteración del optimizador") and x[-1] > 20:
        ax.set_xscale("log")
        unidad += ", escala log"
    es_perdida = metrica.startswith("perdida")
    # Brecha con signo: positiva cuando la validación es peor que el entrenamiento
    brecha = val[-1] - tr[-1] if es_perdida else tr[-1] - val[-1]
    _estilo(ax, f"{nombre}\n{nota + chr(10) if nota else ''}brecha al final: "
            f"{numero(brecha, signo=True)}",
            unidad[0].upper() + unidad[1:], ylabel)
    if ylim is not None:
        ax.set_ylim(*ylim)
    else:
        ax.margins(y=0.22)

    fase2 = s["iteracion_fase2"].iloc[0] if "iteracion_fase2" in s else np.nan
    curvas = [(x, tr), (x, val)]
    if pd.notna(fase2) and fase2 <= x[-1]:
        ax.axvline(fase2, color=NEUTRO, lw=1, ls=(0, (4, 3)))
        curvas.append((np.full(12, fase2), np.linspace(*ax.get_ylim(), 12)))
    if metrica == "puntaje" and tasa is not None:
        _azar(ax, tasa, val)
        curvas.append((x, np.full(len(x), tasa)))
    if es_perdida and referencia is not None:
        _referencia_perdida(ax, referencia)
        curvas.append((x, np.full(len(x), referencia)))
    _brecha(ax, x[-1], tr[-1], val[-1])

    critico = int(np.argmin(val) if es_perdida else np.argmax(val))
    etiqueta = "mínimo" if es_perdida else "máximo"
    ax.scatter([x[critico]], [val[critico]], s=70, color=VALIDACION, edgecolor="white",
               linewidth=2, zorder=5)
    _nota(ax, f"{etiqueta} de validación\niteración {int(x[critico])}: {numero(val[critico])}",
          (x[critico], val[critico]), curvas)


def figura_iteraciones(seguimientos: dict[str, pd.DataFrame], metrica: str,
                       etiqueta_tr: str, etiqueta_val: str, tasa: float | None = None,
                       columnas: int = 2, comun: list[str] | None = None,
                       referencia: float | None = None) -> Figure:
    """Curva A (metrica="perdida_sin_ponderar" o "perdida") o B ("puntaje").

    Un panel por modelo. Los modelos de `comun` comparten la escala vertical, para que se
    puedan comparar a simple vista; los demás (el control, que se aleja mucho) usan su
    propia escala y lo dicen en el título. Sin `comun`, cada panel tiene su escala.
    `referencia` dibuja la pérdida de validación de un modelo sin variables.

    La pérdida sin ponderar es la única comparable entre modelos. Aun así, los modelos
    entrenados con clases balanceadas dan probabilidades infladas (sin calibrar) y por
    eso tienen una pérdida mayor: el título del panel lo indica."""
    n = len(seguimientos)
    columnas = min(columnas, n)
    filas = int(np.ceil(n / columnas))
    fig, ejes = plt.subplots(filas, columnas, figsize=(4.9 * columnas, 3.7 * filas + 1.2),
                             squeeze=False)
    es_perdida = metrica.startswith("perdida")
    ylabel = {"perdida": "Pérdida ponderada (entropía cruzada; menor es mejor)",
              "perdida_sin_ponderar": "Pérdida sin ponderar (entropía cruzada; menor es mejor)",
              }.get(metrica, "PR-AUC (mayor es mejor)")
    comun = [nombre for nombre in (comun or []) if nombre in seguimientos]
    limites = (_limites_comunes(seguimientos, comun, metrica,
                                referencia if es_perdida else None) if comun else None)
    planos = list(ejes.ravel())
    for ax, (nombre, s) in zip(planos, seguimientos.items(), strict=False):
        notas = []
        if comun and nombre not in comun:
            notas.append("escala propia")
        if (metrica == "perdida_sin_ponderar" and "perdida_ponderada" in s
                and bool(s["perdida_ponderada"].iloc[0])):
            notas.append("clases balanceadas: probabilidades sin calibrar")
        _panel_iteraciones(ax, s, metrica, nombre, ylabel, tasa,
                           limites if nombre in comun else None,
                           referencia if es_perdida else None, " · ".join(notas))
    for ax in planos[n:]:
        ax.set_visible(False)
    letra, que = ("A", "Pérdida") if es_perdida else ("B", "PR-AUC")
    if comun:
        escala = ("escala común en los modelos de la Fase 2; el control usa la suya"
                  if len(comun) < n else "escala común en todos los paneles")
    else:
        escala = "cada panel tiene su propia escala: no se comparan alturas entre paneles"
    _titulo(fig, f"{letra}. {que} de entrenamiento y de validación durante el entrenamiento",
            f"Entrenamiento: {etiqueta_tr} · Validación: {etiqueta_val} · C5 no interviene · "
            + escala)
    extra = [Line2D([], [], color=NEUTRO, lw=1, ls=(0, (4, 3)),
                    label="Iteraciones elegidas en la Fase 2")]
    if es_perdida and referencia is not None:
        extra.append(Line2D([], [], color=NEUTRO, lw=1, ls=":",
                            label=f"Sin modelo (todos con la tasa del entrenamiento): "
                                  f"{numero(referencia)}"))
    _leyenda(fig, extra)
    _ajustar(fig)
    return fig


# --------------------------------------------------------------------------- #
# C. Curvas por tamaño del entrenamiento
# --------------------------------------------------------------------------- #
def figura_tamano(curvas: pd.DataFrame, etiqueta_tr: str, etiqueta_val: str,
                  tasa: float | None = None, metrica: str = "puntaje") -> Figure:
    datos = curvas[curvas["metrica"] == metrica]
    modelos = list(dict.fromkeys(datos["modelo"]))
    fig, ejes = plt.subplots(1, len(modelos), figsize=(3.9 * len(modelos), 4.5),
                             sharey=True, squeeze=False)
    paneles = []
    for ax, modelo in zip(ejes[0], modelos, strict=True):
        d = datos[datos["modelo"] == modelo].sort_values("n")
        for columna, color, marcador in (("entrenamiento", ENTRENAMIENTO, "s"),
                                         ("validacion", VALIDACION, "o")):
            ax.fill_between(d["n"], d[columna] - d[f"{columna}_de"],
                            d[columna] + d[f"{columna}_de"], color=color, alpha=0.12, lw=0)
            ax.plot(d["n"], d[columna], color=color, lw=2, marker=marcador,
                    ms=3.5 if marcador == "s" else 5, markeredgecolor="white")
        ultimo = d.iloc[-1]
        brecha = ultimo["entrenamiento"] - ultimo["validacion"]
        _estilo(ax, f"{modelo}\nbrecha con todos los datos: {numero(brecha, signo=True)}",
                "Estudiantes en el entrenamiento",
                "PR-AUC (mayor es mejor)" if metrica == "puntaje" else "Pérdida")
        ax.yaxis.set_tick_params(labelleft=True)
        paneles.append((ax, d, ultimo))
    for ax, d, ultimo in paneles:          # con el eje vertical común ya definido
        ax.margins(y=0.12)
        n = d["n"].to_numpy(dtype=float)
        curvas_panel = []
        for columna in ("entrenamiento", "validacion"):
            curvas_panel += [(n, (d[columna] + d[f"{columna}_de"]).to_numpy()),
                             (n, (d[columna] - d[f"{columna}_de"]).to_numpy())]
        if metrica == "puntaje" and tasa is not None:
            _azar(ax, tasa, d["validacion"].to_numpy())
            curvas_panel.append((n, np.full(len(n), tasa)))
        _brecha(ax, ultimo["n"], ultimo["entrenamiento"], ultimo["validacion"])
        ax.scatter([ultimo["n"]], [ultimo["validacion"]], s=70, color=VALIDACION,
                   edgecolor="white", linewidth=2, zorder=5)
        _nota(ax, f"con todos los datos\nvalidación {numero(ultimo['validacion'])}",
              (ultimo["n"], ultimo["validacion"]), curvas_panel)
    _titulo(fig, "C. Curvas de aprendizaje según el tamaño del entrenamiento",
            f"Submuestras de {etiqueta_tr} · Validación fija: {etiqueta_val} · "
            "banda = ±1 desviación entre submuestras")
    _leyenda(fig)
    _ajustar(fig)
    return fig


# --------------------------------------------------------------------------- #
# D. Curvas de validación por hiperparámetro
# --------------------------------------------------------------------------- #
def figura_hiperparametros(curvas: pd.DataFrame, etiqueta_tr: str, etiqueta_val: str,
                           tasa: float | None = None) -> Figure:
    modelos = list(dict.fromkeys(curvas["modelo"]))
    fig, ejes = plt.subplots(1, len(modelos), figsize=(3.9 * len(modelos), 4.5),
                             sharey=True, squeeze=False)
    paneles = []
    for ax, modelo in zip(ejes[0], modelos, strict=True):
        d = curvas[curvas["modelo"] == modelo].sort_values("valor")
        nombre = d["hiperparametro"].iloc[0]
        eje, corto = ETIQUETAS_HIPERPARAMETRO.get(nombre, (nombre, nombre))
        ax.plot(d["valor"], d["puntaje_entrenamiento"], color=ENTRENAMIENTO, lw=2,
                marker="s", ms=3.5)
        ax.plot(d["valor"], d["puntaje_validacion"], color=VALIDACION, lw=2, marker="o",
                ms=5, markeredgecolor="white")
        ax.set_xscale("log")
        _estilo(ax, modelo, eje, "PR-AUC (mayor es mejor)")
        ax.yaxis.set_tick_params(labelleft=True)
        paneles.append((ax, d, corto))
    for ax, d, corto in paneles:
        ax.margins(y=0.12)
        x = d["valor"].to_numpy(dtype=float)
        curvas_panel = [(x, d["puntaje_entrenamiento"].to_numpy()),
                        (x, d["puntaje_validacion"].to_numpy())]
        fase2 = d["valor_fase2"].iloc[0]
        if pd.notna(fase2) and x.min() <= fase2 <= x.max():
            ax.axvline(fase2, color=NEUTRO, lw=1, ls=(0, (4, 3)))
            curvas_panel.append((np.full(12, fase2), np.linspace(*ax.get_ylim(), 12)))
        if tasa is not None:
            _azar(ax, tasa, d["puntaje_validacion"].to_numpy())
            curvas_panel.append((x, np.full(len(x), tasa)))
        mejor = d.loc[d["puntaje_validacion"].idxmax()]
        ax.scatter([mejor["valor"]], [mejor["puntaje_validacion"]], s=70, color=VALIDACION,
                   edgecolor="white", linewidth=2, zorder=5)
        _nota(ax, f"máximo de validación\n{corto} = {mejor['valor']:.3g}".replace(".", ","),
              (mejor["valor"], mejor["puntaje_validacion"]), curvas_panel)
    _titulo(fig, "D. Curvas de validación: efecto de un hiperparámetro",
            f"Entrenamiento: {etiqueta_tr} · Validación: {etiqueta_val} · "
            "los demás hiperparámetros, como en la Fase 2")
    _leyenda(fig, [Line2D([], [], color=NEUTRO, lw=1, ls=(0, (4, 3)),
                          label="Valor del modelo (Fase 2; en el control, su valor fijo)")])
    _ajustar(fig)
    return fig


# --------------------------------------------------------------------------- #
# Estrategias: antes y después
# --------------------------------------------------------------------------- #
def _etiqueta_estrategia(fila) -> str:
    tipo = getattr(fila, "tipo_fila", "estrategia")
    nombre = fila.estrategia
    if len(nombre) > 34 and " (" in nombre:            # «E4a · … (solo variables)»
        nombre = nombre.replace(" (", "\n(", 1)
    if tipo == "estrategia":
        return f"{nombre}\n[contra el {fila.problema}]"
    return nombre.replace(" · ", "\n", 1)          # «Referencia» o «Contraprueba» ya lo dicen


def _panel_diferencias(ax, e: pd.DataFrame, etiqueta_val: str) -> None:
    """Diferencia de PR-AUC (después − antes) con su IC 95 % y la réplica."""
    y = np.arange(len(e))
    cambio = e["cambio_puntaje_validacion"].to_numpy(dtype=float)
    inferior = e["ic_inferior"].to_numpy(dtype=float)
    superior = e["ic_superior"].to_numpy(dtype=float)
    replica = e["cambio_replica"].to_numpy(dtype=float)
    con_ic = ~np.isnan(inferior)
    ax.axvline(0, color=NEUTRO, lw=1)
    ax.hlines(y[con_ic], inferior[con_ic], superior[con_ic], color=VALIDACION, lw=2,
              alpha=0.55, zorder=2)
    ax.scatter(cambio, y, s=40, color=VALIDACION, edgecolor="white", linewidth=1, zorder=4)
    ax.scatter(replica, y - 0.28, s=34, marker="D", color="white", edgecolor=ENTRENAMIENTO,
               linewidth=1.5, zorder=3)
    for fila, valor in zip(y, cambio, strict=True):
        ax.text(valor, fila + 0.24, numero(valor, signo=True), fontsize=8, color=TINTA,
                ha="center")
    extremos = np.concatenate([cambio, replica, inferior[con_ic], superior[con_ic]])
    alto = float(np.nanmax(np.abs(extremos))) or 0.01
    ax.set_xlim(-1.18 * alto, 1.18 * alto)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=4, symmetric=True))
    _estilo(ax, "Diferencia de PR-AUC (después − antes)",
            f"{etiqueta_val} con IC 95 % bootstrap · ◇ réplica C2 → C3", "")


def figura_estrategias(estrategias: pd.DataFrame, etiqueta_val: str) -> Figure:
    """Un panel por medida, con la misma lista de estrategias: PR-AUC de validación antes
    y después, la diferencia con su IC 95 % y la réplica (si se calcularon), la brecha y,
    si se calculó, Lift@k (la métrica principal del proyecto).

    El panel de la brecha usa una escala comprimida (lineal hasta ±0,05 y logarítmica
    después), para que una brecha muy grande no aplaste a las demás. Las filas de
    referencia y de contraprueba quedan abajo, separadas por una línea."""
    e = estrategias.iloc[::-1].reset_index(drop=True)   # E1 arriba
    etiquetas = [_etiqueta_estrategia(fila) for fila in e.itertuples()]
    paneles = [("puntaje_validacion", f"PR-AUC en validación ({etiqueta_val})",
                "mayor es mejor · eje recortado")]
    if "ic_inferior" in e:
        paneles.append(("diferencia", "", ""))
    paneles.append(("brecha", "Brecha entrenamiento − validación",
                    "más cerca de cero es mejor · escala comprimida"))
    if "lift_k_validacion_antes" in e:
        paneles.append(("lift_k_validacion", f"Lift@k por familia ({etiqueta_val})",
                        "métrica principal · mayor es mejor"))
    fig, ejes = plt.subplots(1, len(paneles), sharey=True, squeeze=False,
                             figsize=(3.1 * len(paneles) + 3.4, 0.95 * len(e) + 2.6))
    separador = None
    if "tipo_fila" in e:
        extra = np.flatnonzero(e["tipo_fila"].to_numpy() != "estrategia")
        if len(extra) and len(extra) < len(e):
            separador = extra.max() + 0.5
    for ax, (columna, titulo, lectura) in zip(ejes[0], paneles, strict=True):
        if columna == "diferencia":
            _panel_diferencias(ax, e, etiqueta_val)
        else:
            antes, despues = e[f"{columna}_antes"], e[f"{columna}_despues"]
            decimales = 2 if columna == "lift_k_validacion" else 3
            valores = pd.concat([antes, despues])
            if columna == "brecha":
                ax.set_xscale("symlog", linthresh=0.05, linscale=1.5)
                ax.set_xlim(min(-0.02, valores.min() * 1.6), max(0.08, valores.max() * 1.6))
                marcas = [m for m in (-0.05, 0, 0.05, 0.2, 1.0)
                          if ax.get_xlim()[0] <= m <= ax.get_xlim()[1]]
                ax.set_xticks(marcas, [f"{m:g}".replace(".", ",") for m in marcas])
                ax.minorticks_off()
                ax.axvline(0, color=NEUTRO, lw=1)
            else:
                margen = 0.16 * ((valores.max() - valores.min()) or 0.01)
                ax.set_xlim(valores.min() - margen, valores.max() + margen)
                if columna == "lift_k_validacion" and ax.get_xlim()[0] < 1:
                    ax.axvline(1, color=NEUTRO, lw=1)
            for y, (a, d) in enumerate(zip(antes, despues, strict=True)):
                if abs(d - a) > 1e-9:
                    ax.annotate("", xy=(d, y), xytext=(a, y), zorder=2,
                                arrowprops={"arrowstyle": "-|>", "color": NEUTRO, "lw": 1.5})
                ax.text(d, y + 0.24, numero(d, decimales), fontsize=8, color=TINTA,
                        ha="center")
                ax.text(a, y - 0.3, numero(a, decimales), fontsize=8, color=TINTA_SUAVE,
                        ha="center", va="top")
            ax.scatter(antes, range(len(e)), s=70, color="white", edgecolor=NEUTRO,
                       linewidth=2, zorder=3)
            ax.scatter(despues, range(len(e)), s=34, color=VALIDACION, edgecolor="white",
                       linewidth=1, zorder=4)
            _estilo(ax, titulo, lectura, "")
        if separador is not None:
            ax.axhline(separador, color=TINTA_SUAVE, lw=0.8, ls=(0, (2, 2)))
        ax.set_yticks(range(len(e)), etiquetas, fontsize=8.5, color=TINTA)
        ax.set_ylim(-0.75, len(e) - 0.35)
    _titulo(fig, "Estrategias de mejora: antes y después",
            "Cada estrategia cambia una sola cosa del modelo de partida · las flechas van de "
            "antes a después · C5 no interviene")
    claves = [Line2D([], [], marker="o", ls="", ms=8, markerfacecolor="white",
                     markeredgecolor=NEUTRO, markeredgewidth=2, label="Antes"),
              Line2D([], [], marker="o", ls="", ms=6, markerfacecolor=VALIDACION,
                     markeredgecolor="white", label="Después")]
    if "ic_inferior" in e:
        claves += [Line2D([], [], color=VALIDACION, lw=2, alpha=0.55, marker="o", ms=6,
                          markerfacecolor=VALIDACION, markeredgecolor="white",
                          label=f"Diferencia en {etiqueta_val} e IC 95 % (familias)"),
                   Line2D([], [], marker="D", ls="", ms=6, markerfacecolor="white",
                          markeredgecolor=ENTRENAMIENTO, markeredgewidth=1.5,
                          label="Diferencia en la réplica C2 → C3")]
    fig.legend(handles=claves, loc="lower center", ncol=len(claves), frameon=False,
               fontsize=9, labelcolor=TINTA, bbox_to_anchor=(0.5, 0.0))
    _ajustar(fig)
    return fig
