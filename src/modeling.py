"""
Fase 2 · Modelado, optimización, calibración y evaluación.

Protocolo temporal (v5, 6.2; decisión C1 del 01-oct-2026):
1. Optimización de hiperparámetros con Optuna dentro del entrenamiento:
   se entrena con la(s) cohorte(s) más antigua(s) y se valida con la más reciente
   (p. ej., C2 → C3). Objetivo: PR-AUC (precisión promedio), estable con pocos eventos.
2. Cada candidato se reentrena con todas las cohortes de entrenamiento y se evalúa
   en C4 con la métrica principal (Lift@k / Precision@k familiar).
3. Se elige el mejor candidato frente a las reglas D y D2; se calibra en C4
   (Platt, no cambia el orden) y se congela.
4. C5 se evalúa una sola vez con el sistema congelado.

Convención: y_no_matricula = 1 es el evento; `riesgo` = P(no matrícula).
La probabilidad de matrícula del v5 es p = 1 − riesgo.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import optuna
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline

from src.data_processing import (
    CATEGORICAS,
    NUMERICAS,
    construir_matriz_x,
    construir_preprocesador,
)
from src.evaluate import consolidar_familias, precision_at_k_familiar
from src.utils import celda_complementaria

log = logging.getLogger("lemas.modelado")
optuna.logging.set_verbosity(optuna.logging.WARNING)

# Conjuntos de variables: "reducido" quita `curso` (muchas categorías para pocos eventos)
CONJUNTOS = {
    "completo": (CATEGORICAS, NUMERICAS),
    "reducido": ([c for c in CATEGORICAS if c != "curso"], NUMERICAS),
}
TIPOS = ("logistica", "arboles", "hibrido")
NOMBRES = {"logistica": "Regresión logística regularizada",
           "arboles": "Gradient boosting (árboles, monotonía en atrasos)",
           "hibrido": "Logística híbrida (señales de D2 + variables académicas)"}

# Modelo híbrido (D39, registrado antes de evaluarlo en C4): parte de las señales de la
# regla D2 y agrega pocas variables académicas, para medir si la IA aporta algo más.
HIBRIDAS_BINARIAS = ["pago_tardio", "es_nuevo", "reserva_extraordinaria", "conducta_no_A"]
HIBRIDAS_CATEGORICAS = ["atrasos_tramo", "subnivel"]
HIBRIDAS_NUMERICAS = ["promedio"]


def variables_hibridas(X: pd.DataFrame) -> pd.DataFrame:
    """Deriva las variables del modelo híbrido a partir de la matriz X estándar."""
    atrasos = pd.to_numeric(X["atrasos_pension"], errors="coerce").fillna(0)
    return pd.DataFrame({
        "pago_tardio": (X["pago_origen"] == "tardio").astype(float),
        "es_nuevo": (X["pago_origen"] == "nuevo").astype(float),
        "reserva_extraordinaria": pd.to_numeric(X["reserva_extraordinaria"],
                                                errors="coerce").fillna(0),
        "conducta_no_A": (pd.to_numeric(X["conducta"], errors="coerce") < 5).astype(float),
        "atrasos_tramo": pd.cut(atrasos, [-1, 0, 2, 5, 99],
                                labels=["0", "1-2", "3-5", "6+"]).astype(str),
        "subnivel": X["subnivel"].astype(str),
        "promedio": pd.to_numeric(X["promedio"], errors="coerce"),
    }, index=X.index)


def _nombres_hibridas(_transformador, _entrada):
    return np.array(HIBRIDAS_BINARIAS + HIBRIDAS_CATEGORICAS + HIBRIDAS_NUMERICAS)


def _preprocesador_hibrido() -> Pipeline:
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

    columnas = ColumnTransformer([
        ("bin", "passthrough", HIBRIDAS_BINARIAS),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
         HIBRIDAS_CATEGORICAS),
        ("num", Pipeline([("imputar", SimpleImputer(strategy="median")),
                          ("escalar", StandardScaler())]), HIBRIDAS_NUMERICAS),
    ], verbose_feature_names_out=False)
    return Pipeline([
        ("derivar", FunctionTransformer(variables_hibridas, feature_names_out=_nombres_hibridas)),
        ("columnas", columnas),
    ])


# --------------------------------------------------------------------------- #
# Construcción de modelos
# --------------------------------------------------------------------------- #
def _penalizacion_elastica() -> dict:
    """scikit-learn < 1.8 exige penalty='elasticnet' para usar l1_ratio (Colab puede
    tener una versión anterior); desde 1.8 basta con l1_ratio."""
    import sklearn

    mayor, menor = (int(x) for x in sklearn.__version__.split(".")[:2])
    return {"penalty": "elasticnet"} if (mayor, menor) < (1, 8) else {}


def construir_modelo(tipo: str, params: dict, semilla: int) -> Pipeline:
    """Pipeline preprocesamiento + clasificador a partir de los hiperparámetros."""
    categoricas, numericas = CONJUNTOS[params.get("conjunto", "completo")]
    if tipo == "logistica":
        prep = construir_preprocesador(escalar=True, categoricas=categoricas,
                                       numericas=numericas)
        modelo = LogisticRegression(
            C=params["C"], l1_ratio=params.get("l1_ratio", 0.0), solver="saga",
            class_weight="balanced" if params.get("balanceado", True) else None,
            max_iter=5000, random_state=semilla, **_penalizacion_elastica())
    elif tipo == "hibrido":
        prep = _preprocesador_hibrido()
        modelo = LogisticRegression(
            C=params["C"], class_weight="balanced" if params.get("balanceado", True) else None,
            max_iter=5000, random_state=semilla)
    elif tipo == "arboles":
        prep = construir_preprocesador(escalar=False, categoricas=categoricas,
                                       numericas=numericas).set_output(transform="pandas")
        modelo = HistGradientBoostingClassifier(
            learning_rate=params["learning_rate"], max_depth=params["max_depth"],
            max_leaf_nodes=params["max_leaf_nodes"],
            min_samples_leaf=params["min_samples_leaf"],
            l2_regularization=params["l2_regularization"], max_iter=params["max_iter"],
            class_weight="balanced" if params.get("balanceado", True) else None,
            # Más pensiones pagadas tarde nunca reducen el riesgo (supuesto de dominio)
            monotonic_cst={"atrasos_pension": 1}, early_stopping=False,
            random_state=semilla)
    else:
        raise ValueError(f"Tipo de modelo desconocido: {tipo}")
    return Pipeline([("prep", prep), ("modelo", modelo)])


def _espacio(tipo: str, trial: optuna.Trial) -> dict:
    if tipo == "hibrido":   # variables fijas: solo se ajusta la regularización
        return {"balanceado": trial.suggest_categorical("balanceado", [True, False]),
                "C": trial.suggest_float("C", 1e-3, 10, log=True)}
    # Mismo orden de sugerencias que en la primera ejecución: resultados reproducibles
    params = {"conjunto": trial.suggest_categorical("conjunto", list(CONJUNTOS)),
              "balanceado": trial.suggest_categorical("balanceado", [True, False])}
    if tipo == "logistica":
        params.update(C=trial.suggest_float("C", 1e-3, 10, log=True),
                      l1_ratio=trial.suggest_float("l1_ratio", 0.0, 1.0))
    else:
        params.update(
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            max_depth=trial.suggest_int("max_depth", 2, 4),
            max_leaf_nodes=trial.suggest_int("max_leaf_nodes", 4, 15),
            min_samples_leaf=trial.suggest_int("min_samples_leaf", 20, 120),
            l2_regularization=trial.suggest_float("l2_regularization", 1e-3, 10, log=True),
            max_iter=trial.suggest_int("max_iter", 50, 400))
    return params


def optimizar(
    tipo: str, X_tr: pd.DataFrame, y_tr: np.ndarray, X_val: pd.DataFrame, y_val: np.ndarray,
    n_trials: int, semilla: int,
) -> optuna.Study:
    """Optuna (TPE con semilla) maximizando PR-AUC en la validación interna."""
    def objetivo(trial):
        modelo = construir_modelo(tipo, _espacio(tipo, trial), semilla).fit(X_tr, y_tr)
        return average_precision_score(y_val, modelo.predict_proba(X_val)[:, 1])

    estudio = optuna.create_study(direction="maximize",
                                  sampler=optuna.samplers.TPESampler(seed=semilla))
    estudio.optimize(objetivo, n_trials=n_trials, show_progress_bar=False)
    return estudio


# --------------------------------------------------------------------------- #
# Métricas
# --------------------------------------------------------------------------- #
def metricas(datos: pd.DataFrame, riesgo: np.ndarray, k_por_sede: dict, semilla: int) -> dict:
    """Métrica principal por familia (Precision/Lift/Recall@k) y complementarias."""
    y = datos["y_no_matricula"].to_numpy()
    total = precision_at_k_familiar(consolidar_familias(datos, riesgo), k_por_sede,
                                    semilla).query("sede == 'TOTAL'").iloc[0]
    salida = {"precision_k": total["precision_k"], "lift_k": total["lift_k"],
              "recall_k": total["recall_k"],
              "pr_auc": round(float(average_precision_score(y, riesgo)), 4),
              "roc_auc": round(float(roc_auc_score(y, riesgo)), 4)}
    if np.all((riesgo >= 0) & (riesgo <= 1)):
        salida["brier"] = round(float(brier_score_loss(y, riesgo)), 4)
    return salida


def puntajes_reglas(datos: pd.DataFrame) -> dict[str, np.ndarray]:
    """Reglas sin aprendizaje (Fase 1): D y D2."""
    atrasos = pd.to_numeric(datos["atrasos_pension"], errors="coerce").fillna(0).to_numpy()
    tardio = (datos["pago_origen"] == "tardio").to_numpy().astype(float)
    extra = pd.to_numeric(datos["reserva_extraordinaria"], errors="coerce").fillna(0).to_numpy()
    return {"D · más atrasos primero": atrasos,
            "D2 · señales administrativas": 100 * tardio + 20 * extra + atrasos}


def bootstrap_ic(
    datos: pd.DataFrame, riesgo: np.ndarray, k_por_sede: dict, semilla: int,
    repeticiones: int = 2000,
) -> dict:
    """IC 95 % de Precision@k, Lift@k y Recall@k remuestreando representantes por sede."""
    familias = consolidar_familias(datos, riesgo)
    rng = np.random.default_rng(semilla)
    sedes = familias["sede"].to_numpy()
    grupos = [np.flatnonzero(sedes == s) for s in np.unique(sedes)]
    valores = {"precision_k": [], "lift_k": [], "recall_k": []}
    for _ in range(repeticiones):
        indices = np.concatenate([rng.choice(g, size=len(g), replace=True) for g in grupos])
        muestra = familias.iloc[indices].reset_index(drop=True)
        muestra["id_familia"] = np.arange(len(muestra))
        total = precision_at_k_familiar(muestra, k_por_sede, semilla).query("sede == 'TOTAL'")
        for clave in valores:
            valores[clave].append(float(total[clave].iloc[0]))
    return {clave: [round(float(np.nanpercentile(v, 2.5)), 4),
                    round(float(np.nanpercentile(v, 97.5)), 4)]
            for clave, v in valores.items()}


# --------------------------------------------------------------------------- #
# Entrenamiento de candidatos y selección en C4
# --------------------------------------------------------------------------- #
@dataclass
class Candidato:
    tipo: str
    params: dict
    modelo: Pipeline
    pr_auc_validacion_interna: float
    metricas_entrenamiento: dict = field(default_factory=dict)
    metricas_c4: dict = field(default_factory=dict)
    historial: pd.DataFrame = field(default_factory=pd.DataFrame)   # trials de Optuna


def entrenar_candidatos(
    dataset: pd.DataFrame, config: dict, cohortes_entrenamiento: list[str],
    k_por_sede: dict, n_trials: int = 40,
) -> dict[str, Candidato]:
    """Optimiza y reentrena cada tipo de modelo; evalúa en entrenamiento y en C4."""
    semilla = config["proyecto"]["semilla"]
    entrenamiento = dataset[dataset["cohorte"].isin(cohortes_entrenamiento)]
    seleccion = dataset[dataset["rol"] == "seleccion"]
    # Validación interna temporal: la última cohorte de entrenamiento valida a las previas
    ultima = sorted(cohortes_entrenamiento)[-1]
    previas = [c for c in cohortes_entrenamiento if c != ultima]
    if not previas:
        raise ValueError("Se necesitan al menos dos cohortes de entrenamiento.")
    tr = entrenamiento[entrenamiento["cohorte"].isin(previas)]
    va = entrenamiento[entrenamiento["cohorte"] == ultima]
    log.info("Optimización: %s → %s (%d trials por modelo)", "+".join(previas), ultima,
             n_trials)

    candidatos = {}
    X_e, y_e = construir_matriz_x(entrenamiento), entrenamiento["y_no_matricula"].to_numpy()
    for tipo in TIPOS:
        estudio = optimizar(tipo, construir_matriz_x(tr), tr["y_no_matricula"].to_numpy(),
                            construir_matriz_x(va), va["y_no_matricula"].to_numpy(),
                            n_trials, semilla)
        params = dict(estudio.best_params)
        modelo = construir_modelo(tipo, params, semilla).fit(X_e, y_e)
        candidato = Candidato(tipo, params, modelo, round(estudio.best_value, 4))
        candidato.historial = estudio.trials_dataframe(attrs=("number", "value", "params"))
        candidato.metricas_entrenamiento = metricas(
            entrenamiento, modelo.predict_proba(X_e)[:, 1], k_por_sede, semilla)
        candidato.metricas_c4 = metricas(
            seleccion, modelo.predict_proba(construir_matriz_x(seleccion))[:, 1],
            k_por_sede, semilla)
        candidatos[tipo] = candidato
        log.info("%s: PR-AUC interna %.3f | Lift@k C4 %.2f", tipo,
                 candidato.pr_auc_validacion_interna, candidato.metricas_c4["lift_k"])
    return candidatos


def tabla_seleccion(candidatos: dict[str, Candidato], dataset: pd.DataFrame,
                    k_por_sede: dict, semilla: int) -> pd.DataFrame:
    """Candidatos y reglas en C4, ordenados por Lift@k (desempate: PR-AUC)."""
    seleccion = dataset[dataset["rol"] == "seleccion"]
    filas = [{"candidato": NOMBRES[c.tipo], "tipo": c.tipo, **c.metricas_c4}
             for c in candidatos.values()]
    for nombre, puntaje in puntajes_reglas(seleccion).items():
        filas.append({"candidato": nombre, "tipo": "regla",
                      **metricas(seleccion, puntaje, k_por_sede, semilla)})
    tabla = pd.DataFrame(filas).sort_values(["lift_k", "pr_auc"], ascending=False)
    return tabla.reset_index(drop=True)


def diagnostico_ajuste(candidatos: dict[str, Candidato]) -> pd.DataFrame:
    """Brecha entrenamiento − C4 (actividad de la semana 3: sobreajuste/subajuste)."""
    filas = []
    for c in candidatos.values():
        tr, c4 = c.metricas_entrenamiento["pr_auc"], c.metricas_c4["pr_auc"]
        brecha = round(tr - c4, 4)
        estado = ("sobreajuste" if brecha > 0.10 else
                  "subajuste" if tr < 0.15 else "ajuste razonable")
        filas.append({"modelo": NOMBRES[c.tipo], "pr_auc_entrenamiento": tr,
                      "pr_auc_C4": c4, "brecha": brecha, "diagnostico": estado})
    return pd.DataFrame(filas)


def calibrar(modelo: Pipeline, datos_c4: pd.DataFrame) -> CalibratedClassifierCV:
    """Calibración de Platt en C4 sobre el modelo congelado (no altera el ranking)."""
    calibrado = CalibratedClassifierCV(FrozenEstimator(modelo), method="sigmoid")
    return calibrado.fit(construir_matriz_x(datos_c4), datos_c4["y_no_matricula"])


# --------------------------------------------------------------------------- #
# Congelamiento y trazabilidad
# --------------------------------------------------------------------------- #
def guardar_sistema(sistema: dict, ruta: Path) -> str:
    """Guarda el sistema congelado y devuelve su huella SHA-256 (se registra antes de C5)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(sistema, ruta)
    huella = hashlib.sha256(ruta.read_bytes()).hexdigest()
    meta = {k: v for k, v in sistema.items() if k not in {"modelo", "calibrado"}}
    ruta.with_suffix(".json").write_text(
        json.dumps({**meta, "sha256": huella}, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8")
    return huella


# --------------------------------------------------------------------------- #
# Evaluación final, equidad y proyección
# --------------------------------------------------------------------------- #
def lineas_base_brier(datos: pd.DataFrame, entrenamiento: pd.DataFrame) -> pd.DataFrame:
    """R, B0 y B1 del v5 (no ordenan familias): Brier sobre P(no matrícula).

    R ("si reservó, continúa") y B0 (clase mayoritaria = matrícula) asignan riesgo 0;
    B1 asigna la tasa histórica de no matrícula del entrenamiento.
    """
    y = datos["y_no_matricula"].to_numpy()
    tasa = float(entrenamiento["y_no_matricula"].mean())
    cero = np.zeros(len(y))
    filas = [{"linea_base": "R · si reservó, continúa", "brier": brier_score_loss(y, cero)},
             {"linea_base": "B0 · clase mayoritaria", "brier": brier_score_loss(y, cero)},
             {"linea_base": f"B1 · tasa histórica ({tasa:.3f})",
              "brier": brier_score_loss(y, np.full(len(y), tasa))}]
    return pd.DataFrame(filas).round(4)


def equidad(datos: pd.DataFrame, riesgo: np.ndarray, k_por_sede: dict, semilla: int,
            grupos: list[str], minimo: int = 5) -> pd.DataFrame:
    """Por grupo: familias, eventos, tasa de selección, precisión y recall dentro del top-k.

    Se calcula por representante (unidad de contacto). Los grupos y los conteos de eventos
    menores que `minimo` se ocultan, y se aplica supresión complementaria (D48).
    """
    familias = consolidar_familias(datos, riesgo)
    propios = [g for g in grupos if g != "sede"]   # la sede ya viene de la consolidación
    atributos = datos.groupby(["cohorte", "id_familia"])[propios].max().reset_index()
    familias = familias.merge(atributos, on=["cohorte", "id_familia"], how="left")
    seleccionadas = set()
    for (_, sede), grupo in familias.groupby(["cohorte", "sede"]):
        k = k_por_sede.get(str(sede), 0)
        desempate = np.random.default_rng(semilla).random(len(grupo))
        orden = grupo.assign(_d=desempate).sort_values(["score", "_d"], ascending=[False, True])
        seleccionadas |= set(orden.head(k).index)
    familias["seleccionada"] = familias.index.isin(seleccionadas)
    filas = []
    for variable in grupos:
        for valor, g in familias.groupby(variable):
            eventos = int(g["evento"].sum())
            elegidas = g[g["seleccionada"]]
            fila = {"variable": variable, "grupo": str(valor), "familias": len(g),
                    "eventos": eventos,
                    "tasa_seleccion": round(len(elegidas) / len(g), 4),
                    "precision_k": round(elegidas["evento"].mean(), 4) if len(elegidas) else np.nan,
                    "recall_k": round(elegidas["evento"].sum() / eventos, 4) if eventos else np.nan}
            if len(g) < minimo or (0 < eventos < minimo):
                fila.update(familias=f"<{minimo}" if len(g) < minimo else len(g),
                            eventos=f"<{minimo}", precision_k=np.nan, recall_k=np.nan)
            filas.append(fila)
    return completar_supresion(pd.DataFrame(filas), minimo)


OCULTO = "oculto"


def completar_supresion(tabla: pd.DataFrame, minimo: int = 5) -> pd.DataFrame:
    """Supresión complementaria en la tabla de equidad.

    Dentro de cada variable, si solo una celda de `familias` o de `eventos` está oculta, su
    valor se deduce restando las demás del total. En ese caso se oculta también la celda
    visible más pequeña (marcada «oculto»), junto con su precisión y su recall.
    """
    if tabla.empty:
        return tabla
    salida = tabla.copy()
    salida[["familias", "eventos"]] = salida[["familias", "eventos"]].astype(object)
    marcas = {f"<{minimo}", OCULTO}
    for _, bloque in salida.groupby("variable", sort=False):
        for columna in ("familias", "eventos"):
            valores = salida.loc[bloque.index, columna]
            otra = celda_complementaria(valores, valores.astype(str).isin(marcas))
            if otra is None:
                continue
            salida.loc[otra, "eventos"] = OCULTO
            if columna == "familias":
                salida.loc[otra, "familias"] = OCULTO
            salida.loc[otra, ["precision_k", "recall_k"]] = np.nan
    return salida


def proyeccion(datos: pd.DataFrame, riesgo_calibrado: np.ndarray, tasa_b1: float,
               minimo: int = 10) -> pd.DataFrame:
    """Matrículas esperadas (suma de p = 1 − riesgo) frente a observadas por sede y subnivel.

    MAPE solo en grupos con al menos `minimo` matrículas observadas (v5, 6.2), comparado
    con B1 (N × tasa histórica de continuidad).
    """
    tabla = datos.assign(p=1 - np.asarray(riesgo_calibrado),
                         m=1 - datos["y_no_matricula"])
    grupos = tabla.groupby(["sede", "subnivel"]).agg(N=("m", "size"), observadas=("m", "sum"),
                                                     esperadas_modelo=("p", "sum"))
    grupos["esperadas_B1"] = grupos["N"] * (1 - tasa_b1)
    grupos = grupos[grupos["observadas"] >= minimo].copy()
    for col in ("modelo", "B1"):
        grupos[f"ape_{col}"] = (grupos[f"esperadas_{col}"] - grupos["observadas"]).abs() / \
            grupos["observadas"]
    return grupos.round(3).reset_index()
