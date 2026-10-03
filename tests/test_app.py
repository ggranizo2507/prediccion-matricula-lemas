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
    # D49: la lista lleva el motivo, no una probabilidad por familia
    assert "motivo" in lista.columns
    assert not [c for c in lista.columns if "prob" in c.lower()]
    # orden D2: nadie fuera de la lista tiene más prioridad que el último de su sede
    for sede, grupo in lista.groupby("sede"):
        fuera = puntuados[(puntuados["sede"] == sede)
                          & ~puntuados["id_familia"].isin(grupo["id_familia"])]
        assert fuera["prioridad_d2"].max() <= grupo["prioridad_d2"].min() + 1e-9


def test_desempate_como_en_la_validacion(preparado, config):
    """D48: los empates se resuelven al azar con semilla fija; la probabilidad no ordena."""
    base, sistema = preparado
    poblacion, _ = construir_poblacion(base, ciclo_por_defecto(base), config)
    puntuados = puntuar(poblacion, sistema)
    k = {"Mucho Lote 1": 25, "Mucho Lote 2": 15}
    lista = lista_contactos(puntuados, k)
    # la probabilidad del modelo no cambia quién entra ni en qué puesto
    invertida = puntuados.assign(prob_no_matricula=1 - puntuados["prob_no_matricula"])
    assert lista_contactos(invertida, k)["id_familia"].tolist() == lista["id_familia"].tolist()
    # tampoco el orden de las filas del archivo
    barajada = puntuados.sample(frac=1, random_state=7)
    assert lista_contactos(barajada, k)["id_familia"].tolist() == lista["id_familia"].tolist()
    # la semilla sí: es un sorteo entre empatados, reproducible
    assert lista_contactos(puntuados, k, semilla=1)["id_familia"].tolist() != \
        lista["id_familia"].tolist()
    # dentro de cada sede el puntaje D2 nunca sube al bajar de puesto
    for _, grupo in lista.groupby("sede"):
        assert grupo.sort_values("puesto")["prioridad_d2"].is_monotonic_decreasing
    # y agrandar k solo añade familias al final
    mayor = lista_contactos(puntuados, {s: v + 5 for s, v in k.items()})
    for sede, grupo in lista.groupby("sede"):
        assert mayor[mayor["sede"] == sede]["id_familia"].tolist()[:len(grupo)] == \
            grupo["id_familia"].tolist()


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
