"""Pruebas del análisis de alcance de la lista de contactos (src/alcance.py)."""

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from src import alcance as al  # noqa: E402
from src import graficos_alcance as ga  # noqa: E402
from src.data_processing import construir_dataset, limpiar_base  # noqa: E402
from src.evaluate import (  # noqa: E402
    calcular_k_por_sede,
    consolidar_familias,
    precision_at_k_familiar,
    primeras_k,
)
from src.modeling import OCULTO, puntajes_reglas  # noqa: E402
from src.synthetic import generar  # noqa: E402
from src.utils import Cohorte, cargar_config, cohortes_desde_config  # noqa: E402

SEMILLA = 42
SEDE = "Mucho Lote 1"


@pytest.fixture(scope="module")
def config():
    return cargar_config()


@pytest.fixture(scope="module")
def dataset(config):
    datos, _ = construir_dataset(limpiar_base(generar(config, semilla=5).astype(str), config),
                                 config)
    return datos


@pytest.fixture(scope="module")
def cohortes(config):
    return {c.nombre: c for c in cohortes_desde_config(config)}


@pytest.fixture(scope="module")
def k(dataset):
    entrenamiento = dataset[dataset["cohorte"].isin(["C2", "C3"])]
    return calcular_k_por_sede(consolidar_familias(entrenamiento, np.zeros(len(entrenamiento))),
                               2)


@pytest.fixture(scope="module")
def familias(dataset, cohortes):
    return al.tabla_familias(al.sin_prueba(dataset), cohortes)


@pytest.fixture(scope="module")
def tablas(familias, k):
    return {"desglose": al.desglose_evento(familias, k, SEMILLA),
            "por_k": al.alcance_por_k(familias, k, SEMILLA, personal=10),
            "semanal": al.foto_semanal(familias, k, SEMILLA),
            "campana": al.campana(familias, k, SEMILLA, repeticiones=8)}


def _a_mano(score, evento, dia_resuelta, cohorte="C2", ventana=69):
    """Tabla de familias mínima para probar la campaña con casos escritos a mano."""
    n = len(score)
    return pd.DataFrame({
        "cohorte": cohorte, "sede": SEDE, "id_familia": [f"F{i:03d}" for i in range(n)],
        "score": np.asarray(score, dtype=float), "evento": evento,
        "dia_resuelta": np.asarray(dia_resuelta, dtype=float), "dias_ventana": ventana,
        "tipo": np.where(np.asarray(evento) == 1, "sin_pago", "en_plazo"),
        "dias_tarde": np.nan})


# --------------------------------------------------------------------------- #
# Tabla de familias
# --------------------------------------------------------------------------- #
def _estudiante(familia, pago, evento):
    return {"cohorte": "C2", "sede": SEDE, "id_familia": familia,
            "id_estudiante": f"E-{familia}-{pago}", "atrasos_pension": 0,
            "pago_origen": "en_plazo", "reserva_extraordinaria": 0,
            "fecha_pago_destino": pd.Timestamp(pago) if pago else pd.NaT,
            "y_no_matricula": evento}


def test_tabla_familias_clasifica_como_termino_cada_familia():
    t0, h = pd.Timestamp("2023-02-20"), pd.Timestamp("2023-04-30")
    cohorte = {"C2": Cohorte("C2", 2022, "entrenamiento", t0, h)}
    datos = pd.DataFrame([
        _estudiante("A", "2023-03-01", 0),                       # paga en plazo
        _estudiante("B", "2023-05-20", 1),                       # paga 20 días tarde
        _estudiante("C", None, 1),                               # no registra pago
        _estudiante("D", "2023-02-25", 0), _estudiante("D", None, 1),   # paga por un hijo
        _estudiante("E", "2023-02-22", 0), _estudiante("E", "2023-04-10", 0),
        _estudiante("F", "2023-04-30", 0),                       # paga el último día: en plazo
        _estudiante("G", "2023-02-20", 0),                       # paga el mismo día del corte
        _estudiante("H", None, 1), _estudiante("H", None, 1),    # ningún hijo registra pago
    ])
    tabla = al.tabla_familias(datos, cohorte).set_index("id_familia")
    assert tabla["tipo"].to_dict() == {
        "A": "en_plazo", "B": "tardia", "C": "sin_pago", "D": "parcial", "E": "en_plazo",
        "F": "en_plazo", "G": "en_plazo", "H": "sin_pago"}
    assert tabla.loc["A", "dia_resuelta"] == 9
    assert tabla.loc["E", "dia_resuelta"] == 49          # pendiente hasta que paga el último
    assert tabla.loc["F", "dia_resuelta"] == 69 and tabla.loc["G", "dia_resuelta"] == 0
    assert tabla.loc["B", "dias_tarde"] == 20
    assert tabla.loc[["C", "D", "H"], "dia_resuelta"].isna().all()   # siguen pendientes
    assert tabla.loc[["A", "C", "D"], "dias_tarde"].isna().all()
    assert (tabla["dias_ventana"] == 69).all()


