"""
Aplicación Streamlit · Priorización de contacto y proyección de matrícula (LEMAS).

Ejecutar desde la raíz del repositorio:
    streamlit run app/app.py                         # modo demo (datos sintéticos)
    LEMAS_MODO=institucional streamlit run app/app.py --server.address 127.0.0.1
                                                     # solo dentro de LEMAS (iniciar_lemas.bat)

Diseño de dos modos aprobado el 01-oct-2026 (D42): la versión pública nunca recibe
datos reales. En modo institucional (D45) la aplicación también seudonimiza el Excel de
LEMAS y muestra la lista con nombres, siempre en el mismo equipo y sin guardar nada.
Ver docs/arquitectura.md y docs/manual_usuario.md.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

PAQUETES_PROPIOS = ("src", "tools")
MARCA = "_lemas_fecha_archivo"


def _inicio_del_proceso() -> float | None:
    """Hora en que arrancó el proceso (solo Linux, que es donde corre la versión pública)."""
    try:
        campos = Path(f"/proc/{os.getpid()}/stat").read_text().rsplit(")", 1)[1].split()
        arranque = next(int(linea.split()[1])
                        for linea in Path("/proc/stat").read_text().splitlines()
                        if linea.startswith("btime"))
        return arranque + int(campos[19]) / os.sysconf("SC_CLK_TCK")
    except (OSError, ValueError, IndexError, StopIteration, AttributeError):
        return None


def descartar_modulos_viejos() -> bool:
    """Si el código de `src/` o `tools/` cambió en disco, obliga a importarlo de nuevo.

    Streamlit vuelve a leer este archivo en cada ejecución, pero conserva en memoria los
    módulos importados. Tras una actualización del repositorio, la aplicación podía quedar
    con `app.py` nuevo y `src/` viejo, y fallar al llamar una función con otros argumentos
    (03-oct-2026). Cada módulo cargado lleva anotada la fecha de su archivo; si no coincide
    con la del disco, se descartan todos los módulos propios y las cachés.
    """
    cargados = {nombre: modulo for nombre, modulo in list(sys.modules.items())
                if nombre.split(".")[0] in PAQUETES_PROPIOS}
    viejo = False
    for modulo in cargados.values():
        ruta = getattr(modulo, "__file__", None)
        if not ruta:
            continue
        try:
            en_disco = Path(ruta).stat().st_mtime_ns
        except OSError:
            viejo = True
            break
        anotada = getattr(modulo, MARCA, None)
        if anotada is None:     # cargado antes de existir esta revisión
            inicio = _inicio_del_proceso()
            if inicio is not None and en_disco / 1e9 > inicio:
                viejo = True
                break
        elif anotada != en_disco:
            viejo = True
            break
    if viejo:
        for nombre in cargados:
            sys.modules.pop(nombre, None)
        st.cache_data.clear()
        st.cache_resource.clear()
    return viejo


def anotar_modulos() -> None:
    """Anota en cada módulo propio la fecha del archivo con que se cargó."""
    for nombre, modulo in list(sys.modules.items()):
        ruta = getattr(modulo, "__file__", None)
        if nombre.split(".")[0] in PAQUETES_PROPIOS and ruta and not hasattr(modulo, MARCA):
            try:
                setattr(modulo, MARCA, Path(ruta).stat().st_mtime_ns)
            except OSError:
                pass


descartar_modulos_viejos()

from src.inferencia import (  # noqa: E402
    RUTA_SISTEMA_REAL,
    ErrorEntrada,
    cargar_sistema_congelado,
    ciclo_por_defecto,
    construir_poblacion,
    entrenar_sistema,
    estimar_estudiante,
    lista_contactos,
    modo_actual,
    preparar_base,
    proyeccion_actual,
    puntuar,
    seguimiento_al_corte,
    validar_entrada,
)
from src.institucional import (  # noqa: E402
    es_equipo_local,
    leer_clave,
    lista_con_nombres,
    nueva_clave,
    seudonimizar_excel,
)
from src.utils import cargar_config  # noqa: E402

anotar_modulos()

COLOR = "#8B1E3F"
COLOR_SUAVE = "#9DB4C9"
st.set_page_config(page_title="Matrícula LEMAS · Priorización", page_icon="🎓", layout="wide")

CONFIG = cargar_config(RAIZ / "config.yaml")
MODO = modo_actual()


def _host() -> str | None:
    try:
        return st.context.headers.get("Host")
    except Exception:   # sin navegador (pruebas automáticas)
        return None


# Excel institucional, clave y nombres: solo en modo institucional y en el mismo equipo
LOCAL = es_equipo_local(_host())
INSTITUCIONAL = MODO == "institucional"
RESULTADOS = json.loads((RAIZ / "app/assets/resultados_validacion.json").read_text("utf-8"))


# --------------------------------------------------------------------------- #
# Carga y procesamiento (en memoria; nada se guarda en disco)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def leer_csv(contenido: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(contenido), dtype=str)


@st.cache_resource(show_spinner=False)
def preparar(huella: str, contenido: bytes):
    """Limpia la base y obtiene el sistema (congelado si existe; si no, reentrena)."""
    del huella  # solo identifica el archivo en la caché
    df = leer_csv(contenido)
    validar_entrada(df, MODO)
    base = preparar_base(df, CONFIG)
    sistema = None
    if MODO == "institucional":
        sistema = cargar_sistema_congelado(RAIZ / RUTA_SISTEMA_REAL)
    if sistema is None:
        sistema = entrenar_sistema(base, CONFIG)
    return base, sistema


def bytes_ejemplo() -> bytes:
    return (RAIZ / CONFIG["rutas"]["base_sintetica"]).read_bytes()


def usar_datos(contenido: bytes, origen: str, institucional=None) -> None:
    """Cambia la fuente de datos de la sesión. La última acción del usuario manda."""
    for clave in ("generar", "puntuados", "lista", "institucional"):
        st.session_state.pop(clave, None)
    if institucional is not None:
        st.session_state["institucional"] = institucional
    st.session_state["contenido"] = contenido
    st.session_state["origen"] = origen


def borrar_sesion() -> None:
    """Descarta de la memoria el Excel, la clave, el padrón y los resultados."""
    reinicio = st.session_state.get("reinicio", 0) + 1
    st.session_state.clear()
    st.cache_data.clear()
    st.cache_resource.clear()
    st.session_state["reinicio"] = reinicio   # vacía también los cuadros de carga


# --------------------------------------------------------------------------- #
# Encabezado y barra lateral
# --------------------------------------------------------------------------- #
st.title("🎓 Continuidad estudiantil · Unidad Educativa LEMAS")
st.caption("Priorización de contacto a familias con reserva aprobada y proyección de matrícula "
           "al corte del 20 de febrero.")
if MODO == "demo":
    st.info("**Modo demostración.** Solo acepta datos **sintéticos**: ningún resultado describe "
            "a estudiantes reales. Los datos de LEMAS se procesan únicamente en el modo "
            "institucional, dentro de la institución.", icon="🧪")
elif LOCAL:
    st.warning("**Modo institucional.** Todo se procesa **en este equipo** y nada se guarda: "
               "el Excel se convierte aquí en la base seudonimizada y el sistema trabaja solo "
               "con seudónimos. Los nombres aparecen únicamente en las pestañas **Lista con "
               "nombres** y **Seguimiento**, tras confirmar, para uso interno de LEMAS.", icon="🔒")
else:
    st.error("**Modo institucional abierto desde otro equipo.** Por seguridad, la carga del "
             "Excel con cédulas y la lista con nombres solo funcionan en el mismo computador "
             "donde se ejecuta la aplicación (inicie con `iniciar_lemas.bat`). Desde aquí "
             "solo se acepta la base ya seudonimizada.", icon="⛔")

REINICIO = st.session_state.get("reinicio", 0)
with st.sidebar:
    st.header("1 · Datos")
    if INSTITUCIONAL and LOCAL:
        st.markdown("**Excel institucional y clave**")
        excel = st.file_uploader(
            "Excel de LEMAS (.xlsx)", type=["xlsx", "xls"], key=f"excel_{REINICIO}",
            help="El archivo de siempre: una hoja por ciclo, con cédulas y nombres. Se "
                 "seudonimiza en este equipo y no se guarda.")
        archivo_clave = st.file_uploader(
            "Clave del custodio (.key)", type=["key", "txt"], key=f"clave_{REINICIO}",
            help="El archivo clave_lemas.key que guarda el custodio. Use siempre la misma.")
        if excel is not None and archivo_clave is not None:
            firma = hashlib.sha256(excel.getvalue() + archivo_clave.getvalue()).hexdigest()
            if st.session_state.get("visto_excel") != firma:   # archivos nuevos: procesar
                st.session_state["visto_excel"] = firma
                st.session_state.pop("error_excel", None)
                try:
                    with st.spinner("Seudonimizando en este equipo…"):
                        resultado = seudonimizar_excel(
                            excel.getvalue(), excel.name,
                            leer_clave(archivo_clave.getvalue()), CONFIG)
                except ErrorEntrada as error:
                    st.session_state["error_excel"] = str(error)
                except Exception:   # sin detalles técnicos ni datos en pantalla
                    st.session_state["error_excel"] = (
                        "No se pudo procesar el Excel. Revise que tenga una hoja por ciclo "
                        "con los encabezados acordados (ver manual de usuario).")
                else:
                    usar_datos(resultado.csv, f"{excel.name} (seudonimizado aquí)", resultado)
            if "error_excel" in st.session_state:
                st.error(st.session_state["error_excel"])
        else:
            st.session_state.pop("visto_excel", None)
            st.session_state.pop("error_excel", None)
            if excel is not None or archivo_clave is not None:
                st.caption("Se necesitan los dos archivos: el Excel y la clave.")
        with st.expander("¿LEMAS aún no tiene clave?"):
            st.caption("Solo la **primera vez**. Si ya existe una clave, úsela siempre: con una "
                       "clave distinta los seudónimos cambian y las listas anteriores no se "
                       "pueden cruzar ni identificar.")
            if st.checkbox("Confirmo que LEMAS todavía no tiene una clave",
                           key=f"sin_clave_{REINICIO}"):
                st.session_state.setdefault("clave_nueva", nueva_clave())
                st.download_button("⬇️ Descargar clave nueva",
                                   st.session_state["clave_nueva"].encode("utf-8"),
                                   file_name="clave_lemas.key", mime="text/plain")
                st.caption("Entréguela al custodio, guarde un respaldo y luego súbala arriba. "
                           "Nunca la envíe por correo ni la suba a internet.")
        st.divider()
    if st.button("▶️ Prueba con ejemplo", use_container_width=True,
                 help="Carga la base sintética incluida en el repositorio."):
        usar_datos(bytes_ejemplo(), "Ejemplo sintético")
    archivo = st.file_uploader(
        "…o suba la base (CSV)" if not INSTITUCIONAL else "…o suba base_seud.csv",
        type=["csv"], key=f"csv_{REINICIO}",
        help="Estructura de base_seud.csv (ver manual). Sin cédulas, nombres ni códigos.")
    if archivo is None:
        st.session_state.pop("visto_csv", None)
    else:
        firma_csv = hashlib.sha256(archivo.getvalue()).hexdigest()
        if st.session_state.get("visto_csv") != firma_csv:   # archivo nuevo: usarlo
            st.session_state["visto_csv"] = firma_csv
            usar_datos(archivo.getvalue(), archivo.name)
    if "contenido" in st.session_state:
        st.success(f"Datos: {st.session_state['origen']}")
    if INSTITUCIONAL:
        st.button("🧹 Borrar datos de la sesión", on_click=borrar_sesion,
                  use_container_width=True,
                  help="Descarta de la memoria el Excel, la clave, los nombres y los "
                       "resultados. Úselo al terminar.")

contenido = st.session_state.get("contenido")
if contenido is None:
    st.markdown("### ¿Cómo empezar?")
    if INSTITUCIONAL and LOCAL:
        st.markdown(
            "1. En la barra lateral suba el **Excel de LEMAS** y la **clave del custodio**. "
            "La aplicación lo seudonimiza en este equipo.\n"
            "2. Elija el ciclo y revise el número de familias a contactar por sede (k).\n"
            "3. Pulse **Generar lista**.\n"
            "4. Abra la pestaña **Lista con nombres** para ver a quién contactar.\n"
            "5. Al terminar, pulse **Borrar datos de la sesión** y cierre la aplicación.\n\n"
            "Para practicar sin datos reales use **▶️ Prueba con ejemplo**.")
    else:
        st.markdown(
            "1. Pulse **▶️ Prueba con ejemplo** en la barra lateral (o suba una base).\n"
            "2. Elija el ciclo y revise el número de familias a contactar por sede (k).\n"
            "3. Pulse **Generar lista** y descargue el resultado.\n\n"
            "La pestaña **Acerca de** resume cómo se validó el sistema y sus limitaciones.")
    st.stop()

try:
    with st.spinner("Validando y preparando los datos…"):
        BASE, SISTEMA = preparar(hashlib.sha256(contenido).hexdigest(), contenido)
except ErrorEntrada as error:
    st.error(f"No se pudo usar el archivo: {error}")
    st.stop()
except Exception:   # mensaje amable, sin detalles técnicos para el usuario final
    st.error("El archivo no tiene la estructura esperada. Revise el manual de usuario "
             "(columnas obligatorias y formato de fechas) e intente de nuevo.")
    st.stop()

DATOS_INSTITUCIONALES = st.session_state.get("institucional") if INSTITUCIONAL and LOCAL else None
if DATOS_INSTITUCIONALES is not None:
    cifras = DATOS_INSTITUCIONALES.resumen
    with st.expander(f"🔐 Excel seudonimizado en este equipo · {cifras['filas']:,} filas · "
                     f"huella de la clave {cifras['huella_clave']}".replace(",", ".")):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Hojas (ciclos)", len(cifras["hojas"]))
        m2.metric("Estudiantes", f"{cifras['estudiantes']:,}".replace(",", "."))
        m3.metric("Representantes", f"{cifras['familias']:,}".replace(",", "."))
        m4.metric("Huella de la clave", cifras["huella_clave"],
                  help="Debe ser la misma cada año. Si cambia, se usó otra clave.")
        st.markdown("✅ Verificado: la base de trabajo **no contiene nombres ni cédulas**. "
                    f"Columnas eliminadas: {', '.join(cifras['columnas_eliminadas'])}.")
        if cifras["sin_cedula_estudiante"] or cifras["sin_cedula_representante"]:
            st.warning(f"{cifras['sin_cedula_estudiante']} filas sin cédula de estudiante y "
                       f"{cifras['sin_cedula_representante']} sin cédula de representante. "
                       "Las filas sin cédula de estudiante no entran al análisis.")
        d1, d2 = st.columns(2)
        d1.download_button("⬇️ base_seud.csv (seudónimos)", DATOS_INSTITUCIONALES.csv,
                           file_name="base_seud.csv", mime="text/csv",
                           help="La misma base que genera el cuaderno 00a.")
        d2.download_button("⬇️ Acta de extracción", json.dumps(
            DATOS_INSTITUCIONALES.acta, indent=2, ensure_ascii=False).encode("utf-8"),
            file_name="base_seud.acta.json", mime="application/json")

with st.sidebar:
    st.header("2 · Parámetros")
    anios = sorted(BASE["anio_origen"].dropna().astype(int).unique())
    anio = st.selectbox("Ciclo de origen", anios, index=anios.index(ciclo_por_defecto(BASE)),
                        format_func=lambda a: f"{a}-{a + 1} (corte 20-feb-{a + 1})",
                        help="Ciclo cuyas reservas aprobadas se van a priorizar.")
    st.markdown("**Familias a contactar (k)**")
    k_editado = {}
    for sede, k in SISTEMA.k_por_sede.items():
        k_editado[sede] = st.number_input(
            sede, min_value=1, max_value=2000, value=int(k), step=1,
            help="Valor aprobado: 2 × el promedio histórico (ciclos de entrenamiento) de "
                 "familias con no matrícula. Representa la capacidad de contacto de la sede, "
                 "por eso no cambia al elegir otro ciclo; ajústelo si cambia el personal.")
    st.caption("k es la capacidad de contacto: se calcula una vez con los ciclos de "
               "entrenamiento y no depende del ciclo elegido.")
    if anio != ciclo_por_defecto(BASE):
        st.warning("Ciclo histórico: el resultado es retrospectivo. Los ciclos de "
                   "entrenamiento y selección ya se usaron para ajustar el sistema, así que "
                   "no equivale a una predicción nueva.", icon="🕰️")
    st.caption(SISTEMA.descripcion)

if INSTITUCIONAL:   # la pestaña con nombres no existe en la versión pública
    tab_lista, tab_nombres, tab_seguimiento, tab_proy, tab_estudiante, tab_acerca = st.tabs(
        ["📋 Lista de contactos", "🪪 Lista con nombres", "📅 Seguimiento", "📈 Proyección",
         "🧑‍🎓 Evaluar un estudiante", "ℹ️ Acerca de"])
else:
    tab_nombres = None
    tab_lista, tab_seguimiento, tab_proy, tab_estudiante, tab_acerca = st.tabs(
        ["📋 Lista de contactos", "📅 Seguimiento", "📈 Proyección",
         "🧑‍🎓 Evaluar un estudiante", "ℹ️ Acerca de"])

# --------------------------------------------------------------------------- #
# Lista de contactos
# --------------------------------------------------------------------------- #
with tab_lista:
    if st.button("Generar lista", type="primary"):
        st.session_state["generar"] = True
    if st.session_state.get("generar"):
        with st.spinner("Calculando prioridades…"):
            poblacion, resumen = construir_poblacion(BASE, anio, CONFIG)
            if poblacion.empty:
                st.warning("Ese ciclo no tiene estudiantes con reserva aprobada antes del corte.")
                st.stop()
            puntuados = puntuar(poblacion, SISTEMA)
            lista = lista_contactos(puntuados, k_editado, CONFIG["proyecto"]["semilla"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Estudiantes elegibles", f"{resumen['elegibles']:,}".replace(",", "."))
        c2.metric("Familias (representantes)", f"{resumen['representantes']:,}".replace(",", "."))
        c3.metric("Familias a contactar", len(lista))
        c4.metric("Cobertura", f"{len(lista) / max(resumen['representantes'], 1):.0%}",
                  help="Porcentaje de familias elegibles que entra en la lista.")
        st.markdown(
            "**Cómo se ordena:** regla **D2**, primero quien pagó tarde la matrícula anterior, "
            "luego reserva extraordinaria y luego más pensiones pagadas tarde. Los empates "
            "se resuelven al azar, igual que en la validación. Con datos reales, esta regla "
            "encontró **casi el doble** de familias que no se matricularon que una selección "
            "al azar (Lift = 1,97).")
        st.dataframe(
            lista.drop(columns=["prioridad_d2"]).rename(columns={
                "puesto": "Puesto", "id_familia": "Familia (seudónimo)", "sede": "Sede",
                "estudiantes": "Estudiantes",
                "estudiantes_ids": "Estudiantes (seudónimos)", "motivo": "Motivo"}),
            use_container_width=True, hide_index=True)
        st.download_button("⬇️ Descargar lista (CSV)", lista.to_csv(index=False).encode("utf-8"),
                           file_name=f"lista_contactos_{anio}.csv", mime="text/csv")
        col_a, col_b = st.columns(2)
        motivos = lista["motivo"].str.split("; ").explode().str.replace(
            r"^\d+ pensiones", "pensiones", regex=True).value_counts().reset_index()
        motivos.columns = ["Señal", "Familias"]
        col_a.plotly_chart(px.bar(motivos, x="Familias", y="Señal", orientation="h",
                                  title="Señales presentes en la lista",
                                  color_discrete_sequence=[COLOR]), use_container_width=True)
        col_b.plotly_chart(px.histogram(puntuados, x="prob_no_matricula", nbins=30,
                                        title="Probabilidad de no matrícula (todos los elegibles)",
                                        labels={"prob_no_matricula": "probabilidad"},
                                        color_discrete_sequence=[COLOR_SUAVE]),
                           use_container_width=True)
        st.caption("La lista es un apoyo: Secretaría revisa y decide a quién contactar. La "
                   "aplicación no contacta familias ni toma decisiones.")
        st.session_state["puntuados"] = puntuados
        st.session_state["lista"] = lista

# --------------------------------------------------------------------------- #
# Lista con nombres (solo modo institucional, en el mismo equipo)
# --------------------------------------------------------------------------- #
if tab_nombres is not None:
    with tab_nombres:
        lista_actual = st.session_state.get("lista")
        if not LOCAL:
            st.error("Disponible solo en el computador donde se ejecuta la aplicación.")
        elif DATOS_INSTITUCIONALES is None:
            st.info("Para ver nombres, suba en la barra lateral el **Excel de LEMAS** y la "
                    "**clave del custodio**. Con `base_seud.csv` o con el ejemplo no es "
                    "posible, porque esos archivos no contienen nombres.")
        elif lista_actual is None or lista_actual.empty:
            st.info("Primero genere la lista en la pestaña **Lista de contactos**.")
        else:
            st.warning("**Datos personales · uso interno de LEMAS.** Esta lista sirve para "
                       "ofrecer apoyo a las familias. No se usa para negar cupos, becas ni "
                       "servicios, y no debe salir de la institución.", icon="🪪")
            if st.checkbox("Soy personal autorizado y deseo ver los nombres",
                           key=f"ver_nombres_{REINICIO}"):
                nombres = lista_con_nombres(lista_actual, DATOS_INSTITUCIONALES.padron, anio)
                st.dataframe(
                    nombres.drop(columns=["id_familia"]).rename(columns={
                        "puesto": "Puesto", "sede": "Sede", "representante": "Representante",
                        "cedula_representante": "Cédula del representante",
                        "estudiantes": "Estudiantes (curso)", "motivo": "Motivo",
                        "observacion": "Observación"}),
                    use_container_width=True, hide_index=True)
                st.download_button(
                    "⬇️ Descargar lista con nombres (CSV para Excel)",
                    nombres.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"lista_contactos_con_nombres_{anio}.csv", mime="text/csv")
                st.caption("El archivo descargado contiene datos personales: guárdelo solo en "
                           "carpetas autorizadas y elimínelo al terminar la campaña. Al "
                           "finalizar, pulse **Borrar datos de la sesión**.")

# --------------------------------------------------------------------------- #
# Seguimiento: familias que siguen sin pagar a una fecha de corte (D51)
# --------------------------------------------------------------------------- #
with tab_seguimiento:
    puntuados = st.session_state.get("puntuados")
    if puntuados is None:
        st.info("Primero genere la lista en la pestaña **Lista de contactos**.")
    else:
        calendario = CONFIG["calendario"]
        t0 = pd.Timestamp(year=anio + 1, month=calendario["t0_mes_dia"][0],
                          day=calendario["t0_mes_dia"][1])
        cierre = pd.Timestamp(year=anio + 1, month=calendario["h_mes_dia"][0],
                              day=calendario["h_mes_dia"][1])
        st.markdown(
            "**Segunda etapa de la campaña.** La lista del 20 de febrero llega a cerca de "
            "un tercio de las familias que no se matriculan. Unas semanas después, la "
            "mayoría ya pagó y basta mirar quién sigue pendiente. Esta pestaña muestra a "
            "**todas las familias que siguen sin pagar** a la fecha que usted elija. Es un "
            "**listado**, no una predicción.")
        corte = st.date_input(
            "Fecha de corte", value=(t0 + pd.Timedelta(days=28)).date(),
            min_value=t0.date(), max_value=cierre.date(), format="DD/MM/YYYY",
            help="Entre el 20 de febrero y el 30 de abril. Sugerido: cuatro o cinco semanas "
                 "después del 20 de febrero. Use la fecha del archivo: se cuentan los pagos "
                 "registrados hasta ese día, inclusive.")
        seguimiento, cifras = seguimiento_al_corte(
            BASE, puntuados, anio, corte, k_editado, CONFIG, CONFIG["proyecto"]["semilla"])
        sin_pagos = cifras["dias_desde_t0"] > 0 and cifras["pagos_desde_t0"] == 0
        if sin_pagos:
            st.warning(
                f"El archivo no registra pagos de matrícula del ciclo {anio + 1}-{anio + 2} "
                "entre el 20 de febrero y la fecha de corte, así que no se puede saber quién "
                "sigue pendiente. Cargue el archivo actualizado a esa fecha. Con el ejemplo, "
                "elija un ciclo anterior en la barra lateral.", icon="📂")
        else:
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Familias al 20 de febrero", f"{cifras['familias_t0']:,}".replace(",", "."))
            s2.metric("Ya pagaron", f"{cifras['familias_pagaron']:,}".replace(",", "."))
            s3.metric("Siguen sin pagar", f"{cifras['familias_pendientes']:,}".replace(",", "."),
                      help="Familias con al menos un estudiante sin pago de matrícula.")
            s4.metric("No estaban en la lista inicial",
                      f"{cifras['pendientes_fuera_de_lista_inicial']:,}".replace(",", "."),
                      help="Familias pendientes que no entraron en la lista del 20 de febrero.")
            ultimo = cifras["ultimo_pago_registrado"]
            st.caption(
                f"Quedan {cifras['dias_hasta_cierre']} días hasta el 30 de abril. El listado "
                "solo es correcto si el archivo está actualizado a la fecha de corte"
                + (f" (último pago registrado: {pd.Timestamp(ultimo):%d-%m-%Y})." if ultimo
                   else "."))
            if cifras["pendientes_sin_representante"]:
                st.warning(f"{cifras['pendientes_sin_representante']} estudiantes sin pago no "
                           "tienen cédula de representante en el archivo y no aparecen en "
                           "el listado. Revíselos aparte.")
            solo_nuevas = st.checkbox(
                "Ocultar las familias de la lista del 20 de febrero (ya contactadas)",
                key=f"solo_nuevas_{REINICIO}",
                help="La marca se recalcula con el archivo y la k de hoy. Use la misma k "
                     "que el 20 de febrero; si guardó la lista de ese día, esa es la "
                     "referencia.")
            visible = seguimiento
            if solo_nuevas:
                visible = seguimiento[~seguimiento["en_lista_inicial"]]
                visible = visible.assign(puesto=visible.groupby("sede").cumcount() + 1)
            tabla = visible.assign(
                en_lista_inicial=visible["en_lista_inicial"].map({True: "Sí", False: "No"}))
            columnas = ["puesto", "id_familia", "sede", "en_lista_inicial", "estudiantes",
                        "estudiantes_ids", "motivo"]
            st.dataframe(
                tabla[columnas].rename(columns={
                    "puesto": "N.º", "id_familia": "Familia (seudónimo)", "sede": "Sede",
                    "en_lista_inicial": "En la lista del 20-feb",
                    "estudiantes": "Estudiantes sin pago",
                    "estudiantes_ids": "Estudiantes sin pago (seudónimos)",
                    "motivo": "Señales al 20 de febrero"}),
                use_container_width=True, hide_index=True)
            st.download_button(
                "⬇️ Descargar seguimiento (CSV)",
                tabla[columnas].to_csv(index=False).encode("utf-8"),
                file_name=f"seguimiento_{anio}_{cifras['fecha_corte']}.csv", mime="text/csv")
            st.caption(
                "El orden de la tabla es el de la regla del 20 de febrero y solo sirve para "
                "presentarla: a mitad de campaña esa regla ya no distingue mejor que el azar, "
                "por eso se listan todas las familias pendientes. Contactar en dos etapas es "
                "una propuesta para la campaña de 2027 que todavía no se ha probado.")
            if DATOS_INSTITUCIONALES is not None and not visible.empty:
                st.warning("**Datos personales · uso interno de LEMAS.** Igual que la lista "
                           "inicial, este listado sirve para ofrecer apoyo, no para negar "
                           "cupos, becas ni servicios.", icon="🪪")
                if st.checkbox("Soy personal autorizado y deseo ver los nombres",
                               key=f"ver_nombres_seguimiento_{REINICIO}"):
                    con_nombres = lista_con_nombres(visible, DATOS_INSTITUCIONALES.padron, anio)
                    con_nombres = con_nombres.merge(
                        tabla[["id_familia", "en_lista_inicial"]], on="id_familia", how="left")
                    st.dataframe(
                        con_nombres.drop(columns=["id_familia"]).rename(columns={
                            "puesto": "N.º", "sede": "Sede", "representante": "Representante",
                            "cedula_representante": "Cédula del representante",
                            "estudiantes": "Estudiantes sin pago (curso)",
                            "motivo": "Señales al 20 de febrero", "observacion": "Observación",
                            "en_lista_inicial": "En la lista del 20-feb"}),
                        use_container_width=True, hide_index=True)
                    st.download_button(
                        "⬇️ Descargar seguimiento con nombres (CSV para Excel)",
                        con_nombres.to_csv(index=False).encode("utf-8-sig"),
                        file_name=f"seguimiento_con_nombres_{anio}_{cifras['fecha_corte']}.csv",
                        mime="text/csv")
                    st.caption("El archivo descargado contiene datos personales: guárdelo solo "
                               "en carpetas autorizadas y elimínelo al terminar la campaña.")

# --------------------------------------------------------------------------- #
# Proyección
# --------------------------------------------------------------------------- #
with tab_proy:
    puntuados = st.session_state.get("puntuados")
    if puntuados is None:
        st.info("Primero genere la lista en la pestaña **Lista de contactos**.")
    else:
        proy = proyeccion_actual(puntuados, SISTEMA.tasa_historica)
        st.markdown("Matrículas **esperadas** del ciclo siguiente entre los elegibles, por sede "
                    "y subnivel. Se compara con **B1** (tasa histórica), que en la validación "
                    "tuvo el mismo error (MAPE ≈ 2,8 %).")
        largo = proy.melt(id_vars=["sede", "subnivel"],
                          value_vars=["elegibles", "esperadas_modelo", "esperadas_B1"],
                          var_name="serie", value_name="estudiantes")
        largo["serie"] = largo["serie"].map({"elegibles": "Elegibles",
                                             "esperadas_modelo": "Esperadas (modelo)",
                                             "esperadas_B1": "Esperadas (B1)"})
        figura = px.bar(largo, x="subnivel", y="estudiantes", color="serie", barmode="group",
                        facet_col="sede", labels={"serie": "", "subnivel": ""},
                        color_discrete_sequence=["#C9D6E3", COLOR, COLOR_SUAVE])
        figura.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        st.plotly_chart(figura, use_container_width=True)
        st.dataframe(proy, use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------- #
# Evaluar un estudiante (formulario validado)
# --------------------------------------------------------------------------- #
with tab_estudiante:
    st.markdown("Ingrese los datos **conocidos al 20 de febrero** de un estudiante con reserva "
                "aprobada. No se piden nombres ni cédulas.")
    with st.form("estudiante"):
        f1, f2, f3 = st.columns(3)
        sede = f1.selectbox("Sede", ["Mucho Lote 1", "Mucho Lote 2"])
        subnivel = f1.selectbox("Subnivel", ["Inicial", "Preparatoria",
                                             "Educación General Básica", "Bachillerato"])
        pago = f2.selectbox("Pago de la matrícula anterior",
                            ["en_plazo", "tardio", "anticipado", "nuevo"],
                            format_func={"en_plazo": "En plazo (20-feb a 30-abr)",
                                         "tardio": "Tardío (después del 30-abr)",
                                         "anticipado": "Anticipado (antes del 20-feb)",
                                         "nuevo": "Estudiante nuevo"}.get)
        atrasos = f2.number_input("Pensiones pagadas tarde (mayo–enero)", 0, 9, 0)
        reserva = f3.radio("Tipo de reserva", ["ORDINARIA", "EXTRAORDINARIA"], horizontal=True)
        promedio = f3.number_input("Promedio final (0–10)", 0.0, 10.0, 9.0, step=0.01)
        conducta = f3.selectbox("Conducta", list("ABCDE"))
        enviado = st.form_submit_button("Estimar", type="primary")
    if enviado:
        resultado = estimar_estudiante({
            "sede": sede, "subnivel": subnivel, "pago_origen": pago,
            "atrasos_pension": atrasos, "reserva_extraordinaria": int(reserva == "EXTRAORDINARIA"),
            "promedio": promedio, "conducta": {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}[conducta],
        }, SISTEMA)
        r1, r2, r3 = st.columns(3)
        r1.metric("Prioridad D2", resultado["nivel"])
        r2.metric("Prob. de no matrícula", f"{resultado['prob_no_matricula']:.1%}",
                  delta=f"{resultado['prob_no_matricula'] - resultado['tasa_historica']:+.1%} "
                        "vs. tasa histórica", delta_color="inverse")
        r3.metric("Tasa histórica (B1)", f"{resultado['tasa_historica']:.1%}")
        st.markdown(f"**Señales:** {resultado['motivo']}.")
        st.caption("La probabilidad individual es orientativa: en la validación no superó a la "
                   "tasa histórica. Para decidir a quién contactar use la lista D2.")

# --------------------------------------------------------------------------- #
# Acerca de
# --------------------------------------------------------------------------- #
with tab_acerca:
    st.markdown("""
