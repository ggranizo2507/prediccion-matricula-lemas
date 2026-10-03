"""Pruebas del diagnóstico de sobreajuste y subajuste (actividad de la semana 3)."""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from src import diagnostico as dg  # noqa: E402
from src import graficos_diagnostico as gd  # noqa: E402
from src.data_processing import construir_dataset, limpiar_base  # noqa: E402
from src.evaluate import calcular_k_por_sede, consolidar_familias  # noqa: E402
from src.modeling import NOMBRES  # noqa: E402
from src.synthetic import generar  # noqa: E402
from src.utils import cargar_config  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
COHORTES = ["C2", "C3"]
SEMILLA = 42
PARAMETROS = {
    "logistica": {"conjunto": "reducido", "balanceado": False, "C": 0.05, "l1_ratio": 0.5},
    "arboles": {"conjunto": "reducido", "balanceado": True, "learning_rate": 0.05,
                "max_depth": 2, "max_leaf_nodes": 6, "min_samples_leaf": 60,
                "l2_regularization": 1.0, "max_iter": 40},
    "hibrido": {"balanceado": False, "C": 0.05},
}


@pytest.fixture(scope="module")
def config():
    return cargar_config()


@pytest.fixture(scope="module")
def dataset(config):
    datos, _ = construir_dataset(limpiar_base(generar(config, semilla=5).astype(str), config),
                                 config)
    return datos


@pytest.fixture(scope="module")
def particion(dataset):
    return dg.particion_diagnostico(dataset, COHORTES)


@pytest.fixture(scope="module")
def interna(dataset):
    return dg.particion_interna(dataset, COHORTES)


@pytest.fixture(scope="module")
def k(dataset, config):
    entrenamiento = dataset[dataset["cohorte"].isin(COHORTES)]
    return calcular_k_por_sede(consolidar_familias(entrenamiento, np.zeros(len(entrenamiento))),
                               config["capacidad"]["multiplicador_k"])


@pytest.fixture(scope="module")
def seguimiento(particion):
    return dg.seguir_boosting(PARAMETROS["arboles"], particion, SEMILLA, iteraciones=60,
                              iteracion_fase2=40)


@pytest.fixture(scope="module")
def estrategias(particion, interna, k):
    return dg.evaluar_estrategias(PARAMETROS, particion, interna, SEMILLA, k)


# --------------------------------------------------------------------------- #
# Protocolo: orden temporal y C5 intacta
# --------------------------------------------------------------------------- #
def test_particiones_respetan_el_orden_temporal_y_excluyen_c5(particion, interna):
    for p in (particion, interna):
        assert "prueba" not in set(p.datos_tr["rol"]) | set(p.datos_val["rol"])
        assert p.datos_tr["cohorte"].max() < p.datos_val["cohorte"].min()   # C2 < C3 < C4
    assert set(particion.datos_tr["cohorte"]) == {"C2", "C3"}
    assert set(particion.datos_val["cohorte"]) == {"C4"}
    assert (interna.etiqueta_tr, interna.etiqueta_val) == ("C2", "C3")
    assert particion.resumen()["n_validacion"] == len(particion.datos_val)


def test_el_diagnostico_no_depende_de_c5(dataset, particion, k):
    """Si se alteran las etiquetas de C5, ningún resultado cambia."""
    alterado = dataset.copy()
    es_c5 = alterado["rol"] == "prueba"
    assert es_c5.any()
    alterado.loc[es_c5, "y_no_matricula"] = 1 - alterado.loc[es_c5, "y_no_matricula"]
    original = dg.tabla_diagnostico(PARAMETROS, particion, SEMILLA, k)
    otra = dg.tabla_diagnostico(PARAMETROS, dg.particion_diagnostico(alterado, COHORTES),
                                SEMILLA, k)
    pd.testing.assert_frame_equal(original, otra)


def test_particion_interna_exige_dos_cohortes(dataset):
    with pytest.raises(ValueError, match="dos cohortes"):
        dg.particion_interna(dataset, ["C3"])


