"""Pruebas del modo institucional (D45): Excel -> base seudonimizada -> lista con nombres.

Todas usan un Excel de ejemplo con personas ficticias (tools/generar_excel_ejemplo.py).
"""

import io
import json
from pathlib import Path

import pandas as pd
import pytest

from src.inferencia import (
    ErrorEntrada,
    ciclo_por_defecto,
    construir_poblacion,
    entrenar_sistema,
    lista_contactos,
    preparar_base,
    puntuar,
    validar_entrada,
)
from src.institucional import (
    es_equipo_local,
    leer_clave,
    lista_con_nombres,
    nueva_clave,
    seudonimizar_excel,
)
from src.utils import cargar_config
from tools import seudonimizar as seud
from tools.generar_excel_ejemplo import CLAVE_EJEMPLO, excel_ejemplo, tabla_ejemplo

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def config():
    return cargar_config()


@pytest.fixture(scope="module")
def clave():
    return leer_clave(CLAVE_EJEMPLO.encode())


@pytest.fixture(scope="module")
def tabla():
    return tabla_ejemplo()


@pytest.fixture(scope="module")
def excel(tabla):
    return excel_ejemplo(tabla)


@pytest.fixture(scope="module")
def resultado(excel, clave, config):
    return seudonimizar_excel(excel, "ejemplo_institucional.xlsx", clave, config)


@pytest.fixture(scope="module")
def lista_y_anio(resultado, config):
    base = preparar_base(pd.read_csv(io.BytesIO(resultado.csv), dtype=str), config)
    sistema = entrenar_sistema(base, config)
    anio = ciclo_por_defecto(base)
    poblacion, _ = construir_poblacion(base, anio, config)
    return lista_contactos(puntuar(poblacion, sistema), sistema.k_por_sede), anio


# --------------------------------------------------------------------------- #
# Clave
# --------------------------------------------------------------------------- #
def test_clave_nueva_es_valida_y_distinta():
    primera, segunda = nueva_clave(), nueva_clave()
    assert primera != segunda
    assert len(leer_clave(primera.encode())) == 32


@pytest.mark.parametrize("contenido", [b"", b"no es una clave", b"abcd", "ñ".encode("latin-1")])
def test_clave_invalida_da_mensaje_claro(contenido):
    with pytest.raises(ErrorEntrada, match="clave"):
        leer_clave(contenido)


def test_huella_de_clave_es_estable_y_no_revela_la_clave(clave):
    huella = seud.huella_clave(clave)
    assert huella == seud.huella_clave(clave)
    assert huella.replace("-", "") not in CLAVE_EJEMPLO
    assert huella != seud.huella_clave(leer_clave(nueva_clave().encode()))


# --------------------------------------------------------------------------- #
# Seudonimización del Excel
# --------------------------------------------------------------------------- #
def test_base_sin_identificadores_y_aceptada_por_la_app(resultado, tabla):
    base = resultado.base
    assert len(base) == len(tabla)
    for columna in ("CI", "cedulap", "Codigo", "Nombre Completo",
                    "Nombres completos padre de familia", "Orden"):
        assert columna not in base.columns
    assert seud.columnas_identificatorias(base) == []
    validar_entrada(base, "institucional")          # no lanza
    texto = resultado.csv.decode("utf-8")
    assert "Estudiante 0001" not in texto and "Representante 0001" not in texto
    assert tabla["CI"].iloc[0] not in texto


def test_seudonimos_coinciden_con_la_herramienta_del_cuaderno(resultado, tabla, clave):
    """La app y el cuaderno 00a producen los mismos códigos con la misma clave."""
    esperado_est = tabla["CI"].map(lambda v: seud.seudonimo(v, clave, "EST"))
    esperado_fam = tabla["cedulap"].map(lambda v: seud.seudonimo(v, clave, "FAM"))
    assert (resultado.base["id_seudonimo"].to_numpy() == esperado_est.to_numpy()).all()
    assert (resultado.base["id_familia_seudonimo"].to_numpy() == esperado_fam.to_numpy()).all()


