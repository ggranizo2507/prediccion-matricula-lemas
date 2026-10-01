"""
Aplicación Streamlit · Priorización de contacto y proyección de matrícula (LEMAS).

Ejecutar desde la raíz del repositorio:
    streamlit run app/app.py                         # modo demo (datos sintéticos)
    LEMAS_MODO=institucional streamlit run app/app.py # solo dentro de LEMAS

Diseño de dos modos aprobado el 01-oct-2026 (D42): la versión pública nunca recibe
datos reales. Ver docs/arquitectura.md y docs/manual_usuario.md.
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

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
    validar_entrada,
)
from src.utils import cargar_config  # noqa: E402

COLOR = "#8B1E3F"
COLOR_SUAVE = "#9DB4C9"
st.set_page_config(page_title="Matrícula LEMAS · Priorización", page_icon="🎓", layout="wide")

CONFIG = cargar_config(RAIZ / "config.yaml")
MODO = modo_actual()
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
else:
    st.warning("**Modo institucional.** Use solo la base seudonimizada (cuaderno 00a). Los "
               "resultados identifican familias por seudónimo; la reidentificación la hace el "
               "custodio de datos.", icon="🔒")

with st.sidebar:
    st.header("1 · Datos")
    if st.button("▶️ Prueba con ejemplo", use_container_width=True,
                 help="Carga la base sintética incluida en el repositorio."):
        st.session_state["contenido"] = bytes_ejemplo()
        st.session_state["origen"] = "Ejemplo sintético"
    archivo = st.file_uploader(
        "…o suba la base (CSV)", type=["csv"],
        help="Estructura de base_seud.csv (ver manual). Sin cédulas, nombres ni códigos.")
    if archivo is not None:
        st.session_state["contenido"] = archivo.getvalue()
        st.session_state["origen"] = archivo.name
    if "contenido" in st.session_state:
        st.success(f"Datos: {st.session_state['origen']}")

contenido = st.session_state.get("contenido")
if contenido is None:
    st.markdown("### ¿Cómo empezar?")
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
            help="Valor aprobado: 2 × el promedio histórico de familias con no matrícula.")
    st.caption(SISTEMA.descripcion)

tab_lista, tab_proy, tab_estudiante, tab_acerca = st.tabs(
    ["📋 Lista de contactos", "📈 Proyección", "🧑‍🎓 Evaluar un estudiante", "ℹ️ Acerca de"])

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
            lista = lista_contactos(puntuados, k_editado)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Estudiantes elegibles", f"{resumen['elegibles']:,}".replace(",", "."))
        c2.metric("Familias (representantes)", f"{resumen['representantes']:,}".replace(",", "."))
        c3.metric("Familias a contactar", len(lista))
        c4.metric("Cobertura", f"{len(lista) / max(resumen['representantes'], 1):.0%}",
                  help="Porcentaje de familias elegibles que entra en la lista.")
        st.markdown(
            "**Cómo se ordena:** regla **D2**, primero quien pagó tarde la matrícula anterior, "
            "luego reserva extraordinaria y luego más pensiones pagadas tarde. Empates: "
            "mayor probabilidad del modelo. En la validación con datos reales, esta regla "
            "encontró **casi el doble** de familias que no se matricularon que una selección "
            "al azar (Lift = 1,97).")
        st.dataframe(
            lista.drop(columns=["prioridad_d2"]).rename(columns={
                "puesto": "Puesto", "id_familia": "Familia (seudónimo)", "sede": "Sede",
                "prob_max": "Prob. no matrícula", "estudiantes": "Estudiantes",
                "estudiantes_ids": "Estudiantes (seudónimos)", "motivo": "Motivo"}),
            use_container_width=True, hide_index=True,
            column_config={"Prob. no matrícula": st.column_config.ProgressColumn(
                format="%.2f", min_value=0.0, max_value=float(max(lista["prob_max"].max(), 0.3)),
                help="Probabilidad calibrada; en promedio se parece a la tasa histórica.")})
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
- Solo cubre estudiantes **antiguos con reserva aprobada**; no predice nuevos ingresos.
- {RESULTADOS['equidad']} Se recomienda revisar también a familias becadas con atrasos.
- La lista es un **apoyo a la decisión humana**: no se usa para negar cupos, becas ni
  servicios. Las familias aparecen solo con seudónimos.

### Privacidad
- **Modo demo (público):** solo datos sintéticos; rechaza archivos con cédulas o nombres.
- **Modo institucional:** solo dentro de LEMAS; procesa en memoria y no guarda nada.
- La reidentificación de seudónimos la hace únicamente el custodio de datos de LEMAS.

Proyecto final · Maestría en Inteligencia Artificial (UEES) · Guillermo Granizo y José Ulloa.
Código: [github.com/ggranizo2507/prediccion-matricula-lemas](https://github.com/ggranizo2507/prediccion-matricula-lemas)
""")
