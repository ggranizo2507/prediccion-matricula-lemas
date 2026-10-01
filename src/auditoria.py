"""
Auditoría de datos exigida en Sprint 1 (Checklist SMART y Ficha técnica):

1. Conteo de eventos de no matrícula por estudiante y por representante en cada
   cohorte, con verificación de suficiencia (mínimo de eventos y regla EPV).
2. Comparabilidad de C1 frente a C2-C3:
   a) diferencias estandarizadas (SMD) de los predictores y de la tasa del evento;
   b) configuraciones de entrenamiento con y sin C1 evaluadas en C4 (selección).
   C1 se incorpora solo si no degrada la priorización en C4 más allá de la tolerancia.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline

from src.data_processing import (
    CATEGORICAS,
    NUMERICAS,
    construir_matriz_x,
    construir_preprocesador,
)
from src.evaluate import calcular_k_por_sede, consolidar_familias, precision_at_k_familiar

log = logging.getLogger("lemas.auditoria")


# --------------------------------------------------------------------------- #
# 1. Conteo de eventos
# --------------------------------------------------------------------------- #
def conteo_eventos(dataset: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Eventos por estudiante y por representante en cada cohorte, con semáforo."""
    reglas = config["auditoria"]
    filas = []
    for cohorte, datos in dataset.groupby("cohorte"):
        familias = datos.groupby("id_familia")["y_no_matricula"].max()
        eventos = int(datos["y_no_matricula"].sum())
        filas.append({
            "cohorte": cohorte, "rol": datos["rol"].iloc[0],
            "estudiantes": len(datos), "eventos_estudiante": eventos,
            "tasa_estudiante": round(eventos / len(datos), 4),
            "familias": len(familias), "eventos_familia": int(familias.sum()),
            "tasa_familiar": round(familias.mean(), 4),
            "suficiente": eventos >= reglas["min_eventos_por_cohorte"],
        })
    return pd.DataFrame(filas)


def eventos_por_predictor(dataset: pd.DataFrame, cohortes: list[str]) -> float:
    """EPV: eventos del entrenamiento divididos entre columnas del modelo lineal."""
    datos = dataset[dataset["cohorte"].isin(cohortes)]
    if datos.empty:
        return float("nan")
    columnas = construir_preprocesador().fit(construir_matriz_x(datos)).get_feature_names_out()
    return round(datos["y_no_matricula"].sum() / len(columnas), 2)


# --------------------------------------------------------------------------- #
# 2a. Diferencias estandarizadas
# --------------------------------------------------------------------------- #
def _smd(a: pd.Series, b: pd.Series) -> float:
    """Diferencia de medias estandarizada con desviación combinada."""
    a, b = a.dropna().astype(float), b.dropna().astype(float)
    if a.empty or b.empty:
        return float("nan")
    combinada = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    return float((a.mean() - b.mean()) / combinada) if combinada > 0 else 0.0