# --------------------------------------------------------------------------- #
# Hiperparámetros de la Fase 2
# --------------------------------------------------------------------------- #
def test_mejores_parametros_lee_el_historial_guardado():
    filas = []
    for tipo, nombre in NOMBRES.items():
        for numero, valor in enumerate([0.10, 0.14, 0.14]):
            fila = {"modelo": nombre, "number": numero, "value": valor,
                    "params_balanceado": numero == 1, "params_C": 0.1 * (numero + 1)}
            if tipo != "hibrido":
                fila["params_conjunto"] = "reducido"
            if tipo == "logistica":
                fila["params_l1_ratio"] = 0.3
            if tipo == "arboles":
                fila.update(params_learning_rate=0.05, params_max_depth=3.0,
                            params_max_leaf_nodes=8.0, params_min_samples_leaf=50.0,
                            params_l2_regularization=1.0, params_max_iter=120.0)
            filas.append(fila)
    parametros = dg.mejores_parametros(pd.DataFrame(filas))
    assert set(parametros) == set(NOMBRES)
    assert parametros["logistica"]["C"] == pytest.approx(0.2)      # primera de las mejores
    assert parametros["logistica"]["balanceado"] is True
    assert isinstance(parametros["arboles"]["max_iter"], int)
    assert parametros["arboles"]["max_depth"] == 3
    assert "conjunto" not in parametros["hibrido"]


def test_mejores_parametros_avisa_si_falta_un_modelo():
    incompleto = pd.DataFrame([{"modelo": NOMBRES["hibrido"], "value": 0.1,
                                "params_balanceado": True, "params_C": 1.0}])
    with pytest.raises(ValueError, match="faltan"):
        dg.mejores_parametros(incompleto)


# --------------------------------------------------------------------------- #
# Seguimiento de métricas
# --------------------------------------------------------------------------- #
def test_registro_de_metricas():
    registro = dg.RegistroMetricas()
    for paso in (1, 2):
        registro.registrar("m", paso, "entrenamiento", 0.6 / paso, 0.2)
        registro.registrar("m", paso, "validacion", 0.7, 0.15)
    assert len(registro.tabla()) == 4
    registro.registrar("m", 2, "validacion", 0.65, 0.16)     # repetido: reemplaza, no duplica
    assert len(registro.tabla()) == 4
    ancho = registro.ancho()
    assert ancho["perdida_validacion"].iloc[-1] == pytest.approx(0.65)
    assert list(ancho["iteracion"]) == [1, 2]
    assert {"perdida_entrenamiento", "perdida_validacion", "puntaje_entrenamiento",
            "puntaje_validacion"} <= set(ancho.columns)


def test_seguimiento_registra_cada_iteracion(seguimiento):
    assert list(seguimiento["iteracion"]) == list(range(1, 61))
    assert seguimiento["perdida_entrenamiento"].iloc[-1] < seguimiento[
        "perdida_entrenamiento"].iloc[0]                 # el entrenamiento siempre mejora
    assert seguimiento[["puntaje_entrenamiento", "puntaje_validacion"]].stack().between(
        0, 1).all()
    assert (seguimiento["iteracion_fase2"] == 40).all()


def test_seguimiento_coincide_con_el_modelo_final(particion, seguimiento):
    """La última iteración registrada es el mismo modelo que se evalúa de una vez."""
    final = dg.evaluar("arboles", {**PARAMETROS["arboles"], "max_iter": 60}, particion, SEMILLA)
    assert seguimiento["puntaje_validacion"].iloc[-1] == pytest.approx(
        final["puntaje_validacion"])
    assert seguimiento["perdida_validacion"].iloc[-1] == pytest.approx(
        final["perdida_validacion"])


def test_resumen_detecta_que_la_validacion_empeora():
    iteraciones = np.arange(1, 101)
    curva = pd.DataFrame({
        "iteracion": iteraciones,
        "perdida_entrenamiento": 0.7 - 0.005 * iteraciones,
        "perdida_validacion": 0.7 - 0.01 * np.minimum(iteraciones, 20)
        + 0.004 * np.maximum(iteraciones - 20, 0),
        "puntaje_entrenamiento": 0.1 + 0.005 * iteraciones,
        "puntaje_validacion": 0.15 - 0.0005 * np.abs(iteraciones - 20),
        "iteracion_fase2": 60})
    resumen = dg.resumen_seguimiento(curva)
    assert resumen["iteracion_optima"] == 20 and not resumen["minimo_en_el_limite"]
    assert resumen["validacion_empeora"] and resumen["brecha_crece"]
    assert resumen["deterioro_perdida"] == pytest.approx(0.32)
    assert resumen["iteracion_fase2"] == 60
    assert resumen["perdida_validacion_fase2"] > resumen["perdida_validacion_minima"]