def test_el_evento_coincide_con_el_tipo(familias):
    assert ((familias["tipo"] == "en_plazo") == (familias["evento"] == 0)).all()
    en_plazo = familias[familias["tipo"] == "en_plazo"]
    assert (en_plazo["dia_resuelta"] >= 0).all()
    assert (en_plazo["dia_resuelta"] <= en_plazo["dias_ventana"]).all()
    tardias = familias[familias["tipo"] == "tardia"]
    assert (tardias["dias_tarde"] > 0).all()
    assert (tardias["dia_resuelta"] > tardias["dias_ventana"]).all()
    assert set(familias["dias_ventana"]) <= {69, 70}             # 70 en año bisiesto


def test_no_usa_la_cohorte_de_prueba(dataset, cohortes, familias, k, tablas):
    """Cambiar C5 no altera ninguna de las cuatro tablas."""
    assert "C5" not in set(familias["cohorte"])
    alterado = dataset.copy()
    prueba = alterado["rol"] == "prueba"
    alterado.loc[prueba, "y_no_matricula"] = 1 - alterado.loc[prueba, "y_no_matricula"]
    alterado.loc[prueba, "fecha_pago_destino"] = pd.NaT
    otra = al.tabla_familias(al.sin_prueba(alterado), cohortes)
    pd.testing.assert_frame_equal(al.desglose_evento(otra, k, SEMILLA), tablas["desglose"])
    pd.testing.assert_frame_equal(al.alcance_por_k(otra, k, SEMILLA, personal=10),
                                  tablas["por_k"])
    pd.testing.assert_frame_equal(al.foto_semanal(otra, k, SEMILLA), tablas["semanal"])
    pd.testing.assert_frame_equal(al.campana(otra, k, SEMILLA, repeticiones=8),
                                  tablas["campana"])


def test_la_lista_es_la_de_la_validacion(dataset, familias, k, tablas):
    """Mismas familias (no solo el mismo recall) que la selección usada al validar."""
    en_lista = al.seleccionar(familias, k, SEMILLA)
    for cohorte, datos in al.sin_prueba(dataset).groupby("cohorte"):
        consolidado = consolidar_familias(datos, puntajes_reglas(datos)[al.REGLA])
        esperadas = set()
        for sede, grupo in consolidado.groupby("sede"):
            esperadas |= set(primeras_k(grupo, k[sede], SEMILLA)["id_familia"])
        obtenidas = set(familias.loc[en_lista & (familias["cohorte"] == cohorte), "id_familia"])
        assert obtenidas == esperadas, cohorte
        total = precision_at_k_familiar(consolidado, k, SEMILLA)
        total = total[total["sede"] == "TOTAL"].iloc[0]
        fila = tablas["desglose"].set_index("cohorte").loc[cohorte]
        assert fila["aciertos"] == total["aciertos"]
        assert fila["recall"] == pytest.approx(total["recall_k"], abs=1e-4)


# --------------------------------------------------------------------------- #
# 1. Desglose
# --------------------------------------------------------------------------- #
def test_desglose_suma_y_protege_celdas_pequenas(familias, k):
    tabla = al.desglose_evento(familias, k, SEMILLA, minimo=1).set_index("cohorte")
    total = tabla.loc[al.TODAS]
    assert sum(total[t] for t in al.TIPOS) == total["eventos"]
    assert sum(total[f"aciertos_{t}"] for t in al.TIPOS) == total["aciertos"]
    assert tabla.drop(index=al.TODAS)["eventos"].sum() == total["eventos"]

    # con un mínimo alto, el detalle por cohorte desaparece y no puede deducirse del total
    estricta = al.desglose_evento(familias, k, SEMILLA, minimo=40).set_index("cohorte")
    columnas = [c for t in al.TIPOS for c in (t, f"aciertos_{t}")]
    assert (estricta.drop(index=al.TODAS)[columnas] == OCULTO).all().all()
    assert estricta.drop(index=al.TODAS)["recall_tardia"].isna().all()
    assert (estricta["eventos"] == tabla["eventos"]).all()      # los totales ya son públicos


