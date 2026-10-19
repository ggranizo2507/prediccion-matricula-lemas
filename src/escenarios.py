"""
Simulación de escenarios críticos (workshop de la semana 5, D57).

Pregunta guía: ¿hasta qué nivel de perturbación la lista sigue siendo útil, y qué hace el
sistema cuando deja de serlo?

Se perturban los datos **de C4** (la cohorte de selección) y se mide el sistema ya elegido,
sin reentrenarlo ni volver a elegir nada:

- **D2** (la regla que prioriza) no aprende: solo cambia lo que recibe.
- **Logística híbrida**: entrenada con C2 + C3, como en la Fase 2. Solo se reentrena en el
  escenario de cambio de distribución, donde entrenar con un subgrupo es el escenario mismo.

C5 nunca interviene. Las perturbaciones imitan fallas reales del Excel de Secretaría:

1. **Errores de registro** (ruido): con probabilidad *p* se invierte el pago tardío o el tipo
   de reserva, o el conteo de atrasos se corre en uno. Las señales de D2 son discretas, así que
   el ruido gaussiano solo se aplica al promedio, que usa la logística híbrida.
2. **Datos faltantes**: una fracción de una señal llega vacía (cada señal por separado).
3. **Desbalance extremo**: se quitan familias con caso hasta una tasa del 5 %, 3 % y 1 %.
4. **Cambio de distribución**: la logística híbrida se entrena con una sede (o con los no
   becados) y se prueba con la otra (o con los becados).
5. **Señal caída**: una señal llega constante (toda en cero o toda «en plazo»).

Métricas: Lift@k, Recall@k y Precision@k por familia con el k aprobado, PR-AUC y, para las
probabilidades, Brier y la razón observados / esperados. No se usa F1: la lista ordena con
capacidad fija, no clasifica con un umbral. Cada nivel se repite `repeticiones` veces, con
otra perturbación y otro sorteo de empates de D2 (que pesa: en C4 el Lift de D2 va de 1,53 a
1,99 según el sorteo, D50); se publica la media y el rango del 5 % al 95 % (no conteos). Por
eso el nivel «sin perturbar» es la media de los sorteos y no el 1,93 de la semilla fija.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from src.data_processing import construir_matriz_x
from src.diagnostico import numero
from src.modeling import calibrar, construir_modelo, metricas, puntajes_reglas

REGLA = "D2 · señales administrativas"
HIBRIDO = "Logística híbrida"
SENALES = {"pago_tardio": "Pago tardío de la matrícula anterior",
           "reserva_extraordinaria": "Reserva extraordinaria",
           "atrasos_pension": "Pensiones pagadas tarde",
           "promedio": "Promedio (solo logística híbrida)"}
NIVELES_RUIDO = (0.0, 0.01, 0.02, 0.05, 0.10, 0.20)
SIGMAS_PROMEDIO = (0.0, 0.25, 0.5, 1.0, 2.0)
NIVELES_FALTANTES = (0.0, 0.10, 0.20, 0.30, 0.40, 0.50)
TASAS_DESBALANCE = (None, 0.05, 0.03, 0.01)
UMBRAL_UTIL = 1.20            # meta del proyecto: Lift@k ≥ 1,20 (también umbral de alerta)

Puntuador = Callable[[pd.DataFrame], np.ndarray]


# --------------------------------------------------------------------------- #
# Sistemas a evaluar
# --------------------------------------------------------------------------- #
def puntuador_d2(datos: pd.DataFrame) -> np.ndarray:
    return puntajes_reglas(datos)[REGLA]


def entrenar_hibrido(entrenamiento: pd.DataFrame, params: dict, semilla: int):
    """La logística híbrida de la Fase 2 (mismos hiperparámetros, mismas cohortes)."""
    return construir_modelo("hibrido", params, semilla).fit(
        construir_matriz_x(entrenamiento), entrenamiento["y_no_matricula"].to_numpy())


def puntuador_modelo(modelo) -> Puntuador:
    return lambda datos: modelo.predict_proba(construir_matriz_x(datos))[:, 1]


# --------------------------------------------------------------------------- #
# Perturbaciones (siempre sobre una copia)
# --------------------------------------------------------------------------- #
def _con_dato_de_pago(datos: pd.DataFrame) -> np.ndarray:
    """Estudiantes con matrícula anterior registrada (los nuevos no tienen esa señal)."""
    return datos["pago_origen"].isin(["tardio", "en_plazo", "anticipado"]).to_numpy()


def ruido_registro(datos: pd.DataFrame, p: float, rng: np.random.Generator) -> pd.DataFrame:
    """Errores de digitación en las tres señales de D2, cada una con probabilidad `p`."""
    salida = datos.copy()
    if p <= 0:
        return salida
    n = len(salida)
    pago = salida["pago_origen"].astype(object).to_numpy().copy()
    cambia = (rng.random(n) < p) & _con_dato_de_pago(salida)
    pago[cambia] = np.where(pago[cambia] == "tardio", "en_plazo", "tardio")
    salida["pago_origen"] = pago
    extra = pd.to_numeric(salida["reserva_extraordinaria"], errors="coerce").fillna(0)
    cambia = rng.random(n) < p
    salida["reserva_extraordinaria"] = np.where(cambia, 1 - extra, extra).astype(int)
    atrasos = pd.to_numeric(salida["atrasos_pension"], errors="coerce")
    cambia = (rng.random(n) < p) & atrasos.notna().to_numpy()
    paso = rng.choice([-1, 1], size=n)
    salida["atrasos_pension"] = np.where(cambia, np.clip(atrasos + paso, 0, None), atrasos)
    return salida


def ruido_gaussiano(datos: pd.DataFrame, columna: str, sigma: float,
                    rng: np.random.Generator, minimo: float = 0.0,
                    maximo: float = 10.0) -> pd.DataFrame:
    """Ruido N(0, σ) en una variable numérica, recortado a su rango válido."""
    salida = datos.copy()
    if sigma <= 0:
        return salida
    valores = pd.to_numeric(salida[columna], errors="coerce")
    salida[columna] = np.clip(valores + rng.normal(0, sigma, len(valores)), minimo, maximo)
    return salida


def faltantes(datos: pd.DataFrame, senal: str, fraccion: float,
              rng: np.random.Generator) -> pd.DataFrame:
    """Una fracción de la señal llega vacía, como una celda en blanco en el Excel.

    Pago tardío vacío → «sin_dato» (sin prioridad); reserva y atrasos vacíos → dato
    ausente (la regla los lee como 0 y el modelo los imputa); promedio → ausente.
    """
    salida = datos.copy()
    if fraccion <= 0:
        return salida
    tapa = rng.random(len(salida)) < fraccion
    if senal == "pago_tardio":
        tapa &= _con_dato_de_pago(salida)
        pago = salida["pago_origen"].astype(object).to_numpy().copy()
        pago[tapa] = "sin_dato"
        salida["pago_origen"] = pago
    elif senal in ("reserva_extraordinaria", "atrasos_pension", "promedio"):
        valores = pd.to_numeric(salida[senal], errors="coerce").astype(float)
        salida[senal] = valores.mask(tapa)
    else:
        raise ValueError(f"Señal desconocida: {senal}")
    return salida


def senal_caida(datos: pd.DataFrame, senal: str) -> pd.DataFrame:
    """La señal llega constante: la columna no se calculó o se exportó vacía."""
    salida = datos.copy()
    if senal == "pago_tardio":
        salida["pago_origen"] = np.where(_con_dato_de_pago(salida), "en_plazo",
                                         salida["pago_origen"].astype(object))
    elif senal == "reserva_extraordinaria":
        salida["reserva_extraordinaria"] = 0
    elif senal == "atrasos_pension":
        salida["atrasos_pension"] = 0.0
    elif senal == "promedio":
        promedio = pd.to_numeric(salida["promedio"], errors="coerce")
        salida["promedio"] = float(promedio.median())
    elif senal == "todas_d2":
        for nombre in ("pago_tardio", "reserva_extraordinaria", "atrasos_pension"):
            salida = senal_caida(salida, nombre)
    else:
        raise ValueError(f"Señal desconocida: {senal}")
    return salida


def desbalance(datos: pd.DataFrame, tasa: float | None,
               rng: np.random.Generator) -> pd.DataFrame:
    """Quita familias con caso (con todos sus estudiantes) hasta la tasa familiar `tasa`."""
    if tasa is None:
        return datos.copy()
    familias = datos.groupby("id_familia")["y_no_matricula"].max()
    con_caso = familias[familias == 1].index.to_numpy()
    sin_caso = int((familias == 0).sum())
    objetivo = int(round(tasa * sin_caso / (1 - tasa)))
    if objetivo >= len(con_caso):
        return datos.copy()
    quedan = set(rng.choice(con_caso, size=max(objetivo, 1), replace=False))
    fuera = set(con_caso) - quedan
    return datos[~datos["id_familia"].isin(fuera)].copy()


# --------------------------------------------------------------------------- #
# Medición
# --------------------------------------------------------------------------- #
def medir(datos: pd.DataFrame, puntuador: Puntuador, k_por_sede: dict, semilla: int) -> dict:
    """Lift@k, Recall@k, Precision@k y PR-AUC (y Brier si son probabilidades)."""
    m = metricas(datos, puntuador(datos), k_por_sede, semilla)
    salida = {c: m.get(c, np.nan) for c in ("lift_k", "recall_k", "precision_k", "pr_auc", "brier")}
    if puntuador is puntuador_d2:   # el puntaje de D2 no es una probabilidad
        salida["brier"] = np.nan
    return salida


def _resumir(valores: list[dict]) -> dict:
    tabla = pd.DataFrame(valores)
    salida = {}
    for columna in tabla.columns:
        serie = pd.to_numeric(tabla[columna], errors="coerce").dropna()
        if serie.empty:
            continue
        salida[columna] = round(float(serie.mean()), 4)
        if len(serie) > 1:
            salida[f"{columna}_p05"] = round(float(serie.quantile(0.05)), 4)
            salida[f"{columna}_p95"] = round(float(serie.quantile(0.95)), 4)
    return salida


def barrer(datos: pd.DataFrame, sistemas: dict[str, Puntuador], k_por_sede: dict,
           semilla: int, escenario: str, variable: str, niveles,
           perturbar: Callable[[pd.DataFrame, object, np.random.Generator], pd.DataFrame],
           repeticiones: int, solo: set[str] | None = None) -> pd.DataFrame:
    """Mide cada sistema en cada nivel de perturbación, `repeticiones` veces."""
    filas = []
    for nivel in niveles:
        veces = repeticiones
        por_sistema = {nombre: [] for nombre in sistemas if not solo or nombre in solo}
        for r in range(veces):
            rng = np.random.default_rng(semilla + 1000 * r + 7)
            perturbados = perturbar(datos, nivel, rng)
            for nombre in por_sistema:   # el sorteo de empates también cambia con r
                por_sistema[nombre].append(medir(perturbados, sistemas[nombre], k_por_sede,
                                                 semilla + r))
        for nombre, valores in por_sistema.items():
            filas.append({"escenario": escenario, "variable": variable, "sistema": nombre,
                          "nivel": "base" if nivel is None else nivel, "repeticiones": veces,
                          **_resumir(valores)})
    return pd.DataFrame(filas)


def escenario_ruido(datos, sistemas, k_por_sede, semilla, repeticiones) -> pd.DataFrame:
    partes = [barrer(datos, sistemas, k_por_sede, semilla, "ruido", "errores_registro",
                     NIVELES_RUIDO, ruido_registro, repeticiones)]
    if HIBRIDO in sistemas:
        partes.append(barrer(
            datos, sistemas, k_por_sede, semilla, "ruido", "promedio_gaussiano",
            SIGMAS_PROMEDIO, lambda d, s, rng: ruido_gaussiano(d, "promedio", s, rng),
            repeticiones, solo={HIBRIDO}))
    return pd.concat(partes, ignore_index=True)


def escenario_faltantes(datos, sistemas, k_por_sede, semilla, repeticiones) -> pd.DataFrame:
    partes = []
    for senal in SENALES:
        solo = {HIBRIDO} if senal == "promedio" else None
        if solo and HIBRIDO not in sistemas:
            continue
        partes.append(barrer(
            datos, sistemas, k_por_sede, semilla, "faltantes", senal, NIVELES_FALTANTES,
            lambda d, f, rng, s=senal: faltantes(d, s, f, rng), repeticiones, solo=solo))
    return pd.concat(partes, ignore_index=True)


def escenario_desbalance(datos, sistemas, k_por_sede, semilla, repeticiones) -> pd.DataFrame:
    tabla = barrer(datos, sistemas, k_por_sede, semilla, "desbalance", "tasa_familiar",
                   TASAS_DESBALANCE, desbalance, repeticiones)
    base = datos.groupby("id_familia")["y_no_matricula"].max().mean()
    tabla["tasa_real"] = [round(float(base), 4) if n == "base" else n for n in tabla["nivel"]]
    return tabla


def escenario_caida(datos, sistemas, k_por_sede, semilla, repeticiones) -> pd.DataFrame:
    """La señal llega constante. La perturbación es fija; se repite solo el sorteo de
    empates, que pesa mucho cuando una señal deja de ordenar."""
    filas = []
    for senal in ["ninguna", *SENALES, "todas_d2"]:
        perturbados = datos.copy() if senal == "ninguna" else senal_caida(datos, senal)
        for nombre, puntuador in sistemas.items():
            if senal == "promedio" and nombre != HIBRIDO:
                continue
            valores = [medir(perturbados, puntuador, k_por_sede, semilla + r)
                       for r in range(repeticiones)]
            filas.append({"escenario": "senal_caida", "variable": senal, "sistema": nombre,
                          "nivel": "constante" if senal != "ninguna" else "base",
                          "repeticiones": repeticiones, **_resumir(valores)})
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# Cambio de distribución (solo la logística híbrida aprende)
# --------------------------------------------------------------------------- #
@dataclass
class Corte:
    nombre: str
    columna: str
    grupo_a: object
    grupo_b: object


CORTES = (Corte("sede", "sede", "Mucho Lote 1", "Mucho Lote 2"),
          Corte("beca", "beca", 0, 1))


def _grupo(datos: pd.DataFrame, columna: str, valor) -> pd.DataFrame:
    serie = datos[columna]
    if isinstance(valor, (int, float)):
        serie = pd.to_numeric(serie, errors="coerce").fillna(0)
    return datos[serie == valor]


def _probabilidades(y: np.ndarray, prob: np.ndarray, minimo: int,
                    es_probabilidad: bool = True) -> dict:
    eventos = int(y.sum())
    if eventos < minimo or eventos == len(y):
        return {"eventos": f"<{minimo}" if eventos < minimo else eventos, "pr_auc": np.nan,
                "roc_auc": np.nan, "brier": np.nan, "observados_sobre_esperados": np.nan}
    salida = {"eventos": eventos,
              "pr_auc": round(float(average_precision_score(y, prob)), 4),
              "roc_auc": round(float(roc_auc_score(y, prob)), 4),
              "brier": np.nan, "observados_sobre_esperados": np.nan}
    if es_probabilidad:
        salida["brier"] = round(float(brier_score_loss(y, prob)), 4)
        salida["observados_sobre_esperados"] = round(float(y.sum() / prob.sum()), 3)
    return salida


def escenario_cambio(entrenamiento: pd.DataFrame, seleccion: pd.DataFrame, params: dict,
                     semilla: int, minimo: int = 5,
                     cortes: tuple[Corte, ...] = CORTES) -> pd.DataFrame:
    """Entrenar con un subgrupo y probar con otro (A → B y B → A).

    Para cada dirección se compara, en C4 del grupo de destino:
    - **transferido**: entrenado con C2 + C3 del otro grupo y calibrado (Platt) en C4 del
      otro grupo;
    - **referencia**: el modelo de la Fase 2, entrenado con todos y calibrado en todo C4.
    La regla D2 no aprende; su PR-AUC en el grupo de destino se agrega como contexto.
    """
    referencia = entrenar_hibrido(entrenamiento, params, semilla)
    referencia_cal = calibrar(referencia, seleccion)
    filas = []
    for corte in cortes:
        for origen, destino in ((corte.grupo_a, corte.grupo_b), (corte.grupo_b, corte.grupo_a)):
            tr = _grupo(entrenamiento, corte.columna, origen)
            cal = _grupo(seleccion, corte.columna, origen)
            prueba = _grupo(seleccion, corte.columna, destino)
            if tr.empty or prueba.empty or tr["y_no_matricula"].sum() < minimo:
                continue
            y = prueba["y_no_matricula"].to_numpy()
            X = construir_matriz_x(prueba)
            transferido = entrenar_hibrido(tr, params, semilla)
            puede_calibrar = cal["y_no_matricula"].sum() >= minimo
            prob_t = (calibrar(transferido, cal).predict_proba(X)[:, 1] if puede_calibrar
                      else np.full(len(prueba), np.nan))
            base = {"corte": corte.nombre, "origen": str(origen), "destino": str(destino),
                    "estudiantes_destino": len(prueba)}
            if puede_calibrar:
                filas.append({**base, "modelo": "transferido",
                              **_probabilidades(y, prob_t, minimo)})
            filas.append({**base, "modelo": "referencia (todos)",
                          **_probabilidades(y, referencia_cal.predict_proba(X)[:, 1], minimo)})
            filas.append({**base, "modelo": "regla D2 (sin aprendizaje)",
                          **_probabilidades(y, puntuador_d2(prueba), minimo, False)})
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# Límites operativos
# --------------------------------------------------------------------------- #
def limites(resultados: pd.DataFrame, umbral: float = UMBRAL_UTIL,
            sistema: str = REGLA) -> pd.DataFrame:
    """Para cada barrido, el mayor nivel en que la lista sigue siendo útil (Lift ≥ umbral).

    «Útil» se exige en la media y en el percentil 5 de las repeticiones, para que no dependa
    de una perturbación favorable.
    """
    filas = []
    datos = resultados[(resultados["sistema"] == sistema)
                       & resultados["escenario"].isin(["ruido", "faltantes", "desbalance"])]
    for (escenario, variable), grupo in datos.groupby(["escenario", "variable"], sort=False):
        grupo = grupo.copy()
        grupo["_nivel"] = pd.to_numeric(grupo["nivel"].replace("base", np.nan), errors="coerce")
        p05 = grupo["lift_k_p05"] if "lift_k_p05" in grupo else grupo["lift_k"]
        util = (grupo["lift_k"] >= umbral) & (p05.fillna(grupo["lift_k"]) >= umbral)
        if escenario == "desbalance":
            grupo = grupo.assign(_orden=grupo["_nivel"].fillna(1.0)).sort_values(
                "_orden", ascending=False)
        else:
            grupo = grupo.assign(_orden=grupo["_nivel"].fillna(0.0)).sort_values("_orden")
        util = util.loc[grupo.index]
        ultimo = None
        for indice, ok in util.items():
            if not ok:
                break
            ultimo = grupo.loc[indice, "_orden"]
        primero_falla = grupo.loc[~util, "_orden"]
        filas.append({"escenario": escenario, "variable": variable, "sistema": sistema,
                      "umbral_lift": umbral,
                      "ultimo_nivel_util": ultimo,
                      "primer_nivel_no_util": (float(primero_falla.iloc[0])
                                               if not primero_falla.empty else None),
                      "lift_base": float(grupo["lift_k"].iloc[0])})
    caida = resultados[(resultados["sistema"] == sistema)
                       & (resultados["escenario"] == "senal_caida")]
    for _, fila in caida.iterrows():
        if fila["variable"] == "ninguna":
            continue
        filas.append({"escenario": "senal_caida", "variable": fila["variable"],
                      "sistema": sistema, "umbral_lift": umbral,
                      "ultimo_nivel_util": "constante" if fila["lift_k"] >= umbral else None,
                      "primer_nivel_no_util": None if fila["lift_k"] >= umbral else "constante",
                      "lift_base": fila["lift_k"]})
    return pd.DataFrame(filas)


def _pct(valor) -> str:
    return f"{numero(100 * float(valor), 0)} %"


def conclusiones(resultados: pd.DataFrame, cambio: pd.DataFrame, lim: pd.DataFrame,
                 umbral: float = UMBRAL_UTIL) -> list[str]:
    """Frases con las cifras de la ejecución, para el documento y el cuaderno."""
    textos = []
    d2 = resultados[resultados["sistema"] == REGLA]
    base = d2[(d2["escenario"] == "senal_caida") & (d2["variable"] == "ninguna")]
    if not base.empty:
        textos.append(f"Sin perturbar, la regla D2 tiene en C4 un Lift@k de "
                      f"{numero(base['lift_k'].iloc[0], 2)} y un Recall@k de "
                      f"{_pct(base['recall_k'].iloc[0])}.")
    lift_base = float(base["lift_k"].iloc[0]) if not base.empty else np.nan
    if lift_base < umbral:
        textos.append(f"Sin perturbar, la lista ya está por debajo del umbral de utilidad "
                      f"(Lift ≥ {numero(umbral, 2)}) en esta cohorte, así que no se pueden fijar "
                      "límites operativos con estos datos; se describe solo cómo cambia.")
    else:
        ruido = lim[(lim["escenario"] == "ruido") & (lim["variable"] == "errores_registro")]
        if not ruido.empty:
            f = ruido.iloc[0]
            if f["primer_nivel_no_util"] is None or pd.isna(f["primer_nivel_no_util"]):
                textos.append("Con errores de registro de hasta el "
                              f"{_pct(max(NIVELES_RUIDO))} en cada señal, la lista sigue por "
                              f"encima del umbral (Lift ≥ {numero(umbral, 2)}).")
            else:
                textos.append(f"La lista tolera errores de registro hasta el "
                              f"{_pct(f['ultimo_nivel_util'] or 0)} de las filas; desde el "
                              f"{_pct(f['primer_nivel_no_util'])} cae bajo el umbral.")
        for _, f in lim[lim["escenario"] == "faltantes"].iterrows():
            nombre = SENALES.get(f["variable"], f["variable"]).lower()
            if f["primer_nivel_no_util"] is None or pd.isna(f["primer_nivel_no_util"]):
                textos.append(f"Con hasta el {_pct(max(NIVELES_FALTANTES))} de vacíos en "
                              f"{nombre}, la lista sigue siendo útil.")
            else:
                textos.append(f"Con vacíos en {nombre}, la lista deja de ser útil desde el "
                              f"{_pct(f['primer_nivel_no_util'])} de las filas.")
    caida = d2[(d2["escenario"] == "senal_caida") & (d2["variable"] != "ninguna")]
    for _, f in caida.iterrows():
        if f["variable"] == "promedio":
            continue
        if f["variable"] == "todas_d2":
            sujeto = "las tres señales llegan constantes"
        else:
            nombre = SENALES.get(f["variable"], f["variable"]).lower()
            sujeto = f"la señal «{nombre}» llega constante"
        textos.append(f"Si {sujeto}, el Lift@k pasa a "
                      f"{numero(f['lift_k'], 2)} (Recall@k {_pct(f['recall_k'])}).")
    desb = d2[d2["escenario"] == "desbalance"]
    for _, f in desb.iterrows():
        if f["nivel"] == "base":
            continue
        rango = ""
        if "lift_k_p05" in f and pd.notna(f.get("lift_k_p05")):
            rango = (f" (del {numero(f['lift_k_p05'], 2)} al {numero(f['lift_k_p95'], 2)} "
                     "según qué familias queden)")
        textos.append(f"Con una tasa familiar del {_pct(f['nivel'])}, el Lift@k medio es "
                      f"{numero(f['lift_k'], 2)}{rango}.")
    if not cambio.empty:
        for (_corte, origen, destino), grupo in cambio.groupby(["corte", "origen", "destino"],
                                                              sort=False):
            t = grupo[grupo["modelo"] == "transferido"]
            r = grupo[grupo["modelo"] == "referencia (todos)"]
            if t.empty or r.empty or pd.isna(t["pr_auc"].iloc[0]):
                continue
            etiqueta = {"0": "no becados", "1": "becados"}
            o, d = etiqueta.get(origen, origen), etiqueta.get(destino, destino)
            textos.append(
                f"Logística híbrida entrenada con {o} y probada con {d}: PR-AUC "
                f"{numero(t['pr_auc'].iloc[0], 3)} frente a {numero(r['pr_auc'].iloc[0], 3)} "
                "del modelo entrenado con todos; observados / esperados = "
                f"{numero(t['observados_sobre_esperados'].iloc[0], 2)}.")
    return textos