# --------------------------------------------------------------------------- #
# Diagnóstico
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tr,val,tasa,esperado", [
    (0.60, 0.12, 0.08, "sobreajuste"),        # gran brecha
    (0.09, 0.085, 0.08, "subajuste"),         # sin brecha, pero no supera al azar
    (0.17, 0.16, 0.08, "ajuste adecuado"),    # brecha pequeña y el doble que el azar
])
def test_diagnosticar(tr, val, tasa, esperado):
    assert dg.diagnosticar(tr, val, tasa)["diagnostico"] == esperado


def test_resumen_avisa_si_el_minimo_esta_en_el_ultimo_paso():
    curva = pd.DataFrame({"iteracion": [1, 2, 3], "perdida_entrenamiento": [0.7, 0.6, 0.5],
                          "perdida_validacion": [0.7, 0.65, 0.62],
                          "puntaje_entrenamiento": [0.1, 0.2, 0.3],
                          "puntaje_validacion": [0.1, 0.12, 0.14]})
    resumen = dg.resumen_seguimiento(curva)
    assert resumen["minimo_en_el_limite"] and not resumen["validacion_empeora"]
    assert "iteracion_fase2" not in resumen


def test_diagnostico_indeterminado_sin_datos():
    assert dg.diagnosticar(float("nan"), 0.1, 0.08)["diagnostico"] == "indeterminado"
    assert dg.diagnosticar(0.0, 0.1, 0.08)["diagnostico"] == "indeterminado"
    assert dg.diagnosticar(0.2, 0.1, 0.0)["diagnostico"] == "indeterminado"


def test_umbrales_configurables():
    assert dg.diagnosticar(0.20, 0.16, 0.08)["diagnostico"] == "ajuste adecuado"
    assert dg.diagnosticar(0.20, 0.16, 0.08, {"brecha_relativa_max": 0.1}
                           )["diagnostico"] == "sobreajuste"


def test_los_controles_se_reconocen(particion, k):
    tabla = dg.tabla_diagnostico(PARAMETROS, particion, SEMILLA, k).set_index("modelo")
    assert tabla.loc[dg.CONTROL_COMPLEJO, "diagnostico"] == "sobreajuste"
    assert tabla.loc[dg.CONTROL_RIGIDO, "diagnostico"] == "subajuste"
    assert tabla.loc[dg.CONTROL_RIGIDO, "mejora_sobre_azar"] == pytest.approx(1.0, abs=0.05)
    assert set(tabla["rol"]) == {"Fase 2", "control"}
    assert {"lift_k_validacion", "veces_azar_entrenamiento", "perdida_ponderada"} <= set(
        tabla.columns)


def test_perdida_ponderada_y_sin_ponderar():
    y = np.array([0, 0, 0, 1])
    prob = np.array([0.1, 0.1, 0.1, 0.5])
    pesos = dg.pesos_de_clase(y, True)
    assert pesos == {0: pytest.approx(4 / 6), 1: pytest.approx(2.0)}
    assert dg.pesos_de_clase(y, False) is None
    assert dg.perdida(y, prob, pesos) > dg.perdida(y, prob)   # el evento pesa más
    assert np.isnan(dg.puntaje(np.zeros(4), prob))


# --------------------------------------------------------------------------- #
# Curvas de scikit-learn
# --------------------------------------------------------------------------- #
def test_curva_por_tamano(particion):
    curva = dg.curva_por_tamano("hibrido", PARAMETROS["hibrido"], particion, SEMILLA,
                                fracciones=(0.3, 0.6, 1.0), repeticiones=2)
    puntajes = curva[curva["metrica"] == "puntaje"]
    assert list(puntajes["n"]) == sorted(puntajes["n"])
    assert puntajes["n"].iloc[-1] == len(particion.datos_tr)
    assert puntajes["validacion_de"].iloc[-1] == pytest.approx(0)   # misma muestra completa
    assert set(curva["metrica"]) == {"puntaje", "perdida"}
    assert (curva[curva["metrica"] == "perdida"]["validacion"] > 0).all()


