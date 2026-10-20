"""
Incertidumbre de la equidad, carga operativa y tamaño de la reserva al azar (D60).

Responde a la retroalimentación docente del workshop de la semana 4:

1. **Brechas por grupo con intervalos y prueba exacta.** Intervalo de Wilson para el Recall@k
   y para el porcentaje de familias seleccionadas de cada grupo, prueba exacta de Fisher para
   comparar dos grupos e intervalo de la razón de selección (método de Katz, en escala log).
2. **Carga operativa.** Llamadas necesarias por familia en riesgo hallada, con la lista y al
   azar.
3. **Reserva al azar.** Cuántas familias, y cuántas campañas, harían falta para detectar que
   la llamada reduce la no matrícula, si una parte de la lista se reserva sin llamar.

Todo se calcula con tablas agregadas (`equidad_C5_<fuente>.csv`,
`resultados_finales_<fuente>.json`): no usa datos de estudiantes ni vuelve a evaluar C5.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, norm

__all__ = [
    "wilson",
    "fisher_2x2",
    "razon_ic",
    "equidad_con_ic",
    "comparaciones",
    "llamadas_por_caso",
    "tamano_reserva",
    "tabla_reserva",
    "conclusiones",
]

Z95 = norm.ppf(0.975)


def wilson(aciertos: int, total: int, confianza: float = 0.95) -> tuple[float, float]:
    """Intervalo de Wilson para una proporción (mejor que el de Wald con pocos casos)."""
    if total <= 0:
        return (np.nan, np.nan)
    z = norm.ppf(0.5 + confianza / 2)
    p = aciertos / total
    centro = p + z * z / (2 * total)
    radio = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
    divisor = 1 + z * z / total
    return (max(0.0, (centro - radio) / divisor), min(1.0, (centro + radio) / divisor))


def fisher_2x2(x1: int, n1: int, x2: int, n2: int) -> float:
    """Valor p bilateral de la prueba exacta de Fisher para x1/n1 frente a x2/n2."""
    return float(fisher_exact([[x1, n1 - x1], [x2, n2 - x2]])[1])


def razon_ic(x1: int, n1: int, x2: int, n2: int) -> tuple[float, float, float]:
    """Razón (x1/n1) / (x2/n2) con su IC 95 % de Katz. Sin casos en un grupo → NaN."""
    if min(x1, x2) == 0:
        return (np.nan, np.nan, np.nan)
    razon = (x1 / n1) / (x2 / n2)
    error = math.sqrt(1 / x1 - 1 / n1 + 1 / x2 - 1 / n2)
    return (razon, razon * math.exp(-Z95 * error), razon * math.exp(Z95 * error))


def _entero(valor) -> int | None:
    numero = pd.to_numeric(pd.Series([valor]), errors="coerce").iloc[0]
    return None if pd.isna(numero) else int(round(float(numero)))


def equidad_con_ic(tabla: pd.DataFrame) -> pd.DataFrame:
    """Añade conteos e IC de Wilson a la tabla de equidad publicada.

    Los conteos se recuperan de las tasas publicadas (familias × % seleccionadas, eventos ×
    Recall@k). Donde la tabla oculta los eventos (`<5`, `oculto`), el recall queda sin dato.
    """
    filas = []
    for _, fila in tabla.iterrows():
        familias = int(fila["familias"])
        seleccionadas = int(round(float(fila["tasa_seleccion"]) * familias))
        eventos = _entero(fila["eventos"])
        salida = {
            "variable": fila["variable"],
            "grupo": str(fila["grupo"]),
            "familias": familias,
            "seleccionadas": seleccionadas,
            "pct_seleccion": seleccionadas / familias,
        }
        salida["ic95_seleccion"] = wilson(seleccionadas, familias)
        if eventos is None or pd.isna(fila.get("recall_k")):
            salida.update(eventos=None, hallados=None, recall=np.nan, ic95_recall=(np.nan, np.nan))
        else:
            hallados = int(round(float(fila["recall_k"]) * eventos))
            salida.update(
                eventos=eventos,
                hallados=hallados,
                recall=hallados / eventos,
                ic95_recall=wilson(hallados, eventos),
            )
        filas.append(salida)
    salida = pd.DataFrame(filas)
    for nombre in ("seleccion", "recall"):
        ic = salida.pop(f"ic95_{nombre}")
        salida[f"{nombre}_ic_bajo"] = [round(a, 4) for a, _ in ic]
        salida[f"{nombre}_ic_alto"] = [round(b, 4) for _, b in ic]
    return salida.round({"pct_seleccion": 4, "recall": 4})


def comparaciones(con_ic: pd.DataFrame, referencias: dict[str, str]) -> pd.DataFrame:
    """Cada grupo frente al de referencia de su variable: Fisher y razón de selección.

    `referencias` = {variable: grupo de referencia}, p. ej. {"beca": "0"}. Solo se comparan
    los grupos con eventos publicados.
    """
    filas = []
    for variable, base in referencias.items():
        datos = con_ic[con_ic["variable"] == variable].set_index("grupo")
        if base not in datos.index:
            continue
        r = datos.loc[base]
        for grupo, g in datos.drop(index=base).iterrows():
            sel = (
                int(g["seleccionadas"]),
                int(g["familias"]),
                int(r["seleccionadas"]),
                int(r["familias"]),
            )
            razon, bajo, alto = razon_ic(*sel)
            fila = {
                "variable": variable,
                "grupo": grupo,
                "referencia": base,
                "razon_seleccion": round(razon, 3),
                "razon_ic_bajo": round(bajo, 3),
                "razon_ic_alto": round(alto, 3),
                "p_seleccion": round(fisher_2x2(*sel), 4),
            }
            if pd.notna(g["hallados"]) and pd.notna(r["hallados"]):
                fila["diferencia_recall"] = round(float(g["recall"] - r["recall"]), 4)
                fila["p_recall"] = round(
                    fisher_2x2(
                        int(g["hallados"]), int(g["eventos"]), int(r["hallados"]), int(r["eventos"])
                    ),
                    4,
                )
            else:
                fila["diferencia_recall"], fila["p_recall"] = np.nan, np.nan
            filas.append(fila)
    return pd.DataFrame(filas)


def llamadas_por_caso(k_total: int, hallados: int, tasa_familiar: float) -> dict:
    """Llamadas necesarias por familia en riesgo encontrada: con la lista y al azar."""
    return {
        "llamadas": k_total,
        "casos_hallados": hallados,
        "llamadas_por_caso_lista": round(k_total / hallados, 2) if hallados else np.nan,
        "llamadas_por_caso_azar": round(1 / tasa_familiar, 2) if tasa_familiar else np.nan,
    }


def tamano_reserva(
    tasa_sin_llamar: float,
    reduccion: float,
    fraccion_control: float = 0.5,
    alfa: float = 0.05,
    potencia: float = 0.80,
) -> dict:
    """Familias necesarias para detectar que la llamada reduce la no matrícula.

    Diseño: de las familias de la lista, una fracción (`fraccion_control`) se elige al azar y
    no se llama; el resto sí. Se compara la tasa de no matrícula de ambos grupos con una prueba
    de dos proporciones (bilateral). `tasa_sin_llamar` = tasa esperada en la lista sin llamada
    (la Precision@k de la prueba final); `reduccion` = efecto relativo de la llamada.
    """
    p0 = tasa_sin_llamar
    p1 = p0 * (1 - reduccion)
    razon = (1 - fraccion_control) / fraccion_control  # llamados por cada control
    za, zb = norm.ppf(1 - alfa / 2), norm.ppf(potencia)
    pbar = (p0 + razon * p1) / (1 + razon)
    control = (
        (
            za * math.sqrt(pbar * (1 - pbar) * (1 + 1 / razon))
            + zb * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1) / razon)
        )
        ** 2
    ) / (p0 - p1) ** 2
    control = math.ceil(control)
    llamados = math.ceil(control * razon)
    return {
        "reduccion": reduccion,
        "fraccion_control": fraccion_control,
        "tasa_sin_llamar": round(p0, 4),
        "tasa_con_llamada": round(p1, 4),
        "familias_control": control,
        "familias_llamadas": llamados,
        "familias_total": control + llamados,
    }


def tabla_reserva(
    tasa_sin_llamar: float,
    familias_por_campana: int,
    reducciones=(0.5, 0.25, 0.10),
    fracciones=(0.5, 0.25),
) -> pd.DataFrame:
    """Tamaño necesario y campañas equivalentes para varios efectos y fracciones de control."""
    filas = [tamano_reserva(tasa_sin_llamar, r, f) for r in reducciones for f in fracciones]
    tabla = pd.DataFrame(filas)
    tabla["campanas"] = (tabla["familias_total"] / familias_por_campana).round(1)
    return tabla


def _pct(valor: float) -> str:
    return f"{100 * valor:.0f} %"


def _n(valor: float, decimales: int = 2) -> str:
    return f"{valor:.{decimales}f}".replace(".", ",")


def conclusiones(
    con_ic: pd.DataFrame, comparado: pd.DataFrame, carga: dict, reserva: pd.DataFrame
) -> list[str]:
    """Frases con las cifras, en español y con coma decimal."""
    textos = []
    for _, c in comparado.iterrows():
        g = con_ic[(con_ic["variable"] == c["variable"]) & (con_ic["grupo"] == c["grupo"])].iloc[0]
        r = con_ic[
            (con_ic["variable"] == c["variable"]) & (con_ic["grupo"] == c["referencia"])
        ].iloc[0]
        if pd.notna(c["p_recall"]):
            textos.append(
                f"{c['variable']} = {c['grupo']} frente a {c['referencia']}: Recall@k "
                f"{_pct(g['recall'])} [{_pct(g['recall_ic_bajo'])}–{_pct(g['recall_ic_alto'])}] "
                f"frente a {_pct(r['recall'])} [{_pct(r['recall_ic_bajo'])}–"
                f"{_pct(r['recall_ic_alto'])}]; prueba exacta de Fisher p = {_n(c['p_recall'])}. "
                f"Razón de selección {_n(c['razon_seleccion'])} [{_n(c['razon_ic_bajo'])}–"
                f"{_n(c['razon_ic_alto'])}], p = {_n(c['p_seleccion'], 3)}."
            )
    textos.append(
        f"Carga operativa: {_n(carga['llamadas_por_caso_lista'], 1)} llamadas por familia en "
        f"riesgo hallada con la lista, frente a {_n(carga['llamadas_por_caso_azar'], 1)} al azar."
    )
    for _, f in reserva[reserva["fraccion_control"] == 0.5].iterrows():
        textos.append(
            f"Para detectar que la llamada reduce la no matrícula un {_pct(f['reduccion'])} "
            f"(reservando la mitad de la lista sin llamar) se necesitan unas "
            f"{int(f['familias_total']):,} familias".replace(",", ".")
            + f", unas {_n(f['campanas'], 1)} campañas de la lista actual."
        )
    return textos
