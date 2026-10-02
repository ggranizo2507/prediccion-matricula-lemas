"""
Fase 3 · Lógica de la aplicación (separada de Streamlit para poder probarla).

Uso operativo (D42): al corte t0 (20 de febrero) se carga la base seudonimizada con
la hoja del ciclo actual y, de preferencia, la del ciclo anterior. La aplicación:

1. Arma la población elegible del ciclo actual (reserva aprobada antes de t0, sin 3.º
   de bachillerato y sin pago de matrícula ya confirmado).
2. Prioriza representantes con la regla **D2** (decisión D40/D41).
3. Estima la probabilidad de no matrícula con el modelo calibrado (referencia: B1).
4. Proyecta matrículas esperadas por sede y subnivel.

Todo ocurre en memoria. Nada se guarda en disco ni se envía a terceros.

Modos (D42):
- ``demo``: solo datos sintéticos (columna ``origen_datos = SINTETICO``).
- ``institucional``: base seudonimizada real; solo en un equipo de LEMAS o en Colab
  autorizado (variable de entorno ``LEMAS_MODO=institucional``). Desde D45 la aplicación
  también seudonimiza el Excel y muestra la lista con nombres (``src/institucional.py``);
  este módulo sigue recibiendo únicamente la base seudonimizada.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.data_processing import (
    agregar_predictores,
    construir_dataset,
    construir_matriz_x,
    es_curso_terminal,
    limpiar_base,
)
from src.evaluate import calcular_k_por_sede, consolidar_familias
from src.modeling import calibrar, construir_modelo, puntajes_reglas

MODOS = ("demo", "institucional")
# Columnas que delatan identificadores directos: nunca se aceptan en la app
PATRON_IDENTIFICADOR = re.compile(
    r"(?i)^(ci|c[eé]dula.*|cedulap|nombre.*|nombres.*|apellido.*|codigo|c[oó]digo|"
    r"tel[eé]fono.*|correo.*|email.*|direcci[oó]n.*)$")
COLUMNAS_MINIMAS = ["anoa", "Sede", "Nivel", "Paralelo", "P.Académico", "P.Conducta",
                    "fecha_pago", "Reserva", "RColegio", "Fecha Reserva", "Tiempo", "beca",
                    "# meses caído", "anio_ingreso", "id_seudonimo", "id_familia_seudonimo"]
REGLA_PRIORIZACION = "D2 · señales administrativas"
# Hiperparámetros de la logística híbrida elegidos por Optuna en la Fase 2 (datos reales);
# en modo demo se reentrena con ellos sobre la base sintética.
PARAMS_DEMO = {"C": 9.0, "balanceado": True}
RUTA_SISTEMA_REAL = "models/sistema_real.joblib"


def modo_actual() -> str:
    """El modo institucional solo se activa explícitamente por variable de entorno."""
    modo = os.environ.get("LEMAS_MODO", "demo").strip().lower()
    return modo if modo in MODOS else "demo"


# --------------------------------------------------------------------------- #
# Validación de la entrada
# --------------------------------------------------------------------------- #
class ErrorEntrada(ValueError):  # noqa: N818  (nombre en español)
    """Error con un mensaje apto para el usuario final (sin detalles técnicos)."""


def validar_entrada(df: pd.DataFrame, modo: str) -> None:
    """Reglas de seguridad y de estructura antes de procesar un archivo."""
    if df.empty:
        raise ErrorEntrada("El archivo no tiene filas.")
    identificadores = [c for c in df.columns if PATRON_IDENTIFICADOR.match(str(c).strip())]
    if identificadores:
        raise ErrorEntrada(
            "El archivo contiene columnas con identificadores directos "
            f"({', '.join(identificadores)}). Un archivo CSV debe estar seudonimizado. En "
            "LEMAS, suba el Excel junto con la clave en el modo institucional (o use el "
            "cuaderno 00a). La versión pública nunca recibe cédulas, nombres ni códigos.")
    faltan = [c for c in COLUMNAS_MINIMAS if c not in df.columns]
    if faltan:
        raise ErrorEntrada(f"Faltan columnas obligatorias: {', '.join(faltan)}.")
    if modo == "demo":
        origen = df.get("origen_datos", pd.Series(dtype=str)).astype(str).str.upper()
        if origen.empty or not (origen == "SINTETICO").all():
            raise ErrorEntrada(
                "La versión pública solo acepta datos sintéticos (columna origen_datos = "
                "SINTETICO). Los datos reales se procesan únicamente en el modo institucional, "
                "dentro de LEMAS.")


# --------------------------------------------------------------------------- #
# Población del ciclo actual
# --------------------------------------------------------------------------- #
def anios_disponibles(base_limpia: pd.DataFrame) -> list[int]:
    return sorted(int(a) for a in base_limpia["anio_origen"].dropna().unique())


def construir_poblacion(base_limpia: pd.DataFrame, anio_origen: int, config: dict) -> tuple[
        pd.DataFrame, dict]:
    """Elegibles del ciclo `anio_origen` en la foto t0 (sin etiqueta: aún no se conoce)."""
    mes, dia = config["calendario"]["t0_mes_dia"]
    t0 = pd.Timestamp(year=anio_origen + 1, month=mes, day=dia)
    reglas = config["elegibilidad"]
    origen = agregar_predictores(base_limpia[base_limpia["anio_origen"] == anio_origen], config)
    resumen = {"ciclo": f"{anio_origen}-{anio_origen + 1}", "corte_t0": t0.date().isoformat(),
               "estudiantes_ciclo": len(origen)}
    paso = origen[origen["categoria_reserva"].isin(reglas["estados_aprobados"])]
    resumen["reserva_aprobada"] = len(paso)
    paso = paso[~(paso["fecha_reserva"].notna() & (paso["fecha_reserva"] >= t0))]
    paso = paso[~es_curso_terminal(paso, reglas["cursos_terminales_regex"])]
    destino = base_limpia[base_limpia["anio_origen"] == anio_origen + 1]
    if not destino.empty:   # si ya hay pagos del ciclo siguiente antes de t0, ya se matricularon
        pagos = destino.set_index("id_estudiante")["fecha_pago"]
        ya_pagaron = paso["id_estudiante"].map(pagos) < t0
        resumen["ya_matriculados_antes_t0"] = int(ya_pagaron.sum())
        paso = paso[~ya_pagaron.fillna(False)]
    resumen["elegibles"] = len(paso)
    resumen["representantes"] = int(paso["id_familia"].nunique())
    return paso.reset_index(drop=True), resumen


# --------------------------------------------------------------------------- #
# Sistema de predicción
# --------------------------------------------------------------------------- #
@dataclass
class Sistema:
    calibrado: object
    k_por_sede: dict
    tasa_historica: float
    descripcion: str


def entrenar_sistema(base_limpia: pd.DataFrame, config: dict, params: dict | None = None
                     ) -> Sistema:
    """Reproduce el protocolo de la Fase 2 con la base dada: entrena la logística híbrida
    con C2+C3, la calibra en C4 y calcula k con el multiplicador aprobado."""
    dataset, _ = construir_dataset(base_limpia, config)
    entrenamiento = dataset[dataset["cohorte"].isin(["C2", "C3"])]
    seleccion = dataset[dataset["rol"] == "seleccion"]
    if entrenamiento.empty or seleccion.empty:
        raise ErrorEntrada("La base no tiene suficientes ciclos para entrenar (se "
                              "necesitan al menos 2022 a 2025).")
    modelo = construir_modelo("hibrido", params or PARAMS_DEMO, config["proyecto"]["semilla"])
    modelo.fit(construir_matriz_x(entrenamiento), entrenamiento["y_no_matricula"])
    k = calcular_k_por_sede(consolidar_familias(entrenamiento, np.zeros(len(entrenamiento))),
                            config["capacidad"].get("multiplicador_k", 1.0))
    return Sistema(calibrar(modelo, seleccion), k,
                   float(entrenamiento["y_no_matricula"].mean()),
                   "Logística híbrida calibrada (Platt en C4)")


def cargar_sistema_congelado(ruta) -> Sistema | None:
    """Modo institucional: usa el sistema validado en la Fase 2 si existe en el equipo."""
    from pathlib import Path

    import joblib

    ruta = Path(ruta)
    if not ruta.exists():
        return None
    guardado = joblib.load(ruta)
    return Sistema(guardado["calibrado"], guardado["k_por_sede"],
                   float(guardado["tasa_historica_no_matricula"]),
                   f"Sistema congelado de la Fase 2 ({guardado.get('nombre', 'modelo')})")


def puntuar(poblacion: pd.DataFrame, sistema: Sistema) -> pd.DataFrame:
    """Agrega prioridad D2 y probabilidad calibrada de no matrícula a cada estudiante."""
    datos = poblacion.copy()
    datos["prioridad_d2"] = puntajes_reglas(datos)[REGLA_PRIORIZACION]
    datos["prob_no_matricula"] = sistema.calibrado.predict_proba(construir_matriz_x(datos))[:, 1]
    datos["motivo"] = [_motivo(f) for _, f in datos.iterrows()]
    return datos


def _motivo(fila: pd.Series) -> str:
    """Explicación en lenguaje simple de por qué un estudiante sube en la lista D2."""
    partes = []
    if fila.get("pago_origen") == "tardio":
        partes.append("pagó tarde la matrícula anterior")
    if fila.get("reserva_extraordinaria") == 1:
        partes.append("reserva extraordinaria")
    atrasos = fila.get("atrasos_pension")
    if pd.notna(atrasos) and atrasos > 0:
        partes.append(f"{int(atrasos)} pensiones pagadas tarde")
    return "; ".join(partes) if partes else "sin señales administrativas"


def lista_contactos(puntuados: pd.DataFrame, k_por_sede: dict) -> pd.DataFrame:
    """Top-k representantes por sede según D2 (un contacto por representante).

    Desempate dentro del mismo puntaje D2: mayor probabilidad del modelo.
    """
    datos = puntuados.assign(_orden=puntuados["prioridad_d2"] + puntuados["prob_no_matricula"])
    datos = datos.sort_values("_orden", ascending=False)
    familias = datos.groupby("id_familia", sort=False).agg(
        sede=("sede", "first"), prioridad_d2=("prioridad_d2", "max"),
        prob_max=("prob_no_matricula", "max"), estudiantes=("id_estudiante", "size"),
        estudiantes_ids=("id_estudiante", lambda s: ", ".join(map(str, s))),
        motivo=("motivo", "first"), _orden=("_orden", "max")).reset_index()
    filas = []
    for sede, grupo in familias.groupby("sede"):
        k = int(k_por_sede.get(str(sede), 0))
        top = grupo.sort_values("_orden", ascending=False).head(k).copy()
        top.insert(0, "puesto", range(1, len(top) + 1))
        filas.append(top)
    if not filas:
        return pd.DataFrame()
    lista = pd.concat(filas, ignore_index=True).drop(columns="_orden")
    lista["prob_max"] = lista["prob_max"].round(3)
    return lista


def proyeccion_actual(puntuados: pd.DataFrame, tasa_historica: float) -> pd.DataFrame:
    """Matrículas esperadas del ciclo siguiente por sede y subnivel (modelo y B1)."""
    tabla = puntuados.groupby(["sede", "subnivel"]).agg(
        elegibles=("prob_no_matricula", "size"),
        esperadas_modelo=("prob_no_matricula", lambda p: float((1 - p).sum())))
    tabla["esperadas_B1"] = tabla["elegibles"] * (1 - tasa_historica)
    return tabla.round(1).reset_index()


def estimar_estudiante(valores: dict, sistema: Sistema) -> dict:
    """Formulario individual: probabilidad calibrada y nivel de prioridad D2."""
    fila = pd.DataFrame([valores])
    for col in ("curso", "hermanos_lemas", "anios_permanencia", "beca"):
        fila[col] = fila.get(col, pd.Series([np.nan]))
    prob = float(sistema.calibrado.predict_proba(construir_matriz_x(fila))[:, 1][0])
    d2 = float(puntajes_reglas(fila)[REGLA_PRIORIZACION][0])
    nivel = ("Alta" if d2 >= 100 else "Media" if d2 >= 20 or valores["atrasos_pension"] >= 3
             else "Baja")
    return {"prob_no_matricula": prob, "prioridad_d2": d2, "nivel": nivel,
            "motivo": _motivo(fila.iloc[0]), "tasa_historica": sistema.tasa_historica}


def preparar_base(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Limpieza estándar del proyecto (mismas reglas que los cuadernos)."""
    return limpiar_base(df, config)


def ciclo_por_defecto(base_limpia: pd.DataFrame) -> int:
    """Último ciclo con reservas registradas (el que se prioriza en el corte t0)."""
    con_reserva = base_limpia[base_limpia["categoria_reserva"] != "sin_reserva"]
    return int(con_reserva["anio_origen"].max())
