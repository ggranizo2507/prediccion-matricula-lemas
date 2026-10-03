"""Pruebas de la aplicación: lógica de inferencia y recorrido de la interfaz."""

import sys
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
    seguimiento_al_corte,
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


# --------------------------------------------------------------------------- #
# Seguimiento a una fecha de corte (D51)
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def ciclo_con_pagos(preparado, config):
    """Último ciclo que ya tiene la hoja del ciclo siguiente, con sus familias puntuadas."""
    base, sistema = preparado
    anio = ciclo_por_defecto(base) - 1
    poblacion, _ = construir_poblacion(base, anio, config)
    return base, sistema, anio, puntuar(poblacion, sistema)


def test_seguimiento_en_t0_es_toda_la_poblacion_y_marca_la_lista_inicial(ciclo_con_pagos, config):
    base, sistema, anio, puntuados = ciclo_con_pagos
    inicial = lista_contactos(puntuados, sistema.k_por_sede, 42)
    sin_destino = base[base["anio_origen"] != anio + 1]      # nadie ha pagado todavía
    lista, cifras = seguimiento_al_corte(sin_destino, puntuados, anio, f"{anio + 1}-02-20",
                                         sistema.k_por_sede, config, 42)
    assert cifras["familias_pendientes"] == cifras["familias_t0"]
    assert cifras["familias_t0"] == puntuados["id_familia"].nunique()
    assert cifras["familias_pagaron"] == 0 and cifras["dias_desde_t0"] == 0
    assert set(lista.loc[lista["en_lista_inicial"], "id_familia"]) == set(inicial["id_familia"])
    # mismo orden que la lista del 20 de febrero: las primeras k son las mismas, en orden
    for sede, k in sistema.k_por_sede.items():
        primeras = lista[lista["sede"] == sede].head(k)["id_familia"].tolist()
        assert primeras == inicial[inicial["sede"] == sede]["id_familia"].tolist()


def test_seguimiento_lista_solo_a_quien_sigue_sin_pagar(ciclo_con_pagos, config):
    base, sistema, anio, puntuados = ciclo_con_pagos
    corte = pd.Timestamp(year=anio + 1, month=3, day=20)
    lista, cifras = seguimiento_al_corte(base, puntuados, anio, corte, sistema.k_por_sede,
                                         config, 42)
    pagos = base[base["anio_origen"] == anio + 1].set_index("id_estudiante")["fecha_pago"]
    fecha = puntuados["id_estudiante"].map(pagos)
    sin_pago = puntuados[~(fecha <= corte).fillna(False).to_numpy()]
    assert set(lista["id_familia"]) == set(sin_pago["id_familia"])
    assert 0 < cifras["familias_pendientes"] < cifras["familias_t0"]
    assert cifras["familias_pendientes"] + cifras["familias_pagaron"] == cifras["familias_t0"]
    assert lista["id_familia"].is_unique
    # solo se nombran los estudiantes que siguen sin pago
    nombrados = {i for ids in lista["estudiantes_ids"] for i in ids.split(", ")}
    assert nombrados == set(sin_pago["id_estudiante"])
    assert lista["estudiantes"].sum() == len(sin_pago)
    # puestos consecutivos por sede y ninguna probabilidad por familia (D49)
    for _, grupo in lista.groupby("sede"):
        assert grupo["puesto"].tolist() == list(range(1, len(grupo) + 1))
    assert "prob_no_matricula" not in lista.columns
    assert cifras["pendientes_fuera_de_lista_inicial"] == int((~lista["en_lista_inicial"]).sum())