def test_desglose_total_oculta_solo_lo_necesario():
    """En «Todas» se oculta la celda pequeña y una más, no todo el desglose."""
    # 3 familias pagan tarde, 20 pagan en parte y 100 no registran pago; 400 pagan en plazo
    tipos = ["tardia"] * 3 + ["parcial"] * 20 + ["sin_pago"] * 100 + ["en_plazo"] * 400
    rng = np.random.default_rng(0)
    evento = [0 if t == "en_plazo" else 1 for t in tipos]
    familias = _a_mano(rng.integers(0, 5, len(tipos)), evento, [np.nan] * len(tipos))
    familias["tipo"] = tipos
    familias["dias_tarde"] = [10.0 if t == "tardia" else np.nan for t in tipos]
    total = al.desglose_evento(familias, {SEDE: 150}, SEMILLA).set_index("cohorte").loc[al.TODAS]
    assert total["tardia"] == "<5" and total["parcial"] == OCULTO      # la pequeña y otra más
    assert total["sin_pago"] == 100                                    # el resto se publica
    assert total["aciertos_tardia"] == OCULTO and total["aciertos_parcial"] == OCULTO
    assert isinstance(total["aciertos_sin_pago"], (int, np.integer))
    assert 0 < total["recall_sin_pago"] < 1 and np.isnan(total["recall_tardia"])
    assert np.isnan(total["pct_tardia"]) and np.isnan(total["mediana_dias_tarde"])
    assert total["pct_sin_pago"] == pytest.approx(100 / 123, abs=1e-4)
    # y las frases solo usan lo publicable
    textos = al.conclusiones(
        al.desglose_evento(familias, {SEDE: 150}, SEMILLA),
        al.alcance_por_k(familias, {SEDE: 150}, SEMILLA),
        al.foto_semanal(familias, {SEDE: 150}, SEMILLA),
        al.campana(familias, {SEDE: 150}, SEMILLA, repeticiones=3))
    assert _sin_basura(textos)


def test_supresion_complementaria_entre_cohortes():
    """Una sola cohorte oculta se deduciría restando las demás de «Todas»."""
    tabla = pd.DataFrame({"cohorte": ["C2", "C3", "C4", al.TODAS], "aciertos": [3, 12, 9, 24],
                          "recall": [0.1, 0.3, 0.2, 0.2]})
    al._ocultar(tabla, "aciertos", ["recall"], minimo=5)
    assert tabla["aciertos"].tolist() == ["<5", 12, OCULTO, 24]     # C4 es la visible menor
    assert tabla["recall"].isna().tolist() == [True, False, True, False]

    sin_celdas = pd.DataFrame({"cohorte": ["C2", "C3", al.TODAS], "aciertos": [0, 8, 8],
                               "recall": [0.0, 0.3, 0.2]})
    antes = sin_celdas.copy()
    al._ocultar(sin_celdas, "aciertos", ["recall"], minimo=5)
    pd.testing.assert_frame_equal(sin_celdas, antes)                # el cero no se oculta


# --------------------------------------------------------------------------- #
# 2. Alcance según k
# --------------------------------------------------------------------------- #
def test_alcance_por_k_crece_con_los_contactos(familias, k, tablas):
    total = tablas["por_k"]
    total = total[total["cohorte"] == al.TODAS].reset_index(drop=True)
    assert total["contactos"].is_monotonic_increasing
    assert total["aciertos"].is_monotonic_increasing             # las listas están anidadas
    todas = total.iloc[-1]
    assert todas["multiplicador"] == "todas" and todas["recall"] == 1
    assert todas["contactos"] == len(familias)
    assert (total["recall_azar"] == total["pct_familias"]).all()
    aprobado = total[total["multiplicador"] == 1.0].iloc[0]
    desglose = tablas["desglose"].set_index("cohorte")
    assert aprobado["aciertos"] == desglose.loc[al.TODAS, "aciertos"]
    campanas = familias["cohorte"].nunique()
    assert aprobado["contactos_por_persona_semana"] == pytest.approx(
        aprobado["contactos"] / campanas / 10 / 10, abs=0.01)


