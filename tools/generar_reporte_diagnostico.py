"""
Genera el reporte técnico de la actividad de la semana 3 (`docs/diagnostic_report.pdf`).

El reporte se arma con los agregados que guarda `notebooks/overfitting_analysis.ipynb`
en `results/metrics` y `results/figures`, de modo que las cifras y las frases del PDF
siempre coinciden con la última ejecución:

    python tools/generar_reporte_diagnostico.py --fuente real
    python tools/generar_reporte_diagnostico.py --fuente sintetica   # versión preliminar

Requiere `reportlab` (pip install reportlab). No usa datos individuales.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import matplotlib
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.diagnostico import _g, numero  # noqa: E402
from src.utils import cargar_config  # noqa: E402

VINO, TINTA, SUAVE, FONDO, LINEA = "#8B1E3F", "#1F2933", "#5B6670", "#F5F1F3", "#D9DDE2"
ANCHO = A4[0] - 4 * cm
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
CODIGO = "<font face='Texto-Cursiva'>{}</font>"


# --------------------------------------------------------------------------- #
# Estilos
# --------------------------------------------------------------------------- #
def _fuentes() -> None:
    """DejaVu Sans (incluida con matplotlib): tiene tildes, flechas y el signo menos."""
    carpeta = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    for nombre, archivo in {"Texto": "DejaVuSans.ttf", "Texto-Negrita": "DejaVuSans-Bold.ttf",
                            "Texto-Cursiva": "DejaVuSans-Oblique.ttf"}.items():
        pdfmetrics.registerFont(TTFont(nombre, str(carpeta / archivo)))
    pdfmetrics.registerFontFamily("Texto", normal="Texto", bold="Texto-Negrita",
                                  italic="Texto-Cursiva", boldItalic="Texto-Negrita")


def _estilos() -> dict[str, ParagraphStyle]:
    base = {"fontName": "Texto", "textColor": colors.HexColor(TINTA)}
    negrita = {**base, "fontName": "Texto-Negrita"}
    suave = {**base, "textColor": colors.HexColor(SUAVE)}
    return {
        "titulo": ParagraphStyle("titulo", fontSize=19, leading=23, spaceAfter=4, **negrita),
        "subtitulo": ParagraphStyle("subtitulo", fontSize=10, leading=14, spaceAfter=10,
                                    **suave),
        "h1": ParagraphStyle("h1", fontSize=13.5, leading=17, spaceBefore=14, spaceAfter=6,
                             keepWithNext=1,
                             **{**negrita, "textColor": colors.HexColor(VINO)}),
        "h2": ParagraphStyle("h2", fontSize=10.5, leading=14, spaceBefore=9, spaceAfter=4,
                             keepWithNext=1, **negrita),
        "texto": ParagraphStyle("texto", fontSize=9.3, leading=13.2, spaceAfter=6,
                                alignment=TA_JUSTIFY, **base),
        "izquierda": ParagraphStyle("izquierda", fontSize=9.3, leading=13.2, spaceAfter=6,
                                    **base),
        "vineta": ParagraphStyle("vineta", fontSize=9.3, leading=13.2, spaceAfter=3.5,
                                 leftIndent=12, bulletIndent=2, **base),
        "pie": ParagraphStyle("pie", fontSize=8.2, leading=11, spaceAfter=10,
                              **{**suave, "fontName": "Texto-Cursiva"}),
        "celda": ParagraphStyle("celda", fontSize=8, leading=10.2, **base),
        "cabecera": ParagraphStyle("cabecera", fontSize=8, leading=10.2,
                                   **{**negrita, "textColor": colors.white}),
        "aviso": ParagraphStyle("aviso", fontSize=9, leading=12.5, **base),
        "referencia": ParagraphStyle("referencia", fontSize=8.6, leading=12, spaceAfter=4,
                                     leftIndent=18, firstLineIndent=-18, **base),
    }


# --------------------------------------------------------------------------- #
# Piezas
# --------------------------------------------------------------------------- #
def _vinetas(frases: list[str], e: dict) -> list:
    return [Paragraph(frase, e["vineta"], bulletText="•") for frase in frases]


def _tabla(encabezados: list[str], filas: list[list], anchos: list[float], e: dict) -> Table:
    datos = [[Paragraph(str(c), e["cabecera"]) for c in encabezados]]
    datos += [[Paragraph(str(c), e["celda"]) for c in fila] for fila in filas]
    total = sum(anchos)
    tabla = Table(datos, colWidths=[ANCHO * a / total for a in anchos], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(VINO)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(FONDO)]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor(LINEA)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tabla


def _figura(ruta: Path, pie: str, e: dict, titulo: str | None = None,
            ancho: float = ANCHO) -> KeepTogether:
    """Figura con su pie. Si se da `titulo`, el encabezado queda en la misma página."""
    from PIL import Image as Lector

    with Lector.open(ruta) as imagen:
        proporcion = imagen.height / imagen.width
    piezas = [Paragraph(titulo, e["h2"])] if titulo else []
    return KeepTogether(piezas + [Image(str(ruta), width=ancho, height=ancho * proporcion),
                                  Spacer(1, 3), Paragraph(pie, e["pie"])])


def _aviso(texto: str, e: dict, color: str = "#FFF4D6", borde: str = "#C98A00") -> Table:
    caja = Table([[Paragraph(texto, e["aviso"])]], colWidths=[ANCHO])
    caja.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(color)),
        ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor(borde)),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return caja


def _lista(nombres: list[str]) -> str:
    if len(nombres) <= 1:
        return "".join(nombres)
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


# --------------------------------------------------------------------------- #
# Frases calculadas con los resultados
# --------------------------------------------------------------------------- #
def _por_diagnostico(diag: pd.DataFrame) -> str:
    fase2 = diag[diag["rol"] == "Fase 2"]
    frases = []
    for estado in ("sobreajuste", "subajuste", "ajuste adecuado", "indeterminado"):
        nombres = [nombre.lower() for nombre in fase2[fase2["diagnostico"] == estado]["modelo"]]
        if nombres:
            verbo = "presenta" if len(nombres) == 1 else "presentan"
            frases.append(f"<b>{_lista(nombres).capitalize()}</b> {verbo} <b>{estado}</b>.")
    return " ".join(frases)


def _controles(diag: pd.DataFrame) -> str:
    estados = list(diag[diag["rol"] == "control"]["diagnostico"])
    if estados == ["sobreajuste", "subajuste"]:
        return ("Los dos modelos de control, que son casos extremos, se clasifican como se "
                "esperaba (sobreajuste y subajuste). Esto comprueba la regla en casos claros, "
                "no en los casos cercanos a los umbrales.")
    return ("Atención: los modelos de control no se clasificaron como se esperaba "
            f"({_lista(estados)}); conviene revisar los umbrales.")


def _estrategias(estrategias: pd.DataFrame, val: str) -> list[str]:
    activas = estrategias[~estrategias["modelo_sin_cambios"]]
    sin_cambios = [n.split(" · ")[0] for n in
                   estrategias[estrategias["modelo_sin_cambios"]]["estrategia"]]
    conteo = activas["efecto_validacion"].value_counts()
    frases = [
        f"De las {len(estrategias)} estrategias evaluadas, la PR-AUC en {val} mejora en "
        f"{int(conteo.get('mejora', 0))}, empeora en {int(conteo.get('empeora', 0))} y no "
        f"cambia de forma apreciable en {int(conteo.get('sin cambio apreciable', 0))}"
        + (f"; {_lista(sin_cambios)} no modificó el modelo en esta ejecución."
           if sin_cambios else ".")]
    mejor = estrategias.loc[estrategias["cambio_puntaje_validacion"].idxmax()]
    if mejor["efecto_validacion"] == "mejora":
        frase = (f"La de mayor efecto es <b>{mejor['estrategia']}</b>: de "
                 f"{numero(mejor['puntaje_validacion_antes'])} a "
                 f"{numero(mejor['puntaje_validacion_despues'])}")
        if "lift_k_validacion_antes" in mejor:
            frase += (f" (Lift@k de {numero(mejor['lift_k_validacion_antes'], 2)} a "
                      f"{numero(mejor['lift_k_validacion_despues'], 2)})")
        frases.append(frase + ".")
    fuera = [f.estrategia.split(" · ")[0] for f in activas.itertuples()
             if not f.aplica_al_diagnostico]
    if fuera:
        frases.append(f"En {_lista(fuera)} el modelo de partida no presentaba el problema "
                      "que la estrategia busca corregir: esos resultados son comprobaciones, "
                      "no correcciones.")
    contra = estrategias[estrategias["problema"] == "sobreajuste"]
    frases.append(f"Reducen la brecha {int((contra['efecto_brecha'] == 'reduce').sum())} de "
                  f"las {len(contra)} estrategias contra el sobreajuste.")
    cambian = estrategias[estrategias["diagnostico_antes"] != estrategias["diagnostico_despues"]]
    if len(cambian):
        frases.append("Cambian el diagnóstico: " + "; ".join(
            f"{f.estrategia.split(' · ')[0]} ({f.diagnostico_antes} → {f.diagnostico_despues})"
            for f in cambian.itertuples()) + ".")
    return frases


def _mas_datos(ganancia: pd.DataFrame) -> str:
    concluyentes = ganancia[ganancia["concluyente"]]
    if concluyentes.empty:
        return ("Al pasar de la mitad al total del entrenamiento, el cambio de la PR-AUC de "
                "validación es menor que dos veces la variación entre submuestras en los "
                "tres modelos: con estos datos no se puede afirmar que más datos ayuden ni "
                "que no ayuden.")
    partes = [f"{g.modelo.lower()} ({numero(g.ganancia, signo=True)})"
              for g in concluyentes.itertuples()]
    return ("Al pasar de la mitad al total del entrenamiento, la PR-AUC de validación cambia "
            f"más del doble de la variación entre submuestras en: {_lista(partes)}.")


def _lectura_hiperparametros(hiper: pd.DataFrame) -> list[str]:
    frases = []
    for modelo, d in hiper.groupby("modelo", sort=False):
        d = d.sort_values("valor")
        mejor = d.loc[d["puntaje_validacion"].idxmax()]
        nombre = {"C": "C", "learning_rate": "la tasa de aprendizaje"}.get(
            d["hiperparametro"].iloc[0], d["hiperparametro"].iloc[0])
        fase2, extremo = d["valor_fase2"].iloc[0], d.iloc[-1]
        frases.append(
            f"<b>{modelo}</b>, al variar {nombre}: la validación es máxima en "
            f"{_g(mejor['valor'])} ({numero(mejor['puntaje_validacion'])}); la Fase 2 eligió "
            f"{_g(fase2)}. En el valor más alto ({_g(extremo['valor'])}), el entrenamiento "
            f"llega a {numero(extremo['puntaje_entrenamiento'])} y la validación queda en "
            f"{numero(extremo['puntaje_validacion'])}.")
    return frases


# --------------------------------------------------------------------------- #
# Documento
# --------------------------------------------------------------------------- #
def construir(fuente: str, salida: Path) -> Path:
    config = cargar_config(RAIZ / "config.yaml")
    met, fig = RAIZ / config["rutas"]["metricas"], RAIZ / config["rutas"]["figuras"]
    try:
        resultado = json.loads((met / f"diagnostico_semana3_{fuente}.json").read_text("utf-8"))
        diag = pd.read_csv(met / f"diagnostico_modelos_{fuente}.csv")
        estrategias = pd.read_csv(met / f"estrategias_mejora_{fuente}.csv")
        hiper = pd.read_csv(met / f"curvas_hiperparametros_{fuente}.csv")
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"Faltan resultados de la fuente '{fuente}'. Ejecute primero "
            "notebooks/overfitting_analysis.ipynb.") from error

    _fuentes()
    e = _estilos()
    val = resultado["validacion"]
    tr = "+".join(resultado["cohortes_entrenamiento"])
    u = resultado["umbrales"]
    principal, interna = resultado["particiones"]
    c = resultado["conclusiones"]
    ganancia = pd.DataFrame(resultado["ganancia_por_datos"])
    hoy = date.today()
    fecha = f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"
    sintetico = fuente != "real"
    n_estrategias = len(estrategias)
    h = []

    # ---- Portada y resumen ejecutivo (una página) ---------------------------------
    h.append(Paragraph("Diagnóstico de sobreajuste y subajuste", e["titulo"]))
    h.append(Paragraph(
        "Reporte técnico · Actividad de la semana 3<br/>Proyecto: Predicción de matrícula y "
        "continuidad estudiantil, Unidad Educativa LEMAS<br/>Guillermo Granizo y José Ulloa · "
        f"Maestría en Inteligencia Artificial, UEES · {fecha}", e["subtitulo"]))
    if sintetico:
        h.append(_aviso(
            "<b>Versión preliminar con datos sintéticos.</b> Las cifras de este documento "
            "prueban el método y no describen a LEMAS. La versión final se genera con los "
            "datos reales seudonimizados.", e))
        h.append(Spacer(1, 6))
    h.append(Paragraph("1. Resumen ejecutivo", e["h1"]))
    h.append(Paragraph(
        "<b>Qué se hizo.</b> Se diagnosticó si los tres modelos de la Fase 2 (regresión "
        "logística regularizada, gradient boosting y logística híbrida) memorizan los datos "
        "de entrenamiento o no aprenden lo suficiente. Para ello se registraron las métricas "
        "durante el entrenamiento, se generaron cuatro tipos de curvas de aprendizaje, se "
        f"cuantificó el ajuste con dos reglas prácticas y se evaluaron {n_estrategias} "
        f"estrategias de mejora con comparación antes y después. Se entrenó con {tr} y se "
        f"validó con {val}; la cohorte de prueba (C5) no intervino.", e["texto"]))
    h.append(Paragraph("<b>Qué se encontró.</b>", e["texto"]))
    h += _vinetas([_por_diagnostico(diag), _controles(diag), *_estrategias(estrategias, val),
                   _mas_datos(ganancia)], e)
    h.append(Spacer(1, 4))
    h.append(Paragraph(
        "<b>Qué significa para el proyecto.</b> Este análisis no cambia la decisión final, "
        f"que es priorizar el contacto con la regla D2. Las diferencias observadas en {val} "
        f"son indicios y no pruebas: {val} ya se usó para seleccionar y calibrar en la Fase 2, "
        f"y solo tiene {principal['eventos_validacion']} eventos. Para confirmar una mejora "
        "hace falta una cohorte que no haya participado en ninguna decisión.", e["texto"]))
    h.append(Paragraph(
        f"<b>Entregables.</b> Cuaderno {CODIGO.format('overfitting_analysis.ipynb')}, módulos "
        f"{CODIGO.format('src/diagnostico.py')} y {CODIGO.format('src/graficos_diagnostico.py')} "
        "con pruebas automáticas, cinco figuras a 300 DPI y este reporte.", e["izquierda"]))
    h.append(PageBreak())

    # ---- Metodología ---------------------------------------------------------------
    h.append(Paragraph("2. Metodología utilizada", e["h1"]))
    h.append(Paragraph("2.1 Datos y particiones", e["h2"]))
    h.append(Paragraph(
        "Cada fila es un estudiante con reserva aprobada al 20 de febrero; el evento es no "
        "pagar la matrícula hasta el 30 de abril. Las particiones respetan el orden temporal: "
        "se entrena con cohortes anteriores y se valida con la siguiente. No se usan "
        "particiones al azar entre años, porque filtrarían información del futuro.",
        e["texto"]))
    h.append(_tabla(
        ["Partición", "Entrena con", "Valida con", "N<br/>entr.", "Eventos<br/>entr.",
         "N<br/>val.", "Eventos<br/>val.", "Uso"],
        [["Diagnóstico", principal["entrenamiento"], principal["validacion"],
          principal["n_entrenamiento"], principal["eventos_entrenamiento"],
          principal["n_validacion"], principal["eventos_validacion"],
          "Curvas, diagnóstico y medición de las estrategias"],
         ["Interna", interna["entrenamiento"], interna["validacion"],
          interna["n_entrenamiento"], interna["eventos_entrenamiento"],
          interna["n_validacion"], interna["eventos_validacion"],
          f"Elegir sin mirar {val} (parada temprana)"]],
        [1.8, 1.9, 1.6, 1.0, 1.4, 1.0, 1.4, 3.6], e))
    h.append(Spacer(1, 6))
    h.append(Paragraph(
        "<b>Puntaje y pérdida.</b> La actividad pide una curva de exactitud o de puntaje. La "
        f"tasa de eventos en {val} es {numero(100 * resultado['tasa_validacion'], 1)} %: con "
        "clases tan desbalanceadas la exactitud no informa, porque un modelo que nunca "
        "detecta un caso acierta en casi todos. Por eso el puntaje es la <b>PR-AUC</b> "
        "(precisión promedio), donde un ordenamiento al azar obtiene la tasa de eventos. La "
        "<b>pérdida</b> es la entropía cruzada; en los modelos entrenados con clases "
        "balanceadas se pondera igual que durante el entrenamiento, así que la pérdida solo "
        "se compara entre curvas del mismo modelo.", e["texto"]))

    h.append(Paragraph("2.2 Seguimiento de métricas", e["h2"]))
    h.append(Paragraph(
        "Los modelos son de scikit-learn. El seguimiento está en "
        f"{CODIGO.format('src/diagnostico.py')} y guarda cada medición en un mismo registro "
        f"({CODIGO.format('RegistroMetricas')}: una fila por modelo, paso y conjunto):",
        e["izquierda"]))
    h += _vinetas([
        f"<b>Gradient boosting, por iteración.</b> {CODIGO.format('seguir_boosting')} mide la "
        "pérdida y la PR-AUC de entrenamiento y de validación después de cada árbol añadido.",
        f"<b>Regresiones logísticas, por iteración del optimizador.</b> scikit-learn no "
        f"expone su estado intermedio, así que {CODIGO.format('seguir_logistica')} entrena "
        "con un límite de iteraciones creciente hasta que el optimizador converge; el último "
        "punto es el modelo final.",
        f"<b>learning_curve</b> de scikit-learn, para el efecto del tamaño del entrenamiento "
        f"({resultado['repeticiones']} submuestras por tamaño).",
        "<b>validation_curve</b> de scikit-learn, para el efecto de un hiperparámetro con el "
        "resto fijo.",
    ], e)

    h.append(Paragraph("2.3 Modelos analizados", e["h2"]))
    comprobacion = resultado.get("comprobacion_fase2", {})
    if not comprobacion.get("realizada"):
        frase = "No había una tabla de la Fase 2 guardada para comprobar la coincidencia."
    elif comprobacion["coincide"]:
        frase = ("Al reentrenarlos, su PR-AUC en la validación coincide con la tabla de la "
                 f"Fase 2 (diferencia máxima {numero(comprobacion['diferencia_maxima'], 4)}).")
    else:
        frase = ("Atención: al reentrenarlos, su PR-AUC en la validación difiere de la tabla "
                 f"de la Fase 2 en hasta {numero(comprobacion['diferencia_maxima'], 4)}.")
    h.append(Paragraph(
        "Los modelos base son los tres de la Fase 2, con los hiperparámetros que eligió "
        f"Optuna, leídos del historial guardado. {frase} Se añaden dos modelos de control, "
        "definidos de antemano, que no son candidatos: un gradient boosting sin regularizar, "
        "que debe sobreajustar, y una regresión logística con penalización L1 extrema, que "
        "debe subajustar.", e["texto"]))

    h.append(Paragraph("2.4 Reglas de diagnóstico", e["h2"]))
    h.append(_tabla(
        ["Diagnóstico", "Patrón en las curvas", "Regla cuantitativa"],
        [["Sobreajuste", "La brecha crece; el entrenamiento mejora y la validación se "
          "estanca o empeora",
          f"Brecha relativa de PR-AUC mayor que {numero(100 * u['brecha_relativa_max'], 0)} %"],
         ["Subajuste", "Las dos curvas quedan juntas en un nivel pobre",
          "Sin esa brecha, PR-AUC de validación menor que "
          f"{numero(u['mejora_minima_sobre_azar'], 1)} veces el azar"],
         ["Ajuste adecuado", "Brecha pequeña y estable en un nivel útil",
          "Ninguna de las dos condiciones anteriores"]],
        [1.6, 3.6, 3.6], e))
    h.append(Spacer(1, 6))
    h.append(Paragraph(
        "Brecha relativa = (entrenamiento − validación) / entrenamiento. En las curvas "
        "durante el entrenamiento se mide además el paso con menor pérdida de validación y "
        "cuánto sube la pérdida después (deterioro, si supera "
        f"{numero(u['tolerancia_perdida'], 2)}). Una estrategia «mejora» o «empeora» solo si "
        f"la PR-AUC cambia al menos {numero(u['cambio_minimo'], 3)}.", e["texto"]))
    h.append(Paragraph(
        "<b>Alcance de estas reglas.</b> Son reglas prácticas, no pruebas estadísticas. Los "
        f"umbrales están en {CODIGO.format('config.yaml')} y se fijaron el 2 de octubre de "
        "2026, antes de ejecutar este análisis con datos reales, pero cuando ya se conocían "
        "las PR-AUC de entrenamiento y de C4 de la Fase 2. La brecha compara dos conjuntos "
        "cuya tasa de eventos puede ser distinta, por eso la Tabla 1 muestra también cuántas "
        "veces supera al azar cada conjunto. La tabla de ajuste de la Fase 2 usó una regla "
        "más simple (brecha absoluta mayor que 0,10; entrenamiento menor que 0,15), que puede "
        "diferir de esta en casos límite.", e["texto"]))

    # ---- Resultados del diagnóstico ------------------------------------------------
    h.append(Paragraph("3. Resultados del diagnóstico", e["h1"]))
    filas = [[f.modelo, f.rol, numero(f.puntaje_entrenamiento), numero(f.puntaje_validacion),
              numero(f.brecha, signo=True), f"{numero(100 * f.brecha_relativa, 0)} %",
              numero(f.veces_azar_entrenamiento, 2), numero(f.mejora_sobre_azar, 2),
              f"<b>{f.diagnostico}</b>"] for f in diag.itertuples()]
    h.append(_tabla(["Modelo", "Rol", "PR-AUC<br/>entr.", f"PR-AUC<br/>{val}", "Brecha",
                     "Brecha<br/>relativa", "Veces el azar<br/>(entr.)",
                     f"Veces el azar<br/>({val})", "Diagnóstico"],
                    filas, [3.0, 1.3, 1.45, 1.45, 1.35, 1.45, 1.6, 1.6, 2.4], e))
    h.append(Paragraph(f"Tabla 1. Diagnóstico por modelo ({tr} → {val}).", e["pie"]))
    h += _vinetas([_por_diagnostico(diag), _controles(diag)], e)

    # ---- Curvas --------------------------------------------------------------------
    h.append(PageBreak())
    h.append(Paragraph("4. Análisis de curvas de aprendizaje", e["h1"]))
    h.append(Paragraph(
        "Todas las figuras se generan a 300 DPI. Azul es entrenamiento y rosa con marcadores "
        "redondos es validación. En las regresiones logísticas cada punto es un "
        "entrenamiento completo con ese límite de iteraciones.", e["texto"]))
    h.append(_figura(fig / f"{fuente}_19_curva_perdida.png",
                     "Figura 1. Pérdida de entrenamiento y de validación en cada paso. Cada "
                     "panel tiene su propia escala.", e,
                     "4.1 Curva A: pérdida durante el entrenamiento"))
    h += _vinetas(c["curvas"], e)
    h.append(_figura(fig / f"{fuente}_20_curva_puntaje.png",
                     "Figura 2. PR-AUC de entrenamiento y de validación en cada paso.", e,
                     "4.2 Curva B: PR-AUC durante el entrenamiento"))
    lecturas = []
    for nombre, r in resultado["resumen_seguimiento"].items():
        lecturas.append(
            f"<b>{nombre}</b>: la PR-AUC de validación es máxima en el paso "
            f"{r['iteracion_mejor_puntaje']} ({numero(r['mejor_puntaje_validacion'])}). Al "
            f"final (paso {r['iteraciones']}), la brecha de PR-AUC es "
            f"{numero(r['brecha_puntaje_final'], signo=True)} y la de pérdida "
            f"{numero(r['brecha_perdida_final'])}"
            + (", mayor que en el punto óptimo." if r["brecha_crece"] else "."))
    h += _vinetas(lecturas, e)

    h.append(_figura(fig / f"{fuente}_21_curva_tamano.png",
                     "Figura 3. PR-AUC según el número de estudiantes en el entrenamiento. "
                     "La banda es ±1 desviación entre submuestras.", e,
                     "4.3 Curva C: tamaño del entrenamiento (opcional)"))
    h += _vinetas([
        f"<b>{g.modelo}</b>: la validación pasa de {numero(g.validacion_mitad)} con "
        f"{g.n_mitad} estudiantes a {numero(g.validacion_todo)} con {g.n_todo} "
        f"({numero(g.ganancia, signo=True)}; variación entre submuestras "
        f"±{numero(g.variacion_entre_submuestras)}). "
        + ("La diferencia supera el doble de esa variación." if g.concluyente
           else "La diferencia no llega al doble de esa variación: no es concluyente.")
        for g in ganancia.itertuples()], e)

    h.append(_figura(fig / f"{fuente}_22_curva_hiperparametros.png",
                     "Figura 4. PR-AUC al variar un hiperparámetro; la línea discontinua "
                     "marca el valor de la Fase 2.", e,
                     "4.4 Curva D: hiperparámetros (opcional)"))
    h += _vinetas(_lectura_hiperparametros(hiper), e)

    # ---- Estrategias ---------------------------------------------------------------
    h.append(Paragraph("5. Estrategias implementadas y resultados", e["h1"]))
    h.append(Paragraph(
        f"Se implementaron {n_estrategias} estrategias (la actividad pide al menos dos), "
        "todas medidas en la misma partición. Cada una aplica un solo tipo de cambio (E3 "
        "ajusta a la vez los hiperparámetros de complejidad), con dos excepciones: E1 parte "
        "de un modelo de control y no de un candidato, y E4 cambia las variables y también "
        "los hiperparámetros. La parada temprana elige "
        f"sus iteraciones por menor pérdida en la validación interna "
        f"({interna['entrenamiento']} → {interna['validacion']}) y solo puede recortar el "
        "entrenamiento.", e["texto"]))
    con_lift = "lift_k_validacion_antes" in estrategias
    filas = []
    for f in estrategias.itertuples():
        efecto = "el modelo no cambia" if f.modelo_sin_cambios else f.efecto_validacion
        fila = [f"<b>{f.estrategia}</b> (contra el {f.problema})<br/>{f.cambio}",
                f"{numero(f.puntaje_validacion_antes)} → {numero(f.puntaje_validacion_despues)}"
                f"<br/><b>{efecto}</b>",
                f"{numero(f.brecha_antes, signo=True)} → {numero(f.brecha_despues, signo=True)}"
                + ("" if f.modelo_sin_cambios else
                   f"<br/>{'se reduce' if f.efecto_brecha == 'reduce' else f.efecto_brecha}")]
        if con_lift:
            fila.append(f"{numero(f.lift_k_validacion_antes, 2)} → "
                        f"{numero(f.lift_k_validacion_despues, 2)}")
        fila.append(f.diagnostico_antes if f.diagnostico_antes == f.diagnostico_despues
                    else f"{f.diagnostico_antes} → {f.diagnostico_despues}")
        filas.append(fila)
    encabezados = ["Estrategia y cambio aplicado", f"PR-AUC {val}", "Brecha"]
    anchos = [4.6, 2.2, 2.3]
    if con_lift:
        encabezados.append("Lift@k")
        anchos.append(1.9)
    h.append(_tabla(encabezados + ["Diagnóstico"], filas, anchos + [2.0], e))
    h.append(Paragraph("Tabla 2. Antes → después de cada estrategia. Las palabras «mejora» y "
                       "«empeora» se refieren a la PR-AUC; el efecto sobre la brecha se juzga "
                       "por su tamaño (valor absoluto).", e["pie"]))
    h.append(_figura(fig / f"{fuente}_23_estrategias.png",
                     "Figura 5. Efecto de cada estrategia sobre la PR-AUC de validación, la "
                     "brecha y el Lift@k por familia.", e))
    h += _vinetas(_estrategias(estrategias, val), e)

    # ---- Conclusiones --------------------------------------------------------------
    h.append(Paragraph("6. Conclusiones y recomendaciones futuras", e["h1"]))
    h.append(Paragraph("Conclusiones", e["h2"]))
    h += _vinetas(c["balance"] + [
        "Una brecha pequeña no basta para dar por bueno un modelo: también debe superar al "
        "azar con margen. Medir las dos cosas evita confundir estabilidad con utilidad.",
        "Reducir la brecha y mejorar la validación son efectos distintos. La Tabla 2 los "
        "muestra por separado para cada estrategia.",
    ], e)
    h.append(Paragraph("Limitaciones", e["h2"]))
    h += _vinetas([
        f"Las estrategias se compararon en {val}, que ya se usó para seleccionar y calibrar "
        "en la Fase 2. Una diferencia pequeña puede ser ruido.",
        f"Hay {principal['eventos_validacion']} eventos en la validación: las diferencias "
        "de pocas milésimas de PR-AUC no son concluyentes.",
        "La validación usa una sola cohorte. Las tasas cambian entre ciclos, así que el "
        "resultado puede no repetirse el año siguiente.",
        "Los umbrales de diagnóstico son reglas prácticas y se fijaron conociendo ya los "
        "resultados de la Fase 2.",
    ], e)
    h.append(Paragraph("Recomendaciones", e["h2"]))
    h += _vinetas([
        "Repetir este diagnóstico cada mayo, cuando se conozca el resultado del ciclo, y "
        "evaluar en esa cohorte nueva las estrategias que aquí mejoraron la validación.",
        "Si se vuelve a entrenar un gradient boosting, elegir el número de iteraciones en "
        "la validación interna y comprobar la curva de pérdida antes de aceptarlo.",
        "Probar información nueva, por ejemplo una señal temprana de intención de la "
        "familia, y medir con estas mismas curvas si eleva la validación.",
        "Conservar la regla D2 para priorizar mientras ningún modelo la supere en una "
        "cohorte que no haya participado en las decisiones.",
    ], e)

    # ---- Referencias ---------------------------------------------------------------
    h.append(Paragraph("7. Referencias técnicas", e["h1"]))
    referencias = [
        "F. Pedregosa <i>et al.</i>, «Scikit-learn: Machine Learning in Python», "
        "<i>Journal of Machine Learning Research</i>, vol. 12, pp. 2825-2830, 2011.",
        "scikit-learn developers, «Validation curves: plotting scores to evaluate models», "
        "Guía de usuario de scikit-learn. https://scikit-learn.org/stable/modules/"
        "learning_curve.html",
        "T. Hastie, R. Tibshirani y J. Friedman, <i>The Elements of Statistical Learning</i>, "
        "2.ª ed. Nueva York: Springer, 2009, cap. 7.",
        "I. Goodfellow, Y. Bengio y A. Courville, <i>Deep Learning</i>. Cambridge, MA: "
        "MIT Press, 2016, caps. 5 y 7.",
        "L. Prechelt, «Early Stopping — But When?», en <i>Neural Networks: Tricks of the "
        "Trade</i>, LNCS 1524. Berlín: Springer, 1998, pp. 55-69.",
        "J. H. Friedman, «Greedy function approximation: A gradient boosting machine», "
        "<i>The Annals of Statistics</i>, vol. 29, n.º 5, pp. 1189-1232, 2001.",
        "H. Zou y T. Hastie, «Regularization and variable selection via the elastic net», "
        "<i>Journal of the Royal Statistical Society: Series B</i>, vol. 67, n.º 2, "
        "pp. 301-320, 2005.",
        "T. Akiba, S. Sano, T. Yanase, T. Ohta y M. Koyama, «Optuna: A Next-generation "
        "Hyperparameter Optimization Framework», en <i>Proc. 25th ACM SIGKDD</i>, 2019, "
        "pp. 2623-2631.",
        "T. Saito y M. Rehmsmeier, «The Precision-Recall Plot Is More Informative than the "
        "ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets», "
        "<i>PLoS ONE</i>, vol. 10, n.º 3, e0118432, 2015.",
    ]
    h += [Paragraph(f"[{i}] {texto}", e["referencia"]) for i, texto in enumerate(referencias, 1)]
    h.append(Spacer(1, 8))
    h.append(Paragraph(
        "Código y resultados: github.com/ggranizo2507/prediccion-matricula-lemas "
        f"({CODIGO.format('notebooks/overfitting_analysis.ipynb')}, "
        f"{CODIGO.format('src/diagnostico.py')}, {CODIGO.format('results/')}).",
        e["izquierda"]))

    def pie_de_pagina(lienzo, documento):
        lienzo.saveState()
        lienzo.setFont("Texto", 7.5)
        lienzo.setFillColor(colors.HexColor(SUAVE))
        etiqueta = "Diagnóstico de sobreajuste y subajuste · LEMAS"
        if sintetico:
            etiqueta += " · versión preliminar con datos sintéticos"
        lienzo.drawString(2 * cm, 1.2 * cm, etiqueta)
        lienzo.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {documento.page}")
        lienzo.restoreState()

    salida.parent.mkdir(parents=True, exist_ok=True)
    documento = SimpleDocTemplate(
        str(salida), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
        bottomMargin=2 * cm, title="Diagnóstico de sobreajuste y subajuste",
        author="Guillermo Granizo y José Ulloa",
        subject="Actividad de la semana 3 · Predicción de matrícula LEMAS")
    documento.build(h, onFirstPage=pie_de_pagina, onLaterPages=pie_de_pagina)
    return salida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fuente", choices=["real", "sintetica"], default="real")
    parser.add_argument("--salida", default=str(RAIZ / "docs" / "diagnostic_report.pdf"))
    args = parser.parse_args(argv)
    try:
        ruta = construir(args.fuente, Path(args.salida))
    except FileNotFoundError as error:
        print(error)
        return 1
    print(f"Reporte generado: {ruta} (fuente: {args.fuente})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
