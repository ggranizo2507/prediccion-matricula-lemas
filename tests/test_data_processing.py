"""Pruebas de las reglas del estudio: etiqueta, elegibilidad y ausencia de fuga."""

import pandas as pd
import pytest

from src.data_processing import (
    construir_cohorte,
    construir_dataset,
    construir_matriz_x,
    construir_preprocesador,
    limpiar_base,
    separar_nivel,
    verificar_sin_fuga,
)
from src.synthetic import generar
from src.utils import cargar_config, cohortes_desde_config, tasa_por_grupo

COLUMNAS = ["hoja", "anoa", "anos", "Sede", "Nivel", "Paralelo", "P.Académico", "P.Conducta",
            "fecha_pago_matricula", "Reserva", "RColegio", "Fecha Reserva", "Tiempo", "beca",
            "# meses caído", "anio_ingreso", "id_seudonimo", "id_familia_seudonimo"]


def _fila(anio, est, fam, pago, reserva="SI", estado="Aprobar", fecha_reserva="2021-10-01 10:00",
          nivel="5to EGB A - Básica Media", ingreso=2018):
    return [f"{anio}-{anio + 1}", anio, anio + 1, "Mucho Lote 1", nivel, "A", "8.5", "A",
            pago, reserva, estado, fecha_reserva, "ORDINARIA", "NO", "1", ingreso, est, fam]


@pytest.fixture(scope="module")
def config():
    return cargar_config()


@pytest.fixture(scope="module")
def cohorte_c1(config):
    return next(c for c in cohortes_desde_config(config) if c.nombre == "C1")


@pytest.fixture(scope="module")
def base(config):
    origen = [
        _fila(2021, "E01", "F1", "2021-03-01"),                      # matricula en plazo
        _fila(2021, "E02", "F2", "2021-03-01"),                      # no aparece en destino
        _fila(2021, "E03", "F3", "2021-03-01"),                      # matrícula tardía
        _fila(2021, "E04", "F4", "2021-03-01"),                      # pagó antes de t0
        _fila(2021, "E05", "F5", "2021-03-01", reserva="NO"),
        _fila(2021, "E06", "F6", "2021-03-01", estado="En proceso"),
        _fila(2021, "E07", "F7", "2021-03-01", nivel="3ro BGU A - BGU"),
        _fila(2021, "E08", "F8", "2021-03-01", fecha_reserva="2022-03-01 09:00"),
        _fila(2021, "E09", "F9", "2021-03-01", estado="Aprobar extraordinaria"),
        _fila(2021, "E10", "F1", "2021-03-01"),                      # hermano de E01
        _fila(2021, "E11", "F11", "2021-03-01"),                     # pago justo en t0
        _fila(2021, "E12", "F12", "2021-03-01"),                     # pago justo en H
    ]
    destino = [
        _fila(2022, "E01", "F1", "2022-03-01"),
        _fila(2022, "E03", "F3", "2022-05-10"),
        _fila(2022, "E04", "F4", "2022-01-15"),
        _fila(2022, "E09", "F9", "2022-03-15"),
        _fila(2022, "E10", "F1", "2022-04-02"),
        _fila(2022, "E11", "F11", "2022-02-20"),
        _fila(2022, "E12", "F12", "2022-04-30"),
    ]
    return limpiar_base(pd.DataFrame(origen + destino, columns=COLUMNAS), config)


def test_etiqueta_por_caso(base, cohorte_c1, config):
    tabla, _ = construir_cohorte(base, cohorte_c1, config)
    y = tabla.set_index("id_estudiante")["y_no_matricula"].to_dict()
    assert y == {"E01": 0, "E02": 1, "E03": 1, "E09": 0, "E10": 0, "E11": 0, "E12": 0}
    tardias = tabla.set_index("id_estudiante")["matricula_tardia"]
    assert tardias["E03"] == 1 and tardias["E02"] == 0