def test_seguimiento_se_reduce_con_el_tiempo_y_no_altera_la_lista_inicial(ciclo_con_pagos, config):
    base, sistema, anio, puntuados = ciclo_con_pagos
    antes = lista_contactos(puntuados, sistema.k_por_sede, 42)
    pendientes = []
    for dia in (0, 14, 28, 42, 69):
        corte = pd.Timestamp(year=anio + 1, month=2, day=20) + pd.Timedelta(days=dia)
        _, cifras = seguimiento_al_corte(base, puntuados, anio, corte, sistema.k_por_sede,
                                         config, 42)
        pendientes.append(cifras["familias_pendientes"])
    assert pendientes == sorted(pendientes, reverse=True) and pendientes[-1] < pendientes[0]
    pd.testing.assert_frame_equal(antes, lista_contactos(puntuados, sistema.k_por_sede, 42))


def test_seguimiento_cuenta_el_pago_del_dia_del_corte(ciclo_con_pagos, config):
    """Un pago registrado el mismo día del corte ya no está pendiente (como en la etiqueta)."""
    base, sistema, anio, puntuados = ciclo_con_pagos
    pagos = base[base["anio_origen"] == anio + 1].set_index("id_estudiante")["fecha_pago"]
    fecha = puntuados["id_estudiante"].map(pagos)
    t0 = pd.Timestamp(year=anio + 1, month=2, day=20)
    cierre = pd.Timestamp(year=anio + 1, month=4, day=30)
    corte = fecha[(fecha > t0) & (fecha <= cierre)].mode().iloc[0]     # día con más pagos
    lista, _ = seguimiento_al_corte(base, puntuados, anio, corte, sistema.k_por_sede,
                                    config, 42)
    ese_dia = set(puntuados.loc[(fecha == corte).to_numpy(), "id_estudiante"])
    nombrados = {i for ids in lista["estudiantes_ids"] for i in ids.split(", ")}
    assert ese_dia and not ese_dia & nombrados
    # en el cierre, las pendientes son exactamente las familias con el evento
    al_cierre, _ = seguimiento_al_corte(base, puntuados, anio, cierre, sistema.k_por_sede,
                                        config, 42)
    con_evento = puntuados[~fecha.between(t0, cierre).fillna(False).to_numpy()]
    assert set(al_cierre["id_familia"]) == set(con_evento["id_familia"])


def test_seguimiento_avisa_de_estudiantes_sin_representante(ciclo_con_pagos, config):
    base, sistema, anio, puntuados = ciclo_con_pagos
    corte = pd.Timestamp(year=anio + 1, month=3, day=20)
    lista, cifras = seguimiento_al_corte(base, puntuados, anio, corte, sistema.k_por_sede,
                                         config, 42)
    assert cifras["pendientes_sin_representante"] == 0
    pendiente = lista["estudiantes_ids"].iloc[0].split(", ")[0]
    sin_familia = puntuados.copy()
    sin_familia.loc[sin_familia["id_estudiante"] == pendiente, "id_familia"] = pd.NA
    _, cifras = seguimiento_al_corte(base, sin_familia, anio, corte, sistema.k_por_sede,
                                     config, 42)
    assert cifras["pendientes_sin_representante"] == 1


@pytest.mark.parametrize("fecha", ["02-19", "05-01"])
def test_seguimiento_rechaza_fechas_fuera_de_la_campana(ciclo_con_pagos, config, fecha):
    base, sistema, anio, puntuados = ciclo_con_pagos
    with pytest.raises(ErrorEntrada, match="fecha de corte"):
        seguimiento_al_corte(base, puntuados, anio, f"{anio + 1}-{fecha}", sistema.k_por_sede,
                             config, 42)


def test_seguimiento_sin_hoja_del_ciclo_siguiente_avisa_con_cero_pagos(preparado, config):
    base, sistema = preparado
    anio = ciclo_por_defecto(base)
    poblacion, _ = construir_poblacion(base, anio, config)
    puntuados = puntuar(poblacion, sistema)
    lista, cifras = seguimiento_al_corte(base, puntuados, anio, f"{anio + 1}-03-20",
                                         sistema.k_por_sede, config, 42)
    assert cifras["pagos_desde_t0"] == 0 and cifras["ultimo_pago_registrado"] is None
    assert len(lista) == cifras["familias_t0"]


