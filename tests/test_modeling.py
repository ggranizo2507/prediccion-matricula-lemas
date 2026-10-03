"""Pruebas de la Fase 2: modelos, protocolo temporal, IC, equidad y proyección."""

import numpy as np
import pandas as pd
import pytest

from src.data_processing import construir_dataset, construir_matriz_x, limpiar_base
from src.evaluate import calcular_k_por_sede, consolidar_familias
from src.modeling import (
    OCULTO,
    bootstrap_ic,
    calibrar,
    completar_supresion,
    construir_modelo,
    entrenar_candidatos,
    equidad,
    lineas_base_brier,
    proyeccion,
)
from src.synthetic import generar
from src.utils import cargar_config, celda_complementaria


@pytest.fixture(scope="module")
def config():
    return cargar_config()


@pytest.fixture(scope="module")
def dataset(config):
    datos, _ = construir_dataset(limpiar_base(generar(config, semilla=5).astype(str), config),
                                 config)
    return datos


@pytest.fixture(scope="module")
def k(dataset, config):
    entrenamiento = dataset[dataset["cohorte"].isin(["C2", "C3"])]
    return calcular_k_por_sede(consolidar_familias(entrenamiento, np.zeros(len(entrenamiento))),
                               config["capacidad"]["multiplicador_k"])


PARAMS = {
    "logistica": {"conjunto": "reducido", "C": 0.1, "l1_ratio": 0.5},
    "hibrido": {"C": 0.5, "balanceado": False},
    "arboles": {"conjunto": "completo", "learning_rate": 0.05, "max_depth": 3,
                "max_leaf_nodes": 8, "min_samples_leaf": 30, "l2_regularization": 1.0,
                "max_iter": 50},
}


@pytest.mark.parametrize("tipo", ["logistica", "arboles", "hibrido"])
def test_modelos_entrenan_y_devuelven_probabilidades(dataset, tipo):
    entrenamiento = dataset[dataset["cohorte"].isin(["C2", "C3"])]
    modelo = construir_modelo(tipo, PARAMS[tipo], 42).fit(
        construir_matriz_x(entrenamiento), entrenamiento["y_no_matricula"])
    prob = modelo.predict_proba(construir_matriz_x(dataset[dataset["rol"] == "prueba"]))[:, 1]
    assert np.all((prob >= 0) & (prob <= 1))


def test_reducido_no_usa_curso(dataset):
    entrenamiento = dataset[dataset["cohorte"].isin(["C2", "C3"])]
    modelo = construir_modelo("logistica", PARAMS["logistica"], 42).fit(
        construir_matriz_x(entrenamiento), entrenamiento["y_no_matricula"])
    nombres = modelo.named_steps["prep"].get_feature_names_out()
    assert not any(n.startswith("curso") for n in nombres)


def test_arboles_monotonos_en_atrasos(dataset):
    entrenamiento = dataset[dataset["cohorte"].isin(["C2", "C3"])]
    X = construir_matriz_x(entrenamiento)
    modelo = construir_modelo("arboles", PARAMS["arboles"], 42).fit(
        X, entrenamiento["y_no_matricula"])
    base = X.iloc[[0] * 10].copy()
    base["atrasos_pension"] = np.arange(10)
    riesgo = modelo.predict_proba(base)[:, 1]
    assert np.all(np.diff(riesgo) >= -1e-12)


def test_candidatos_no_usan_c5(dataset, config, k, monkeypatch):
    vistos = []
    import src.modeling as modeling
    original = modeling.construir_matriz_x

    def espia(datos):
        vistos.extend(set(datos["cohorte"]))
        return original(datos)

    monkeypatch.setattr(modeling, "construir_matriz_x", espia)
    entrenar_candidatos(dataset, config, ["C2", "C3"], k, n_trials=2)
    assert "C5" not in vistos and "C4" in vistos


def test_calibracion_conserva_el_orden(dataset):
    entrenamiento = dataset[dataset["cohorte"].isin(["C2", "C3"])]
    c4 = dataset[dataset["rol"] == "seleccion"]
    modelo = construir_modelo("logistica", PARAMS["logistica"], 42).fit(
        construir_matriz_x(entrenamiento), entrenamiento["y_no_matricula"])
    crudo = modelo.predict_proba(construir_matriz_x(c4))[:, 1]
    calibrado = calibrar(modelo, c4).predict_proba(construir_matriz_x(c4))[:, 1]
    assert (np.argsort(crudo, kind="stable") == np.argsort(calibrado, kind="stable")).mean() > 0.99