def test_curva_por_hiperparametro(particion):
    valores = [0.001, 0.1, 10.0]
    curva = dg.curva_por_hiperparametro("logistica", PARAMETROS["logistica"], particion,
                                        SEMILLA, "C", valores)
    assert list(curva["valor"]) == valores
    assert (curva["valor_fase2"] == 0.05).all()
    # Con poca regularización el modelo se ajusta más al entrenamiento
    assert curva["puntaje_entrenamiento"].iloc[-1] > curva["puntaje_entrenamiento"].iloc[0]


# --------------------------------------------------------------------------- #
# Estrategias
# --------------------------------------------------------------------------- #
def test_estrategias_antes_y_despues(estrategias):
    assert len(estrategias) == 6
    assert list(estrategias["problema"]) == ["sobreajuste"] * 3 + ["subajuste"] * 3
    e1 = estrategias.iloc[0]
    assert e1["modelo_antes"] == dg.CONTROL_COMPLEJO
    assert e1["diagnostico_antes"] == "sobreajuste"
    assert e1["brecha_despues"] < e1["brecha_antes"] and e1["efecto_brecha"] == "reduce"
    for columna in ("puntaje_validacion", "brecha", "lift_k_validacion", "diagnostico"):
        assert f"{columna}_antes" in estrategias and f"{columna}_despues" in estrategias
    assert np.allclose(estrategias["cambio_puntaje_validacion"],
                       estrategias["puntaje_validacion_despues"]
                       - estrategias["puntaje_validacion_antes"])
    assert set(estrategias["efecto_validacion"]) <= {"mejora", "empeora",
                                                     "sin cambio apreciable"}
    assert set(estrategias["efecto_brecha"]) <= {"reduce", "aumenta", "sin cambio apreciable"}
    # E1 parte de un modelo con sobreajuste: la estrategia sí aplica a su diagnóstico
    assert e1["aplica_al_diagnostico"] and not e1["modelo_sin_cambios"]
    sin_cambios = estrategias[estrategias["modelo_sin_cambios"]]
    assert (sin_cambios["cambio_puntaje_validacion"] == 0).all()


def test_el_efecto_respeta_el_cambio_minimo(estrategias):
    """Un cambio menor que el mínimo no cuenta como mejora ni como empeoramiento."""
    minimo = dg.UMBRALES["cambio_minimo"]
    for e in estrategias.itertuples():
        cambio = e.cambio_puntaje_validacion
        esperado = ("sin cambio apreciable" if abs(cambio) < minimo
                    else "mejora" if cambio > 0 else "empeora")
        assert e.efecto_validacion == esperado
        tamano = abs(e.brecha_despues) - abs(e.brecha_antes)      # se compara en valor absoluto
        assert e.cambio_brecha == pytest.approx(tamano)


def test_e3_y_e6_cambian_una_sola_cosa(estrategias, particion, k):
    """E3 conserva las iteraciones; E6 solo las duplica."""
    e3 = dg.evaluar("arboles", dg.modelo_simple(PARAMETROS["arboles"]), particion, SEMILLA, k)
    e6 = dg.evaluar("arboles", {**PARAMETROS["arboles"], "max_iter": 80}, particion, SEMILLA, k)
    assert estrategias.iloc[2]["puntaje_validacion_despues"] == pytest.approx(
        e3["puntaje_validacion"])
    assert estrategias.iloc[5]["puntaje_validacion_despues"] == pytest.approx(
        e6["puntaje_validacion"])
    assert dg.modelo_simple(PARAMETROS["arboles"])["max_iter"] == PARAMETROS["arboles"]["max_iter"]


