"""Pruebas de las comprobaciones de la revisión final (src/revision.py, src/reglas.py) y del
espacio de búsqueda leído de config.yaml."""

import re

import numpy as np
import pandas as pd
import pytest
from optuna.distributions import CategoricalDistribution, FloatDistribution, IntDistribution

from src import modeling, reglas
from src import revision as rv
from src.sensibilidad import ESPACIOS
from src.utils import cargar_config

K = {"A": 3, "B": 2}


def _datos(semilla: int = 0, familias: int = 40) -> pd.DataFrame:
    """Familias de 1 a 3 estudiantes; las de más hijos tienen más casos (para el azar)."""
    rng = np.random.default_rng(semilla)
    filas = []
    for f in range(familias):
        hijos = 1 + f % 3
        evento = int(rng.random() < 0.08 * hijos)
        for h in range(hijos):
            filas.append({"cohorte": ["C1", "C2", "C3", "C4"][f % 4], "sede": "AB"[f % 2],
                          "id_familia": f"F{f}", "y_no_matricula": evento if h == 0 else 0,
                          "pago_origen": "tardio" if f % 5 == 0 else "en_plazo",
                          "reserva_extraordinaria": int(f % 7 == 0),
                          "atrasos_pension": int(f % 4), "promedio": 8 + (f % 3) / 2,
                          "rol": "seleccion"})
    return pd.DataFrame(filas)


# ------------------------------------------------------------------ reglas (una definición)
def test_reglas_es_la_unica_definicion():
    assert modeling.puntajes_reglas is reglas.puntajes_reglas


def test_d2_respeta_el_orden_lexicografico():
    datos = pd.DataFrame({"pago_origen": ["tardio", "en_plazo", "en_plazo", "en_plazo"],
                          "reserva_extraordinaria": [0, 1, 0, 0],
                          "atrasos_pension": [0, 0, 10, 3]})
    puntaje = reglas.puntaje_d2(datos)
    # pago tardío > reserva extraordinaria > cualquier número de atrasos
    assert list(np.argsort(-puntaje)) == [0, 1, 2, 3]
    assert np.array_equal(reglas.puntaje_d(datos), [0, 0, 10, 3])


# ------------------------------------------------------- espacio de búsqueda en config.yaml
def test_espacio_de_config_es_el_de_la_fase_2():
    esperado = {
        "logistica": {"conjunto": CategoricalDistribution(["completo", "reducido"]),
                      "balanceado": CategoricalDistribution([True, False]),
                      "C": FloatDistribution(1e-3, 10, log=True),
                      "l1_ratio": FloatDistribution(0.0, 1.0)},
        "arboles": {"conjunto": CategoricalDistribution(["completo", "reducido"]),
                    "balanceado": CategoricalDistribution([True, False]),
                    "learning_rate": FloatDistribution(0.01, 0.2, log=True),
                    "max_depth": IntDistribution(2, 4),
                    "max_leaf_nodes": IntDistribution(4, 15),
                    "min_samples_leaf": IntDistribution(20, 120),
                    "l2_regularization": FloatDistribution(1e-3, 10, log=True),
                    "max_iter": IntDistribution(50, 400)},
        "hibrido": {"balanceado": CategoricalDistribution([True, False]),
                    "C": FloatDistribution(1e-3, 10, log=True)},
    }
    config = cargar_config()
    for tipo, distribuciones in esperado.items():
        espacio = modeling.espacio_de(tipo, config)
        assert list(espacio) == list(distribuciones)        # mismo orden de sugerencias
        assert espacio == distribuciones
        assert ESPACIOS[tipo] == distribuciones
    opciones = config["optimizacion"]["espacios"]["logistica"]["conjunto"]["opciones"]
    assert set(opciones) == set(modeling.CONJUNTOS)
    assert config["optimizacion"]["trials_por_modelo"] == 60


def test_tipo_de_hiperparametro_desconocido():
    with pytest.raises(ValueError, match="desconocido"):
        modeling.distribuciones({"x": {"tipo": "texto"}})


# ------------------------------------------------------------------ descubrimiento de D2
def test_senales_por_periodo_y_orden():
    datos = _datos(familias=400)
    tabla = rv.senales_por_periodo(datos, {"C1–C3": ["C1", "C2", "C3"]}, min_celda=1)
    assert set(tabla["senal"]) == {"pago_tardio", "reserva_extraordinaria", "atrasos_pension"}
    referencia = tabla[(tabla["senal"] == "pago_tardio") & (tabla["nivel"] == "no")]
    assert referencia["riesgo_relativo"].iloc[0] == 1.0
    orden = rv.orden_senales(tabla)
    assert len(orden) == 1 and isinstance(orden["igual_a_D2"].iloc[0], (bool, np.bool_))
    assert sorted(orden["orden"].iloc[0].split(" > ")) == sorted(reglas.PESOS_D2)


def test_senales_suprime_celdas_pequenas():
    datos = _datos(familias=20)
    tabla = rv.senales_por_periodo(datos, {"C1": ["C1"]}, min_celda=5)
    pequenas = tabla[tabla["estudiantes"] < 5]
    assert pequenas["tasa"].isna().all() and pequenas["eventos"].isna().all()


