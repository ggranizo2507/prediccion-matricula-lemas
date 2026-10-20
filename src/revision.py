"""
Comprobaciones pedidas en la revisión de la entrega final (D59).

1. **Descubrimiento de D2 sin C4 ni C5.** El análisis exploratorio del cuaderno 01 calculó las
   tasas por señal con todas las cohortes. Aquí se repite solo con las cohortes anteriores a la
   selección (C1–C3) y se comprueba si el orden de las señales, que es lo único que define a
   D2, habría sido el mismo.
2. **Sorteo de desempate.** D2 tiene muchos empates; el Lift@k depende de cómo se resuelven.
   Se mide la distribución del Lift@k con muchos sorteos.
3. **Diferencia pareada D2 − D.** IC 95 % por bootstrap de representantes, con las dos reglas
   evaluadas sobre la misma remuestra y un sorteo de empates nuevo en cada repetición.
4. **Línea base del azar.** El azar se sortea por estudiante y la familia toma el máximo, como
   cualquier otro puntaje; eso favorece a las familias con más hijos. Se compara con un sorteo
   uniforme por familia.
5. **Estadísticos descriptivos** de las variables numéricas por cohorte (sin la etiqueta).

Todas las salidas son agregados. Las celdas con menos de `min_celda` estudiantes o eventos
se suprimen.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.evaluate import consolidar_familias, precision_at_k_familiar
from src.reglas import PESOS_D2, senales

__all__ = ["NOMBRES_SENALES", "senales_por_periodo", "orden_senales", "sorteos_desempate",
           "resumen_sorteos", "diferencia_pareada", "azar_dos_versiones", "descriptivos",
           "conclusiones"]

log = logging.getLogger("lemas.revision")

NOMBRES_SENALES = {"pago_tardio": "pago tardío de la matrícula anterior",
                   "reserva_extraordinaria": "reserva extraordinaria",
                   "atrasos_pension": "al menos una pensión pagada tarde"}
TRAMOS_ATRASOS = [(0, 0, "0"), (1, 2, "1-2"), (3, 5, "3-5"), (6, 99, "6 o más")]
NUMERICAS = ["promedio", "conducta", "anios_permanencia", "atrasos_pension", "hermanos_lemas"]


# --------------------------------------------------------------------------- #
# 1. Descubrimiento de D2 con C1–C3
# --------------------------------------------------------------------------- #
def _fila(periodo: str, senal: str, nivel: str, mascara: np.ndarray, y: np.ndarray,
          referencia: float, min_celda: int) -> dict:
    estudiantes, eventos = int(mascara.sum()), int(y[mascara].sum())
    tasa = eventos / estudiantes if estudiantes else np.nan
    visible = estudiantes >= min_celda and eventos >= min_celda
    return {"periodo": periodo, "senal": senal, "nivel": nivel,
            "estudiantes": estudiantes, "eventos": eventos if visible else np.nan,
            "tasa": round(tasa, 4) if visible else np.nan,
            "riesgo_relativo": round(tasa / referencia, 2) if visible and referencia else np.nan}


def senales_por_periodo(dataset: pd.DataFrame, periodos: dict[str, list[str]],
                        min_celda: int = 5) -> pd.DataFrame:
    """Tasa de no matrícula por señal de D2, para cada periodo (lista de cohortes).

    El riesgo relativo compara cada nivel con el nivel sin la señal (0 atrasos, pago en
    plazo o anticipado, reserva ordinaria).
    """
    filas = []
    for periodo, cohortes in periodos.items():
        datos = dataset[dataset["cohorte"].isin(cohortes)]
        if datos.empty:
            continue
        y = datos["y_no_matricula"].to_numpy().astype(int)
        valores = senales(datos)
        for nombre in ("pago_tardio", "reserva_extraordinaria"):
            con = valores[nombre] > 0
            base = y[~con].mean() if (~con).any() else np.nan
            filas.append(_fila(periodo, nombre, "no", ~con, y, base, min_celda))
            filas.append(_fila(periodo, nombre, "sí", con, y, base, min_celda))
        atrasos = valores["atrasos_pension"]
        base = y[atrasos == 0].mean() if (atrasos == 0).any() else np.nan
        for bajo, alto, etiqueta in TRAMOS_ATRASOS:
            mascara = (atrasos >= bajo) & (atrasos <= alto)
            filas.append(_fila(periodo, "atrasos_pension", etiqueta, mascara, y, base, min_celda))
        filas.append(_fila(periodo, "atrasos_pension", "1 o más", atrasos >= 1, y, base,
                           min_celda))
    return pd.DataFrame(filas)


def orden_senales(tabla: pd.DataFrame) -> pd.DataFrame:
    """Orden de las señales por riesgo relativo en cada periodo, frente al orden de D2.

    Para comparar señales binarias entre sí, los atrasos se resumen como "1 o más".
    """
    esperado = list(PESOS_D2)
    nivel = {"pago_tardio": "sí", "reserva_extraordinaria": "sí", "atrasos_pension": "1 o más"}
    filas = []
    for periodo, datos in tabla.groupby("periodo", sort=False):
        rr = {}
        for s, n in nivel.items():
            valor = datos.loc[(datos["senal"] == s) & (datos["nivel"] == n), "riesgo_relativo"]
            rr[s] = float(valor.iloc[0]) if len(valor) else np.nan
        orden = sorted(rr, key=lambda s: -np.nan_to_num(rr[s], nan=-np.inf))
        filas.append({"periodo": periodo,
                      **{f"rr_{s}": rr[s] for s in esperado},
                      "orden": " > ".join(orden), "igual_a_D2": orden == esperado})
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# 2. Sorteo de desempate
# --------------------------------------------------------------------------- #
def sorteos_desempate(datos: pd.DataFrame, riesgo: np.ndarray, k_por_sede: dict,
                      semillas: list[int] | range) -> pd.DataFrame:
    """Lift@k, Recall@k y Precision@k con cada semilla de desempate."""
    familias = consolidar_familias(datos, riesgo)
    filas = []
    for semilla in semillas:
        total = precision_at_k_familiar(familias, k_por_sede, int(semilla)).query(
            "sede == 'TOTAL'").iloc[0]
        filas.append({"semilla": int(semilla), "lift_k": float(total["lift_k"]),
                      "recall_k": float(total["recall_k"]),
                      "precision_k": float(total["precision_k"])})
    return pd.DataFrame(filas)


def resumen_sorteos(sorteos: pd.DataFrame, semilla_oficial: int) -> dict:
    """Media, percentiles y posición del valor con la semilla oficial."""
    lift = sorteos["lift_k"].to_numpy()
    oficial = float(sorteos.loc[sorteos["semilla"] == semilla_oficial, "lift_k"].iloc[0]) \
        if (sorteos["semilla"] == semilla_oficial).any() else np.nan
    return {"sorteos": len(lift), "lift_media": round(float(lift.mean()), 4),
            "lift_p05": round(float(np.percentile(lift, 5)), 4),
            "lift_p50": round(float(np.percentile(lift, 50)), 4),
            "lift_p95": round(float(np.percentile(lift, 95)), 4),
            "lift_min": round(float(lift.min()), 4), "lift_max": round(float(lift.max()), 4),
            "lift_semilla_oficial": round(oficial, 4),
            "percentil_semilla_oficial": round(float((lift < oficial).mean() * 100), 1),
            "recall_media": round(float(sorteos["recall_k"].mean()), 4)}


# --------------------------------------------------------------------------- #
# 3. Diferencia pareada
# --------------------------------------------------------------------------- #
def diferencia_pareada(datos: pd.DataFrame, riesgo_a: np.ndarray, riesgo_b: np.ndarray,
                       k_por_sede: dict, semilla: int, repeticiones: int = 2000) -> dict:
    """IC 95 % del Lift@k de A, de B y de A − B sobre las mismas remuestras de representantes.

    En cada repetición se remuestrean representantes por sede (con reemplazo) y se usa un
    sorteo de empates distinto, así que el IC incluye las dos fuentes de variación.
    """
    fa = consolidar_familias(datos, riesgo_a).set_index(["cohorte", "id_familia"])
    fb = consolidar_familias(datos, riesgo_b).set_index(["cohorte", "id_familia"]).loc[fa.index]
    rng = np.random.default_rng(semilla)
    sedes = fa["sede"].to_numpy()
    grupos = [np.flatnonzero(sedes == s) for s in np.unique(sedes)]
    lifts_a, lifts_b = [], []
    for i in range(repeticiones):
        indices = np.concatenate([rng.choice(g, size=len(g), replace=True) for g in grupos])
        for tabla, destino in ((fa, lifts_a), (fb, lifts_b)):
            muestra = tabla.iloc[indices].reset_index()
            muestra["sede"] = sedes[indices]     # misma sede para A y B
            muestra["id_familia"] = np.arange(len(muestra))
            total = precision_at_k_familiar(muestra, k_por_sede, semilla + i).query(
                "sede == 'TOTAL'")
            destino.append(float(total["lift_k"].iloc[0]))
    a, b = np.array(lifts_a), np.array(lifts_b)
    d = a - b

    def ic(v):
        return [round(float(np.nanpercentile(v, 2.5)), 4),
                round(float(np.nanpercentile(v, 97.5)), 4)]

    return {"repeticiones": repeticiones, "lift_a_media": round(float(np.nanmean(a)), 4),
            "ic95_lift_a": ic(a), "lift_b_media": round(float(np.nanmean(b)), 4),
            "ic95_lift_b": ic(b), "diferencia_media": round(float(np.nanmean(d)), 4),
            "ic95_diferencia": ic(d), "prob_a_mejor": round(float(np.nanmean(d > 0)), 3)}


# --------------------------------------------------------------------------- #
# 4. Línea base del azar
# --------------------------------------------------------------------------- #
def azar_dos_versiones(datos: pd.DataFrame, k_por_sede: dict, semilla: int,
                       repeticiones: int = 500) -> dict:
    """Lift@k medio del azar por estudiante (la referencia A publicada) y por familia.

    Por estudiante, una familia con más hijos tiene más números en el sorteo y más
    probabilidad de quedar en la lista; si esas familias tienen más casos, el Lift supera 1.
    Por familia, cada representante tiene la misma probabilidad y el Lift esperado es ≈ 1.
    """
    rng = np.random.default_rng(semilla)
    base = consolidar_familias(datos, np.zeros(len(datos)))
    por_estudiante, por_familia = [], []
    for _ in range(repeticiones):
        familias = consolidar_familias(datos, rng.random(len(datos)))
        por_estudiante.append(float(precision_at_k_familiar(familias, k_por_sede, semilla)
                                    .query("sede == 'TOTAL'")["lift_k"].iloc[0]))
        uniforme = base.assign(score=rng.random(len(base)))
        por_familia.append(float(precision_at_k_familiar(uniforme, k_por_sede, semilla)
                                 .query("sede == 'TOTAL'")["lift_k"].iloc[0]))
    con, sin = base[base["evento"] == 1], base[base["evento"] == 0]
    return {"repeticiones": repeticiones,
            "lift_azar_por_estudiante": round(float(np.mean(por_estudiante)), 4),
            "lift_azar_por_familia": round(float(np.mean(por_familia)), 4),
            "estudiantes_por_familia_con_caso": round(float(con["estudiantes"].mean()), 3),
            "estudiantes_por_familia_sin_caso": round(float(sin["estudiantes"].mean()), 3)}


# --------------------------------------------------------------------------- #
# 5. Estadísticos descriptivos
# --------------------------------------------------------------------------- #
def descriptivos(dataset: pd.DataFrame, columnas: list[str] | None = None,
                 min_celda: int = 5) -> pd.DataFrame:
    """Media, DE y percentiles (5, 25, 50, 75, 95) por cohorte y en total.

    Se informan los percentiles 5 y 95 en lugar del mínimo y el máximo, que serían valores
    de un solo estudiante. Grupos con menos de `min_celda` estudiantes no se muestran.
    """
    columnas = columnas or [c for c in NUMERICAS if c in dataset.columns]
    filas = []
    grupos = [(str(c), d) for c, d in dataset.groupby("cohorte")] + [("Total", dataset)]
    for grupo, datos in grupos:
        for col in columnas:
            v = pd.to_numeric(datos[col], errors="coerce").dropna()
            if len(v) < min_celda:
                continue
            filas.append({"cohorte": grupo, "variable": col, "n": len(v),
                          "vacios": int(datos[col].isna().sum()),
                          "media": round(float(v.mean()), 2), "de": round(float(v.std()), 2),
                          **{f"p{p:02d}": round(float(np.percentile(v, p)), 2)
                             for p in (5, 25, 50, 75, 95)}})
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# Conclusiones
# --------------------------------------------------------------------------- #
def _n(valor: float, decimales: int = 2) -> str:
    return f"{valor:.{decimales}f}".replace(".", ",")


def conclusiones(orden: pd.DataFrame, sorteos: dict, pareada: dict, azar: dict,
                 cohorte: str = "C4") -> list[str]:
    """Frases en español con las cifras de cada comprobación."""
    textos = []
    for _, fila in orden.iterrows():
        nombres = " > ".join(NOMBRES_SENALES[s] for s in fila["orden"].split(" > "))
        veredicto = ("el mismo orden de D2" if fila["igual_a_D2"]
                     else "un orden distinto al de D2")
        textos.append(f"Con {fila['periodo']}, las señales se ordenan así por riesgo relativo: "
                      f"{nombres}; es {veredicto}.")
    textos.append(
        f"En {cohorte}, con {sorteos['sorteos']} sorteos de desempate, el Lift@k de D2 tiene "
        f"media {_n(sorteos['lift_media'])} (percentiles 5 y 95: {_n(sorteos['lift_p05'])} y "
        f"{_n(sorteos['lift_p95'])}); la semilla oficial da {_n(sorteos['lift_semilla_oficial'])}"
        f", más que el {_n(sorteos['percentil_semilla_oficial'], 0)} % de los sorteos.")
    bajo, alto = pareada["ic95_diferencia"]
    signo = ("D2 es mejor que D" if bajo > 0 else
             "no se puede afirmar que D2 sea mejor que D")
    textos.append(
        f"En {cohorte}, la diferencia de Lift@k D2 − D es {_n(pareada['diferencia_media'])} "
        f"[IC 95 %: {_n(bajo)}; {_n(alto)}]; D2 supera a D en el "
        f"{_n(100 * pareada['prob_a_mejor'], 0)} % de las remuestras: {signo}.")
    textos.append(
        f"El azar por estudiante da un Lift@k medio de {_n(azar['lift_azar_por_estudiante'])} y "
        f"el azar por familia, {_n(azar['lift_azar_por_familia'])}. Las familias con caso tienen "
        f"{_n(azar['estudiantes_por_familia_con_caso'])} estudiantes en promedio, frente a "
        f"{_n(azar['estudiantes_por_familia_sin_caso'])} las demás.")
    return textos