### Qué hace
Al corte del **20 de febrero**, prioriza a las familias con reserva aprobada que podrían
**no formalizar la matrícula** hasta el 30 de abril, para que Secretaría y Admisiones las
contacten a tiempo. También estima cuántas matrículas se esperan por sede y subnivel.

### Cómo se validó (datos reales de LEMAS, sin publicar datos individuales)
Validación temporal: entrenamiento con los ciclos 2022–2023 y 2023–2024, selección en
2024–2025 y **prueba única** en la matrícula 2026–2027. Se compararon tres modelos de IA
(regresión logística, gradient boosting y una logística híbrida) con reglas simples.
""")
    c5 = pd.DataFrame(RESULTADOS["c5"])
    c5["IC 95 %"] = c5["ic95"].map(lambda v: f"[{v[0]:.2f}; {v[1]:.2f}]" if v else "—")
    st.dataframe(c5.drop(columns="ic95").rename(columns={
        "sistema": "Sistema", "lift": "Lift@k", "precision": "Precision@k",
        "recall": "Recall@k"}), hide_index=True, use_container_width=True)
    st.plotly_chart(px.bar(c5, x="lift", y="sistema", orientation="h",
                           title="Lift@k en la prueba final (1 = azar)",
                           color_discrete_sequence=[COLOR]).add_vline(x=1, line_dash="dash"),
                    use_container_width=True)
    st.markdown(f"""
