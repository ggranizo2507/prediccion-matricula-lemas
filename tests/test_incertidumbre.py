"""Pruebas de intervalos, pruebas exactas, carga operativa y tamaño de la reserva (D60)."""

import importlib.util
import math

import numpy as np
import pandas as pd
import pytest

from src import incertidumbre as inc
from src.utils import RAIZ


def test_wilson_valores_conocidos():
    bajo, alto = inc.wilson(2, 11)
    assert bajo == pytest.approx(0.0514, abs=1e-3) and alto == pytest.approx(0.4770, abs=1e-3)
    assert inc.wilson(0, 10)[0] == pytest.approx(0.0, abs=1e-12)
    assert inc.wilson(10, 10)[1] == pytest.approx(1.0, abs=1e-12)
    assert all(math.isnan(v) for v in inc.wilson(0, 0))


def test_fisher_y_razon():
    assert inc.fisher_2x2(5, 10, 5, 10) == pytest.approx(1.0)
    assert inc.fisher_2x2(9, 10, 1, 10) < 0.01
    razon, bajo, alto = inc.razon_ic(10, 100, 20, 100)
    assert razon == pytest.approx(0.5) and bajo < 0.5 < alto
    assert all(math.isnan(v) for v in inc.razon_ic(0, 10, 3, 10))


def test_equidad_con_ic_recupera_conteos_y_respeta_celdas_ocultas():
    tabla = pd.DataFrame(
        [
            {
                "variable": "beca",
                "grupo": "0",
                "familias": 930,
                "eventos": "63",
                "tasa_seleccion": 0.1591,
                "precision_k": 0.1351,
                "recall_k": 0.3175,
            },
            {
                "variable": "beca",
                "grupo": "1",
                "familias": 163,
                "eventos": "11",
                "tasa_seleccion": 0.1043,
                "precision_k": 0.1176,
                "recall_k": 0.1818,
            },
            {
                "variable": "subnivel",
                "grupo": "Inicial",
                "familias": 115,
                "eventos": "oculto",
                "tasa_seleccion": 0.087,
                "precision_k": np.nan,
                "recall_k": np.nan,
            },
        ]
    )
    con_ic = inc.equidad_con_ic(tabla)
    becadas = con_ic.set_index("grupo").loc["1"]
    assert becadas["hallados"] == 2 and becadas["seleccionadas"] == 17
    inicial = con_ic.set_index("grupo").loc["Inicial"]
    assert pd.isna(inicial["recall"]) and pd.notna(inicial["seleccion_ic_bajo"])
    comparado = inc.comparaciones(con_ic, {"beca": "0"})
    assert comparado.iloc[0]["razon_seleccion"] == pytest.approx(0.655, abs=1e-3)
    assert 0 < comparado.iloc[0]["p_recall"] < 1


def test_llamadas_por_caso():
    carga = inc.llamadas_por_caso(165, 22, 74 / 1093)
    assert carga["llamadas_por_caso_lista"] == 7.5
    assert carga["llamadas_por_caso_azar"] == pytest.approx(14.77, abs=0.01)


def test_tamano_reserva_crece_cuando_el_efecto_es_menor():
    grande = inc.tamano_reserva(0.133, 0.5)
    chico = inc.tamano_reserva(0.133, 0.25)
    assert chico["familias_total"] > 4 * grande["familias_total"]
    assert grande["familias_control"] == grande["familias_llamadas"]  # mitad y mitad
    cuarto = inc.tamano_reserva(0.133, 0.5, fraccion_control=0.25)
    assert cuarto["familias_llamadas"] == pytest.approx(3 * cuarto["familias_control"], abs=1)
    tabla = inc.tabla_reserva(0.133, 165)
    assert set(tabla["reduccion"]) == {0.5, 0.25, 0.1} and (tabla["campanas"] > 0).all()


def test_herramienta_con_resultados_reales(tmp_path, monkeypatch):
    ruta = RAIZ / "tools" / "generar_incertidumbre.py"
    especificacion = importlib.util.spec_from_file_location("generar_incertidumbre", ruta)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    for nombre in ("equidad_C5_real.csv", "resultados_finales_real.json"):
        (tmp_path / nombre).write_bytes((modulo.METRICAS / nombre).read_bytes())
    monkeypatch.setattr(modulo, "METRICAS", tmp_path)
    resumen = modulo.generar("real")
    assert resumen["carga_operativa"]["casos_hallados"] == 22
    assert any("Fisher" in t for t in resumen["conclusiones"])
    assert all("." not in t.split("p = ")[-1][:4] for t in resumen["conclusiones"] if "p = " in t)