def test_filtros_de_elegibilidad(base, cohorte_c1, config):
    tabla, reporte = construir_cohorte(base, cohorte_c1, config)
    excluidos = {"E04", "E05", "E06", "E07", "E08"}
    assert excluidos.isdisjoint(set(tabla["id_estudiante"]))
    assert reporte["confirmados_antes_t0"] == 1
    assert reporte["terminales_excluidos"] == 1
    assert reporte["reserva_despues_t0"] == 1
    assert reporte["en_proceso"] == 1


def test_sensibilidad_excluye_aprobaciones_extraordinarias(base, cohorte_c1, config):
    tabla, _ = construir_cohorte(base, cohorte_c1, config,
                                 config["elegibilidad"]["estados_sensibilidad"])
    assert "E09" not in set(tabla["id_estudiante"])


def test_predictores_derivados(base, cohorte_c1, config):
    tabla, _ = construir_cohorte(base, cohorte_c1, config)
    fila = tabla.set_index("id_estudiante")
    assert fila.loc["E01", "hermanos_lemas"] == 1
    assert fila.loc["E02", "hermanos_lemas"] == 0
    assert fila.loc["E01", "anios_permanencia"] == 3


def test_guardas_anti_fuga(base, cohorte_c1, config):
    tabla, _ = construir_cohorte(base, cohorte_c1, config)
    X = construir_matriz_x(tabla)
    verificar_sin_fuga(X, config)
    X["fecha_pago_destino"] = tabla["fecha_pago_destino"]
    with pytest.raises(ValueError, match="Fuga"):
        verificar_sin_fuga(X, config)


def test_separar_nivel():
    assert separar_nivel("Inicial 1 A - Inicial", "A") == ("Inicial 1", "Inicial")
    assert separar_nivel("", "A") == ("SIN_DATO", "SIN_DATO")


def test_pipeline_completo_con_datos_sinteticos(config):
    datos = generar(config, semilla=7)
    assert set(COLUMNAS) <= set(datos.columns)
    dataset, reporte = construir_dataset(limpiar_base(datos.astype(str), config), config)
    assert set(reporte["estado"]) == {"ok"}
    assert 0.03 < dataset["y_no_matricula"].mean() < 0.3
    verificar_sin_fuga(construir_matriz_x(dataset), config)


def test_conducta_en_letras_es_ordinal(config):
    crudo = pd.DataFrame([_fila(2021, f"E{i}", "F", "2021-03-01") for i in range(4)],
                         columns=COLUMNAS)
    crudo["P.Conducta"] = ["A", " b", "E", "Z"]
    limpia = limpiar_base(crudo, config)
    assert limpia["conducta"].tolist()[:3] == [5.0, 4.0, 1.0]
    assert pd.isna(limpia["conducta"].iloc[3])


def test_preprocesador_ajusta_en_entrenamiento_y_transforma_prueba(config):
    datos = limpiar_base(generar(config, semilla=3).astype(str), config)
    dataset, _ = construir_dataset(datos, config)
    X = construir_matriz_x(dataset)
    entrenamiento = dataset["rol"] == "entrenamiento"
    prep = construir_preprocesador().fit(X[entrenamiento])
    prueba = X[dataset["rol"] == "prueba"].copy()
    prueba.loc[prueba.index[0], "curso"] = "CURSO_NUEVO"
    salida = prep.transform(prueba)
    assert salida.shape[0] == len(prueba)
    assert not pd.isna(salida).any()


def test_tasa_por_grupo_oculta_grupos_pequenos():
    datos = pd.DataFrame({"g": ["a"] * 6 + ["b"] * 2, "y_no_matricula": [1, 0, 0, 0, 0, 0, 1, 1]})
    tabla = tasa_por_grupo(datos, "g", minimo=5)
    assert tabla["g"].tolist() == ["a"] and tabla["n"].iloc[0] == 6
