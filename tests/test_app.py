"""Pruebas de la aplicación: lógica de inferencia y recorrido de la interfaz."""

from pathlib import Path

import pandas as pd
import pytest

from src.inferencia import (
    ErrorEntrada,
    ciclo_por_defecto,
    construir_poblacion,
    entrenar_sistema,
    estimar_estudiante,
    lista_contactos,
    preparar_base,
    proyeccion_actual,
    puntuar,
    validar_entrada,
)
from src.utils import cargar_config

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def config():
    return cargar_config()


@pytest.fixture(scope="module")
def crudo(config):
    return pd.read_csv(RAIZ / config["rutas"]["base_sintetica"], dtype=str)


@pytest.fixture(scope="module")
def preparado(crudo, config):
    base = preparar_base(crudo, config)
    return base, entrenar_sistema(base, config)


def test_demo_rechaza_datos_no_sinteticos(crudo):
    with pytest.raises(ErrorEntrada, match="sintéticos"):
        validar_entrada(crudo.drop(columns="origen_datos"), "demo")


@pytest.mark.parametrize("columna", ["CI", "cedulap", "Nombre Completo", "Codigo", "correo"])
def test_rechaza_identificadores_directos(crudo, columna):
    with pytest.raises(ErrorEntrada, match="identificadores"):
        validar_entrada(crudo.assign(**{columna: "x"}), "institucional")


def test_rechaza_columnas_faltantes(crudo):
    with pytest.raises(ErrorEntrada, match="Faltan"):
        validar_entrada(crudo.drop(columns="RColegio"), "institucional")


def test_lista_respeta_k_y_un_contacto_por_familia(preparado, config):
    base, sistema = preparado
    poblacion, resumen = construir_poblacion(base, ciclo_por_defecto(base), config)
    puntuados = puntuar(poblacion, sistema)
    k = {"Mucho Lote 1": 10, "Mucho Lote 2": 5}
    lista = lista_contactos(puntuados, k)
    assert lista.groupby("sede").size().to_dict() == k
    assert lista["id_familia"].is_unique
    assert resumen["elegibles"] == len(poblacion)
    # orden D2: nadie fuera de la lista tiene más prioridad que el último de su sede
    for sede, grupo in lista.groupby("sede"):
        fuera = puntuados[(puntuados["sede"] == sede)
                          & ~puntuados["id_familia"].isin(grupo["id_familia"])]
        assert fuera["prioridad_d2"].max() <= grupo["prioridad_d2"].min() + 1e-9


def test_poblacion_excluye_ultimo_curso_y_no_aprobados(preparado, config):
    base, _ = preparado
    poblacion, _ = construir_poblacion(base, ciclo_por_defecto(base), config)
    assert set(poblacion["categoria_reserva"]) <= set(config["elegibilidad"]["estados_aprobados"])
    assert not poblacion["curso"].str.contains("Tercero de bachillerato").any()


def test_proyeccion_y_formulario(preparado, config):
    base, sistema = preparado
    poblacion, _ = construir_poblacion(base, ciclo_por_defecto(base), config)
    proy = proyeccion_actual(puntuar(poblacion, sistema), sistema.tasa_historica)
    assert proy["elegibles"].sum() == len(poblacion)
    alto = estimar_estudiante({"sede": "Mucho Lote 1", "subnivel": "Preparatoria",
                               "pago_origen": "tardio", "atrasos_pension": 5,
                               "reserva_extraordinaria": 1, "promedio": 8.0, "conducta": 4},
                              sistema)
    bajo = estimar_estudiante({"sede": "Mucho Lote 1", "subnivel": "Bachillerato",
                               "pago_origen": "en_plazo", "atrasos_pension": 0,
                               "reserva_extraordinaria": 0, "promedio": 9.5, "conducta": 5},
                              sistema)
    assert alto["nivel"] == "Alta" and bajo["nivel"] == "Baja"
    assert 0 <= bajo["prob_no_matricula"] <= 1


def test_interfaz_recorrido_completo():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(RAIZ / "app/app.py"), default_timeout=120)
    app.run()
    assert not app.exception
    app.sidebar.button[0].click().run()          # "Prueba con ejemplo"
    assert not app.exception
    generar = next(b for b in app.button if b.label == "Generar lista")
    generar.click().run()
    assert not app.exception
    assert any("Familias a contactar" in m.label for m in app.metric)
    formulario = next(b for b in app.button if b.label == "Estimar")
    formulario.click().run()
    assert not app.exception
