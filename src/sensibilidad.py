"""
Análisis de sensibilidad de hiperparámetros (Workshop S5).

Parte del historial de Optuna ya guardado (`results/metrics/optuna_historial_<fuente>.csv`):
180 pruebas, 60 por modelo, con sus hiperparámetros y la PR-AUC de la validación interna
C2 → C3. Ese archivo no contiene datos de estudiantes, así que el análisis se puede repetir
sin la base real y **no vuelve a entrenar ningún modelo ni usa C4 o C5**.

Se responden cuatro preguntas:

1. **¿Qué hiperparámetros importan?** Importancia por fANOVA (descomposición funcional de
   la varianza sobre un bosque aleatorio, Hutter et al., 2014) y por disminución media de
   impureza, ambas de Optuna, repetidas con varias semillas para ver su estabilidad.
2. **¿Cómo cambia la PR-AUC con cada uno?** Dependencia parcial sobre un modelo sustituto
   (bosque aleatorio entrenado con las 60 pruebas): el efecto promedio de mover un
   hiperparámetro dejando los demás como en las pruebas observadas.
3. **¿Interactúan?** Estadístico H de Friedman para cada par (proporción de la variación
   conjunta que no se explica sumando los efectos por separado) y dependencia parcial 2D
   del par más fuerte.
4. **¿Cuánto ganó la búsqueda?** PR-AUC de la primera prueba, mediana de las 10 primeras
   (fase aleatoria del TPE) y mejor prueba.

Advertencia que acompaña a todas las cifras: con 60 pruebas por modelo y una validación de
81 eventos, el sustituto es aproximado; las conclusiones se leen como tendencias.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np
import optuna
import pandas as pd
from optuna.distributions import CategoricalDistribution, IntDistribution
from sklearn.ensemble import RandomForestRegressor

from src.diagnostico import numero
from src.modeling import espacio_de

optuna.logging.set_verbosity(optuna.logging.WARNING)

# Los mismos espacios con los que se optimizó: una sola definición, en config.yaml
ESPACIOS: dict[str, dict] = {tipo: espacio_de(tipo) for tipo in ("logistica", "arboles", "hibrido")}
PREFIJOS = {"Regresión": "logistica", "Gradient": "arboles", "Logística": "hibrido"}
NOMBRES = {"logistica": "Regresión logística", "arboles": "Gradient boosting",
           "hibrido": "Logística híbrida"}
SEMILLAS = (42, 7, 123, 2024, 9)
N_ALEATORIAS = 10          # pruebas iniciales aleatorias del muestreador TPE (por defecto)


def tipo_de(modelo: str) -> str:
    for prefijo, tipo in PREFIJOS.items():
        if str(modelo).startswith(prefijo):
            return tipo
    raise ValueError(f"Modelo desconocido: {modelo}")


def _valor(nombre: str, crudo, distribucion):
    if isinstance(distribucion, CategoricalDistribution):
        if isinstance(distribucion.choices[0], bool):
            return str(crudo).strip().lower() in {"true", "1"}
        return str(crudo)
    if isinstance(distribucion, IntDistribution):
        return int(round(float(crudo)))
    return float(crudo)


def pruebas_de(historial: pd.DataFrame, tipo: str) -> pd.DataFrame:
    """Las pruebas de un modelo, con columnas `value` y una por hiperparámetro."""
    datos = historial[historial["modelo"].map(tipo_de) == tipo].sort_values("number")
    salida = pd.DataFrame({"number": datos["number"].to_numpy(),
                           "value": datos["value"].to_numpy(dtype=float)})
    for nombre, dist in ESPACIOS[tipo].items():
        salida[nombre] = [_valor(nombre, v, dist) for v in datos[f"params_{nombre}"]]
    return salida


def reconstruir_estudio(pruebas: pd.DataFrame, tipo: str) -> optuna.Study:
    """Estudio de Optuna con las pruebas guardadas (sin volver a entrenar)."""
    estudio = optuna.create_study(direction="maximize")
    for _, fila in pruebas.iterrows():
        params = {n: fila[n] for n in ESPACIOS[tipo]}
        estudio.add_trial(optuna.trial.create_trial(
            params=params, distributions=ESPACIOS[tipo], value=float(fila["value"])))
    return estudio


def importancias(pruebas: pd.DataFrame, tipo: str,
                 semillas: tuple = SEMILLAS) -> pd.DataFrame:
    """Importancia por fANOVA y por impureza, media y desviación entre semillas."""
    estudio = reconstruir_estudio(pruebas, tipo)
    filas = []
    for metodo, clase in (("fANOVA", optuna.importance.FanovaImportanceEvaluator),
                          ("Impureza", optuna.importance.MeanDecreaseImpurityImportanceEvaluator)):
        valores = pd.DataFrame([optuna.importance.get_param_importances(
            estudio, evaluator=clase(seed=s), normalize=True) for s in semillas])
        for nombre in valores.columns:
            filas.append({"modelo": NOMBRES[tipo], "metodo": metodo, "hiperparametro": nombre,
                          "importancia": round(float(valores[nombre].mean()), 4),
                          "desviacion": round(float(valores[nombre].std(ddof=0)), 4)})
    tabla = pd.DataFrame(filas)
    orden = (tabla[tabla["metodo"] == "fANOVA"].sort_values("importancia", ascending=False)
             ["hiperparametro"].tolist())
    tabla["puesto"] = tabla["hiperparametro"].map({n: i + 1 for i, n in enumerate(orden)})
    return tabla.sort_values(["metodo", "puesto"]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Modelo sustituto, dependencia parcial e interacciones
# --------------------------------------------------------------------------- #
@dataclass
class Sustituto:
    tipo: str
    columnas: list[str]
    modelo: RandomForestRegressor
    X: pd.DataFrame

    def predecir(self, X: pd.DataFrame) -> np.ndarray:
        return self.modelo.predict(X[self.columnas])


def _codificar(pruebas: pd.DataFrame, tipo: str) -> pd.DataFrame:
    """Hiperparámetros numéricos (log10 en las escalas logarítmicas; 0/1 en las categorías)."""
    X = pd.DataFrame(index=pruebas.index)
    for nombre, dist in ESPACIOS[tipo].items():
        valores = pruebas[nombre]
        if isinstance(dist, CategoricalDistribution):
            X[nombre] = (valores == dist.choices[0]).astype(float)
        elif getattr(dist, "log", False):
            X[nombre] = np.log10(valores.astype(float))
        else:
            X[nombre] = valores.astype(float)
    return X


def ajustar_sustituto(pruebas: pd.DataFrame, tipo: str, semilla: int = 42,
                      arboles: int = 500) -> Sustituto:
    """Bosque aleatorio que aproxima la PR-AUC como función de los hiperparámetros."""
    X = _codificar(pruebas, tipo)
    modelo = RandomForestRegressor(n_estimators=arboles, min_samples_leaf=3,
                                   random_state=semilla)
    modelo.fit(X, pruebas["value"].to_numpy())
    return Sustituto(tipo, list(X.columns), modelo, X)


def _rejilla(sustituto: Sustituto, nombre: str, puntos: int = 25) -> np.ndarray:
    dist = ESPACIOS[sustituto.tipo][nombre]
    if isinstance(dist, CategoricalDistribution):
        return np.array([1.0, 0.0])
    columna = sustituto.X[nombre]
    if isinstance(dist, IntDistribution) and dist.high - dist.low <= puntos:
        return np.arange(dist.low, dist.high + 1, dtype=float)
    return np.linspace(columna.min(), columna.max(), puntos)


def dependencia_parcial(sustituto: Sustituto, nombre: str, puntos: int = 25) -> pd.DataFrame:
    """PR-AUC promedio predicha al fijar `nombre` en cada valor de la rejilla."""
    filas = []
    for valor in _rejilla(sustituto, nombre, puntos):
        X = sustituto.X.copy()
        X[nombre] = valor
        filas.append({"hiperparametro": nombre, "valor_codificado": valor,
                      "pr_auc": float(sustituto.predecir(X).mean())})
    tabla = pd.DataFrame(filas)
    dist = ESPACIOS[sustituto.tipo][nombre]
    if isinstance(dist, CategoricalDistribution):
        tabla["valor"] = [str(dist.choices[0]) if v == 1 else str(dist.choices[1])
                          for v in tabla["valor_codificado"]]
    elif getattr(dist, "log", False):
        tabla["valor"] = 10 ** tabla["valor_codificado"]
    else:
        tabla["valor"] = tabla["valor_codificado"]
    tabla["modelo"] = NOMBRES[sustituto.tipo]
    return tabla


def _pd_puntual(sustituto: Sustituto, columnas: list[str]) -> np.ndarray:
    """Dependencia parcial evaluada en los propios puntos observados (para el H de Friedman)."""
    observados = sustituto.X[columnas].to_numpy()
    salida = np.empty(len(observados))
    for i, fila in enumerate(observados):
        X = sustituto.X.copy()
        X[columnas] = fila
        salida[i] = sustituto.predecir(X).mean()
    return salida - salida.mean()


def interacciones(sustituto: Sustituto) -> pd.DataFrame:
    """Estadístico H² de Friedman para cada par de hiperparámetros (0 = sin interacción)."""
    individuales = {c: _pd_puntual(sustituto, [c]) for c in sustituto.columnas}
    filas = []
    for a, b in itertools.combinations(sustituto.columnas, 2):
        conjunta = _pd_puntual(sustituto, [a, b])
        denominador = float((conjunta ** 2).sum())
        h2 = (float(((conjunta - individuales[a] - individuales[b]) ** 2).sum()) / denominador
              if denominador > 0 else 0.0)
        filas.append({"modelo": NOMBRES[sustituto.tipo], "par": f"{a} × {b}",
                      "a": a, "b": b, "h2": round(min(max(h2, 0.0), 1.0), 4),
                      "variacion_conjunta": round(float(np.sqrt(denominador / len(conjunta))), 5)})
    return pd.DataFrame(filas).sort_values("h2", ascending=False).reset_index(drop=True)


def dependencia_2d(sustituto: Sustituto, a: str, b: str, puntos: int = 15) -> pd.DataFrame:
    filas = []
    for va in _rejilla(sustituto, a, puntos):
        for vb in _rejilla(sustituto, b, puntos):
            X = sustituto.X.copy()
            X[a], X[b] = va, vb
            filas.append({"a": va, "b": vb, "pr_auc": float(sustituto.predecir(X).mean())})
    return pd.DataFrame(filas)


def sensibilidad(sustituto: Sustituto, pruebas: pd.DataFrame) -> pd.DataFrame:
    """Cuánto cambia la PR-AUC (sustituto) al mover cada hiperparámetro en todo su rango,
    con los demás fijos en la mejor prueba (análisis de uno a la vez)."""
    mejor = sustituto.X.loc[[pruebas["value"].idxmax()]]
    filas = []
    for nombre in sustituto.columnas:
        valores = []
        for v in _rejilla(sustituto, nombre):
            X = mejor.copy()
            X[nombre] = v
            valores.append(float(sustituto.predecir(X)[0]))
        filas.append({"modelo": NOMBRES[sustituto.tipo], "hiperparametro": nombre,
                      "pr_auc_min": round(min(valores), 4), "pr_auc_max": round(max(valores), 4),
                      "rango": round(max(valores) - min(valores), 4)})
    return pd.DataFrame(filas).sort_values("rango", ascending=False).reset_index(drop=True)


def antes_despues(pruebas: pd.DataFrame, tipo: str, tasa_validacion: float | None = None
                  ) -> dict:
    """PR-AUC de la primera prueba, mediana de la fase aleatoria y mejor prueba."""
    mejor = pruebas.loc[pruebas["value"].idxmax()]
    salida = {"modelo": NOMBRES[tipo],
              "primera_prueba": round(float(pruebas["value"].iloc[0]), 4),
              "mediana_aleatorias": round(float(pruebas["value"].iloc[:N_ALEATORIAS].median()), 4),
              "mediana_todas": round(float(pruebas["value"].median()), 4),
              "mejor": round(float(mejor["value"]), 4), "prueba_mejor": int(mejor["number"])}
    salida["ganancia_sobre_aleatorias"] = round(salida["mejor"] - salida["mediana_aleatorias"], 4)
    if tasa_validacion:
        salida["veces_azar_mejor"] = round(salida["mejor"] / tasa_validacion, 2)
    return salida


def conclusiones(imp: pd.DataFrame, inter: pd.DataFrame, sens: pd.DataFrame,
                 antes: pd.DataFrame) -> list[str]:
    textos = []
    fan = imp[imp["metodo"] == "fANOVA"]
    for modelo, grupo in fan.groupby("modelo", sort=False):
        top = grupo.sort_values("importancia", ascending=False).head(2)
        partes = [f"{f['hiperparametro']} ({numero(100 * f['importancia'], 0)} %)"
                  for _, f in top.iterrows()]
        textos.append(f"{modelo}: lo que más explica la variación de la PR-AUC es "
                      + " y ".join(partes) + " (fANOVA).")
    for modelo, grupo in inter.groupby("modelo", sort=False):
        f = grupo.iloc[0]
        nivel = "débil" if f["h2"] < 0.1 else "moderada" if f["h2"] < 0.3 else "fuerte"
        textos.append(f"{modelo}: la interacción más fuerte es {f['par']} "
                      f"(H² = {numero(f['h2'], 2)}, {nivel}).")
    for _, f in antes.iterrows():
        textos.append(f"{f['modelo']}: la búsqueda pasó de una mediana de "
                      f"{numero(f['mediana_aleatorias'], 3)} en las 10 pruebas aleatorias a "
                      f"{numero(f['mejor'], 3)} en la mejor "
                      f"(+{numero(f['ganancia_sobre_aleatorias'], 3)}).")
    return textos
