"""Pruebas del análisis de sensibilidad de hiperparámetros (src/sensibilidad.py, D58)."""

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from src import graficos_sensibilidad as gs  # noqa: E402
from src import sensibilidad as se  # noqa: E402

N = 40


@pytest.fixture(scope="module")
def historial():
    """Historial artificial: la PR-AUC depende sobre todo de C, algo del balanceo y nada
    de l1_ratio ni del conjunto de variables."""
    rng = np.random.default_rng(0)
    c = 10 ** rng.uniform(-3, 1, N)
    balanceado = rng.random(N) < 0.5
    valor = 0.06 + 0.04 / (1 + np.exp(-3 * np.log10(c))) + 0.005 * balanceado
    valor += rng.normal(0, 0.001, N)
    logistica = pd.DataFrame({
        "number": range(N), "value": valor, "params_C": c,
        "params_balanceado": balanceado, "params_conjunto": rng.choice(["completo", "reducido"], N),
        "params_l1_ratio": rng.random(N), "modelo": "Regresión logística regularizada"})
    hibrido = pd.DataFrame({
        "number": range(N), "value": 0.08 + 0.004 * balanceado + rng.normal(0, 0.0005, N),
        "params_C": c, "params_balanceado": balanceado,
        "modelo": "Logística híbrida (señales de D2 + variables académicas)"})
    return pd.concat([logistica, hibrido], ignore_index=True)


def test_tipo_de():
    assert se.tipo_de("Gradient boosting (árboles)") == "arboles"
    with pytest.raises(ValueError):
        se.tipo_de("Otro")


def test_pruebas_y_estudio(historial):
    pruebas = se.pruebas_de(historial, "logistica")
    assert len(pruebas) == N and pruebas["balanceado"].dtype == bool
    estudio = se.reconstruir_estudio(pruebas, "logistica")
    assert len(estudio.trials) == N
    assert estudio.best_value == pytest.approx(pruebas["value"].max())


def test_importancia_ordena_lo_que_importa(historial):
    imp = se.importancias(se.pruebas_de(historial, "logistica"), "logistica", semillas=(1, 2))
    fan = imp[imp["metodo"] == "fANOVA"].set_index("hiperparametro")["importancia"]
    assert fan.sum() == pytest.approx(1, abs=0.01)
    assert fan.idxmax() == "C"
    assert fan["C"] > fan["l1_ratio"] and fan["C"] > fan["conjunto"]


def test_dependencia_parcial_sube_con_c(historial):
    pruebas = se.pruebas_de(historial, "logistica")
    sustituto = se.ajustar_sustituto(pruebas, "logistica", arboles=60)
    curva = se.dependencia_parcial(sustituto, "C", puntos=10)
    assert curva["pr_auc"].iloc[-1] > curva["pr_auc"].iloc[0]
    assert curva["valor"].min() == pytest.approx(pruebas["C"].min(), rel=1e-6)   # escala original
    cat = se.dependencia_parcial(sustituto, "balanceado")
    assert set(cat["valor"]) == {"True", "False"}


def test_interacciones_y_sensibilidad(historial):
    pruebas = se.pruebas_de(historial, "hibrido")
    sustituto = se.ajustar_sustituto(pruebas, "hibrido", arboles=60)
    inter = se.interacciones(sustituto)
    assert len(inter) == 1 and 0 <= inter["h2"].iloc[0] <= 1
    sens = se.sensibilidad(sustituto, pruebas)
    assert sens.iloc[0]["hiperparametro"] == "balanceado"
    assert (sens["rango"] >= 0).all()


def test_antes_despues(historial):
    pruebas = se.pruebas_de(historial, "logistica")
    fila = se.antes_despues(pruebas, "logistica", tasa_validacion=0.06)
    assert fila["mejor"] >= fila["mediana_aleatorias"]
    assert fila["ganancia_sobre_aleatorias"] == pytest.approx(
        fila["mejor"] - fila["mediana_aleatorias"], abs=1e-4)


def test_figuras(historial):
    imps, deps, inters, mapas, pares, pruebas = [], [], [], {}, {}, {}
    for tipo in ("logistica", "hibrido"):
        p = se.pruebas_de(historial, tipo)
        nombre = se.NOMBRES[tipo]
        pruebas[nombre] = p
        imps.append(se.importancias(p, tipo, semillas=(1,)))
        s = se.ajustar_sustituto(p, tipo, arboles=30)
        deps.extend(se.dependencia_parcial(s, n, puntos=5) for n in s.columnas)
        inter = se.interacciones(s)
        inters.append(inter)
        a, b = inter.iloc[0]["a"], inter.iloc[0]["b"]
        mapas[nombre], pares[nombre] = se.dependencia_2d(s, a, b, puntos=4), (a, b)
    imp, dep, inter = (pd.concat(x, ignore_index=True) for x in (imps, deps, inters))
    assert len(gs.figura_importancia(imp).axes) == 2
    assert len(gs.figura_dependencia(dep, pruebas, 0.06).axes) >= 2
    assert len(gs.figura_interacciones(inter, mapas, pares).axes) >= 3