def test_bootstrap_ic_contiene_el_valor(dataset, k):
    c5 = dataset[dataset["rol"] == "prueba"]
    riesgo = pd.to_numeric(c5["atrasos_pension"]).fillna(0).to_numpy()
    ic = bootstrap_ic(c5, riesgo, k, 42, repeticiones=200)
    assert set(ic) == {"precision_k", "lift_k", "recall_k"}
    assert all(bajo <= alto for bajo, alto in ic.values())


def test_equidad_oculta_grupos_pequenos(dataset, k):
    c5 = dataset[dataset["rol"] == "prueba"].copy()
    c5["grupo_raro"] = 0
    c5.loc[c5.index[:3], "grupo_raro"] = 1
    tabla = equidad(c5, np.random.default_rng(0).random(len(c5)), k, 42, ["grupo_raro"])
    raro = tabla[(tabla["variable"] == "grupo_raro") & (tabla["grupo"] == "1")].iloc[0]
    assert raro["familias"] == "<5" and pd.isna(raro["recall_k"])


def test_supresion_complementaria_protege_la_celda_oculta():
    """Con una sola celda oculta, su valor saldría restando las demás del total."""
    tabla = pd.DataFrame({
        "variable": ["subnivel"] * 4 + ["sede"] * 2,
        "grupo": ["A", "B", "C", "D", "S1", "S2"],
        "familias": [122, 743, 115, 113, 640, 453],
        "eventos": ["<5", 55, 6, 12, 44, 30],
        "tasa_seleccion": [0.16, 0.16, 0.09, 0.12, 0.18, 0.10],
        "precision_k": [np.nan, 0.12, 0.20, 0.38, 0.12, 0.17],
        "recall_k": [np.nan, 0.27, 0.33, 0.42, 0.32, 0.27]})
    salida = completar_supresion(tabla, 5)
    subnivel = salida[salida["variable"] == "subnivel"].set_index("grupo")
    assert subnivel.loc["C", "eventos"] == OCULTO          # la celda visible más pequeña
    assert pd.isna(subnivel.loc["C", "recall_k"]) and pd.isna(subnivel.loc["C", "precision_k"])
    assert subnivel.loc["C", "familias"] == 115            # el tamaño del grupo no se oculta
    assert subnivel.loc[["B", "D"], "eventos"].tolist() == [55, 12]
    ocultas = subnivel["eventos"].astype(str).isin({"<5", OCULTO}).sum()
    assert ocultas == 2                                    # ya no se deduce por diferencia
    sede = salida[salida["variable"] == "sede"]
    assert sede["eventos"].tolist() == [44, 30]            # sin celdas ocultas no cambia nada
    assert completar_supresion(salida, 5).equals(salida)   # aplicarla dos veces no cambia más


def test_celda_complementaria():
    valores = pd.Series([3, 40, 9, 0], index=list("abcd"))

    def ocultas(*marcas):
        return pd.Series(marcas, index=valores.index)

    assert celda_complementaria(valores, ocultas(True, False, False, False)) == "c"
    assert celda_complementaria(valores, ocultas(False, False, False, False)) is None
    assert celda_complementaria(valores, ocultas(True, True, False, False)) is None


def test_lineas_base_y_proyeccion(dataset):
    c5 = dataset[dataset["rol"] == "prueba"]
    entrenamiento = dataset[dataset["cohorte"].isin(["C2", "C3"])]
    brier = lineas_base_brier(c5, entrenamiento)
    assert brier.loc[0, "brier"] == pytest.approx(c5["y_no_matricula"].mean(), abs=1e-4)
    tabla = proyeccion(c5, np.full(len(c5), 0.1), 0.1)
    assert (tabla["observadas"] >= 10).all()
    assert np.allclose(tabla["esperadas_modelo"], tabla["esperadas_B1"])


def test_hibrido_usa_solo_variables_registradas(dataset):
    from src.modeling import HIBRIDAS_BINARIAS, HIBRIDAS_NUMERICAS
    entrenamiento = dataset[dataset["cohorte"].isin(["C2", "C3"])]
    modelo = construir_modelo("hibrido", PARAMS["hibrido"], 42).fit(
        construir_matriz_x(entrenamiento), entrenamiento["y_no_matricula"])
    nombres = list(modelo.named_steps["prep"].get_feature_names_out())
    assert set(HIBRIDAS_BINARIAS + HIBRIDAS_NUMERICAS) <= set(nombres)
    assert all(n.split("_")[0] in {"pago", "es", "reserva", "conducta", "atrasos", "subnivel",
                                   "promedio"} for n in nombres)
