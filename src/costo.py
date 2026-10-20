"""
Costo esperado de la lista de contactos: cuándo compensa llamar y cuántas llamadas hacer.

La métrica de negocio clásica es el costo esperado, FP × cFP + FN × cFN, y el umbral que
lo minimiza. En este proyecto hay dos diferencias:

1. **El número de llamadas lo fija la capacidad (k), no un umbral.** Como una llamada de
   más (cFP) cuesta mucho menos que un estudiante perdido (cFN), el umbral de costo mínimo
   pediría llamar a más familias de las que el personal puede atender. Con la capacidad
   como restricción, minimizar el costo equivale a encontrar el mayor número de casos con
   k llamadas: por eso la métrica principal es Lift@k.
2. **Una llamada no rescata todos los casos.** Solo evita una fracción `eficacia` de ellos,
   que aún no se conoce (la mediría el grupo de control del piloto de 2027).

Todo se expresa en unidades de cFP («cuántas llamadas vale un caso rescatado») y con la
razón R = cFN / cFP. No se usan montos reales.

- Beneficio neto de k llamadas: eficacia × R × aciertos − k (en llamadas).
- Llamar compensa si precisión × eficacia × R > 1; la **razón de equilibrio** es
  R* = 1 / (precisión × eficacia): cuanto menor, más fácil es que las llamadas compensen.
- Una llamada adicional compensa si la **precisión marginal** del tramo cumple lo mismo.

Este módulo solo hace aritmética sobre tablas ya publicadas (`results/metrics/alcance_*` y
los resultados finales): no vuelve a leer datos de estudiantes ni a evaluar en C5. Las
celdas ocultas por privacidad («<5», «oculto») quedan como dato ausente.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.diagnostico import numero

EFICACIAS = (0.10, 0.25)
RAZONES = (50, 100, 200)
TODAS = "Todas"


def _valor(x) -> float:
    """Número o NaN (las celdas ocultas «<5» u «oculto» no son números)."""
    convertido = pd.to_numeric(pd.Series([x]), errors="coerce").iloc[0]
    return float(convertido)


def razon_equilibrio(precision: float, eficacia: float) -> float:
    """R* = 1 / (precisión × eficacia). Infinito si no hay aciertos o la llamada no sirve."""
    if precision is None or eficacia is None or np.isnan(precision) or np.isnan(eficacia):
        return float("nan")
    producto = precision * eficacia
    return math.inf if producto <= 0 else 1.0 / producto


def beneficio_neto(aciertos: float, contactos: float, razon: float, eficacia: float) -> float:
    """Beneficio de llamar frente a no llamar, en unidades de cFP (llamadas)."""
    return eficacia * razon * aciertos - contactos


def tabla_equilibrio(escenarios: list[dict], eficacias: tuple = EFICACIAS) -> pd.DataFrame:
    """Razón de equilibrio de cada escenario.

    `escenarios`: dicts con `escenario`, `descripcion`, `cohorte` y `precision`.
    """
    filas = []
    for esc in escenarios:
        fila = {**esc}
        for e in eficacias:
            fila[f"razon_equilibrio_e{int(round(100 * e))}"] = round(
                razon_equilibrio(_valor(esc["precision"]), e), 1
            )
        filas.append(fila)
    return pd.DataFrame(filas)


def _cohorte(por_k: pd.DataFrame, cohorte: str) -> pd.DataFrame:
    """Filas de una cohorte, ordenadas por número de contactos, con conteos numéricos."""
    tabla = por_k[por_k["cohorte"] == cohorte].copy()
    if tabla.empty:
        raise ValueError(f"No hay filas para la cohorte {cohorte!r}")
    for columna in ("contactos", "aciertos", "pct_familias", "precision"):
        tabla[columna] = pd.to_numeric(tabla[columna], errors="coerce")
    return tabla.sort_values("contactos").reset_index(drop=True)


def tasa_base(por_k: pd.DataFrame, cohorte: str) -> float:
    """Proporción de casos en la cohorte: la precisión de llamar a todas las familias."""
    tabla = _cohorte(por_k, cohorte)
    todas = tabla[tabla["multiplicador"].astype(str) == "todas"]
    fila = todas.iloc[0] if not todas.empty else tabla.iloc[-1]
    return float(fila["aciertos"] / fila["contactos"])


def marginales(por_k: pd.DataFrame, cohorte: str, eficacias: tuple = EFICACIAS) -> pd.DataFrame:
    """Precisión de cada tramo de la lista y su razón de equilibrio.

    Un tramo va de un tamaño de lista al siguiente (por ejemplo, de k a 1,5 k). Su
    precisión marginal es aciertos nuevos / contactos nuevos: dice si alargar la lista
    rinde más que llamar al azar.
    """
    tabla = _cohorte(por_k, cohorte)
    base = tasa_base(por_k, cohorte)
    filas, previo_c, previo_a = [], 0.0, 0.0
    for _, fila in tabla.iterrows():
        nuevos_c = fila["contactos"] - previo_c
        nuevos_a = fila["aciertos"] - previo_a
        precision = nuevos_a / nuevos_c if nuevos_c > 0 else float("nan")
        registro = {
            "cohorte": cohorte,
            "multiplicador": fila["multiplicador"],
            "desde": int(previo_c),
            "hasta": int(fila["contactos"]),
            "contactos_nuevos": int(nuevos_c),
            "aciertos_nuevos": nuevos_a,
            "precision_marginal": round(precision, 4),
            "tasa_base": round(base, 4),
            "lift_marginal": round(precision / base, 2) if base else float("nan"),
        }
        for e in eficacias:
            registro[f"razon_equilibrio_e{int(round(100 * e))}"] = round(
                razon_equilibrio(precision, e), 1
            )
        filas.append(registro)
        previo_c, previo_a = fila["contactos"], fila["aciertos"]
    return pd.DataFrame(filas)


def curva_beneficio(
    por_k: pd.DataFrame, cohorte: str, eficacias: tuple = EFICACIAS, razones: tuple = RAZONES
) -> pd.DataFrame:
    """Beneficio neto (en llamadas) de la lista D2 y del azar para cada tamaño de lista."""
    tabla = _cohorte(por_k, cohorte)
    base = tasa_base(por_k, cohorte)
    filas = []
    for _, fila in tabla.iterrows():
        for e in eficacias:
            for r in razones:
                filas.append(
                    {
                        "cohorte": cohorte,
                        "multiplicador": fila["multiplicador"],
                        "contactos": int(fila["contactos"]),
                        "pct_familias": fila["pct_familias"],
                        "eficacia": e,
                        "razon": r,
                        "beneficio_lista": round(
                            beneficio_neto(fila["aciertos"], fila["contactos"], r, e), 1
                        ),
                        "beneficio_azar": round(
                            beneficio_neto(base * fila["contactos"], fila["contactos"], r, e), 1
                        ),
                    }
                )
    return pd.DataFrame(filas)


def mejor_tamano(curva: pd.DataFrame) -> pd.DataFrame:
    """Para cada (eficacia, razón), el tamaño de lista con mayor beneficio neto."""
    filas = []
    for (e, r), grupo in curva.groupby(["eficacia", "razon"]):
        validos = grupo.dropna(subset=["beneficio_lista"])
        mejor = validos.loc[validos["beneficio_lista"].idxmax()]
        filas.append(
            {
                "eficacia": e,
                "razon": r,
                "multiplicador": mejor["multiplicador"],
                "contactos": int(mejor["contactos"]),
                "pct_familias": mejor["pct_familias"],
                "beneficio_lista": mejor["beneficio_lista"],
                "compensa": bool(mejor["beneficio_lista"] > 0),
            }
        )
    return pd.DataFrame(filas)


def pendientes_semana(semanal: pd.DataFrame, semana: int) -> dict:
    """Proporción de casos entre las familias que siguen sin pagar en `semana`."""
    fila = semanal[(semanal["cohorte"] == TODAS) & (semanal["semana"] == semana)]
    if fila.empty:
        raise ValueError(f"No hay datos de la semana {semana}")
    fila = fila.iloc[0]
    return {
        "semana": int(semana),
        "precision": _valor(fila["tasa_base"]),
        "pendientes_por_campana": _valor(fila["pendientes_por_campana"]),
        "dias_ventana_restante": _valor(fila["dias_ventana_restante"]),
    }


def escenarios(
    por_k: pd.DataFrame,
    semanal: pd.DataFrame | None,
    c5: dict | None,
    cohorte: str = "C4",
    semana: int = 5,
) -> list[dict]:
    """Escenarios de la tabla de equilibrio a partir de las tablas publicadas."""
    tabla = marginales(por_k, cohorte)
    mult = tabla["multiplicador"].astype(str)
    k = tabla[mult.isin({"1.0", "1"})].iloc[0]
    medio = tabla[mult.isin({"0.5"})]
    acum_k = _cohorte(por_k, cohorte)
    lista_k = acum_k[acum_k["multiplicador"].astype(str).isin({"1.0", "1"})].iloc[0]
    salida = [
        {
            "escenario": "azar",
            "cohorte": cohorte,
            "descripcion": "Llamar al azar a k familias",
            "precision": round(tasa_base(por_k, cohorte), 4),
        }
    ]
    if not medio.empty:
        salida.append(
            {
                "escenario": "primera_mitad",
                "cohorte": cohorte,
                "descripcion": "Primera mitad de la lista D2 (k/2)",
                "precision": medio.iloc[0]["precision_marginal"],
            }
        )
    salida.append(
        {
            "escenario": "lista_k",
            "cohorte": cohorte,
            "descripcion": "Lista D2 completa (k)",
            "precision": round(float(lista_k["precision"]), 4),
        }
    )
    siguiente = tabla[(tabla["desde"] == k["hasta"])]
    doble = tabla[mult.isin({"2.0", "2"})]
    if not doble.empty:
        hasta = doble.iloc[0]
        nuevos_c = hasta["hasta"] - k["hasta"]
        nuevos_a = (
            acum_k.loc[acum_k["contactos"] == hasta["hasta"], "aciertos"].iloc[0]
            - lista_k["aciertos"]
        )
        salida.append(
            {
                "escenario": "tramo_k_2k",
                "cohorte": cohorte,
                "descripcion": "Alargar la lista de k a 2k",
                "precision": round(nuevos_a / nuevos_c, 4),
            }
        )
    elif not siguiente.empty:
        salida.append(
            {
                "escenario": "tramo_siguiente",
                "cohorte": cohorte,
                "descripcion": "Alargar la lista después de k",
                "precision": siguiente.iloc[0]["precision_marginal"],
            }
        )
    if semanal is not None:
        p = pendientes_semana(semanal, semana)
        salida.append(
            {
                "escenario": f"pendientes_semana_{semana}",
                "cohorte": "C2–C4",
                "descripcion": f"Llamar a quienes siguen sin pagar en la semana {semana}",
                "precision": round(p["precision"], 4),
            }
        )
    if c5:
        salida.append(
            {
                "escenario": "lista_k_c5",
                "cohorte": "C5",
                "descripcion": "Lista D2 completa (k), prueba final ya publicada",
                "precision": round(float(c5["precision_k"]), 4),
            }
        )
        salida.append(
            {
                "escenario": "azar_c5",
                "cohorte": "C5",
                "descripcion": "Llamar al azar, prueba final ya publicada",
                "precision": round(float(c5["precision_k"]) / float(c5["lift_k"]), 4),
            }
        )
    return salida


def _pct(valor: float) -> str:
    return f"{numero(100 * valor, 0)} %"


def conclusiones(
    equilibrio: pd.DataFrame, marg: pd.DataFrame, mejor: pd.DataFrame, eficacia: float = 0.10
) -> list[str]:
    """Frases en lenguaje llano con las cifras del análisis."""
    col = f"razon_equilibrio_e{int(round(100 * eficacia))}"
    por = equilibrio.set_index("escenario")
    textos = []
    if {"azar", "lista_k"} <= set(por.index):
        textos.append(
            f"Si una llamada rescata al {_pct(eficacia)} de los casos, llamar al azar compensa "
            f"cuando un estudiante perdido vale más de {numero(por.loc['azar', col], 0)} "
            f"llamadas; con la lista D2 basta con que valga más de "
            f"{numero(por.loc['lista_k', col], 0)}."
        )
    if {"lista_k_c5", "azar_c5"} <= set(por.index):
        textos.append(
            f"En la prueba final (C5) la misma cuenta da {numero(por.loc['azar_c5', col], 0)} "
            f"al azar y {numero(por.loc['lista_k_c5', col], 0)} con la lista: la lista divide "
            f"por {numero(por.loc['azar_c5', col] / por.loc['lista_k_c5', col], 1)} lo que "
            "debe valer un caso para que las llamadas compensen."
        )
    if {"primera_mitad", "tramo_k_2k", "azar"} <= set(por.index):
        tramo, azar = por.loc["tramo_k_2k", "precision"], por.loc["azar", "precision"]
        cierre = (
            f"casi lo mismo que al azar ({_pct(azar)})"
            if tramo < 1.3 * azar
            else f"frente a {_pct(azar)} al azar"
        )
        textos.append(
            "En la primera mitad de la lista la proporción de casos es "
            f"{_pct(por.loc['primera_mitad', 'precision'])}; si se alarga de k a 2k, las "
            f"familias nuevas tienen {_pct(tramo)} de casos, {cierre}."
        )
    semanas = [i for i in por.index if str(i).startswith("pendientes_semana_")]
    if semanas:
        s = semanas[0]
        textos.append(
            f"Llamar a quienes siguen sin pagar en la semana {s.rsplit('_', 1)[1]} tiene "
            f"{_pct(por.loc[s, 'precision'])} de casos: la capacidad extra rinde más en una "
            "segunda llamada que alargando la lista inicial, aunque con menos días de margen."
        )
    despues = marg.iloc[2:] if len(marg) > 2 else marg.iloc[0:0]
    if not despues.empty:
        rango = despues[col].replace([np.inf], np.nan).dropna()
        if not rango.empty:
            textos.append(
                "Cada tramo que se añade después de k compensa solo si un caso vale más de "
                f"{numero(rango.min(), 0)} a {numero(rango.max(), 0)} llamadas (eficacia de "
                f"{_pct(eficacia)}). Cuánto vale un caso lo decide la institución: el análisis "
                "solo dice a partir de qué valor conviene cada tamaño de lista."
            )
    if not mejor.empty:
        fila = mejor[np.isclose(mejor["eficacia"], eficacia)]
        if not fila.empty:
            partes = [
                f"{int(f['razon'])} llamadas → {_pct(f['pct_familias'])} de las familias"
                for _, f in fila.sort_values("razon").iterrows()
            ]
            textos.append(
                "Tamaño de lista con mayor beneficio, según cuánto vale un caso: "
                + "; ".join(partes)
                + "."
            )
    return textos