def test_parada_temprana_solo_recorta_y_no_mira_c4(dataset, interna):
    """Nunca supera las iteraciones del modelo y no cambia si se alteran las etiquetas de C4."""
    alterado = dataset.copy()
    es_c4 = alterado["rol"] == "seleccion"
    alterado.loc[es_c4, "y_no_matricula"] = 1 - alterado.loc[es_c4, "y_no_matricula"]
    original = dg.iteracion_parada_temprana(PARAMETROS["arboles"], interna, SEMILLA)
    otra = dg.iteracion_parada_temprana(
        PARAMETROS["arboles"], dg.particion_interna(alterado, COHORTES), SEMILLA)
    assert original == otra
    assert 10 <= original <= PARAMETROS["arboles"]["max_iter"]
    assert dg.iteracion_parada_temprana(PARAMETROS["arboles"], interna, SEMILLA, tope=15) <= 15


def test_modelo_simple_no_aumenta_la_complejidad():
    simple = dg.modelo_simple(PARAMETROS["arboles"])
    assert simple["max_depth"] == 2 and simple["max_leaf_nodes"] == 4
    assert simple["min_samples_leaf"] >= PARAMETROS["arboles"]["min_samples_leaf"]
    assert simple["l2_regularization"] >= 10


# --------------------------------------------------------------------------- #
# Seguimiento de la logística, conclusiones y más datos
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tipo", ["logistica", "hibrido"])
def test_seguimiento_logistico_termina_en_el_modelo_final(particion, tipo):
    curva = dg.seguir_logistica(tipo, PARAMETROS[tipo], particion, SEMILLA)
    final = dg.evaluar(tipo, PARAMETROS[tipo], particion, SEMILLA)
    assert curva["iteracion"].is_monotonic_increasing and len(curva) >= 3
    assert curva["puntaje_validacion"].iloc[-1] == pytest.approx(final["puntaje_validacion"])
    assert curva["perdida_entrenamiento"].iloc[-1] == pytest.approx(
        final["perdida_entrenamiento"])
    assert curva["unidad"].iloc[0].startswith("iteración del optimizador")


def test_conclusiones_coinciden_con_las_cifras(particion, k, seguimiento, estrategias):
    tabla = dg.tabla_diagnostico(PARAMETROS, particion, SEMILLA, k)
    resumenes = {"Gradient boosting": dg.resumen_seguimiento(seguimiento)}
    frases = dg.conclusiones(tabla, resumenes, estrategias, "C4")
    assert set(frases) == {"modelos", "controles", "curvas", "estrategias", "balance"}
    assert len(frases["modelos"]) == 3 and len(frases["controles"]) == 2
    assert len(frases["estrategias"]) == 6
    primero = tabla.iloc[0]
    assert dg.numero(primero["puntaje_validacion"]) in frases["modelos"][0]
    assert primero["diagnostico"] in frases["modelos"][0]
    assert estrategias.iloc[0]["efecto_validacion"] in frases["estrategias"][0]
    assert "C5" in frases["balance"][-1]
    solo_modelos = dg.conclusiones(tabla, resumenes, None, "C4")
    assert solo_modelos["estrategias"] == [] and len(solo_modelos["balance"]) == 1


def test_numero_con_coma_y_signo_menos():
    assert dg.numero(0.1234) == "0,123"
    assert dg.numero(-0.0191, signo=True) == "−0,019"
    assert dg.numero(0.02, signo=True) == "+0,020"
    assert dg.numero(-0.0001) == "0,000"          # sin «−0,000»


def test_ganancia_por_datos_usa_la_variacion():
    curva = pd.DataFrame({
        "modelo": "m", "metrica": "puntaje", "n": [100, 200, 300, 400],
        "entrenamiento": [0.3, 0.25, 0.22, 0.2], "entrenamiento_de": 0.0,
        "validacion": [0.10, 0.12, 0.13, 0.15], "validacion_de": [0.02, 0.01, 0.01, 0.0]})
    fila = dg.ganancia_por_datos(curva).iloc[0]
    assert (fila["n_mitad"], fila["n_todo"]) == (200, 400)
    assert fila["ganancia"] == pytest.approx(0.03) and fila["concluyente"]       # 0,03 > 2 × 0,01
    ruidosa = curva.assign(validacion_de=[0.02, 0.02, 0.02, 0.0])
    assert not dg.ganancia_por_datos(ruidosa).iloc[0]["concluyente"]             # 0,03 < 2 × 0,02


