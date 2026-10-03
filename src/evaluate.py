"""
Métricas de priorización por representante (familia) y capacidad de contacto.

Convención del proyecto: y_no_matricula = 1 es el evento de interés y `riesgo` es la
probabilidad estimada de ese evento. Cada representante ocupa un solo cupo de
contacto; su score es el mayor riesgo entre sus estudiantes elegibles y su evento es
1 si al menos uno de ellos no se matriculó en plazo (v5, sección 6.4).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger("lemas.evaluacion")


def consolidar_familias(
    datos: pd.DataFrame,
    riesgo: np.ndarray | pd.Series,
    col_familia: str = "id_familia",
    col_objetivo: str = "y_no_matricula",
) -> pd.DataFrame:
    """Una fila por (cohorte, sede, representante) con score = máximo riesgo.

    Un representante con hijos en ambas sedes se asigna a la sede de su estudiante de
    mayor riesgo, para que cuente una sola vez.
    """
    tabla = datos[["cohorte", "sede", col_familia, col_objetivo]].copy()
    tabla["riesgo"] = np.asarray(riesgo, dtype=float)
    tabla = tabla.sort_values("riesgo", ascending=False)
    familias = tabla.groupby(["cohorte", col_familia], sort=False).agg(
        sede=("sede", "first"), score=("riesgo", "max"), evento=(col_objetivo, "max"),
        estudiantes=(col_objetivo, "size"),
    )
    return familias.reset_index().rename(columns={col_familia: "id_familia"})


def calcular_k_por_sede(
    familias_entrenamiento: pd.DataFrame, multiplicador: float = 1.0
) -> dict[str, int]:
    """Regla aprobada: k de cada sede = multiplicador × promedio, en las cohortes de
    entrenamiento, de representantes con al menos un caso de no matrícula. Mínimo 1.
    El multiplicador vive en config.yaml (capacidad.multiplicador_k)."""
    por_cohorte = familias_entrenamiento.groupby(["sede", "cohorte"])["evento"].sum()
    promedio = por_cohorte.groupby(level="sede").mean()
    return {str(sede): max(int(round(multiplicador * valor)), 1)
            for sede, valor in promedio.items()}


def verificar_capacidad(k_por_sede: dict[str, int], config: dict) -> pd.DataFrame:
    """Contrasta k con el personal disponible durante la campaña (20-feb a 30-abr)."""
    capacidad = config["capacidad"]
    filas = []
    for sede, k in k_por_sede.items():
        personal = capacidad["personal_por_sede"].get(sede)
        por_persona = k / personal if personal else np.nan
        por_semana = por_persona / capacidad["semanas_campania"]
        filas.append({"sede": sede, "k": k, "personal": personal,
                      "familias_por_persona": round(por_persona, 1),
                      "familias_por_persona_semana": round(por_semana, 2)})
    return pd.DataFrame(filas)


def primeras_k(grupo: pd.DataFrame, k: int, semilla: int) -> pd.DataFrame:
    """Primeras k familias por score; los empates se resuelven al azar con semilla fija.

    Es el mismo desempate en la validación y en la aplicación (`inferencia.lista_contactos`).
    """
    desempate = np.random.default_rng(semilla).random(len(grupo))
    ordenado = grupo.assign(_desempate=desempate).sort_values(
        ["score", "_desempate"], ascending=[False, True])
    return ordenado.head(min(k, len(grupo))).drop(columns="_desempate")


def precision_at_k_familiar(
    familias: pd.DataFrame, k_por_sede: dict[str, int], semilla: int = 42
) -> pd.DataFrame:
    """Precision@k, Recall@k y Lift@k por cohorte y sede, más el total por cohorte.

    q = tasa familiar de no matrícula (referencia de una selección aleatoria).
    """
    filas = []
    for (cohorte, sede), grupo in familias.groupby(["cohorte", "sede"]):
        k = k_por_sede.get(str(sede))
        if not k:
            log.warning("Sede sin k definido: %s", sede)
            continue
        seleccion = primeras_k(grupo, k, semilla)
        positivos = int(grupo["evento"].sum())
        aciertos = int(seleccion["evento"].sum())
        filas.append({"cohorte": cohorte, "sede": sede, "familias": len(grupo),
                      "k_efectivo": len(seleccion), "positivos": positivos, "aciertos": aciertos})
    tabla = pd.DataFrame(filas)
    if tabla.empty:
        return tabla
    total = tabla.groupby("cohorte", as_index=False)[
        ["familias", "k_efectivo", "positivos", "aciertos"]].sum().assign(sede="TOTAL")
    tabla = pd.concat([tabla, total], ignore_index=True)
    tabla["precision_k"] = tabla["aciertos"] / tabla["k_efectivo"]
    tabla["recall_k"] = tabla["aciertos"] / tabla["positivos"].replace(0, np.nan)
    tabla["q_familiar"] = tabla["positivos"] / tabla["familias"]
    tabla["lift_k"] = tabla["precision_k"] / tabla["q_familiar"].replace(0, np.nan)
    return tabla.round(4)