def test_k_con_multiplicador_redondea_hacia_arriba_en_la_mitad():
    assert al._k({"A": 47}, "A", 0.5) == 24 and al._k({"A": 47}, "A", 1.5) == 71
    assert al._k({"A": 47}, "A", None) is None and al._k({}, "A", 2) == 0


# --------------------------------------------------------------------------- #
# 3. Lista actualizada durante la campaña
# --------------------------------------------------------------------------- #
def test_foto_semanal(familias, tablas):
    foto = tablas["semanal"]
    assert set(foto["cohorte"]) == {al.TODAS} and len(foto) == 10   # no se publica por cohorte
    visibles = foto[foto["pendientes"] != OCULTO]
    assert visibles["pendientes"].is_monotonic_decreasing
    assert foto["eventos"].nunique() == 1          # quien no pagará en plazo nunca sale
    assert visibles["tasa_base"].is_monotonic_increasing
    assert (visibles["pendientes"] - visibles["eventos"] == visibles["pagaran_en_plazo"]).all()
    primera = foto.iloc[0]
    desglose = tablas["desglose"].set_index("cohorte")
    assert primera["pendientes"] == len(familias)
    assert primera["aciertos"] == desglose.loc[al.TODAS, "aciertos"]   # semana 1 = lista fija


def test_foto_semanal_no_deja_deducir_conteos_pequenos():
    """Entre dos semanas publicadas siempre pagan 0 familias o al menos el mínimo."""
    # 10 casos; pagan 20 familias en la semana 1, 8 en la 2, 3 en la 3, 1 en la 4 y 6 en la 5
    dias = [np.nan] * 10 + [2] * 20 + [9] * 8 + [16] * 3 + [23] * 1 + [30] * 6
    familias = _a_mano([0] * 48, [1] * 10 + [0] * 38, dias)
    foto = al.foto_semanal(familias, {SEDE: 5}, SEMILLA, semanas=6, minimo=5)
    foto = foto.set_index("semana")
    assert foto["pendientes"].tolist() == [48, 28, 20, OCULTO, OCULTO, 10]
    # semana 4 (17 pendientes): pagaron 3 desde la 3 → oculta. La 5 (16) se compara con la 3,
    # la última publicada: pagaron 4 → también oculta. La 6 (10): pagaron 10 → se publica.
    publicadas = pd.to_numeric(foto["pendientes"], errors="coerce").dropna()
    pagaron = -publicadas.diff().dropna()
    assert ((pagaron == 0) | (pagaron >= 5)).all()
    assert foto.loc[[4, 5], ["tasa_base", "pct_pendientes", "recall_azar"]].isna().all().all()
    quedan = pd.to_numeric(foto["pagaran_en_plazo"], errors="coerce").dropna()
    assert ((quedan == 0) | (quedan >= 5)).all()


def test_presupuesto_semanal():
    assert al.presupuesto_semanal(118, 10) == [12] * 8 + [11] * 2
    assert sum(al.presupuesto_semanal(47, 10)) == 47
    assert al.presupuesto_semanal(3, 10) == [1, 1, 1] + [0] * 7


def test_campana(familias, k, tablas):
    total = tablas["campana"]
    total = total[total["cohorte"] == al.TODAS].set_index("estrategia")
    presupuesto = sum(k.values()) * familias["cohorte"].nunique()
    assert (total["cupos"] == presupuesto).all()
    assert (total["llamadas"] <= presupuesto).all()
    inicio, repartida, semanal = (total.loc[c] for c in ("fija_inicio_d2", "fija_repartida_d2",
                                                         "semanal_d2"))
    desglose = tablas["desglose"].set_index("cohorte")
    # la lista fija es la misma de la validación y se llama entera con todo el margen
    assert inicio["aciertos"] == desglose.loc[al.TODAS, "aciertos"]
    assert inicio["cupos_sin_usar"] == 0
    assert inicio["aciertos_primera_mitad"] == inicio["aciertos"]
    assert inicio["margen_medio_dias"] >= 69
    # repartirla no cambia a quién alcanza (los casos nunca dejan de estar pendientes)
    assert repartida["aciertos"] == inicio["aciertos"]
    assert repartida["cupos_sin_usar"] > 0
    # la semanal usa esos cupos y por construcción no alcanza menos casos
    assert semanal["aciertos"] >= repartida["aciertos"]
    assert semanal["cupos_sin_usar"] <= repartida["cupos_sin_usar"]
    assert semanal["margen_medio_dias"] < inicio["margen_medio_dias"]
    assert (total["aciertos_primera_mitad"] <= total["aciertos"]).all()
    assert (total["recall_min"] <= total["recall"]).all()
    assert (total["recall"] <= total["recall_max"]).all()


