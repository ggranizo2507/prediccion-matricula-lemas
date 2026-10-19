"""Pruebas de la simulación de escenarios críticos (src/escenarios.py) y del control de
calidad de las señales en la aplicación (inferencia.revisar_senales), D57."""

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from src import escenarios as es  # noqa: E402
from src import graficos_escenarios as ge  # noqa: E402
from src.data_processing import construir_dataset, limpiar_base  # noqa: E402
from src.diagnostico import sin_prueba  # noqa: E402
from src.inferencia import construir_poblacion, preparar_base, revisar_senales  # noqa: E402
from src.synthetic import generar  # noqa: E402
from src.utils import cargar_config  # noqa: E402

SEMILLA = 42
K = {"Mucho Lote 1": 60, "Mucho Lote 2": 30}
PARAMS = {"C": 1.0, "balanceado": True}


@pytest.fixture(scope="module")
def config():
    return cargar_config()


@pytest.fixture(scope="module")
def dataset(config):
    datos, _ = construir_dataset(limpiar_base(generar(config, semilla=5).astype(str), config),
                                 config)
    return datos


@pytest.fixture(scope="module")
def c4(dataset):
    return dataset[dataset["rol"] == "seleccion"].reset_index(drop=True)


@pytest.fixture(scope="module")
def entrenamiento(dataset):
    datos = sin_prueba(dataset)
    return datos[datos["rol"] == "entrenamiento"]


@pytest.fixture(scope="module")
def sistemas(entrenamiento):
    modelo = es.entrenar_hibrido(entrenamiento, PARAMS, SEMILLA)
    return {es.REGLA: es.puntuador_d2, es.HIBRIDO: es.puntuador_modelo(modelo)}


def rng():
    return np.random.default_rng(0)


# --------------------------------------------------------------------------- #
# Perturbaciones
# --------------------------------------------------------------------------- #
def test_ruido_cero_no_cambia_nada(c4):
    pd.testing.assert_frame_equal(es.ruido_registro(c4, 0.0, rng()), c4)


def test_ruido_cambia_la_fraccion_esperada_y_no_toca_a_los_nuevos(c4):
    salida = es.ruido_registro(c4, 0.20, rng())
    con_dato = c4["pago_origen"].isin(["tardio", "en_plazo", "anticipado"])
    cambiados = (salida["pago_origen"] != c4["pago_origen"]) & con_dato
    assert 0.12 < cambiados.sum() / con_dato.sum() < 0.28
    assert (salida.loc[~con_dato, "pago_origen"] == c4.loc[~con_dato, "pago_origen"]).all()
    assert set(salida["reserva_extraordinaria"].unique()) <= {0, 1}
    assert (pd.to_numeric(salida["atrasos_pension"]).dropna() >= 0).all()
    assert len(salida) == len(c4)


def test_ruido_gaussiano_respeta_el_rango(c4):
    salida = es.ruido_gaussiano(c4, "promedio", 3.0, rng())
    valores = pd.to_numeric(salida["promedio"]).dropna()
    assert valores.between(0, 10).all()
    assert not np.allclose(valores, pd.to_numeric(c4["promedio"]).dropna())


@pytest.mark.parametrize("senal", ["pago_tardio", "reserva_extraordinaria", "atrasos_pension",
                                   "promedio"])
def test_faltantes_vacia_aproximadamente_la_fraccion(c4, senal):
    salida = es.faltantes(c4, senal, 0.30, rng())
    if senal == "pago_tardio":
        con_dato = c4["pago_origen"].isin(["tardio", "en_plazo", "anticipado"])
        fraccion = (salida.loc[con_dato, "pago_origen"] == "sin_dato").mean()
    else:
        antes = pd.to_numeric(c4[senal], errors="coerce").isna()
        fraccion = pd.to_numeric(salida.loc[~antes, senal], errors="coerce").isna().mean()
    assert 0.22 < fraccion < 0.38


