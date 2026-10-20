"""Pruebas del análisis de costo esperado (src/costo.py)."""

from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")

import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from src import costo  # noqa: E402
from src.graficos_costo import figura_costo  # noqa: E402


@pytest.fixture
def por_k() -> pd.DataFrame:
    """Cohorte de 1.000 familias y 100 casos; k = 100."""
    filas = [
        ("C4", 0.5, 50, 15),
        ("C4", 1.0, 100, 22),
        ("C4", 2.0, 200, 32),
        ("C4", "todas", 1000, 100),
    ]
    tabla = pd.DataFrame(filas, columns=["cohorte", "multiplicador", "contactos", "aciertos"])
    tabla["pct_familias"] = tabla["contactos"] / 1000
    tabla["precision"] = tabla["aciertos"] / tabla["contactos"]
    return tabla


@pytest.fixture
def semanal() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "cohorte": ["Todas", "Todas"],
            "semana": [1, 5],
            "tasa_base": [0.1, 0.4],
            "pendientes_por_campana": [1000, 250],
            "dias_ventana_restante": [69, 41],
        }
    )


def test_razon_equilibrio():
    assert costo.razon_equilibrio(0.2, 0.1) == pytest.approx(50)
    assert math.isinf(costo.razon_equilibrio(0.0, 0.1))
    assert math.isnan(costo.razon_equilibrio(float("nan"), 0.1))


def test_beneficio_neto_cero_en_el_equilibrio():
    precision, eficacia = 0.2, 0.1
    razon = costo.razon_equilibrio(precision, eficacia)
    assert costo.beneficio_neto(precision * 100, 100, razon, eficacia) == pytest.approx(0)


def test_tasa_base(por_k):
    assert costo.tasa_base(por_k, "C4") == pytest.approx(0.1)


def test_marginales(por_k):
    marg = costo.marginales(por_k, "C4")
    assert list(marg["contactos_nuevos"]) == [50, 50, 100, 800]
    assert list(marg["aciertos_nuevos"]) == [15, 7, 10, 68]
    assert marg.loc[1, "precision_marginal"] == pytest.approx(0.14)
    assert marg.loc[2, "lift_marginal"] == pytest.approx(1.0)
    assert marg.loc[0, "razon_equilibrio_e10"] == pytest.approx(33.3, abs=0.1)
    # Los tramos suman la cohorte completa.
    assert marg["aciertos_nuevos"].sum() == 100


def test_celdas_ocultas_quedan_ausentes(por_k):
    oculto = por_k.astype({"aciertos": object})
    oculto.loc[0, "aciertos"] = "<5"
    marg = costo.marginales(oculto, "C4")
    assert math.isnan(marg.loc[0, "precision_marginal"])


def test_curva_y_mejor_tamano(por_k):
    curva = costo.curva_beneficio(por_k, "C4", eficacias=(0.1,), razones=(50, 200))
    assert len(curva) == 4 * 2
    fila = curva[(curva["razon"] == 50) & (curva["contactos"] == 100)].iloc[0]
    assert fila["beneficio_lista"] == pytest.approx(0.1 * 50 * 22 - 100)
    assert fila["beneficio_azar"] == pytest.approx(0.1 * 50 * 10 - 100)
    mejor = costo.mejor_tamano(curva).set_index("razon")
    assert mejor.loc[50, "contactos"] == 50  # solo compensa la primera mitad
    assert mejor.loc[200, "contactos"] == 1000  # con un caso muy valioso, llamar a todas


def test_escenarios_y_conclusiones(por_k, semanal):
    c5 = {"precision_k": 0.13, "lift_k": 2.0}
    esc = costo.escenarios(por_k, semanal, c5, "C4", 5)
    nombres = [e["escenario"] for e in esc]
    assert nombres == [
        "azar",
        "primera_mitad",
        "lista_k",
        "tramo_k_2k",
        "pendientes_semana_5",
        "lista_k_c5",
        "azar_c5",
    ]
    eq = costo.tabla_equilibrio(esc).set_index("escenario")
    assert eq.loc["tramo_k_2k", "precision"] == pytest.approx(0.10)
    assert eq.loc["azar_c5", "precision"] == pytest.approx(0.065)
    assert eq.loc["lista_k", "razon_equilibrio_e10"] < eq.loc["azar", "razon_equilibrio_e10"]
    textos = costo.conclusiones(
        eq.reset_index(),
        costo.marginales(por_k, "C4"),
        costo.mejor_tamano(costo.curva_beneficio(por_k, "C4")),
    )
    assert any("semana 5" in t for t in textos)
    assert any("divide por 2,0" in t for t in textos)


def test_cohorte_inexistente(por_k):
    with pytest.raises(ValueError):
        costo.marginales(por_k, "C9")


def test_figura(por_k, semanal):
    eq = costo.tabla_equilibrio(costo.escenarios(por_k, semanal, None))
    fig = figura_costo(eq, costo.curva_beneficio(por_k, "C4"))
    assert len(fig.axes) == 2