def test_orden_detecta_el_orden_de_d2():
    filas = []
    for senal, nivel, rr in [("pago_tardio", "sí", 3.0), ("reserva_extraordinaria", "sí", 1.8),
                             ("atrasos_pension", "1 o más", 1.3)]:
        filas.append({"periodo": "C1–C3", "senal": senal, "nivel": nivel, "riesgo_relativo": rr})
    orden = rv.orden_senales(pd.DataFrame(filas))
    assert bool(orden["igual_a_D2"].iloc[0])
    assert orden["orden"].iloc[0] == "pago_tardio > reserva_extraordinaria > atrasos_pension"


# ------------------------------------------------------------- sorteos y diferencia pareada
def test_sorteos_sin_empates_no_varian():
    datos = _datos()
    riesgo = np.arange(len(datos), dtype=float)          # todos distintos: sin empates
    sorteos = rv.sorteos_desempate(datos, riesgo, K, range(10))
    assert sorteos["lift_k"].nunique() == 1
    resumen = rv.resumen_sorteos(sorteos, 3)
    assert resumen["lift_p05"] == resumen["lift_p95"] == resumen["lift_semilla_oficial"]


def test_diferencia_pareada_de_un_sistema_consigo_mismo_es_cero():
    datos = _datos()
    riesgo = reglas.puntaje_d2(datos)
    resultado = rv.diferencia_pareada(datos, riesgo, riesgo, K, 1, repeticiones=50)
    assert resultado["ic95_diferencia"] == [0.0, 0.0]
    assert resultado["prob_a_mejor"] == 0.0


def test_azar_por_familia_cerca_de_uno_y_por_estudiante_mayor():
    datos = _datos(familias=600)
    resultado = rv.azar_dos_versiones(datos, {"A": 60, "B": 60}, 7, repeticiones=200)
    assert abs(resultado["lift_azar_por_familia"] - 1) < 0.1
    assert resultado["lift_azar_por_estudiante"] > resultado["lift_azar_por_familia"]
    assert (resultado["estudiantes_por_familia_con_caso"]
            > resultado["estudiantes_por_familia_sin_caso"])


# ------------------------------------------------------------------ descriptivos y textos
def test_descriptivos_sin_minimo_ni_maximo():
    tabla = rv.descriptivos(_datos(), ["promedio", "atrasos_pension"], min_celda=5)
    assert {"media", "de", "p05", "p50", "p95"} <= set(tabla.columns)
    assert not {"min", "max"} & set(tabla.columns)
    assert "Total" in set(tabla["cohorte"])


def test_conclusiones_usan_coma_decimal():
    datos = _datos(familias=200)
    tabla = rv.senales_por_periodo(datos, {"C1–C3": ["C1", "C2", "C3"]}, min_celda=1)
    sorteos = rv.resumen_sorteos(rv.sorteos_desempate(datos, reglas.puntaje_d2(datos), K,
                                                      range(20)), 0)
    pareada = rv.diferencia_pareada(datos, reglas.puntaje_d2(datos), reglas.puntaje_d(datos),
                                    K, 0, repeticiones=30)
    azar = rv.azar_dos_versiones(datos, K, 0, repeticiones=30)
    textos = rv.conclusiones(rv.orden_senales(tabla), sorteos, pareada, azar)
    assert len(textos) == 4
    assert all(re.search(r"\d,\d", t) for t in textos[1:])
    assert not any(re.search(r"\d\.\d", t) for t in textos)
    assert any("D2 − D" in t for t in textos)


def test_orden_sin_veredicto_si_falta_una_senal():
    filas = [{"periodo": "C3", "senal": "pago_tardio", "nivel": "sí", "riesgo_relativo": np.nan},
             {"periodo": "C3", "senal": "reserva_extraordinaria", "nivel": "sí",
              "riesgo_relativo": 1.8},
             {"periodo": "C3", "senal": "atrasos_pension", "nivel": "1 o más",
              "riesgo_relativo": 1.4}]
    orden = rv.orden_senales(pd.DataFrame(filas))
    assert orden["igual_a_D2"].iloc[0] is None
    assert "pago_tardio" not in orden["orden"].iloc[0]


def test_para_publicar_evita_deducir_celdas_por_diferencia():
    datos = _datos(familias=400)
    periodos = {"C1–C3": ["C1", "C2", "C3"], "C1": ["C1"], "C2": ["C2"], "C3": ["C3"]}
    tabla = rv.senales_por_periodo(datos, periodos, min_celda=5)
    publicable = rv.para_publicar(tabla, ["C1–C3"])
    por_cohorte = publicable[publicable["periodo"] != "C1–C3"]
    assert por_cohorte[["estudiantes", "eventos", "tasa"]].isna().all().all()
    agrupado = publicable[publicable["periodo"] == "C1–C3"]
    assert agrupado["estudiantes"].notna().all()


def test_descriptivos_suprimen_vacios_pequenos():
    datos = _datos()
    datos.loc[datos.index[:2], "promedio"] = np.nan
    tabla = rv.descriptivos(datos, ["promedio"], min_celda=5)
    assert (tabla.loc[tabla["cohorte"] == "Total", "vacios"] == "<5").all()
