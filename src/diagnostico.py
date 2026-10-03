"""
Diagnóstico de sobreajuste y subajuste (actividad de la semana 3).

Qué hace este módulo:
1. **Seguimiento de métricas** durante el entrenamiento (`RegistroMetricas`,
   `seguir_boosting`, `seguir_logistica`): pérdida y PR-AUC de entrenamiento y de
   validación en cada iteración del gradient boosting y según avanza el optimizador de
   las regresiones logísticas.
2. **Curvas de aprendizaje** con las funciones de scikit-learn que pide la actividad:
   `learning_curve` (por tamaño de datos) y `validation_curve` (por hiperparámetro).
3. **Diagnóstico cuantitativo** (`diagnosticar`, `resumen_seguimiento`): brecha,
   brecha relativa, mejora sobre el azar, iteración óptima y deterioro posterior.
4. **Estrategias de mejora** con comparación antes/después (`evaluar_estrategias`).

Reglas del protocolo que este módulo respeta:
- **C5 nunca se usa.** Ya se evaluó una sola vez (D38, D41). Todo se calcula con las
  cohortes de entrenamiento y con C4; `sin_prueba` descarta C5 antes de cualquier cálculo.
- **Orden temporal.** Las particiones nunca mezclan años: se entrena con cohortes
  anteriores y se valida con la siguiente. No se usan particiones al azar entre años.
- **Sin elegir mirando C4.** Lo que una estrategia debe elegir (por ejemplo, el número
  de iteraciones de la parada temprana) se elige en la validación interna
  (entrenamiento antiguo → cohorte más reciente del entrenamiento) y solo después se
  mide en C4.

Convención: y_no_matricula = 1 es el evento. «Puntaje» es la PR-AUC (precisión
promedio): más alto es mejor y un ordenamiento al azar obtiene la tasa de eventos.
«Pérdida» es la entropía cruzada (log-loss): más baja es mejor.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import average_precision_score, log_loss
from sklearn.model_selection import learning_curve, validation_curve

from src.data_processing import construir_matriz_x
from src.modeling import NOMBRES, construir_modelo, metricas

log = logging.getLogger("lemas.diagnostico")

NOMBRES_CORTOS = {"logistica": "Regresión logística", "arboles": "Gradient boosting",
                  "hibrido": "Logística híbrida"}
# Modelos de control: no son candidatos. Muestran cómo se ve cada problema en estos datos
# y sirven para comprobar que las reglas de diagnóstico los reconocen.
CONTROL_COMPLEJO = "Control: árboles sin regularizar"
CONTROL_RIGIDO = "Control: logística sobrerregularizada"
# Tipos de cada hiperparámetro al leer el historial de Optuna desde un CSV
ENTEROS = ("max_depth", "max_leaf_nodes", "min_samples_leaf", "max_iter")
REALES = ("C", "l1_ratio", "learning_rate", "l2_regularization")
PARAMETROS_POR_TIPO = {
    "logistica": ("conjunto", "balanceado", "C", "l1_ratio"),
    "hibrido": ("balanceado", "C"),
    "arboles": ("conjunto", "balanceado", "learning_rate", "max_depth", "max_leaf_nodes",
                "min_samples_leaf", "l2_regularization", "max_iter"),
}
UMBRALES = {"brecha_relativa_max": 0.30, "mejora_minima_sobre_azar": 1.5,
            "tolerancia_perdida": 0.01, "cambio_minimo": 0.005}


# --------------------------------------------------------------------------- #
# Particiones temporales (sin C5)
# --------------------------------------------------------------------------- #
def sin_prueba(dataset: pd.DataFrame) -> pd.DataFrame:
    """Descarta la cohorte de prueba: el diagnóstico nunca usa C5."""
    return dataset[dataset["rol"] != "prueba"]


@dataclass
class Particion:
    """Un par entrenamiento/validación que respeta el orden temporal."""

    nombre: str
    datos_tr: pd.DataFrame
    datos_val: pd.DataFrame
    etiqueta_tr: str
    etiqueta_val: str

    @property
    def X_tr(self) -> pd.DataFrame:  # noqa: N802  (X, convención de ML)
        return construir_matriz_x(self.datos_tr)

    @property
    def X_val(self) -> pd.DataFrame:  # noqa: N802
        return construir_matriz_x(self.datos_val)

    @property
    def y_tr(self) -> np.ndarray:
        return self.datos_tr["y_no_matricula"].to_numpy()

    @property
    def y_val(self) -> np.ndarray:
        return self.datos_val["y_no_matricula"].to_numpy()

    def resumen(self) -> dict:
        return {"particion": self.nombre, "entrenamiento": self.etiqueta_tr,
                "validacion": self.etiqueta_val, "n_entrenamiento": len(self.datos_tr),
                "eventos_entrenamiento": int(self.y_tr.sum()),
                "n_validacion": len(self.datos_val),
                "eventos_validacion": int(self.y_val.sum()),
                "tasa_validacion": round(float(self.y_val.mean()), 4)}


def particion_diagnostico(dataset: pd.DataFrame, cohortes_entrenamiento: list[str]
                          ) -> Particion:
    """Entrenamiento completo → C4. Es la partición con la que se diagnostica."""
    datos = sin_prueba(dataset)
    tr = datos[datos["cohorte"].isin(cohortes_entrenamiento)]
    val = datos[datos["rol"] == "seleccion"]
    if tr.empty or val.empty:
        raise ValueError("Faltan cohortes de entrenamiento o la cohorte de selección (C4).")
    return Particion("diagnostico", tr, val, "+".join(sorted(cohortes_entrenamiento)),
                     "+".join(sorted(val["cohorte"].unique())))


def particion_interna(dataset: pd.DataFrame, cohortes_entrenamiento: list[str]) -> Particion:
    """Cohortes antiguas → última cohorte del entrenamiento (la misma que usó Optuna).

    Sirve para elegir sin mirar C4 (por ejemplo, la iteración de la parada temprana)."""
    ultima = sorted(cohortes_entrenamiento)[-1]
    previas = [c for c in cohortes_entrenamiento if c != ultima]
    if not previas:
        raise ValueError("Se necesitan al menos dos cohortes de entrenamiento.")
    datos = sin_prueba(dataset)
    return Particion("interna", datos[datos["cohorte"].isin(previas)],
                     datos[datos["cohorte"] == ultima], "+".join(sorted(previas)), ultima)


# --------------------------------------------------------------------------- #
# Hiperparámetros de la Fase 2
# --------------------------------------------------------------------------- #
def mejores_parametros(historial: pd.DataFrame) -> dict[str, dict]:
    """Mejor configuración de cada modelo según el historial de Optuna guardado.

    Así el diagnóstico parte de los mismos modelos de la Fase 2, sin repetir la búsqueda.
    """
    por_nombre = {nombre: tipo for tipo, nombre in NOMBRES.items()}
    salida = {}
    for nombre, pruebas in historial.groupby("modelo", sort=False):
        tipo = por_nombre.get(nombre)
        if tipo is None:
            continue
        mejor = pruebas.loc[pruebas["value"].idxmax()]   # la primera en caso de empate
        params = {}
        for clave in PARAMETROS_POR_TIPO[tipo]:
            valor = mejor[f"params_{clave}"]
            if clave in ENTEROS:
                valor = int(valor)
            elif clave in REALES:
                valor = float(valor)
            elif clave == "balanceado":
                valor = str(valor).strip().lower() in {"true", "1", "1.0"}
            else:
                valor = str(valor)
            params[clave] = valor
        salida[tipo] = params
    faltan = set(NOMBRES) - set(salida)
    if faltan:
        raise ValueError(f"El historial no tiene todos los modelos; faltan: {sorted(faltan)}")
    return salida


def parametros_control(parametros: dict[str, dict]) -> dict[str, tuple[str, dict]]:
    """Dos modelos de control, definidos de antemano, uno por cada problema.

    - **Árboles sin regularizar:** tasa de aprendizaje alta, árboles sin límite de
      profundidad, hojas pequeñas y sin penalización. Debe sobreajustar.
    - **Logística sobrerregularizada:** penalización L1 tan fuerte que anula los
      coeficientes. Debe subajustar (predice casi lo mismo para todos).
    """
    balanceado = parametros["arboles"].get("balanceado", True)
    return {
        CONTROL_COMPLEJO: ("arboles", {
            "conjunto": "completo", "balanceado": balanceado, "learning_rate": 0.1,
            "max_depth": None, "max_leaf_nodes": 31, "min_samples_leaf": 5,
            "l2_regularization": 0.0, "max_iter": 300}),
        CONTROL_RIGIDO: ("logistica", {
            "conjunto": "reducido", "balanceado": False, "C": 0.001, "l1_ratio": 1.0}),
    }


# --------------------------------------------------------------------------- #
# Pérdida y puntaje
# --------------------------------------------------------------------------- #
def pesos_de_clase(y_tr: np.ndarray, balanceado: bool) -> dict | None:
    """Pesos «balanced» de scikit-learn, calculados con el entrenamiento.

    Los modelos balanceados optimizan una pérdida ponderada; para que la curva de
    pérdida describa lo que el modelo realmente minimiza, se mide con los mismos pesos.
    """
    if not balanceado:
        return None
    n, positivos = len(y_tr), int(np.sum(y_tr))
    if positivos in (0, n):
        return None
    return {0: n / (2 * (n - positivos)), 1: n / (2 * positivos)}


def perdida(y: np.ndarray, prob: np.ndarray, pesos: dict | None = None) -> float:
    """Entropía cruzada (log-loss), ponderada por clase si el modelo es balanceado."""
    ponderacion = None if pesos is None else np.where(np.asarray(y) == 1, pesos[1], pesos[0])
    return float(log_loss(y, np.clip(prob, 1e-7, 1 - 1e-7), sample_weight=ponderacion,
                          labels=[0, 1]))


def puntaje(y: np.ndarray, prob: np.ndarray) -> float:
    """PR-AUC (precisión promedio). Sin eventos no está definida: devuelve NaN."""
    return float(average_precision_score(y, prob)) if np.sum(y) > 0 else float("nan")


def _puntuador_perdida(pesos: dict | None):
    def puntuar(estimador, X, y):
        return -perdida(np.asarray(y), estimador.predict_proba(X)[:, 1], pesos)
    return puntuar


def _puntuador_puntaje(estimador, X, y):
    return puntaje(np.asarray(y), estimador.predict_proba(X)[:, 1])


# --------------------------------------------------------------------------- #
# 1. Seguimiento de métricas durante el entrenamiento
# --------------------------------------------------------------------------- #
@dataclass
class RegistroMetricas:
    """Sistema de monitoreo: guarda una fila por modelo, paso y conjunto.

    Uso:
        registro = RegistroMetricas()
        registro.registrar("Gradient boosting", paso=10, conjunto="validacion",
                           perdida=0.61, puntaje=0.14)
        registro.tabla()        # formato largo
        registro.ancho()        # una fila por paso, columnas por conjunto
    """

    filas: dict[tuple, dict] = field(default_factory=dict)

    def registrar(self, modelo: str, paso: int, conjunto: str, perdida: float,
                  puntaje: float, **extra) -> None:
        """Si se repite (modelo, paso, conjunto), el registro nuevo reemplaza al anterior."""
        self.filas[(modelo, int(paso), conjunto)] = {
            "modelo": modelo, "paso": int(paso), "conjunto": conjunto,
            "perdida": float(perdida), "puntaje": float(puntaje), **extra}

    def tabla(self) -> pd.DataFrame:
        return pd.DataFrame(list(self.filas.values()))

    def ancho(self) -> pd.DataFrame:
        tabla = self.tabla().pivot_table(index=["modelo", "paso"], columns="conjunto",
                                         values=["perdida", "puntaje"])
        tabla.columns = [f"{metrica}_{conjunto}" for metrica, conjunto in tabla.columns]
        return tabla.reset_index().rename(columns={"paso": "iteracion"})


def seguir_boosting(params: dict, particion: Particion, semilla: int,
                    iteraciones: int | None = None,
                    registro: RegistroMetricas | None = None,
                    nombre: str = NOMBRES_CORTOS["arboles"],
                    iteracion_fase2: int | None = None) -> pd.DataFrame:
    """Entrena el gradient boosting y registra pérdida y PR-AUC en cada iteración.

    `iteraciones` permite entrenar más allá de lo que eligió Optuna, para ver en qué
    punto la validación deja de mejorar. `iteracion_fase2` marca cuántas iteraciones usó
    el modelo de la Fase 2 (vacío en los modelos de control). Devuelve una fila por
    iteración.
    """
    registro = registro if registro is not None else RegistroMetricas()
    total = int(iteraciones or params["max_iter"])
    modelo = construir_modelo("arboles", {**params, "max_iter": total}, semilla)
    modelo.fit(particion.X_tr, particion.y_tr)
    pesos = pesos_de_clase(particion.y_tr, params.get("balanceado", True))
    preparar, clasificador = modelo[:-1], modelo[-1]
    conjuntos = {"entrenamiento": (preparar.transform(particion.X_tr), particion.y_tr),
                 "validacion": (preparar.transform(particion.X_val), particion.y_val)}
    for conjunto, (X, y) in conjuntos.items():
        for paso, prob in enumerate(clasificador.staged_predict_proba(X), start=1):
            registro.registrar(nombre, paso, conjunto, perdida(y, prob[:, 1], pesos),
                               puntaje(y, prob[:, 1]))
    return _seguimiento(registro, nombre, "iteración (árboles añadidos)", iteracion_fase2)


def _seguimiento(registro: RegistroMetricas, nombre: str, unidad: str,
                 iteracion_fase2: int | None) -> pd.DataFrame:
    tabla = registro.ancho()
    tabla = tabla[tabla["modelo"] == nombre].reset_index(drop=True)
    tabla["unidad"] = unidad
    tabla["iteracion_fase2"] = iteracion_fase2 if iteracion_fase2 else np.nan
    return tabla


PASOS_LOGISTICA = (1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 50, 75, 100, 150, 200, 300, 500,
                   1000, 2000, 5000)


def seguir_logistica(tipo: str, params: dict, particion: Particion, semilla: int,
                     registro: RegistroMetricas | None = None, nombre: str | None = None,
                     pasos: tuple[int, ...] = PASOS_LOGISTICA) -> pd.DataFrame:
    """Registra pérdida y PR-AUC de una regresión logística según avanza su optimizador.

    scikit-learn no expone el estado intermedio de estos optimizadores, así que el modelo
    se entrena desde cero con un límite de iteraciones cada vez mayor (1, 2, 3, 5…) y se
    mide después de cada entrenamiento. Se detiene cuando el optimizador converge antes
    del límite, de modo que el último punto es exactamente el modelo final de la Fase 2.
    Sirve para `tipo` "logistica" e "hibrido".
    """
    registro = registro if registro is not None else RegistroMetricas()
    nombre = nombre or NOMBRES_CORTOS[tipo]
    pesos = pesos_de_clase(particion.y_tr, params.get("balanceado", True))
    X_tr, X_val = particion.X_tr, particion.X_val
    for limite in pasos:
        modelo = construir_modelo(tipo, params, semilla)
        modelo[-1].set_params(max_iter=limite)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)   # aún no converge: esperado
            modelo.fit(X_tr, particion.y_tr)
        usadas = int(np.max(modelo[-1].n_iter_))
        for conjunto, X, y in (("entrenamiento", X_tr, particion.y_tr),
                               ("validacion", X_val, particion.y_val)):
            prob = modelo.predict_proba(X)[:, 1]
            registro.registrar(nombre, usadas, conjunto, perdida(y, prob, pesos),
                               puntaje(y, prob))
        if usadas < limite:      # convergió: es el modelo final
            break
    return _seguimiento(registro, nombre,
                        "iteración del optimizador (un entrenamiento por punto)", None)


# --------------------------------------------------------------------------- #
# 2. Curvas de aprendizaje (scikit-learn, con partición temporal)
# --------------------------------------------------------------------------- #
def _datos_y_division(particion: Particion):
    """Une entrenamiento y validación y devuelve la división fija para scikit-learn."""
    X = pd.concat([particion.X_tr, particion.X_val], ignore_index=True)
    y = np.concatenate([particion.y_tr, particion.y_val])
    n = len(particion.y_tr)
    return X, y, [(np.arange(n), np.arange(n, len(y)))]


def curva_por_tamano(tipo: str, params: dict, particion: Particion, semilla: int,
                     fracciones: tuple[float, ...] = (0.2, 0.36, 0.52, 0.68, 0.84, 1.0),
                     repeticiones: int = 5) -> pd.DataFrame:
    """`learning_curve` de scikit-learn con validación temporal fija.

    El entrenamiento se submuestrea al azar (dentro de sus propias cohortes) y la
    validación es siempre la cohorte siguiente completa. Se repite con varias semillas
    para ver cuánto cambia la curva según la submuestra.
    """
    X, y, division = _datos_y_division(particion)
    pesos = pesos_de_clase(particion.y_tr, params.get("balanceado", True))
    puntuadores = {"puntaje": _puntuador_puntaje, "perdida": _puntuador_perdida(pesos)}
    filas = []
    for repeticion in range(repeticiones):
        for metrica, puntuador in puntuadores.items():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ConvergenceWarning)
                tamanos, tr, val = learning_curve(
                    construir_modelo(tipo, params, semilla), X, y, cv=division,
                    train_sizes=list(fracciones), scoring=puntuador, shuffle=True,
                    random_state=semilla + repeticion, error_score=np.nan)
            signo = -1.0 if metrica == "perdida" else 1.0
            for n, valor_tr, valor_val in zip(tamanos, tr[:, 0], val[:, 0], strict=True):
                filas.append({"n": int(n), "repeticion": repeticion, "metrica": metrica,
                              "entrenamiento": signo * valor_tr,
                              "validacion": signo * valor_val})
    largo = pd.DataFrame(filas)
    tabla = largo.groupby(["metrica", "n"]).agg(
        entrenamiento=("entrenamiento", "mean"), entrenamiento_de=("entrenamiento", "std"),
        validacion=("validacion", "mean"), validacion_de=("validacion", "std")).reset_index()
    tabla.insert(0, "modelo", NOMBRES_CORTOS[tipo])
    tabla["fraccion"] = (tabla["n"] / len(particion.y_tr)).round(2)
    return tabla.fillna({"entrenamiento_de": 0.0, "validacion_de": 0.0})


def curva_por_hiperparametro(tipo: str, params: dict, particion: Particion, semilla: int,
                             nombre: str, valores: list) -> pd.DataFrame:
    """`validation_curve` de scikit-learn: un hiperparámetro varía, el resto queda fijo."""
    X, y, division = _datos_y_division(particion)
    pesos = pesos_de_clase(particion.y_tr, params.get("balanceado", True))
    columnas = {}
    for metrica, puntuador in {"puntaje": _puntuador_puntaje,
                               "perdida": _puntuador_perdida(pesos)}.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            tr, val = validation_curve(
                construir_modelo(tipo, params, semilla), X, y,
                param_name=f"modelo__{nombre}", param_range=valores, cv=division,
                scoring=puntuador, error_score=np.nan)
        signo = -1.0 if metrica == "perdida" else 1.0
        columnas[f"{metrica}_entrenamiento"] = signo * tr[:, 0]
        columnas[f"{metrica}_validacion"] = signo * val[:, 0]
    tabla = pd.DataFrame({"modelo": NOMBRES_CORTOS[tipo], "hiperparametro": nombre,
                          "valor": valores, **columnas})
    tabla["valor_fase2"] = params.get(nombre)
    return tabla


# --------------------------------------------------------------------------- #
# 3. Diagnóstico cuantitativo
# --------------------------------------------------------------------------- #
def evaluar(tipo: str, params: dict, particion: Particion, semilla: int,
            k_por_sede: dict | None = None) -> dict:
    """Entrena con la partición y mide pérdida, PR-AUC y (si hay k) Lift@k familiar."""
    modelo = construir_modelo(tipo, params, semilla).fit(particion.X_tr, particion.y_tr)
    pesos = pesos_de_clase(particion.y_tr, params.get("balanceado", True))
    prob_tr = modelo.predict_proba(particion.X_tr)[:, 1]
    prob_val = modelo.predict_proba(particion.X_val)[:, 1]
    salida = {"puntaje_entrenamiento": puntaje(particion.y_tr, prob_tr),
              "puntaje_validacion": puntaje(particion.y_val, prob_val),
              "perdida_entrenamiento": perdida(particion.y_tr, prob_tr, pesos),
              "perdida_validacion": perdida(particion.y_val, prob_val, pesos)}
    if k_por_sede:
        salida["lift_k_validacion"] = float(
            metricas(particion.datos_val, prob_val, k_por_sede, semilla)["lift_k"])
    return salida


def diagnosticar(puntaje_tr: float, puntaje_val: float, tasa_validacion: float,
                 umbrales: dict | None = None) -> dict:
    """Clasifica el ajuste con dos medidas.

    - **Brecha relativa** = (entrenamiento − validación) / entrenamiento. Si supera el
      umbral, el modelo memoriza el entrenamiento: *sobreajuste*.
    - **Mejora sobre el azar** = PR-AUC de validación / tasa de eventos. Un orden al azar
      obtiene 1. Si la brecha es pequeña pero la mejora no llega al mínimo, el modelo
      no capta la señal: *subajuste*.
    - En otro caso, *ajuste adecuado*. Si falta algún dato, *indeterminado*.

    Son reglas prácticas, no pruebas estadísticas. Limitación: compara la PR-AUC de dos
    conjuntos cuya tasa de eventos puede ser distinta.
    """
    u = {**UMBRALES, **(umbrales or {})}
    valores = (puntaje_tr, puntaje_val, tasa_validacion)
    if any(pd.isna(v) for v in valores) or puntaje_tr <= 0 or tasa_validacion <= 0:
        return {"brecha": float("nan"), "brecha_relativa": float("nan"),
                "mejora_sobre_azar": float("nan"), "diagnostico": "indeterminado"}
    brecha = puntaje_tr - puntaje_val
    relativa = brecha / puntaje_tr
    mejora = puntaje_val / tasa_validacion
    if relativa > u["brecha_relativa_max"]:
        estado = "sobreajuste"
    elif mejora < u["mejora_minima_sobre_azar"]:
        estado = "subajuste"
    else:
        estado = "ajuste adecuado"
    return {"brecha": brecha, "brecha_relativa": relativa, "mejora_sobre_azar": mejora,
            "diagnostico": estado}


def resumen_seguimiento(seguimiento: pd.DataFrame, umbrales: dict | None = None) -> dict:
    """Mide los patrones de la curva por iteración (actividad, sección 3.1).

    - `iteracion_optima`: donde la pérdida de validación es mínima.
    - `minimo_en_el_limite`: el mínimo es la última iteración registrada, es decir, la
      validación seguía mejorando cuando se dejó de entrenar.
    - `deterioro_perdida`: cuánto sube la pérdida de validación desde ese mínimo hasta
      el final (positivo = la validación empeora mientras el entrenamiento mejora).
    - `brecha_crece`: la brecha de pérdida al final supera a la del punto óptimo.
    """
    u = {**UMBRALES, **(umbrales or {})}
    s = seguimiento.sort_values("iteracion").reset_index(drop=True)
    optimo = int(s["perdida_validacion"].idxmin())
    final = s.iloc[-1]
    brecha_perdida = s["perdida_validacion"] - s["perdida_entrenamiento"]
    deterioro = float(final["perdida_validacion"] - s.loc[optimo, "perdida_validacion"])
    salida = {
        "iteraciones": int(final["iteracion"]),
        "iteracion_optima": int(s.loc[optimo, "iteracion"]),
        "minimo_en_el_limite": bool(optimo == len(s) - 1),
        "perdida_validacion_minima": float(s.loc[optimo, "perdida_validacion"]),
        "perdida_validacion_final": float(final["perdida_validacion"]),
        "deterioro_perdida": deterioro,
        "validacion_empeora": bool(deterioro > u["tolerancia_perdida"]),
        "brecha_perdida_en_optimo": float(brecha_perdida.iloc[optimo]),
        "brecha_perdida_final": float(brecha_perdida.iloc[-1]),
        "brecha_crece": bool(brecha_perdida.iloc[-1] - brecha_perdida.iloc[optimo]
                             > u["tolerancia_perdida"]),
        "iteracion_mejor_puntaje": int(s.loc[s["puntaje_validacion"].idxmax(), "iteracion"]),
        "mejor_puntaje_validacion": float(s["puntaje_validacion"].max()),
        "brecha_puntaje_final": float(final["puntaje_entrenamiento"]
                                      - final["puntaje_validacion"]),
        "entrenamiento_sigue_bajando": bool(
            s.loc[optimo, "perdida_entrenamiento"] - final["perdida_entrenamiento"]
            > u["tolerancia_perdida"]),
        "por_optimizador": bool("unidad" in s and str(s["unidad"].iloc[0]).startswith(
            "iteración del optimizador")),
    }
    iteracion_fase2 = s["iteracion_fase2"].iloc[0] if "iteracion_fase2" in s else np.nan
    if pd.notna(iteracion_fase2):
        fila = s[s["iteracion"] == min(int(iteracion_fase2), int(final["iteracion"]))].iloc[0]
        salida["iteracion_fase2"] = int(iteracion_fase2)
        salida["perdida_validacion_fase2"] = float(fila["perdida_validacion"])
        salida["puntaje_validacion_fase2"] = float(fila["puntaje_validacion"])
    return salida


def tabla_diagnostico(parametros: dict[str, dict], particion: Particion, semilla: int,
                      k_por_sede: dict | None = None, umbrales: dict | None = None
                      ) -> pd.DataFrame:
    """Diagnóstico de los modelos de la Fase 2 y de los controles (entrenamiento → C4).

    `veces_azar_entrenamiento` divide la PR-AUC de entrenamiento por la tasa de eventos
    del entrenamiento, para leerla en la misma escala que la validación.
    `perdida_ponderada` indica si la pérdida usa pesos de clase: las pérdidas solo son
    comparables entre modelos con el mismo valor.
    """
    tasa_val, tasa_tr = float(particion.y_val.mean()), float(particion.y_tr.mean())
    modelos = [(NOMBRES_CORTOS[tipo], "Fase 2", tipo, params)
               for tipo, params in parametros.items()]
    modelos += [(nombre, "control", tipo, params)
                for nombre, (tipo, params) in parametros_control(parametros).items()]
    filas = []
    for nombre, rol, tipo, params in modelos:
        medidas = evaluar(tipo, params, particion, semilla, k_por_sede)
        filas.append({"modelo": nombre, "rol": rol, **medidas,
                      **diagnosticar(medidas["puntaje_entrenamiento"],
                                     medidas["puntaje_validacion"], tasa_val, umbrales),
                      "veces_azar_entrenamiento": medidas["puntaje_entrenamiento"] / tasa_tr,
                      "perdida_ponderada": bool(params.get("balanceado", True))})
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# 4. Estrategias de mejora (antes / después)
# --------------------------------------------------------------------------- #
def iteracion_parada_temprana(params: dict, interna: Particion, semilla: int,
                              tope: int | None = None, minimo: int = 10) -> int:
    """Iteraciones con menor pérdida en la validación interna, sin mirar C4.

    Nunca devuelve más iteraciones que `tope` (por defecto, las del propio modelo): la
    parada temprana solo puede recortar el entrenamiento, no alargarlo.
    """
    tope = int(tope or params["max_iter"])
    seguimiento = seguir_boosting(params, interna, semilla, tope)
    return min(tope, max(minimo, resumen_seguimiento(seguimiento)["iteracion_optima"]))


def _g(valor: float) -> str:
    """Tres cifras significativas con coma decimal."""
    return f"{valor:.3g}".replace(".", ",")


def modelo_simple(params: dict) -> dict:
    """Gradient boosting con menos complejidad y más regularización (definido de antemano):
    árboles de dos niveles, pocas hojas, hojas grandes y penalización L2 alta. El número
    de iteraciones no cambia, para medir solo el efecto de la complejidad."""
    return {**params, "max_depth": 2, "max_leaf_nodes": 4,
            "min_samples_leaf": max(int(params["min_samples_leaf"]), 100),
            "l2_regularization": max(float(params["l2_regularization"]), 10.0)}


def _cambios_de_complejidad(antes: dict, despues: dict) -> str:
    """Describe solo los hiperparámetros de complejidad que cambian de verdad."""
    nombres = {"max_depth": "profundidad", "max_leaf_nodes": "hojas",
               "min_samples_leaf": "mínimo de muestras por hoja", "l2_regularization": "L2"}
    partes = [f"{texto} {_g(antes[clave])} → {_g(despues[clave])}"
              for clave, texto in nombres.items() if antes[clave] != despues[clave]]
    return ("; ".join(partes) if partes else "ya era el modelo más simple") + \
        "; mismas iteraciones"


def _efecto(cambio: float, minimo: float, positivo: str, negativo: str) -> str:
    if abs(cambio) < minimo:
        return "sin cambio apreciable"
    return positivo if cambio > 0 else negativo


def evaluar_estrategias(parametros: dict[str, dict], diagnostico: Particion,
                        interna: Particion, semilla: int, k_por_sede: dict | None = None,
                        umbrales: dict | None = None) -> pd.DataFrame:
    """Aplica seis estrategias y compara antes y después en entrenamiento → C4.

    Contra el sobreajuste (árboles):
      E1. Regularización y menor complejidad: del control sin regularizar al gradient
          boosting que eligió Optuna en la Fase 2. El punto de partida es un control, no
          un candidato: muestra el efecto de la regularización que la Fase 2 ya aplicó.
      E2. Parada temprana: menos iteraciones, elegidas por pérdida en la validación
          interna. Solo puede recortar.
      E3. Modelo más simple, con las mismas iteraciones.
    Contra el subajuste:
      E4. Ingeniería de variables: de la regresión logística a la logística híbrida, que
          usa las señales de la regla D2. Cambian las variables y también los
          hiperparámetros (cada modelo usa los que eligió Optuna).
      E5. Menos regularización: C diez veces mayor en la regresión logística.
      E6. Más entrenamiento: el doble de iteraciones en el gradient boosting.

    Un cambio de PR-AUC menor que `cambio_minimo` se informa como «sin cambio apreciable».
    """
    u = {**UMBRALES, **(umbrales or {})}
    arboles, logistica = parametros["arboles"], parametros["logistica"]
    _, complejo = parametros_control(parametros)[CONTROL_COMPLEJO]
    parada = iteracion_parada_temprana(arboles, interna, semilla)
    simple = modelo_simple(arboles)
    doble = 2 * int(arboles["max_iter"])
    gb, rl = NOMBRES_CORTOS["arboles"], NOMBRES_CORTOS["logistica"]
    recorte = (f"iteraciones: {arboles['max_iter']} → {parada}, elegidas por pérdida en la "
               "validación interna" if parada < arboles["max_iter"] else
               f"no recorta: en la validación interna la pérdida sigue bajando hasta la "
               f"iteración {arboles['max_iter']}")
    plan = [
        ("E1 · Regularización y menor complejidad", "sobreajuste",
         CONTROL_COMPLEJO, "arboles", complejo, gb, "arboles", arboles,
         f"búsqueda con Optuna (Fase 2): tasa de aprendizaje 0,1 → "
         f"{_g(arboles['learning_rate'])}; profundidad sin límite → {arboles['max_depth']}; "
         f"mínimo de muestras por hoja 5 → {arboles['min_samples_leaf']}; L2 0 → "
         f"{_g(arboles['l2_regularization'])}"),
        ("E2 · Parada temprana", "sobreajuste", gb, "arboles", arboles,
         gb, "arboles", {**arboles, "max_iter": parada}, recorte),
        ("E3 · Modelo más simple", "sobreajuste", gb, "arboles", arboles,
         gb, "arboles", simple, _cambios_de_complejidad(arboles, simple)),
        ("E4 · Ingeniería de variables", "subajuste", rl, "logistica",
         logistica, NOMBRES_CORTOS["hibrido"], "hibrido", parametros["hibrido"],
         "logística híbrida con las señales de D2 (pago tardío, reserva extraordinaria, "
         "atrasos por tramos); usa sus propios hiperparámetros de la Fase 2"),
        ("E5 · Menos regularización", "subajuste", rl, "logistica", logistica,
         rl, "logistica", {**logistica, "C": logistica["C"] * 10},
         f"C: {_g(logistica['C'])} → {_g(logistica['C'] * 10)}"),
        ("E6 · Más entrenamiento", "subajuste", gb, "arboles", arboles,
         gb, "arboles", {**arboles, "max_iter": doble},
         f"iteraciones: {arboles['max_iter']} → {doble}"),
    ]
    tasa = float(diagnostico.y_val.mean())
    cache: dict[str, dict] = {}
    filas = []
    for (nombre, problema, nombre_antes, tipo_antes, params_antes, nombre_despues,
         tipo_despues, params_despues, cambio) in plan:
        clave = f"{tipo_antes}|{sorted(params_antes.items(), key=str)}"
        if clave not in cache:
            cache[clave] = evaluar(tipo_antes, params_antes, diagnostico, semilla, k_por_sede)
        antes = cache[clave]
        despues = evaluar(tipo_despues, params_despues, diagnostico, semilla, k_por_sede)
        fila = {"estrategia": nombre, "problema": problema, "modelo_antes": nombre_antes,
                "modelo_despues": nombre_despues, "cambio": cambio}
        for momento, medidas in (("antes", antes), ("despues", despues)):
            estado = diagnosticar(medidas["puntaje_entrenamiento"],
                                  medidas["puntaje_validacion"], tasa, umbrales)
            for clave_medida, valor in {**medidas, **estado}.items():
                fila[f"{clave_medida}_{momento}"] = valor
        fila["cambio_puntaje_validacion"] = (despues["puntaje_validacion"]
                                             - antes["puntaje_validacion"])
        # La brecha se compara en valor absoluto: lo que importa es su tamaño
        fila["cambio_brecha"] = abs(fila["brecha_despues"]) - abs(fila["brecha_antes"])
        fila["efecto_validacion"] = _efecto(fila["cambio_puntaje_validacion"],
                                            u["cambio_minimo"], "mejora", "empeora")
        fila["efecto_brecha"] = _efecto(fila["cambio_brecha"], u["cambio_minimo"],
                                        "aumenta", "reduce")
        fila["perdidas_comparables"] = bool(params_antes.get("balanceado", True)
                                            == params_despues.get("balanceado", True))
        # ¿El modelo de partida tenía el problema que la estrategia busca corregir?
        fila["aplica_al_diagnostico"] = bool(fila["diagnostico_antes"] == problema)
        fila["modelo_sin_cambios"] = bool(tipo_antes == tipo_despues
                                          and params_antes == params_despues)
        filas.append(fila)
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# 5. Conclusiones en lenguaje claro (se generan con los resultados, no a mano)
# --------------------------------------------------------------------------- #
def _n(valor: float, decimales: int = 3, signo: bool = False) -> str:
    """Número con coma decimal y signo menos tipográfico, como en la documentación."""
    texto = f"{valor:{'+' if signo else ''}.{decimales}f}".replace(".", ",")
    if set(texto.lstrip("+-")) <= set("0,"):           # evita «−0,000»
        texto = texto.lstrip("+-")
    return texto.replace("-", "−")


numero = _n     # nombre público para cuadernos y reportes


def ganancia_por_datos(curva_tamano: pd.DataFrame) -> pd.DataFrame:
    """¿Ayudaría tener más datos? Compara la validación con la mitad y con todo el
    entrenamiento, y pone la diferencia al lado de la variación entre submuestras.

    `concluyente` es True solo si la diferencia supera dos veces esa variación.
    """
    filas = []
    puntajes = curva_tamano[curva_tamano["metrica"] == "puntaje"]
    for modelo, d in puntajes.groupby("modelo", sort=False):
        d = d.sort_values("n")
        mitad, todo = d.iloc[len(d) // 2 - 1], d.iloc[-1]
        ganancia = float(todo["validacion"] - mitad["validacion"])
        variacion = float(mitad["validacion_de"])
        filas.append({"modelo": modelo, "n_mitad": int(mitad["n"]), "n_todo": int(todo["n"]),
                      "validacion_mitad": float(mitad["validacion"]),
                      "validacion_todo": float(todo["validacion"]), "ganancia": ganancia,
                      "variacion_entre_submuestras": variacion,
                      "concluyente": bool(abs(ganancia) > 2 * variacion),
                      "brecha_con_todo": float(todo["entrenamiento"] - todo["validacion"])})
    return pd.DataFrame(filas)


EXPLICACION = {
    "sobreajuste": "memoriza el entrenamiento y pierde rendimiento con datos nuevos",
    "subajuste": "no capta señal suficiente: rinde poco en ambos conjuntos",
    "ajuste adecuado": "rinde de forma parecida en ambos conjuntos y supera al azar",
    "indeterminado": "faltan datos para clasificarlo",
}


def _frase_brecha(brecha: float, relativa: float) -> str:
    if brecha < 0:
        return (f"la validación supera al entrenamiento en {_n(-brecha)} (no hay brecha "
                "de sobreajuste)")
    return f"brecha de {_n(brecha)} ({_n(100 * relativa, 0)} % del entrenamiento)"


def conclusiones(diagnostico: pd.DataFrame, resumenes: dict[str, dict],
                 estrategias: pd.DataFrame | None, etiqueta_val: str) -> dict[str, list[str]]:
    """Frases que describen el diagnóstico, las curvas y las estrategias.

    El cuaderno y el reporte usan estas mismas frases, así que siempre coinciden con las
    cifras de la ejecución (sintética o real). Con `estrategias=None` solo se describen
    los modelos y las curvas.
    """
    salida: dict[str, list[str]] = {"modelos": [], "controles": [], "curvas": [],
                                    "estrategias": [], "balance": []}
    for fila in diagnostico.itertuples():
        frase = (f"{fila.modelo}: {fila.diagnostico} ({EXPLICACION[fila.diagnostico]}). "
                 f"PR-AUC de {_n(fila.puntaje_entrenamiento)} en entrenamiento y "
                 f"{_n(fila.puntaje_validacion)} en {etiqueta_val}; "
                 f"{_frase_brecha(fila.brecha, fila.brecha_relativa)}; "
                 f"{_n(fila.mejora_sobre_azar, 2)} veces el azar en {etiqueta_val}.")
        salida["controles" if fila.rol == "control" else "modelos"].append(frase)

    for nombre, r in resumenes.items():
        frase = (f"{nombre}: la pérdida de validación es mínima en el paso "
                 f"{r['iteracion_optima']} de {r['iteraciones']} "
                 f"({_n(r['perdida_validacion_minima'])}). ")
        if r["minimo_en_el_limite"] and r.get("por_optimizador"):
            frase += "El mínimo coincide con el último paso, cuando el optimizador converge."
        elif r["minimo_en_el_limite"]:
            frase += ("El mínimo coincide con el último paso: la validación seguía "
                      "mejorando al terminar.")
        elif r["validacion_empeora"] and r.get("entrenamiento_sigue_bajando"):
            frase += (f"Después sube {_n(r['deterioro_perdida'])} mientras el entrenamiento "
                      "sigue bajando: es el patrón de sobreajuste.")
        elif r["validacion_empeora"]:
            frase += f"Después sube {_n(r['deterioro_perdida'])}."
        else:
            frase += (f"Después cambia solo {_n(r['deterioro_perdida'], signo=True)}: la "
                      "validación se estanca, no se deteriora.")
        if "iteracion_fase2" in r:
            frase += (f" La Fase 2 usó {r['iteracion_fase2']} iteraciones (pérdida de "
                      f"validación {_n(r['perdida_validacion_fase2'])}).")
        salida["curvas"].append(frase)

    fase2 = diagnostico[diagnostico["rol"] == "Fase 2"]
    estados = fase2["diagnostico"].value_counts().to_dict()
    por_estado = ("Modelos de la Fase 2 por diagnóstico: "
                  + ", ".join(f"{cantidad} con {estado}" for estado, cantidad in estados.items())
                  + ".")
    if estrategias is None:
        salida["balance"].append(por_estado)
        return salida

    for e in estrategias.itertuples():
        if e.modelo_sin_cambios:
            salida["estrategias"].append(
                f"{e.estrategia}: no modifica el modelo en esta ejecución ({e.cambio}).")
            continue
        verbo = {"mejora": "la PR-AUC mejora", "empeora": "la PR-AUC empeora"}.get(
            e.efecto_validacion, "PR-AUC sin cambio apreciable")
        frase = (f"{e.estrategia}: PR-AUC en {etiqueta_val} de "
                 f"{_n(e.puntaje_validacion_antes)} a {_n(e.puntaje_validacion_despues)} "
                 f"({_n(e.cambio_puntaje_validacion, signo=True)}: {verbo}); "
                 f"brecha de {_n(e.brecha_antes, signo=True)} a "
                 f"{_n(e.brecha_despues, signo=True)} "
                 f"({'se reduce' if e.efecto_brecha == 'reduce' else e.efecto_brecha})")
        if hasattr(e, "lift_k_validacion_antes"):
            cambio_lift = e.lift_k_validacion_despues - e.lift_k_validacion_antes
            frase += (f"; Lift@k de {_n(e.lift_k_validacion_antes, 2)} a "
                      f"{_n(e.lift_k_validacion_despues, 2)}")
            if (abs(cambio_lift) >= 0.05 and e.efecto_validacion != "sin cambio apreciable"
                    and (cambio_lift > 0) != (e.cambio_puntaje_validacion > 0)):
                frase += ", en sentido contrario a la PR-AUC"
        frase += "."
        if not e.aplica_al_diagnostico:
            frase += (f" El modelo de partida no presentaba {e.problema} "
                      f"({e.diagnostico_antes}), así que sirve como comprobación.")
        if e.diagnostico_antes != e.diagnostico_despues:
            frase += f" El diagnóstico pasa de {e.diagnostico_antes} a {e.diagnostico_despues}."
        salida["estrategias"].append(frase)

    activas = estrategias[~estrategias["modelo_sin_cambios"]]
    sin_cambios = estrategias[estrategias["modelo_sin_cambios"]]
    conteo = activas["efecto_validacion"].value_counts()
    salida["balance"].append(
        f"Efecto de las {len(estrategias)} estrategias sobre la PR-AUC en {etiqueta_val}: "
        f"mejora en {int(conteo.get('mejora', 0))}, empeora en "
        f"{int(conteo.get('empeora', 0))} y no cambia de forma apreciable en "
        f"{int(conteo.get('sin cambio apreciable', 0))}"
        + (f"; {', '.join(e.split(' · ')[0] for e in sin_cambios['estrategia'])} no modificó "
           "el modelo." if len(sin_cambios) else "."))
    contra = estrategias[estrategias["problema"] == "sobreajuste"]
    salida["balance"].append(
        f"Estrategias contra el sobreajuste que reducen la brecha: "
        f"{int((contra['efecto_brecha'] == 'reduce').sum())} de {len(contra)}.")
    salida["balance"].insert(0, por_estado)
    salida["balance"].append(
        "Este análisis usa solo las cohortes de entrenamiento y C4. C5 ya se evaluó una "
        "vez y no interviene, así que estas estrategias no cambian la decisión final del "
        "proyecto (priorizar con la regla D2).")
    return salida
