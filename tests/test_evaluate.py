"""Pruebas de la priorización familiar, la regla de k y la auditoría de C1."""

import numpy as np
import pandas as pd
import pytest

from src.auditoria import (
    comparar_configuraciones,
    conteo_eventos,
    decidir_inclusion_c1,
    diferencias_estandarizadas,
    reporte_por_cohorte,
    sensibilidad_estados,
    suprimir_reporte,
)
from src.data_processing import construir_dataset, limpiar_base
from src.evaluate import calcular_k_por_sede, consolidar_familias, precision_at_k_familiar
from src.synthetic import generar
from src.utils import cargar_config


@pytest.fixture(scope="module")
def config():
    return cargar_config()


@pytest.fixture(scope="module")
def base(config):
    return limpiar_base(generar(config, semilla=11).astype(str), config)


@pytest.fixture(scope="module")
def dataset(base, config):
    return construir_dataset(base, config)[0]


def _familias_ejemplo():
    datos = pd.DataFrame({
        "cohorte": ["C4"] * 6,
        "sede": ["Mucho Lote 1"] * 4 + ["Mucho Lote 2"] * 2,
        "id_familia": ["F1", "F1", "F2", "F3", "F4", "F5"],
        "y_no_matricula": [0, 1, 0, 0, 1, 0],
    })
    riesgo = np.array([0.2, 0.9, 0.8, 0.1, 0.7, 0.3])
    return consolidar_familias(datos, riesgo)


def test_consolidacion_usa_maximo_riesgo_y_un_cupo_por_familia():
    familias = _familias_ejemplo().set_index("id_familia")
    assert len(familias) == 5
    assert familias.loc["F1", "score"] == 0.9
    assert familias.loc["F1", "evento"] == 1
    assert familias.loc["F1", "estudiantes"] == 2


def test_precision_lift_recall_por_sede():
    tabla = precision_at_k_familiar(_familias_ejemplo(), {"Mucho Lote 1": 1, "Mucho Lote 2": 1})
    total = tabla[tabla["sede"] == "TOTAL"].iloc[0]
    assert total["aciertos"] == 2 and total["k_efectivo"] == 2
    assert total["precision_k"] == 1.0
    assert total["recall_k"] == 1.0
    assert total["lift_k"] == pytest.approx(1 / (2 / 5), abs=1e-3)


def test_k_por_sede_es_promedio_de_familias_con_evento():
    familias = pd.DataFrame({
        "cohorte": ["C1", "C1", "C2", "C2", "C2"],
        "sede": ["A", "A", "A", "A", "B"],
        "evento": [1, 1, 1, 0, 0],
    })
    assert calcular_k_por_sede(familias) == {"A": 2, "B": 1}


def test_conteo_eventos_por_estudiante_y_familia(dataset, config):
    conteo = conteo_eventos(dataset, config).set_index("cohorte")
    assert set(conteo.index) == {"C1", "C2", "C3", "C4", "C5"}
    assert (conteo["eventos_familia"] <= conteo["eventos_estudiante"]).all()
    assert (conteo["familias"] <= conteo["estudiantes"]).all()


def test_smd_detecta_diferencia_artificial(config):
    datos = pd.DataFrame({
        "cohorte": ["C1"] * 50 + ["C2"] * 50,
        "sede": "A", "subnivel": "EGB", "curso": "5to", "pago_origen": "en_plazo",
        "promedio": [6.0] * 25 + [7.0] * 25 + [8.5] * 25 + [9.5] * 25,
        "conducta": 5.0, "anios_permanencia": 3.0, "atrasos_pension": 1.0,
        "hermanos_lemas": 0.0, "beca": 0.0, "reserva_extraordinaria": 0.0,
        "y_no_matricula": [0, 1] * 50,
    })
    tabla = diferencias_estandarizadas(datos, config, referencia=("C2",)).set_index("variable")
    assert bool(tabla.loc["promedio", "relevante"])
    assert not bool(tabla.loc["y_no_matricula", "relevante"])


def test_comparacion_c1_no_usa_la_cohorte_de_prueba(dataset, config):
    sin_c5 = dataset[dataset["cohorte"] != "C5"]
    resultado = comparar_configuraciones(sin_c5, config)
    assert set(resultado["configuracion"]) == {"con_C1", "sin_C1"}
    assert resultado["precision_k_C4"].between(0, 1).all()
    incluir, motivo = decidir_inclusion_c1(resultado, conteo_eventos(dataset, config), config)
    assert isinstance(incluir, bool) and motivo


def test_reporte_6_3_cuadra_y_suprime(base, dataset, config):
    reporte = construir_dataset(base, config)[1]
    tabla = reporte_por_cohorte(dataset, reporte, config, incluir_c1=True)
    suma = tabla["M matrículas"] + tabla["U no matrículas"]
    assert (suma == tabla["N elegibles pendientes"]).all()
    assert tabla.set_index("Cohorte").loc["C1", "Comparable"] == "Sí"
    publica = suprimir_reporte(tabla.assign(Exclusiones=3), minimo=5)
    assert (publica["Exclusiones"] == "<5").all()


def test_sensibilidad_solo_aprobar_reduce_poblacion(base, config):
    tabla = sensibilidad_estados(base, config)
    assert (tabla["estudiantes_solo_Aprobar"] <= tabla["estudiantes_principal"]).all()


def test_multiplicador_duplica_k():
    from src.evaluate import calcular_k_por_sede
    familias = pd.DataFrame({"sede": ["S"] * 4, "cohorte": ["C1", "C1", "C2", "C2"],
                             "evento": [1, 1, 1, 0]})
    assert calcular_k_por_sede(familias) == {"S": 2}
    assert calcular_k_por_sede(familias, multiplicador=2) == {"S": 3}