def test_campana_a_mano():
    """Cuatro familias, k = 2 y dos semanas: un contacto por semana."""
    # A paga antes de la semana 2; C y D son casos
    familias = _a_mano([100, 20, 5, 0], [0, 0, 1, 1], [3, 30, np.nan, np.nan], ventana=14)
    tabla = al.campana(familias, {SEDE: 2}, SEMILLA, semanas=2, repeticiones=1, minimo=1)
    total = tabla[tabla["cohorte"] == al.TODAS].set_index("estrategia")
    # el orden es A, B: ninguna es un caso, y B sigue pendiente cuando le toca
    for estrategia in ("fija_inicio_d2", "fija_repartida_d2", "semanal_d2"):
        assert total.loc[estrategia, ["llamadas", "aciertos"]].tolist() == [2, 0], estrategia

    # con B primero, a A le toca en la semana 2, cuando ya pagó
    invertida = familias.assign(score=[20.0, 100.0, 5.0, 0.0])
    tabla = al.campana(invertida, {SEDE: 2}, SEMILLA, semanas=2, repeticiones=1, minimo=1)
    total = tabla[tabla["cohorte"] == al.TODAS].set_index("estrategia")
    assert total.loc["fija_inicio_d2", ["llamadas", "aciertos", "cupos_sin_usar"]].tolist() == \
        [2, 0, 0]
    assert total.loc["fija_repartida_d2", ["llamadas", "cupos_sin_usar"]].tolist() == [1, 1]
    # la semanal salta a A y llama a C, que sí es un caso, con 7 días de margen
    assert total.loc["semanal_d2", ["llamadas", "aciertos", "cupos_sin_usar"]].tolist() == \
        [2, 1, 0]
    assert total.loc["semanal_d2", "margen_medio_dias"] == 7
    assert total.loc["semanal_d2", "aciertos_primera_mitad"] == 0


@pytest.mark.parametrize("semilla", range(8))
def test_la_lista_semanal_nunca_alcanza_menos_que_la_fija(semilla):
    """Con empates masivos: mismo orden, así que saltar a quien pagó no puede restar casos."""
    rng = np.random.default_rng(semilla)
    n = 80
    evento = (rng.random(n) < 0.25).astype(int)
    dias = np.where(evento == 1, np.nan, rng.integers(0, 69, n))
    familias = _a_mano(np.zeros(n), evento, dias)                 # todas empatadas
    tabla = al.campana(familias, {SEDE: 20}, semilla, repeticiones=3, minimo=1)
    total = tabla[tabla["cohorte"] == al.TODAS].set_index("estrategia")
    assert total.loc["semanal_d2", "aciertos"] >= total.loc["fija_repartida_d2", "aciertos"]
    assert total.loc["fija_repartida_d2", "aciertos"] == total.loc["fija_inicio_d2", "aciertos"]


# --------------------------------------------------------------------------- #
# Textos y figuras
# --------------------------------------------------------------------------- #
def _sin_basura(textos: dict) -> bool:
    return all("nan" not in frase.lower() and "oculto" not in frase and "<" not in frase
               for frases in textos.values() for frase in frases)


def test_conclusiones_y_figuras(tmp_path, tablas):
    from PIL import Image

    textos = al.conclusiones(*tablas.values())
    assert set(textos) == {"desglose", "por_k", "semanal", "campana"}
    assert all(textos.values()) and _sin_basura(textos)
    por_k = tablas["por_k"]
    total = por_k[(por_k["cohorte"] == al.TODAS) & (por_k["multiplicador"] == 1.0)].iloc[0]
    assert f"{round(100 * total['recall'])} %" in textos["por_k"][0]

    figuras = {"desglose": ga.figura_desglose(tablas["desglose"], "C1–C4"),
               "por_k": ga.figura_por_k(tablas["por_k"], "C1–C4"),
               "semanal": ga.figura_semanal(tablas["semanal"], "C1–C4"),
               "campana": ga.figura_campana(tablas["campana"], "C1–C4")}
    for nombre, figura in figuras.items():
        assert figura.legends, nombre
        ruta = ga.guardar(figura, tmp_path / f"{nombre}.png", dpi=300)
        assert round(Image.open(ruta).info["dpi"][0]) == 300, nombre