def test_reporte_pdf_se_genera_con_los_resultados_guardados(tmp_path):
    """El reporte se arma con los agregados sintéticos del repositorio."""
    pytest.importorskip("reportlab")
    PdfReader = pytest.importorskip("pypdf").PdfReader  # noqa: N806

    from tools.generar_reporte_diagnostico import construir

    ruta = construir("sintetica", tmp_path / "reporte.pdf")
    texto = "\n".join(pagina.extract_text() for pagina in PdfReader(str(ruta)).pages)
    for seccion in ("1. Resumen ejecutivo", "2. Metodología utilizada",
                    "3. Resultados del diagnóstico", "4. Análisis de curvas de aprendizaje",
                    "5. Estrategias implementadas y resultados",
                    "6. Conclusiones y recomendaciones futuras", "7. Referencias técnicas"):
        assert seccion in texto, seccion
    assert "datos sintéticos" in texto          # la versión preliminar queda marcada


def test_reporte_real_usa_el_analisis_del_equipo(tmp_path):
    """Con datos reales el reporte lleva el análisis redactado por el equipo."""
    pytest.importorskip("reportlab")
    PdfReader = pytest.importorskip("pypdf").PdfReader  # noqa: N806

    from tools.generar_reporte_diagnostico import construir

    ruta = construir("real", tmp_path / "reporte.pdf")
    texto = "\n".join(pagina.extract_text() for pagina in PdfReader(str(ruta)).pages)
    assert "Qué aprendimos" in texto and "datos sintéticos" not in texto
    assert "C5 no intervino" in texto


# Cifras del análisis que no salen de los archivos de resultados, con su origen.
CIFRAS_PERMITIDAS = {
    "0,693": "ln 2: pérdida de asignar 0,5 con clases balanceadas",
    "0,5": "probabilidad 0,5 y tasa de aprendizaje máxima de la rejilla",
    "21,9": "exploración del cuaderno (pago tardío)",
    "6,3": "exploración del cuaderno (pago en plazo)",
    "32": "exploración del cuaderno (estudiantes con pago tardío)",
    "0,10": "redondeo de la validación del gradient boosting",
    "0,306": "pérdida de validación de la regresión logística desde la iteración 6",
    "0,01": "valor de C en la rejilla",
    "1,5": "umbral de subajuste", "30": "umbral de sobreajuste",
    "2": "Fase 2", "3": "C3", "4": "C4", "5": "C5",
}


def _cifras_de_resultados(fuente: str) -> list[float]:
    """Todos los números de los resultados guardados, con signo, valor absoluto y porcentaje."""
    carpeta = RAIZ / "results" / "metrics"
    valores: list[float] = []

    def agregar(dato):
        if isinstance(dato, bool):
            return
        if isinstance(dato, (int, float)):
            if not np.isnan(dato):
                valores.extend([float(dato), abs(float(dato)), 100 * float(dato),
                                100 * abs(float(dato))])
        elif isinstance(dato, dict):
            for valor in dato.values():
                agregar(valor)
        elif isinstance(dato, list):
            for valor in dato:
                agregar(valor)

    for nombre in ("diagnostico_modelos", "estrategias_mejora", "curvas_hiperparametros",
                   "curvas_tamano", "curvas_seguimiento", "seleccion_C4"):
        tabla = pd.read_csv(carpeta / f"{nombre}_{fuente}.csv")
        for columna in tabla.select_dtypes("number"):
            agregar(tabla[columna].dropna().tolist())
    resumen = json.loads((carpeta / f"diagnostico_semana3_{fuente}.json").read_text("utf-8"))
    agregar(resumen)
    campana = carpeta / f"alcance_campana_{fuente}.csv"     # nota posterior: sorteo en D2
    if campana.exists():
        fija = pd.read_csv(campana).query("estrategia == 'fija_inicio_d2'")
        seleccion = pd.read_csv(carpeta / f"seleccion_C4_{fuente}.csv")
        es_d2 = seleccion["candidato"].str.startswith("D2")
        lift_d2 = float(seleccion.loc[es_d2, "lift_k"].iloc[0])
        for fila in fija.itertuples():
            agregar([fila.recall, fila.recall_min, fila.recall_max, fila.recall_medio])
            if fila.cohorte == resumen["validacion"]:       # Lift@k equivalente de cada sorteo
                agregar([lift_d2 * fila.recall_min / fila.recall,
                         lift_d2 * fila.recall_max / fila.recall,
                         lift_d2 * fila.recall_medio / fila.recall])
    for particion in resumen["particiones"]:                # tasas de evento por partición
        agregar(particion["eventos_entrenamiento"] / particion["n_entrenamiento"])
        agregar(particion["eventos_validacion"] / particion["n_validacion"])
    return valores