def diferencias_estandarizadas(
    dataset: pd.DataFrame, config: dict, comparada: str = "C1",
    referencia: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """SMD de cada predictor numérico, de cada categoría y de la tasa del evento.

    Por defecto compara C1 con `auditoria.referencia_comparabilidad` (C2-C4, v5 5.3.4).
    Es un análisis descriptivo: C4 no se usa para ajustar nada.
    """
    umbral = config["auditoria"]["umbral_smd"]
    if referencia is None:
        referencia = tuple(config["auditoria"].get("referencia_comparabilidad", ["C2", "C3"]))
    grupo_a = dataset[dataset["cohorte"] == comparada]
    grupo_b = dataset[dataset["cohorte"].isin(referencia)]
    filas = [{"variable": col, "nivel": "", "smd": _smd(grupo_a[col], grupo_b[col])}
             for col in [*NUMERICAS, "y_no_matricula"]]
    for col in CATEGORICAS:
        for nivel in sorted(set(grupo_a[col].dropna()) | set(grupo_b[col].dropna())):
            filas.append({"variable": col, "nivel": nivel,
                          "smd": _smd((grupo_a[col] == nivel).astype(float),
                                      (grupo_b[col] == nivel).astype(float))})
    tabla = pd.DataFrame(filas)
    tabla["smd"] = tabla["smd"].round(3)
    tabla["relevante"] = tabla["smd"].abs() > umbral
    return tabla.sort_values("smd", key=np.abs, ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# 2b. Configuraciones con y sin C1 evaluadas en C4
# --------------------------------------------------------------------------- #
def _modelo_referencia(semilla: int) -> Pipeline:
    """Regresión logística balanceada: modelo base de la Ficha técnica."""
    return Pipeline([
        ("prep", construir_preprocesador(escalar=True)),
        ("modelo", LogisticRegression(class_weight="balanced", max_iter=2000,
                                      random_state=semilla)),
    ])


def comparar_configuraciones(dataset: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Entrena cada configuración y la evalúa en la cohorte de selección (C4).

    C5 no se utiliza. k por sede se calcula con las cohortes de cada configuración.
    """
    semilla = config["proyecto"]["semilla"]
    seleccion = dataset[dataset["rol"] == "seleccion"]
    if seleccion.empty:
        raise ValueError("No hay cohorte de selección (C4) para comparar configuraciones.")
    filas = []
    for nombre, cohortes in config["auditoria"]["configuraciones_entrenamiento"].items():
        entrenamiento = dataset[dataset["cohorte"].isin(cohortes)]
        if entrenamiento.empty or entrenamiento["y_no_matricula"].nunique() < 2:
            log.warning("Configuración %s sin datos o sin ambas clases.", nombre)
            continue
        modelo = _modelo_referencia(semilla).fit(
            construir_matriz_x(entrenamiento), entrenamiento["y_no_matricula"])
        riesgo_entrenamiento = modelo.predict_proba(construir_matriz_x(entrenamiento))[:, 1]
        k_por_sede = calcular_k_por_sede(
            consolidar_familias(entrenamiento, riesgo_entrenamiento),
            config["capacidad"].get("multiplicador_k", 1.0))
        riesgo = modelo.predict_proba(construir_matriz_x(seleccion))[:, 1]
        y = seleccion["y_no_matricula"].to_numpy()
        familias_c4 = consolidar_familias(seleccion, riesgo)
        resumen = precision_at_k_familiar(familias_c4, k_por_sede, semilla)
        total = resumen[resumen["sede"] == "TOTAL"].iloc[0]
        filas.append({
            "configuracion": nombre, "cohortes": "+".join(cohortes),
            "n_entrenamiento": len(entrenamiento),
            "eventos_entrenamiento": int(entrenamiento["y_no_matricula"].sum()),
            "k_por_sede": k_por_sede,
            "precision_k_C4": total["precision_k"], "lift_k_C4": total["lift_k"],
            "recall_k_C4": total["recall_k"],
            "pr_auc_C4": round(average_precision_score(y, riesgo), 4),
            "roc_auc_C4": round(roc_auc_score(y, riesgo), 4),
            # Brier informativo: el modelo balanceado aún no está calibrado (Fase 2)
            "brier_C4": round(brier_score_loss(y, riesgo), 4),
        })
    return pd.DataFrame(filas)


def decidir_inclusion_c1(
    comparacion: pd.DataFrame, conteo: pd.DataFrame, config: dict
) -> tuple[bool, str]:
    """Regla documentada: C1 entra si tiene eventos suficientes y no reduce la
    Precision@k familiar en C4 más que la tolerancia configurada."""
    tolerancia = config["auditoria"]["tolerancia_precision_k"]
    suficiencia = dict(zip(conteo["cohorte"], conteo["suficiente"], strict=True))
    if "C1" not in suficiencia:
        return False, "C1 no está disponible en los datos."
    if not bool(suficiencia["C1"]):
        return False, "C1 no alcanza el mínimo de eventos de no matrícula."
    resultados = comparacion.set_index("configuracion")
    if not {"con_C1", "sin_C1"} <= set(resultados.index):
        return False, "No se pudieron evaluar ambas configuraciones."
    con = resultados.loc["con_C1", "precision_k_C4"]
    sin = resultados.loc["sin_C1", "precision_k_C4"]
    diferencia = round(con - sin, 4)
    if diferencia >= -tolerancia:
        return True, (f"Se incluye C1: Precision@k en C4 {con:.3f} frente a {sin:.3f} "
                      f"sin C1 (Δ = {diferencia:+.3f}).")
    return False, f"Se excluye C1: Precision@k en C4 cae {abs(diferencia):.3f} (> {tolerancia})."


# --------------------------------------------------------------------------- #
# 3. Reporte obligatorio por cohorte (v5, sección 6.3)
# --------------------------------------------------------------------------- #
EXCLUSIONES = ["sin_reserva", "pendientes", "estado_no_reconocido", "reserva_despues_t0",
               "terminales_excluidos", "confirmados_antes_t0"]


def reporte_por_cohorte(
    dataset: pd.DataFrame, reporte: pd.DataFrame, config: dict,
    incluir_c1: bool | None = None,
) -> pd.DataFrame:
    """Tabla de la sección 6.3 del documento v5, con la convención del documento.

    N elegibles pendientes, M matrículas, U no matrículas, q = U/N, familias F,
    familias con no matrícula, q familiar, exclusiones y columna "Comparable".
    """
    conteo = conteo_eventos(dataset, config).set_index("cohorte")
    base = reporte.set_index("cohorte")
    filas = []
    for cohorte in conteo.index:
        n = int(conteo.loc[cohorte, "estudiantes"])
        u = int(conteo.loc[cohorte, "eventos_estudiante"])
        exclusiones = int(sum(base.loc[cohorte].get(c, 0) or 0 for c in EXCLUSIONES
                              if c in base.columns))
        if cohorte == "C1":
            comparable = "Por evaluar" if incluir_c1 is None else ("Sí" if incluir_c1 else "No")
        else:
            comparable = "Sí"
        filas.append({
            "Cohorte": cohorte, "N elegibles pendientes": n, "M matrículas": n - u,
            "U no matrículas": u, "q = U/N": round(u / n, 4) if n else None,
            "Familias F": int(conteo.loc[cohorte, "familias"]),
            "Familias con no matrícula": int(conteo.loc[cohorte, "eventos_familia"]),
            "q familiar": conteo.loc[cohorte, "tasa_familiar"],
            "Exclusiones": exclusiones, "Comparable": comparable,
            "Suficiente (≥ mínimo de eventos)": "Sí" if conteo.loc[cohorte, "suficiente"] else "No",
        })
    return pd.DataFrame(filas)


def suprimir_reporte(tabla: pd.DataFrame, minimo: int) -> pd.DataFrame:
    """Oculta conteos menores al mínimo antes de publicar la tabla."""
    salida = tabla.copy()
    for col in ["N elegibles pendientes", "M matrículas", "U no matrículas", "Familias F",
                "Familias con no matrícula", "Exclusiones"]:
        salida[col] = salida[col].astype(object).where(salida[col] >= minimo, f"<{minimo}")
    return salida


def sensibilidad_estados(base: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Compara la población y la tasa del evento con todos los estados aprobados
    frente a solo "Aprobar" (v5, 5.3.1 y 5.3.2)."""
    from src.data_processing import construir_dataset

    filas = []
    escenarios = {"principal": config["elegibilidad"]["estados_aprobados"],
                  "solo_Aprobar": config["elegibilidad"]["estados_sensibilidad"]}
    for nombre, estados in escenarios.items():
        datos, _ = construir_dataset(base, config, estados)
        for cohorte, grupo in datos.groupby("cohorte"):
            filas.append({"escenario": nombre, "cohorte": cohorte, "estudiantes": len(grupo),
                          "tasa_no_matricula": round(grupo["y_no_matricula"].mean(), 4)})
    tabla = pd.DataFrame(filas).pivot(index="cohorte", columns="escenario",
                                      values=["estudiantes", "tasa_no_matricula"])
    tabla.columns = [f"{a}_{b}" for a, b in tabla.columns]
    for col in [c for c in tabla.columns if c.startswith("estudiantes_")]:
        tabla[col] = tabla[col].fillna(0).astype(int)
    return tabla.reset_index()


# --------------------------------------------------------------------------- #
# 3. Referencias (líneas base) en la cohorte de selección
# --------------------------------------------------------------------------- #
def _puntaje_reglas(datos: pd.DataFrame) -> dict[str, np.ndarray]:
    """Reglas sin aprendizaje que podría aplicar Secretaría con los datos de t0."""
    atrasos = pd.to_numeric(datos["atrasos_pension"], errors="coerce").fillna(0).to_numpy()
    tardio = (datos["pago_origen"] == "tardio").to_numpy().astype(float)
    extra = pd.to_numeric(datos["reserva_extraordinaria"], errors="coerce").fillna(0).to_numpy()
    return {
        "D · más atrasos primero": atrasos,
        # Prioridad lexicográfica: pago anterior tardío, luego reserva extraordinaria, luego atrasos
        "D2 · señales administrativas": 100 * tardio + 20 * extra + atrasos,
    }


def evaluar_referencias(
    dataset: pd.DataFrame, config: dict, cohortes_entrenamiento: list[str],
    k_por_sede: dict[str, int], repeticiones_azar: int = 500,
) -> pd.DataFrame:
    """Compara en C4 (selección) el azar, las reglas D/D2 y la regresión logística base.

    Todas usan el mismo k por sede y la misma consolidación por representante.
    C5 no se utiliza.
    """
    semilla = config["proyecto"]["semilla"]
    seleccion = dataset[dataset["rol"] == "seleccion"]
    entrenamiento = dataset[dataset["cohorte"].isin(cohortes_entrenamiento)]
    y = seleccion["y_no_matricula"].to_numpy()
    filas = []

    def _fila(nombre, riesgo, pr_auc=None):
        total = precision_at_k_familiar(consolidar_familias(seleccion, riesgo), k_por_sede,
                                        semilla).query("sede == 'TOTAL'").iloc[0]
        filas.append({"referencia": nombre, "precision_k_C4": total["precision_k"],
                      "lift_k_C4": total["lift_k"], "recall_k_C4": total["recall_k"],
                      "pr_auc_C4": round(pr_auc if pr_auc is not None
                                         else average_precision_score(y, riesgo), 4)})

    rng = np.random.default_rng(semilla)
    azar = [precision_at_k_familiar(consolidar_familias(seleccion, rng.random(len(seleccion))),
                                    k_por_sede, semilla).query("sede == 'TOTAL'").iloc[0]
            for _ in range(repeticiones_azar)]
    filas.append({"referencia": "R · selección al azar",
                  "precision_k_C4": round(float(np.mean([a["precision_k"] for a in azar])), 4),
                  "lift_k_C4": round(float(np.mean([a["lift_k"] for a in azar])), 4),
                  "recall_k_C4": round(float(np.mean([a["recall_k"] for a in azar])), 4),
                  "pr_auc_C4": round(float(y.mean()), 4)})
    for nombre, puntaje in _puntaje_reglas(seleccion).items():
        _fila(nombre, puntaje)
    modelo = _modelo_referencia(semilla).fit(construir_matriz_x(entrenamiento),
                                             entrenamiento["y_no_matricula"])
    _fila(f"B1 · regresión logística ({'+'.join(cohortes_entrenamiento)})",
          modelo.predict_proba(construir_matriz_x(seleccion))[:, 1])
    return pd.DataFrame(filas)


def bootstrap_diferencia_c1(
    dataset: pd.DataFrame, config: dict, k_por_sede: dict[str, int], repeticiones: int = 2000,
) -> dict:
    """IC 95 % de Precision@k(con C1) − Precision@k(sin C1) en C4, remuestreando
    representantes de C4 por sede. Es informativo: la regla de decisión no cambia."""
    semilla = config["proyecto"]["semilla"]
    seleccion = dataset[dataset["rol"] == "seleccion"]
    familias = {}
    for nombre, cohortes in config["auditoria"]["configuraciones_entrenamiento"].items():
        entrenamiento = dataset[dataset["cohorte"].isin(cohortes)]
        modelo = _modelo_referencia(semilla).fit(construir_matriz_x(entrenamiento),
                                                 entrenamiento["y_no_matricula"])
        riesgo = modelo.predict_proba(construir_matriz_x(seleccion))[:, 1]
        familias[nombre] = consolidar_familias(seleccion, riesgo).set_index("id_familia")
    con, sin = familias["con_C1"], familias["sin_C1"].loc[familias["con_C1"].index]
    rng = np.random.default_rng(semilla)
    diferencias = []
    for _ in range(repeticiones):
        indices = np.concatenate([
            rng.choice(np.flatnonzero(con["sede"].to_numpy() == sede),
                       size=int((con["sede"] == sede).sum()), replace=True)
            for sede in con["sede"].unique()])
        muestra = []
        for tabla in (con, sin):
            remuestra = tabla.iloc[indices].reset_index(drop=True)
            remuestra["id_familia"] = np.arange(len(remuestra))
            total = precision_at_k_familiar(remuestra, k_por_sede, semilla)
            muestra.append(total.query("sede == 'TOTAL'")["precision_k"].iloc[0])
        diferencias.append(muestra[0] - muestra[1])
    bajo, alto = np.percentile(diferencias, [2.5, 97.5])
    return {"diferencia_media": round(float(np.mean(diferencias)), 4),
            "ic95": [round(float(bajo), 4), round(float(alto), 4)],
            "repeticiones": repeticiones}