**Resultado principal:** contactando ≈ 15 % de las familias (k = 118 y 47), la regla **D2**
llega al **30 %** de las que no se matricularon, casi el doble que al azar. Los modelos de IA
no superaron a esta regla con los datos disponibles; el aprendizaje automático sirvió para
**descubrirla, validarla y medir su incertidumbre**.

### Limitaciones y advertencias
- Las probabilidades individuales están calibradas pero **no mejoran a la tasa histórica**
  (Brier 0,0648 frente a 0,0647). Úselas como orientación, no como diagnóstico.
- La lista del 20 de febrero **no alcanza a cerca del 70 %** de los casos: ese día los datos
  no los distinguen. La pestaña **Seguimiento** lista a las familias que siguen sin pagar
  unas semanas después. Es una propuesta para la campaña de 2027, todavía sin probar.
- Solo cubre estudiantes **antiguos con reserva aprobada**; no predice nuevos ingresos.
- {RESULTADOS['equidad']} Se recomienda revisar también a familias becadas con atrasos.
- La lista es un **apoyo a la decisión humana**: no se usa para negar cupos, becas ni
  servicios. Las familias aparecen solo con seudónimos.

### Privacidad
- **Modo demo (público):** solo datos sintéticos; rechaza archivos con cédulas o nombres.
- **Modo institucional:** solo dentro de LEMAS y en el mismo equipo. El Excel se
  seudonimiza en memoria con la clave del custodio, el sistema trabaja con seudónimos y
  nada se guarda en disco.
- Los nombres solo se muestran en el modo institucional, a personal autorizado de LEMAS;
  la versión pública no tiene esa función.

Proyecto final · Maestría en Inteligencia Artificial (UEES) · Guillermo Granizo y José Ulloa.
Código: [github.com/ggranizo2507/prediccion-matricula-lemas](https://github.com/ggranizo2507/prediccion-matricula-lemas)
""")