def test_otra_clave_cambia_todos_los_seudonimos(excel, resultado, config):
    otro = seudonimizar_excel(excel, "e.xlsx", leer_clave(nueva_clave().encode()), config)
    assert not set(otro.base["id_seudonimo"]) & set(resultado.base["id_seudonimo"])
    assert otro.resumen["huella_clave"] != resultado.resumen["huella_clave"]


def test_acta_y_resumen(resultado):
    acta = resultado.acta
    assert acta["filas"] == resultado.resumen["filas"] == len(resultado.base)
    assert acta["huella_clave"] == resultado.resumen["huella_clave"]
    assert len(resultado.resumen["hojas"]) == 6
    json.dumps(acta)                                 # serializable
    assert "Representante" not in json.dumps(acta, ensure_ascii=False)


def test_elimina_columnas_identificatorias_no_previstas(tabla, clave, config):
    con_extra = tabla[tabla["hoja"] == tabla["hoja"].iloc[0]].head(50).assign(
        **{"Teléfono": "0990000000", "Correo electrónico": "x@ejemplo.ec"})
    salida = seudonimizar_excel(excel_ejemplo(con_extra), "e.xlsx", clave, config)
    assert "Teléfono" not in salida.base.columns
    assert "Correo electrónico" not in salida.base.columns
    assert {"Teléfono", "Correo electrónico"} <= set(salida.resumen["columnas_eliminadas"])


def test_excel_sin_columna_obligatoria(tabla, clave, config):
    sin_ci = tabla.head(20).drop(columns="CI")
    with pytest.raises(ErrorEntrada, match="CI"):
        seudonimizar_excel(excel_ejemplo(sin_ci), "e.xlsx", clave, config)


def test_archivo_que_no_es_excel(clave, config):
    with pytest.raises(ErrorEntrada, match="No se pudo leer"):
        seudonimizar_excel(b"esto no es un excel", "e.xlsx", clave, config)


# --------------------------------------------------------------------------- #
# Lista con nombres
# --------------------------------------------------------------------------- #
def test_lista_con_nombres_identifica_a_la_familia_correcta(resultado, lista_y_anio, clave):
    lista, anio = lista_y_anio
    nombres = lista_con_nombres(lista, resultado.padron, anio)
    assert len(nombres) == len(lista)
    assert nombres["representante"].notna().all()
    assert nombres["estudiantes"].str.contains("Estudiante").all()
    # El seudónimo recalculado desde la cédula mostrada es el de la lista
    recalculado = nombres["cedula_representante"].map(lambda v: seud.seudonimo(v, clave, "FAM"))
    normales = ~nombres["id_familia"].str.startswith("IND-")
    assert (recalculado[normales] == nombres.loc[normales, "id_familia"]).all()
    assert list(nombres["puesto"]) == list(lista["puesto"])


def test_lista_con_nombres_avisa_cedula_compartida(resultado, lista_y_anio):
    lista, anio = lista_y_anio
    fila = lista.head(1).copy()
    fila["id_familia"] = "IND-" + fila["estudiantes_ids"].str.split(",").str[0]
    nombres = lista_con_nombres(fila, resultado.padron, anio)
    assert "compartida" in nombres["observacion"].iloc[0]


def test_lista_con_nombres_estudiante_inexistente(resultado, lista_y_anio):
    lista, anio = lista_y_anio
    fila = lista.head(1).assign(estudiantes_ids="EST-NOEXISTE0000")
    nombres = lista_con_nombres(fila, resultado.padron, anio)
    assert "no encontrado" in nombres["observacion"].iloc[0]
    assert pd.isna(nombres["representante"].iloc[0])


# --------------------------------------------------------------------------- #
# Seguridad: equipo local e interfaz
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("host,esperado", [
    ("localhost:8501", True), ("127.0.0.1:8501", True), ("LOCALHOST", True),
    ("[::1]:8501", True), (None, True), ("", True),
    ("192.168.1.20:8501", False), ("continuidad-matricula-lemas.streamlit.app", False),
    ("localhost.evil.com", False)])
def test_es_equipo_local(host, esperado):
    assert es_equipo_local(host) is esperado