def test_faltantes_rechaza_senal_desconocida(c4):
    with pytest.raises(ValueError):
        es.faltantes(c4, "curso", 0.1, rng())


def test_senal_caida_deja_la_senal_constante(c4):
    assert (es.senal_caida(c4, "atrasos_pension")["atrasos_pension"] == 0).all()
    assert (es.senal_caida(c4, "reserva_extraordinaria")["reserva_extraordinaria"] == 0).all()
    pago = es.senal_caida(c4, "pago_tardio")["pago_origen"]
    assert not (pago == "tardio").any()
    todas = es.senal_caida(c4, "todas_d2")
    assert np.unique(es.puntuador_d2(todas)).size == 1      # D2 ya no ordena


def test_desbalance_llega_a_la_tasa_objetivo_y_quita_familias_enteras(c4):
    salida = es.desbalance(c4, 0.03, rng())
    tasa = salida.groupby("id_familia")["y_no_matricula"].max().mean()
    assert tasa == pytest.approx(0.03, abs=0.005)
    sin_caso = c4.groupby("id_familia")["y_no_matricula"].max() == 0
    # no se quita ninguna familia sin caso
    assert set(sin_caso[sin_caso].index) <= set(salida["id_familia"])
    assert es.desbalance(c4, None, rng()).equals(c4)


# --------------------------------------------------------------------------- #
# Medición, barridos y límites
# --------------------------------------------------------------------------- #
def test_sin_perturbar_reproduce_la_metrica_de_la_fase2(c4, sistemas):
    from src.modeling import metricas
    directo = metricas(c4, es.puntuador_d2(c4), K, SEMILLA)
    assert es.medir(c4, es.puntuador_d2, K, SEMILLA)["lift_k"] == directo["lift_k"]


def test_barridos_tienen_todas_las_filas(c4, sistemas):
    ruido = es.escenario_ruido(c4, sistemas, K, SEMILLA, repeticiones=3)
    assert set(ruido["variable"]) == {"errores_registro", "promedio_gaussiano"}
    assert len(ruido) == 2 * len(es.NIVELES_RUIDO) + len(es.SIGMAS_PROMEDIO)
    assert {"lift_k", "lift_k_p05", "lift_k_p95"} <= set(ruido.columns)
    caida = es.escenario_caida(c4, sistemas, K, SEMILLA, repeticiones=3)
    assert caida.query("variable == 'promedio'")["sistema"].tolist() == [es.HIBRIDO]


def test_con_todas_las_senales_caidas_d2_queda_cerca_del_azar(c4, sistemas):
    caida = es.escenario_caida(c4, sistemas, K, SEMILLA, repeticiones=20)
    fila = caida[(caida["variable"] == "todas_d2") & (caida["sistema"] == es.REGLA)].iloc[0]
    assert 0.6 < fila["lift_k"] < 1.4


def _resultados_de_prueba(lifts_ruido, lift_caida):
    filas = [{"escenario": "ruido", "variable": "errores_registro", "sistema": es.REGLA,
              "nivel": nivel, "lift_k": lift, "lift_k_p05": lift - 0.05}
             for nivel, lift in zip(es.NIVELES_RUIDO, lifts_ruido, strict=True)]
    filas.append({"escenario": "senal_caida", "variable": "ninguna", "sistema": es.REGLA,
                  "nivel": "base", "lift_k": lifts_ruido[0], "recall_k": 0.3})
    filas.append({"escenario": "senal_caida", "variable": "pago_tardio", "sistema": es.REGLA,
                  "nivel": "constante", "lift_k": lift_caida, "recall_k": 0.15})
    return pd.DataFrame(filas)