def test_narrativa_real_coincide_con_los_datos():
    """Cada cifra citada en el análisis escrito existe en los resultados guardados."""
    narrativa = json.loads(
        (RAIZ / "docs" / "diagnostic_report_narrativa_real.json").read_text("utf-8"))
    valores = np.array(_cifras_de_resultados("real"))
    sin_respaldo = []
    for clave, contenido in narrativa.items():
        if clave.startswith("_"):
            continue
        for texto in [contenido] if isinstance(contenido, str) else contenido:
            limpio = re.sub(r"\b[CE]\d\b|Fase 2|D2|L1|@k", "", texto)
            for cifra in re.findall(r"(?<![\w,.])[+−±-]?\d+(?:[.,]\d+)?(?![\w])", limpio):
                sin_signo = cifra.lstrip("+−±-")
                if sin_signo in CIFRAS_PERMITIDAS:
                    continue
                if "." in sin_signo and "," not in sin_signo:      # separador de miles: 2.541
                    numero, decimales = float(sin_signo.replace(".", "")), 0
                else:
                    numero = float(sin_signo.replace(",", "."))
                    decimales = len(sin_signo.split(",")[1]) if "," in sin_signo else 0
                tolerancia = 0.5 * 10 ** -decimales + 1e-9
                if not (np.abs(valores - numero) <= tolerancia).any():
                    sin_respaldo.append((clave, cifra, texto[:60]))
    assert not sin_respaldo, sin_respaldo


# --------------------------------------------------------------------------- #
# Figuras
# --------------------------------------------------------------------------- #
def test_figuras_a_300_dpi(tmp_path, particion, seguimiento, estrategias):
    from PIL import Image

    tasa = float(particion.y_val.mean())
    tamano = dg.curva_por_tamano("hibrido", PARAMETROS["hibrido"], particion, SEMILLA,
                                 fracciones=(0.5, 1.0), repeticiones=2)
    hiper = dg.curva_por_hiperparametro("hibrido", PARAMETROS["hibrido"], particion, SEMILLA,
                                        "C", [0.01, 0.1, 1.0])
    logistica = dg.seguir_logistica("hibrido", PARAMETROS["hibrido"], particion, SEMILLA)
    curvas = {"Gradient boosting": seguimiento, "Logística híbrida": logistica,
              "Otro": seguimiento}
    figuras = {
        "perdida": gd.figura_iteraciones(curvas, "perdida", "C2+C3", "C4"),
        "puntaje": gd.figura_iteraciones(curvas, "puntaje", "C2+C3", "C4", tasa),
        "tamano": gd.figura_tamano(tamano, "C2+C3", "C4", tasa),
        "hiper": gd.figura_hiperparametros(hiper, "C2+C3", "C4", tasa),
        "estrategias": gd.figura_estrategias(estrategias, "C4"),
    }
    for nombre, figura in figuras.items():
        ejes = [ax for ax in figura.axes if ax.get_visible() and (ax.lines or ax.collections)]
        assert ejes and all(ax.get_title(loc="left") for ax in ejes), nombre
        assert figura.legends, nombre                      # leyenda presente
        ruta = gd.guardar(figura, tmp_path / f"{nombre}.png", dpi=300)
        dpi = Image.open(ruta).info["dpi"]
        assert round(dpi[0]) == 300 and round(dpi[1]) == 300, nombre