def test_conclusiones_dicen_la_verdad_cuando_la_regla_no_ayuda():
    """Si la regla ordena al revés, las frases no pueden decir que «añade»."""
    rng = np.random.default_rng(3)
    n = 400
    evento = (rng.random(n) < 0.2).astype(int)
    dias = np.where(evento == 1, np.nan, rng.integers(0, 69, n))
    al_reves = _a_mano(np.where(evento == 1, 0.0, 50.0), evento, dias)   # los casos, al final
    k = {SEDE: 60}
    tablas = [al.desglose_evento(al_reves, k, SEMILLA), al.alcance_por_k(al_reves, k, SEMILLA),
              al.foto_semanal(al_reves, k, SEMILLA), al.campana(al_reves, k, SEMILLA,
                                                                repeticiones=20)]
    textos = al.conclusiones(*tablas)
    aporte = next(f for f in textos["campana"] if f.startswith("Aporte de la regla"))
    assert "por debajo del azar" in aporte and "añade" not in aporte
    assert _sin_basura(textos)


def test_conclusiones_y_figuras_con_celdas_ocultas(tmp_path):
    """Con pocos datos casi todo queda oculto: no debe fallar ni escribir «nan»."""
    # 30 familias, 3 casos: los aciertos y el desglose quedan por debajo del mínimo
    dias = [np.nan] * 3 + [68] * 27                                   # casi todas pagan al final
    pocas = _a_mano([5, 0, 0] + [1] * 27, [1] * 3 + [0] * 27, dias)
    pocas.loc[0, "tipo"] = "tardia"
    k = {SEDE: 6}
    tablas = [al.desglose_evento(pocas, k, SEMILLA), al.alcance_por_k(pocas, k, SEMILLA),
              al.foto_semanal(pocas, k, SEMILLA), al.campana(pocas, k, SEMILLA, repeticiones=5)]
    assert tablas[0]["aciertos"].astype(str).str.contains("<5").any()
    textos = al.conclusiones(*tablas)
    assert _sin_basura(textos)
    for nombre, figura in (("desglose", ga.figura_desglose(tablas[0], "C2")),
                           ("por_k", ga.figura_por_k(tablas[1], "C2")),
                           ("semanal", ga.figura_semanal(tablas[2], "C2")),
                           ("campana", ga.figura_campana(tablas[3], "C2"))):
        ga.guardar(figura, tmp_path / f"{nombre}.png", dpi=72)


def test_figura_y_frases_con_aciertos_ocultos_y_casos_visibles(tmp_path):
    """Caso real del 03-oct: los casos por tipo se publican, pero algún acierto queda oculto."""
    # 40 pagan tarde (2 en la lista), 30 en parte, 60 sin pago; 400 pagan en plazo
    tipos = ["tardia"] * 40 + ["parcial"] * 30 + ["sin_pago"] * 60 + ["en_plazo"] * 400
    evento = [0 if t == "en_plazo" else 1 for t in tipos]
    riesgo = [9, 9] + [0] * 38 + [5] * 30 + [5] * 60 + [1] * 400
    familias = _a_mano(riesgo, evento, [np.nan] * len(tipos))
    familias["tipo"] = tipos
    familias["dias_tarde"] = [10.0 if t == "tardia" else np.nan for t in tipos]
    k = {SEDE: 60}
    desglose = al.desglose_evento(familias, k, SEMILLA)
    total = desglose.set_index("cohorte").loc[al.TODAS]
    assert total["tardia"] == 40 and total["aciertos_tardia"] == "<5"
    assert OCULTO in (total["aciertos_parcial"], total["aciertos_sin_pago"])
    figura = ga.figura_desglose(desglose, "C2")                 # antes: ValueError con NaN
    ga.guardar(figura, tmp_path / "desglose.png", dpi=72)
    notas = " ".join(t.get_text() for t in figura.axes[0].texts)
    assert "aciertos ocultos" in notas and "nan" not in notas.lower()
    textos = al.conclusiones(desglose, al.alcance_por_k(familias, k, SEMILLA),
                             al.foto_semanal(familias, k, SEMILLA),
                             al.campana(familias, k, SEMILLA, repeticiones=5))
    assert _sin_basura(textos)