def test_limites_encuentran_el_ultimo_nivel_util():
    resultados = _resultados_de_prueba([1.9, 1.8, 1.7, 1.5, 1.22, 1.0], 1.1)
    lim = es.limites(resultados).set_index("variable")
    # en el 10 % la media es 1,22 pero el percentil 5 (1,17) ya no llega a 1,20
    assert lim.loc["errores_registro", "ultimo_nivel_util"] == pytest.approx(0.05)
    assert lim.loc["errores_registro", "primer_nivel_no_util"] == pytest.approx(0.10)
    assert lim.loc["pago_tardio", "primer_nivel_no_util"] == "constante"
    textos = es.conclusiones(resultados, pd.DataFrame(), es.limites(resultados))
    assert any("tolera errores de registro hasta el 5 %" in t for t in textos)


def test_conclusiones_advierten_si_la_base_ya_no_es_util():
    resultados = _resultados_de_prueba([1.05, 1.0, 1.0, 1.0, 1.0, 1.0], 1.0)
    textos = es.conclusiones(resultados, pd.DataFrame(), es.limites(resultados))
    assert any("ya está por debajo del umbral" in t for t in textos)


def test_cambio_de_distribucion(entrenamiento, c4):
    cambio = es.escenario_cambio(entrenamiento, c4, PARAMS, SEMILLA)
    assert set(cambio["corte"]) == {"sede", "beca"}
    esperados = {"transferido", "referencia (todos)", "regla D2 (sin aprendizaje)"}
    assert esperados <= set(cambio["modelo"])
    d2 = cambio[cambio["modelo"] == "regla D2 (sin aprendizaje)"]
    assert d2["brier"].isna().all()                       # la regla no da probabilidades
    visibles = cambio[cambio["eventos"].apply(lambda v: isinstance(v, (int, np.integer)))]
    assert (visibles["eventos"] >= 5).all()


def test_figuras(c4, sistemas, entrenamiento):
    resultados = pd.concat([es.escenario_ruido(c4, sistemas, K, SEMILLA, 2),
                            es.escenario_faltantes(c4, sistemas, K, SEMILLA, 2),
                            es.escenario_desbalance(c4, sistemas, K, SEMILLA, 2),
                            es.escenario_caida(c4, sistemas, K, SEMILLA, 2)], ignore_index=True)
    assert len(ge.figura_degradacion(resultados).axes) == 4
    cambio = es.escenario_cambio(entrenamiento, c4, PARAMS, SEMILLA)
    assert len(ge.figura_cambio(cambio).axes) == 2


# --------------------------------------------------------------------------- #
# Control de calidad en la aplicación
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def poblacion(config):
    crudo = generar(config, semilla=5).astype(str)
    base = preparar_base(crudo, config)
    anio = int(sorted(base["anio_origen"].dropna().unique())[-2])
    datos, _ = construir_poblacion(base, anio, config)
    return datos


def test_sin_avisos_con_datos_sanos(poblacion, config):
    assert revisar_senales(poblacion, config) == []


def test_avisa_si_los_atrasos_llegan_en_cero(poblacion, config):
    avisos = revisar_senales(poblacion.assign(atrasos_pension=0), config)
    assert any("toda en cero" in a for a in avisos)
    assert "azar" in avisos[-1]


def test_avisa_si_faltan_fechas_de_pago(poblacion, config):
    datos = poblacion.copy()
    no_nuevos = datos.index[datos["pago_origen"] != "nuevo"]
    datos.loc[no_nuevos[: int(0.5 * len(no_nuevos))], "pago_origen"] = "sin_dato"
    assert any("fecha de pago" in a for a in revisar_senales(datos, config))


def test_avisa_si_falta_la_hoja_anterior(poblacion, config):
    avisos = revisar_senales(poblacion.assign(pago_origen="nuevo"), config)
    assert any("hoja del ciclo anterior" in a for a in avisos)


def test_avisa_si_no_hay_ningun_pago_tardio(poblacion, config):
    datos = poblacion.assign(pago_origen=poblacion["pago_origen"].replace("tardio", "en_plazo"))
    assert any("pago tardío" in a for a in revisar_senales(datos, config))


def test_poblacion_pequena_no_se_evalua(poblacion, config):
    assert revisar_senales(poblacion.head(10).assign(atrasos_pension=0), config) == []