def test_interfaz_seguimiento():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(RAIZ / "app/app.py"), default_timeout=120)
    app.run()
    app.sidebar.button[0].click().run()
    next(b for b in app.button if b.label == "Generar lista").click().run()
    assert not app.exception
    # con el ejemplo, el último ciclo aún no tiene pagos del ciclo siguiente: se avisa
    assert any("no registra pagos" in aviso.value for aviso in app.warning)
    ciclo = app.sidebar.selectbox[0]
    ciclo.set_value(ciclo.value - 1).run()      # un ciclo que ya tiene pagos del siguiente
    assert not app.exception
    cifras = {m.label: int(str(m.value).replace(".", "")) for m in app.metric
              if m.label in ("Familias al 20 de febrero", "Ya pagaron", "Siguen sin pagar")}
    assert 0 < cifras["Siguen sin pagar"] < cifras["Familias al 20 de febrero"]
    assert cifras["Ya pagaron"] + cifras["Siguen sin pagar"] == cifras["Familias al 20 de febrero"]
    assert not any("no registra pagos" in aviso.value for aviso in app.warning)
    # el listado no muestra probabilidades por familia
    for tabla in app.dataframe:
        assert not any("prob" in str(c).lower() for c in tabla.value.columns
                       if "Familia" in " ".join(map(str, tabla.value.columns)))


def test_interfaz_recarga_los_modulos_que_cambiaron_en_disco(monkeypatch):
    """Tras una actualización, `app.py` nuevo no debe quedarse con `src/` viejo (03-oct-2026)."""
    from streamlit.testing.v1 import AppTest

    originales = {n: m for n, m in sys.modules.items() if n.split(".")[0] in ("src", "tools")}
    try:
        app = AppTest.from_file(str(RAIZ / "app/app.py"), default_timeout=120)
        app.run()
        viejo = sys.modules["src.inferencia"]
        # módulo en memoria con la firma anterior y una fecha de archivo que ya no coincide
        monkeypatch.setattr(viejo, "lista_contactos", lambda puntuados, k_por_sede: None)
        monkeypatch.setattr(viejo, "_lemas_fecha_archivo", 1)
        app.sidebar.button[0].click().run()
        next(b for b in app.button if b.label == "Generar lista").click().run()
        assert not app.exception
        assert sys.modules["src.inferencia"] is not viejo
        assert any("Familias a contactar" in m.label for m in app.metric)
    finally:
        for nombre in [n for n in sys.modules if n.split(".")[0] in ("src", "tools")]:
            del sys.modules[nombre]
        sys.modules.update(originales)


@pytest.mark.skipif(not Path("/proc/stat").exists(), reason="la hora de arranque se lee de /proc")
def test_interfaz_recarga_modulos_cargados_antes_de_la_revision(monkeypatch, tmp_path):
    """El caso del 03-oct: módulo sin marca cuyo archivo es posterior al arranque del proceso."""
    from streamlit.testing.v1 import AppTest

    originales = {n: m for n, m in sys.modules.items() if n.split(".")[0] in ("src", "tools")}
    try:
        app = AppTest.from_file(str(RAIZ / "app/app.py"), default_timeout=120)
        app.run()
        viejo = sys.modules["src.inferencia"]
        reciente = tmp_path / "inferencia.py"       # archivo «actualizado» tras el arranque
        reciente.write_text("# nueva versión\n", "utf-8")
        monkeypatch.setattr(viejo, "__file__", str(reciente))
        monkeypatch.delattr(viejo, "_lemas_fecha_archivo")
        monkeypatch.setattr(viejo, "lista_contactos", lambda puntuados, k_por_sede: None)
        app.sidebar.button[0].click().run()
        next(b for b in app.button if b.label == "Generar lista").click().run()
        assert not app.exception
        assert sys.modules["src.inferencia"] is not viejo
    finally:
        for nombre in [n for n in sys.modules if n.split(".")[0] in ("src", "tools")]:
            del sys.modules[nombre]
        sys.modules.update(originales)


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