def test_linea_de_comandos_sigue_funcionando(tmp_path, excel):
    """La refactorización no cambia el uso desde el cuaderno 00a."""
    entrada, clave, salida = tmp_path / "base.xlsx", tmp_path / "c.key", tmp_path / "s.csv"
    entrada.write_bytes(excel)
    assert seud.main(["generar-clave", "--salida", str(clave)]) == 0
    assert seud.main(["seudonimizar", "--entrada", str(entrada), "--salida", str(salida),
                      "--clave", str(clave), "--col-estudiante", "CI",
                      "--col-familia", "cedulap", "--derivar-anio-ingreso",
                      "--col-codigo", "Codigo", "--eliminar", "Codigo", "Orden",
                      "Nombre Completo", "Nombres completos padre de familia"]) == 0
    base = pd.read_csv(salida, dtype=str)
    assert {"id_seudonimo", "id_familia_seudonimo", "anio_ingreso"} <= set(base.columns)
    acta = json.loads(salida.with_suffix(".acta.json").read_text("utf-8"))
    assert acta["filas"] == len(base)
    # reidentificación por línea de comandos
    lista = base[["id_familia_seudonimo"]].drop_duplicates().head(5)
    lista.to_csv(tmp_path / "lista.csv", index=False)
    assert seud.main(["reidentificar", "--entrada", str(tmp_path / "lista.csv"),
                      "--padron", str(entrada), "--clave", str(clave),
                      "--col-seudonimo", "id_familia_seudonimo", "--col-padron", "cedulap",
                      "--tipo", "FAM", "--salida", str(tmp_path / "interno.csv")]) == 0
    interno = pd.read_csv(tmp_path / "interno.csv", dtype=str)
    assert interno["Nombres completos padre de familia"].notna().all()


def _app(monkeypatch, modo):
    from streamlit.testing.v1 import AppTest

    if modo:
        monkeypatch.setenv("LEMAS_MODO", modo)
    else:
        monkeypatch.delenv("LEMAS_MODO", raising=False)
    return AppTest.from_file(str(RAIZ / "app/app.py"), default_timeout=180)


def test_interfaz_demo_no_ofrece_excel_ni_nombres(monkeypatch):
    app = _app(monkeypatch, None)
    app.run()
    app.sidebar.button[0].click().run()               # "Prueba con ejemplo"
    assert not app.exception
    assert "🪪 Lista con nombres" not in [t.label for t in app.tabs]
    assert not any("Borrar datos" in b.label for b in app.button)
    assert not any("LEMAS aún no tiene clave" in e.label for e in app.expander)


def test_interfaz_institucional_muestra_nombres_solo_tras_confirmar(monkeypatch, resultado):
    app = _app(monkeypatch, "institucional")
    app.session_state["institucional"] = resultado      # equivale a subir Excel + clave
    app.session_state["contenido"] = resultado.csv
    app.session_state["origen"] = "ejemplo_institucional.xlsx (seudonimizado aquí)"
    app.run()
    assert not app.exception
    assert "🪪 Lista con nombres" in [t.label for t in app.tabs]
    next(b for b in app.button if b.label == "Generar lista").click().run()
    assert not app.exception

    def tablas_con_nombres():
        return [d for d in app.dataframe if "Representante" in d.value.columns]

    assert not tablas_con_nombres()                     # aún no confirmó
    next(c for c in app.checkbox if "autorizado" in c.label).check().run()
    assert not app.exception
    tabla = tablas_con_nombres()[0].value
    assert tabla["Representante"].str.startswith("Representante").all()

    next(b for b in app.button if "Borrar datos" in b.label).click().run()
    assert not app.exception
    assert "institucional" not in app.session_state
    assert "contenido" not in app.session_state


def test_interfaz_institucional_sin_excel_no_muestra_nombres(monkeypatch):
    app = _app(monkeypatch, "institucional")
    app.run()
    app.sidebar.button[0].click().run()                 # ejemplo sintético (sin nombres)
    next(b for b in app.button if b.label == "Generar lista").click().run()
    assert not app.exception
    assert not any("autorizado" in c.label for c in app.checkbox)
    assert any("no es" in i.value and "posible" in i.value for i in app.info)
