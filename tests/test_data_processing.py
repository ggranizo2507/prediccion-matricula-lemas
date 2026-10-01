"""Pruebas de las reglas del estudio: etiqueta, elegibilidad y ausencia de fuga."""

import pandas as pd
import pytest

from src.data_processing import (
    categoria_reserva,
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
            "fecha_pago", "Reserva", "RColegio", "Fecha Reserva", "Tiempo", "beca",
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
    assert reporte["pendientes"] == 1
    assert reporte["sin_reserva"] == 1
    # E05 (sin reserva) no aparece en destino → 0 matriculados fuera de la población
    assert reporte["matriculados_sin_reserva_aprobada"] == 0


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


@pytest.mark.parametrize(("reserva", "estado", "esperado"), [
    ("SI", "Aprobar", "aprobada"),
    ("SI", "Aprobado", "aprobada"),
    ("SI", "Aprobación extraordinaria", "aprobada_extraordinaria"),
    ("SI", "Aprobado Extraordinaria", "aprobada_extraordinaria"),
    ("SI", "En revisión", "pendiente"),
    ("SI", "En Revisión Extraordinaria", "pendiente"),
    ("SI", "En Proceso", "pendiente"),
    ("NO HIZO", "NO HIZO", "sin_reserva"),
    ("NO", None, "sin_reserva"),
    ("SI", "", "sin_reserva"),
])
def test_categoria_reserva_unifica_textos(reserva, estado, esperado):
    assert categoria_reserva(reserva, estado) == esperado


def test_beca_vacia_es_cero(config):
    crudo = pd.DataFrame([_fila(2021, f"E{i}", "F", "2021-03-01") for i in range(3)],
                         columns=COLUMNAS)
    crudo["beca"] = ["SI", "", None]
    assert limpiar_base(crudo, config)["beca"].tolist() == [1, 0, 0]


def test_nuevo_por_presencia_en_el_anio_anterior(config):
    filas = [
        _fila(2021, "A1", "F1", "2021-03-01", ingreso=2019),   # primer año: pago en plazo
        _fila(2021, "N0", "F2", "2021-01-07", ingreso=2020),   # primer año: pago temprano
        _fila(2022, "A1", "F1", "2022-03-01", ingreso=2019),   # estaba en 2021 → antiguo
        _fila(2022, "N1", "F3", "2022-01-10", ingreso=2021),   # no estaba en 2021 → nuevo
    ]
    base = limpiar_base(pd.DataFrame(filas, columns=COLUMNAS), config)
    nuevos = base.set_index(["anio_origen", "id_estudiante"])["es_nuevo"]
    assert not nuevos[(2021, "A1")] and nuevos[(2021, "N0")]
    assert not nuevos[(2022, "A1")] and nuevos[(2022, "N1")]


def test_matriculados_sin_reserva_aprobada_se_reportan(config, cohorte_c1):
    filas = [
        _fila(2021, "E1", "F1", "2021-03-01"),
        _fila(2021, "D1", "F2", "2021-03-01", reserva="NO HIZO", estado="NO HIZO"),
        _fila(2022, "E1", "F1", "2022-03-01"),
        _fila(2022, "D1", "F2", "2022-03-05"),   # matriculado por autorización del director
    ]
    base = limpiar_base(pd.DataFrame(filas, columns=COLUMNAS), config)
    tabla, reporte = construir_cohorte(base, cohorte_c1, config)
    assert set(tabla["id_estudiante"]) == {"E1"}
    assert reporte["matriculados_sin_reserva_aprobada"] == 1


def test_base_seud_equivocada_se_borra(tmp_path):
    from src.utils import obtener_base_seud
    ruta = tmp_path / "base_seud.csv"
    ruta.write_text("Nombre,Nota\nX,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="faltan columnas"):
        obtener_base_seud(ruta, en_colab=False)
    assert not ruta.exists()


@pytest.mark.parametrize("valor", ["2021", "2021.0", "2021-2022", "2021 - 2022", "Ciclo 2021-2022"])
def test_anio_de_ciclo_acepta_formatos(valor):
    from src.data_processing import anio_de_ciclo
    assert anio_de_ciclo(pd.Series([valor])).iloc[0] == 2021


def test_anoa_en_texto_y_filas_vacias_no_rompen_cohortes(config, cohorte_c1):
    filas = [_fila(2021, "E1", "F1", "2021-03-01"), _fila(2022, "E1", "F1", "2022-03-01")]
    crudo = pd.DataFrame(filas, columns=COLUMNAS)
    crudo["anoa"] = ["2021 - 2022", "2022 - 2023"]
    vacias = pd.DataFrame([[None] * len(COLUMNAS)] * 3, columns=COLUMNAS)
    base = limpiar_base(pd.concat([crudo, vacias], ignore_index=True), config)
    assert sorted(base["anio_origen"].tolist()) == [2021, 2022]
    tabla, _ = construir_cohorte(base, cohorte_c1, config)
    assert tabla["y_no_matricula"].tolist() == [0]


def test_anoa_vacio_se_completa_con_la_hoja(tmp_path):
    from src.utils import leer_base_seud
    ruta = tmp_path / "base_seud.csv"
    pd.DataFrame({"hoja": ["2021", "2022"], "anoa": ["2021", None], "fecha_pago": ["", ""],
                  "id_seudonimo": ["E", "E"], "id_familia_seudonimo": ["F", "F"]}).to_csv(ruta,
                                                                                      index=False)
    assert leer_base_seud(ruta)["anoa"].tolist() == ["2021", "2022"]


def test_excel_con_encabezados_distintos_entre_hojas(tmp_path):
    import sys
    sys.path.insert(0, "tools")
    from seudonimizar import _leer
    ruta = tmp_path / "x.xlsx"
    with pd.ExcelWriter(ruta) as w:
        pd.DataFrame({"anoa": ["2021"], "CI": ["1"]}).to_excel(w, sheet_name="2021", index=False)
        pd.DataFrame({"Anoa ": ["2022"], "ci": ["2"]}).to_excel(w, sheet_name="2022", index=False)
    df = _leer(ruta)
    assert list(df.columns) == ["hoja", "anoa", "CI"] and df["anoa"].tolist() == ["2021", "2022"]


def test_alias_anoaa_y_fecha_se_unifican(config, cohorte_c1):
    origen = pd.DataFrame([_fila(2021, "E1", "F1", "2021-03-01")], columns=COLUMNAS)
    destino = pd.DataFrame([_fila(2022, "E1", "F1", "2022-03-01")], columns=COLUMNAS)
    destino = destino.rename(columns={"anoa": "anoaa", "Fecha Reserva": "Fecha"})
    base = limpiar_base(pd.concat([origen, destino], ignore_index=True), config)
    assert sorted(base["anio_origen"].tolist()) == [2021, 2022]
    assert base["fecha_reserva"].notna().all()
    tabla, _ = construir_cohorte(base, cohorte_c1, config)
    assert tabla["y_no_matricula"].tolist() == [0]
