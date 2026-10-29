"""Pruebas de `src/model.py`, el punto de entrada de los modelos que nombra la guía del curso.

`src/model.py` reexporta lo esencial de `src/modeling.py` (modelos de aprendizaje automático)
y de `src/reglas.py` (reglas D y D2). Estas pruebas comprueban que la fachada expone las
mismas funciones y que lo que entrega se comporta como se documenta. Las pruebas detalladas
del entrenamiento están en `tests/test_modeling.py`.
"""

import numpy as np
import pandas as pd
import pytest
from optuna.distributions import BaseDistribution
from sklearn.pipeline import Pipeline

import src.model as model
from src import modeling, reglas


def test_reexporta_los_mismos_objetos():
    """La fachada no duplica código: son las mismas funciones de modeling y reglas."""
    assert model.construir_modelo is modeling.construir_modelo
    assert model.espacio_de is modeling.espacio_de
    assert model.puntaje_d2 is reglas.puntaje_d2
    assert model.TIPOS == ("logistica", "arboles", "hibrido")
    assert set(model.__all__) <= set(dir(model))


def test_d2_respeta_el_orden_de_las_senales():
    """Un pago tardío pesa más que reserva extraordinaria con 10 atrasos, y esta más que 10
    atrasos solos (orden lexicográfico de D2)."""
    datos = pd.DataFrame(
        {
            "pago_origen": ["tardio", "en_plazo", "en_plazo", "en_plazo"],
            "reserva_extraordinaria": [0, 1, 0, 0],
            "atrasos_pension": [0, 10, 10, 0],
        }
    )
    puntaje = model.puntaje_d2(datos)
    assert list(np.argsort(-puntaje)) == [0, 1, 2, 3]
    assert model.puntajes_reglas(datos)[model.REGLA_D].tolist() == [0, 10, 10, 0]


@pytest.mark.parametrize(
    ("tipo", "clave"),
    [("logistica", "C"), ("arboles", "min_samples_leaf"), ("hibrido", "C")],
)
def test_espacio_de_busqueda_desde_config(tipo, clave):
    """El espacio de Optuna sale de config.yaml e incluye el hiperparámetro clave de cada
    modelo según el análisis de sensibilidad."""
    espacio = model.espacio_de(tipo)
    assert clave in espacio
    assert all(isinstance(d, BaseDistribution) for d in espacio.values())


def test_construir_modelo_devuelve_pipeline_y_rechaza_tipos_desconocidos():
    pipeline = model.construir_modelo("hibrido", {"C": 1.0, "balanceado": True}, semilla=42)
    assert isinstance(pipeline, Pipeline)
    assert hasattr(pipeline, "predict_proba")
    with pytest.raises(ValueError, match="desconocido"):
        model.construir_modelo("red_neuronal", {"C": 1.0}, semilla=42)
