"""
Alcance de la lista de contactos: por qué no llega a más familias y qué lo mejoraría.

En la prueba final la regla D2 alcanzó al 30 % de las familias que no pagaron la matrícula
en plazo. Este módulo estudia el 70 % restante con tres análisis **descriptivos** sobre las
cohortes ya usadas en el proyecto (nunca la de prueba, C5):

1. `desglose_evento`: «no pagar en plazo» mezcla a quien paga tarde y a quien no registra
   pago. ¿A cuál de los dos encuentra la lista?
2. `alcance_por_k`: cuántos casos se alcanzarían con más (o menos) contactos.
3. `foto_semanal` y `campana`: qué pasa si la lista se actualiza durante la campaña con
   quién sigue sin pagar, en lugar de fijarla el 20 de febrero.

Ninguno cambia el sistema validado: son insumos para decidir cómo usarlo. Las cohortes de
este análisis son las mismas con las que se exploraron los datos y se eligió la regla, así
que sus cifras describen, no validan.

Privacidad: los conteos entre 1 y `minimo` − 1 se ocultan, y cuando en una fila de cohortes
queda una sola celda oculta se oculta otra más, para que no se deduzca del total. El desglose
por tipo solo se publica por cohorte si ninguna de sus celdas es pequeña, y la foto semanal
solo se publica para el conjunto de las cohortes.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.diagnostico import numero, sin_prueba
from src.evaluate import consolidar_familias, primeras_k
from src.modeling import OCULTO, puntajes_reglas
from src.utils import Cohorte, celda_complementaria

REGLA = "D2 · señales administrativas"
TODAS = "Todas"
MULTIPLICADORES = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0)
TIPOS = {"tardia": "Todos pagan, el último después del 30 de abril",
         "parcial": "Paga por unos estudiantes y no por otros",
         "sin_pago": "No registra ningún pago"}

__all__ = ["REGLA", "TODAS", "TIPOS", "sin_prueba", "numero", "tabla_familias", "seleccionar",
           "desglose_evento", "alcance_por_k", "foto_semanal", "campana",
           "presupuesto_semanal", "conclusiones"]


# --------------------------------------------------------------------------- #
# Tabla de familias
# --------------------------------------------------------------------------- #
def tabla_familias(datos: pd.DataFrame, cohortes: dict[str, Cohorte]) -> pd.DataFrame:
    """Una fila por (cohorte, representante) con el puntaje D2, el evento y cómo terminó.

    - `tipo`: «en_plazo» (todos sus estudiantes pagaron hasta H), «tardia» (todos pagaron,
      el último después de H), «parcial» (pagó por unos estudiantes y por otros no) o
      «sin_pago» (ningún estudiante registra pago en el ciclo de destino).
    - `dia_resuelta`: días desde t0 hasta que la familia terminó de pagar (NaN si nunca).
      Hasta ese día la familia sigue pendiente y tiene sentido contactarla.
    - `dias_tarde`: días después de H en que pagó, para las tardías.
    - `dias_ventana`: días entre t0 y H en su cohorte (69, o 70 en año bisiesto).

    Cada cohorte se consolida por separado y en el mismo orden que en la validación, para
    que la selección (incluido el sorteo entre empatados) sea la misma.
    """
    partes = []
    for _, grupo in datos.groupby("cohorte", sort=True):
        partes.append(consolidar_familias(grupo, puntajes_reglas(grupo)[REGLA]))
    familias = pd.concat(partes, ignore_index=True)
    pagos = datos.assign(_sin=datos["fecha_pago_destino"].isna()).groupby(
        ["cohorte", "id_familia"]).agg(alguno_sin_pago=("_sin", "any"),
                                       ninguno_paga=("_sin", "all"),
                                       ultimo_pago=("fecha_pago_destino", "max")).reset_index()
    familias = familias.merge(pagos, on=["cohorte", "id_familia"], how="left")
    t0 = familias["cohorte"].map(lambda c: cohortes[c].t0)
    h = familias["cohorte"].map(lambda c: cohortes[c].h)
    familias["dias_ventana"] = (h - t0).dt.days
    dias = (familias["ultimo_pago"] - t0).dt.days.astype(float)
    familias["dia_resuelta"] = dias.where(~familias["alguno_sin_pago"])
    familias["tipo"] = np.select(
        [familias["evento"] == 0, familias["ninguno_paga"], familias["alguno_sin_pago"]],
        ["en_plazo", "sin_pago", "parcial"], "tardia")
    tarde = (familias["ultimo_pago"] - h).dt.days.astype(float)
    familias["dias_tarde"] = tarde.where(familias["tipo"] == "tardia")
    return familias.drop(columns=["ultimo_pago", "alguno_sin_pago", "ninguno_paga"])


def _k(k_por_sede: dict, sede: str, multiplicador: float | None) -> int | None:
    """k de la sede con un multiplicador; None significa «todas las familias»."""
    if multiplicador is None:
        return None
    return max(math.floor(k_por_sede.get(str(sede), 0) * multiplicador + 0.5), 0)


def seleccionar(familias: pd.DataFrame, k_por_sede: dict, semilla: int,
                multiplicador: float | None = 1.0) -> pd.Series:
    """Marca las familias que entran en la lista (misma función que la validación)."""
    elegidas: list = []
    for (_, sede), grupo in familias.groupby(["cohorte", "sede"]):
        k = _k(k_por_sede, sede, multiplicador)
        elegidas.extend(primeras_k(grupo, len(grupo) if k is None else k, semilla).index)
    return pd.Series(familias.index.isin(elegidas), index=familias.index)


def _por_cohorte(familias: pd.DataFrame):
    """Itera (nombre, familias) por cohorte y al final el conjunto («Todas»)."""
    for nombre, grupo in familias.groupby("cohorte"):
        yield str(nombre), grupo
    yield TODAS, familias


def _tasa(numerador: float, denominador: float) -> float:
    return round(numerador / denominador, 4) if denominador else np.nan


def _ocultar(tabla: pd.DataFrame, columna: str, dependientes: list[str], minimo: int,
             grupo: str | None = None, filas: pd.Series | None = None) -> None:
    """Oculta los conteos entre 1 y `minimo` − 1 de `columna` y las tasas que los delatan.

    Supresión complementaria: dentro de cada bloque de cohortes (el definido por `grupo`, o
    toda la tabla), si queda una sola cohorte oculta se oculta también la visible más
    pequeña, porque la fila «Todas» permitiría deducirla. `filas` limita a qué filas se aplica.
    """
    valores = pd.to_numeric(tabla[columna], errors="coerce")
    aplica = pd.Series(True, index=tabla.index) if filas is None else filas
    chicas = (valores > 0) & (valores < minimo) & aplica
    if not chicas.any():
        return
    ocultas = chicas.copy()
    cohortes = (tabla["cohorte"] != TODAS) & aplica
    bloques = tabla[cohortes].groupby(grupo, sort=False) if grupo else [(None, tabla[cohortes])]
    for _, bloque in bloques:
        otra = celda_complementaria(valores[bloque.index], chicas[bloque.index])
        if otra is not None:
            ocultas[otra] = True
    tabla[columna] = tabla[columna].astype(object)
    tabla.loc[ocultas & ~chicas, columna] = OCULTO
    tabla.loc[chicas, columna] = f"<{minimo}"
    tabla.loc[ocultas, dependientes] = np.nan


# --------------------------------------------------------------------------- #
# 1. ¿Qué hay dentro del evento?
# --------------------------------------------------------------------------- #
def desglose_evento(familias: pd.DataFrame, k_por_sede: dict, semilla: int,
                    minimo: int = 5) -> pd.DataFrame:
    """Casos por tipo y cuántos de cada tipo están en la lista.

    Las columnas por tipo se publican por cohorte solo si ninguna celda (casos, aciertos o
    casos fuera de la lista) es menor que `minimo`; de lo contrario quedan solo en la fila
    «Todas», para que nada se deduzca por diferencia. En «Todas» se oculta celda a celda
    (`_proteger_total`): lo pequeño se oculta y, si queda una sola celda oculta, otra más.
    """
    en_lista = seleccionar(familias, k_por_sede, semilla)
    filas = []
    for nombre, grupo in _por_cohorte(familias.assign(en_lista=en_lista)):
        fila = {"cohorte": nombre, "familias": len(grupo), "eventos": int(grupo["evento"].sum()),
                "en_lista": int(grupo["en_lista"].sum()),
                "aciertos": int((grupo["en_lista"] & (grupo["evento"] == 1)).sum())}
        fila["recall"] = _tasa(fila["aciertos"], fila["eventos"])
        for tipo in TIPOS:
            del_tipo = grupo["tipo"] == tipo
            fila[tipo] = int(del_tipo.sum())
            fila[f"aciertos_{tipo}"] = int((del_tipo & grupo["en_lista"]).sum())
            fila[f"recall_{tipo}"] = _tasa(fila[f"aciertos_{tipo}"], fila[tipo])
            fila[f"pct_{tipo}"] = _tasa(fila[tipo], fila["eventos"])
        tarde = grupo["dias_tarde"].dropna()
        pronto, despues = int((tarde <= 30).sum()), int((tarde > 30).sum())
        publicable = min(pronto, despues) >= minimo or 0 in (pronto, despues)
        fila["mediana_dias_tarde"] = float(tarde.median()) if len(tarde) >= minimo else np.nan
        fila["pct_tardia_hasta_30_dias"] = (_tasa(pronto, len(tarde))
                                            if len(tarde) >= minimo and publicable else np.nan)
        filas.append(fila)
    tabla = pd.DataFrame(filas)

    conteos = [c for tipo in TIPOS for c in (tipo, f"aciertos_{tipo}")]
    derivadas = [c for tipo in TIPOS for c in (f"recall_{tipo}", f"pct_{tipo}")]
    derivadas += ["mediana_dias_tarde", "pct_tardia_hasta_30_dias"]
    celdas = tabla[conteos].copy()
    for tipo in TIPOS:                                   # también los casos fuera de la lista
        celdas[f"fuera_{tipo}"] = tabla[tipo] - tabla[f"aciertos_{tipo}"]
    chica = ((celdas > 0) & (celdas < minimo)).any(axis=1)
    es_total = tabla["cohorte"] == TODAS
    tabla[conteos] = tabla[conteos].astype(object)
    if chica[~es_total].any():                           # alguna cohorte con celdas pequeñas
        tabla.loc[~es_total, conteos] = OCULTO
        tabla.loc[~es_total, derivadas] = np.nan
    if chica[es_total].any():                            # el total también
        _proteger_total(tabla, tabla.index[es_total][0], minimo)
    _ocultar(tabla, "aciertos", ["recall"], minimo)
    return tabla


def _proteger_total(tabla: pd.DataFrame, fila, minimo: int) -> None:
    """Oculta en la fila «Todas» del desglose solo lo necesario.

    - Casos por tipo: se oculta el que tenga entre 1 y `minimo` − 1 («<minimo») y, si es el
      único, también el menor de los otros («oculto»), porque el total de casos es público.
    - Aciertos por tipo: se ocultan si sus casos están ocultos, o si los aciertos o los casos
      fuera de la lista son pequeños; con la misma regla de la segunda celda.
    """
    casos = pd.Series({t: int(tabla.at[fila, t]) for t in TIPOS})
    aciertos = pd.Series({t: int(tabla.at[fila, f"aciertos_{t}"]) for t in TIPOS})

    def pequena(serie):
        return (serie > 0) & (serie < minimo)

    casos_ocultos = pequena(casos)
    otra = celda_complementaria(casos, casos_ocultos)
    if otra is not None:
        casos_ocultos[otra] = True
    aciertos_ocultos = casos_ocultos | pequena(aciertos) | pequena(casos - aciertos)
    otra = celda_complementaria(aciertos, aciertos_ocultos)
    if otra is not None:
        aciertos_ocultos[otra] = True
    for tipo in TIPOS:
        if casos_ocultos[tipo]:
            tabla.at[fila, tipo] = f"<{minimo}" if 0 < casos[tipo] < minimo else OCULTO
            tabla.at[fila, f"pct_{tipo}"] = np.nan
        if aciertos_ocultos[tipo]:
            chico = 0 < aciertos[tipo] < minimo and not casos_ocultos[tipo]
            tabla.at[fila, f"aciertos_{tipo}"] = f"<{minimo}" if chico else OCULTO
            tabla.at[fila, f"recall_{tipo}"] = np.nan
    if casos_ocultos["tardia"]:
        tabla.loc[fila, ["mediana_dias_tarde", "pct_tardia_hasta_30_dias"]] = np.nan


# --------------------------------------------------------------------------- #
# 2. ¿Y con más contactos?
# --------------------------------------------------------------------------- #
def alcance_por_k(familias: pd.DataFrame, k_por_sede: dict, semilla: int,
                  multiplicadores: tuple = MULTIPLICADORES, personal: int | None = None,
                  semanas: int = 10, minimo: int = 5) -> pd.DataFrame:
    """Recall, precisión y Lift de la lista D2 al cambiar el número de contactos.

    `multiplicador` se aplica al k aprobado de cada sede; la última fila («todas») es
    contactar a todas las familias. `recall_azar` es lo que alcanzaría una selección al azar
    del mismo tamaño. `contactos_por_persona_semana` reparte los contactos de una campaña
    entre el personal y las semanas de la ventana.
    """
    filas = []
    n_cohortes = familias["cohorte"].nunique()
    for multiplicador in [*multiplicadores, None]:
        en_lista = seleccionar(familias, k_por_sede, semilla, multiplicador)
        for nombre, grupo in _por_cohorte(familias.assign(en_lista=en_lista)):
            contactos = int(grupo["en_lista"].sum())
            eventos = int(grupo["evento"].sum())
            aciertos = int((grupo["en_lista"] & (grupo["evento"] == 1)).sum())
            tasa = eventos / len(grupo)
            precision = _tasa(aciertos, contactos)
            campanas = n_cohortes if nombre == TODAS else 1
            fila = {"cohorte": nombre,
                    "multiplicador": "todas" if multiplicador is None else multiplicador,
                    "contactos": contactos, "pct_familias": _tasa(contactos, len(grupo)),
                    "aciertos": aciertos, "recall": _tasa(aciertos, eventos),
                    "precision": precision,
                    "lift": round(precision / tasa, 4) if tasa else np.nan,
                    "recall_azar": _tasa(contactos, len(grupo))}
            if personal:
                fila["contactos_por_persona_semana"] = round(
                    contactos / campanas / personal / semanas, 2)
            filas.append(fila)
    tabla = pd.DataFrame(filas)
    _ocultar(tabla, "aciertos", ["recall", "precision", "lift"], minimo, grupo="multiplicador")
    return tabla


# --------------------------------------------------------------------------- #
# 3. ¿Y si la lista se actualiza durante la campaña?
# --------------------------------------------------------------------------- #
def _pendientes(familias: pd.DataFrame, dia: int) -> pd.Series:
    """Familias que el día `dia` (desde t0) aún no terminan de pagar."""
    return familias["dia_resuelta"].isna() | (familias["dia_resuelta"] >= dia)


def foto_semanal(familias: pd.DataFrame, k_por_sede: dict, semilla: int, semanas: int = 10,
                 minimo: int = 5) -> pd.DataFrame:
    """La misma lista de k familias, hecha cada semana solo con quienes siguen sin pagar.

    Quien paga sale del grupo, y quien no pagará en plazo sigue en él hasta el final: el
    grupo se achica y la proporción de casos sube, con o sin regla. Cerca de H, «seguir
    pendiente» es casi lo mismo que ser un caso.

    Se publica solo el conjunto de las cohortes. Una semana se oculta si entre ella y la
    última semana publicada pagaron entre 1 y `minimo` − 1 familias, o si le quedan tan
    pocas por pagar en plazo: así ningún conteo pequeño se deduce por diferencia.
    """
    filas = []
    eventos = int(familias["evento"].sum())
    campanas = max(familias["cohorte"].nunique(), 1)
    k_total = int(seleccionar(familias, k_por_sede, semilla).sum())
    for semana in range(semanas):
        dia = 7 * semana
        pendientes = familias[_pendientes(familias, dia)]
        en_lista = seleccionar(pendientes, k_por_sede, semilla)
        contactos = int(en_lista.sum())
        aciertos = int((en_lista & (pendientes["evento"] == 1)).sum())
        tasa = eventos / len(pendientes) if len(pendientes) else np.nan
        precision = _tasa(aciertos, contactos)
        filas.append({"cohorte": TODAS, "semana": semana + 1, "dia": dia,
                      "pendientes": len(pendientes),
                      "pct_pendientes": _tasa(len(pendientes), len(familias)),
                      "pendientes_por_campana": int(round(len(pendientes) / campanas)),
                      "veces_k": round(len(pendientes) / k_total, 2) if k_total else np.nan,
                      "pagaran_en_plazo": len(pendientes) - eventos,
                      "eventos": eventos, "tasa_base": round(tasa, 4),
                      "contactos": contactos, "aciertos": aciertos,
                      "recall": _tasa(aciertos, eventos), "precision": precision,
                      "lift": round(precision / tasa, 4) if tasa else np.nan,
                      "recall_azar": _tasa(contactos, len(pendientes)),
                      "dias_ventana_restante": int(familias["dias_ventana"].min()) - dia})
    tabla = pd.DataFrame(filas)
    _ocultar(tabla, "aciertos", ["recall", "precision", "lift"], minimo)

    ocultar, ultima_publicada = [], None
    for indice, fila in tabla.iterrows():
        pagaron = 0 if ultima_publicada is None else ultima_publicada - fila["pendientes"]
        if 0 < pagaron < minimo or 0 < fila["pagaran_en_plazo"] < minimo:
            ocultar.append(indice)
        else:
            ultima_publicada = fila["pendientes"]
    if ocultar:
        conteos = ["pendientes", "pagaran_en_plazo", "contactos"]
        tabla[conteos] = tabla[conteos].astype(object)
        tabla.loc[ocultar, conteos] = OCULTO
        tabla.loc[ocultar, ["pct_pendientes", "pendientes_por_campana", "veces_k", "tasa_base",
                            "precision", "lift", "recall_azar"]] = np.nan
    return tabla


def presupuesto_semanal(k: int, semanas: int) -> list[int]:
    """Reparte k contactos en `semanas` partes lo más parejas posible (suman k)."""
    base, resto = divmod(int(k), semanas)
    return [base + (1 if i < resto else 0) for i in range(semanas)]


MEDIDAS = ("cupos", "llamadas", "aciertos", "aciertos_primera_mitad", "suma_margen")


def _medir(cupos: int, llamadas: pd.DataFrame, semana_de_llamada: np.ndarray,
           semanas: int) -> np.ndarray:
    """Resume una campaña: cupos, llamadas hechas, aciertos, aciertos en la primera mitad de
    las semanas y suma de los días que faltaban hasta H al empezar la semana de cada acierto."""
    acierto = llamadas["evento"].to_numpy() == 1
    margen = llamadas["dias_ventana"].to_numpy() - 7 * semana_de_llamada
    return np.array([cupos, len(llamadas), acierto.sum(),
                     (acierto & (semana_de_llamada < semanas / 2)).sum(),
                     margen[acierto].sum()], dtype=float)


def _orden(grupo: pd.DataFrame, semilla: int, usar_regla: bool) -> pd.DataFrame:
    """Todas las familias en el orden de la lista (el sorteo de empates se hace una vez)."""
    datos = grupo if usar_regla else grupo.assign(score=0.0)
    return grupo.loc[primeras_k(datos, len(datos), semilla).index]


def _fija_inicio(orden: pd.DataFrame, k: int, semanas: int) -> np.ndarray:
    """La lista del 20 de febrero, llamada entera en la primera semana."""
    lista = orden.head(k)
    return _medir(k, lista, np.zeros(len(lista), dtype=int), semanas)


def _fija_repartida(orden: pd.DataFrame, k: int, semanas: int) -> np.ndarray:
    """La lista del 20 de febrero, repartida en la campaña. A quien ya pagó cuando le toca
    el turno no se le llama, y su cupo queda sin usar."""
    lista = orden.head(k)
    semana = np.repeat(np.arange(semanas), presupuesto_semanal(len(lista), semanas))
    sigue_pendiente = ~(lista["dia_resuelta"].to_numpy() < 7 * semana)     # NaN: pendiente
    return _medir(k, lista[sigue_pendiente], semana[sigue_pendiente], semanas)


def _semanal(orden: pd.DataFrame, k: int, semanas: int) -> np.ndarray:
    """Mismo orden, pero cada semana se llama a las siguientes familias que aún no pagan:
    el cupo de quien ya pagó pasa a la siguiente de la lista."""
    resuelta = orden["dia_resuelta"].to_numpy()
    disponible = np.ones(len(orden), dtype=bool)
    posiciones: list[int] = []
    semana_de_llamada: list[int] = []
    for semana, cupo in enumerate(presupuesto_semanal(k, semanas)):
        pendiente = disponible & ~(resuelta < 7 * semana)
        elegidas = np.flatnonzero(pendiente)[:cupo]
        disponible[elegidas] = False
        posiciones.extend(elegidas)
        semana_de_llamada.extend([semana] * len(elegidas))
    return _medir(k, orden.iloc[posiciones], np.array(semana_de_llamada, dtype=int), semanas)


ESTRATEGIAS = {
    "fija_inicio_d2": ("Lista fija, toda en la semana 1 · regla D2", _fija_inicio, True),
    "fija_repartida_d2": ("Lista fija, repartida en la campaña · regla D2", _fija_repartida,
                          True),
    "semanal_d2": ("Lista semanal · regla D2", _semanal, True),
    "fija_inicio_azar": ("Lista fija, toda en la semana 1 · al azar", _fija_inicio, False),
    "semanal_azar": ("Lista semanal · al azar", _semanal, False),
}


def campana(familias: pd.DataFrame, k_por_sede: dict, semilla: int, semanas: int = 10,
            repeticiones: int = 100, minimo: int = 5) -> pd.DataFrame:
    """Compara tres formas de usar los mismos k contactos, con y sin regla.

    - Lista fija en la semana 1: el mejor caso del diseño actual (todo el margen de tiempo).
    - Lista fija repartida: se llama en orden durante la campaña y se salta a quien ya pagó.
    - Lista semanal: igual, pero el cupo de quien ya pagó pasa a la siguiente familia
      pendiente del mismo orden. Por construcción no puede alcanzar menos casos que la fija.

    Las versiones al azar separan cuánto se gana solo por saber quién sigue pendiente y
    cuánto añade la regla. Alcanzar un caso tarde vale menos que alcanzarlo pronto: por eso
    se informa cuántos aciertos ocurren en la primera mitad de las semanas y el margen medio
    (días que faltaban hasta H al empezar la semana de la llamada).

    Las estrategias con regla usan el sorteo de empates de la validación (`semilla`);
    `recall_medio`, `recall_min` y `recall_max` muestran cuánto cambian con otros
    `repeticiones` sorteos. Las estrategias al azar son el promedio de `repeticiones` órdenes
    al azar.

    Supuesto: las fechas de pago son las históricas, como si las llamadas no las cambiaran.
    """
    filas = []
    nombres = [str(c) for c in familias["cohorte"].unique()] + [TODAS]
    eventos = {nombre: int(grupo["evento"].sum()) for nombre, grupo in _por_cohorte(familias)}
    posicion = {m: i for i, m in enumerate(MEDIDAS)}
    for clave, (etiqueta, funcion, usar_regla) in ESTRATEGIAS.items():
        semillas = ([semilla] if usar_regla else []) + [
            semilla + 1000 + r for r in range(repeticiones)]
        resultados = {nombre: np.zeros((len(semillas), len(MEDIDAS))) for nombre in nombres}
        for i, s in enumerate(semillas):
            for (cohorte, sede), grupo in familias.groupby(["cohorte", "sede"]):
                medidas = funcion(_orden(grupo, s, usar_regla),
                                  int(k_por_sede.get(str(sede), 0)), semanas)
                for nombre in (str(cohorte), TODAS):
                    resultados[nombre][i] += medidas
        for nombre in nombres:
            # con regla: el sorteo de la validación; al azar: el promedio de los sorteos
            valores = resultados[nombre][0] if usar_regla else resultados[nombre].mean(axis=0)
            medidas = dict(zip(MEDIDAS, valores, strict=True))
            recalls = resultados[nombre][:, posicion["aciertos"]] / max(eventos[nombre], 1)
            aciertos = medidas["aciertos"]
            filas.append({
                "cohorte": nombre, "estrategia": clave, "descripcion": etiqueta,
                "con_regla": usar_regla, "cupos": int(medidas["cupos"]),
                "llamadas": round(medidas["llamadas"], 1),
                "cupos_sin_usar": round(medidas["cupos"] - medidas["llamadas"], 1),
                "aciertos": round(aciertos, 1), "eventos": eventos[nombre],
                "recall": _tasa(aciertos, eventos[nombre]),
                "recall_medio": round(float(recalls.mean()), 4),
                "recall_min": round(float(recalls.min()), 4),
                "recall_max": round(float(recalls.max()), 4),
                "precision": _tasa(aciertos, medidas["llamadas"]),
                "aciertos_primera_mitad": round(medidas["aciertos_primera_mitad"], 1),
                "recall_primera_mitad": _tasa(medidas["aciertos_primera_mitad"],
                                              eventos[nombre]),
                "margen_medio_dias": (round(medidas["suma_margen"] / aciertos, 1)
                                      if aciertos else np.nan)})
    tabla = pd.DataFrame(filas)
    # Solo los conteos reales (estrategias con regla); los promedios al azar no lo son
    reales = tabla["con_regla"]
    _ocultar(tabla, "aciertos", ["recall", "recall_medio", "recall_min", "recall_max",
                                 "precision", "margen_medio_dias"], minimo, grupo="estrategia",
             filas=reales)
    _ocultar(tabla, "aciertos_primera_mitad", ["recall_primera_mitad"], minimo,
             grupo="estrategia", filas=reales)
    return tabla.drop(columns="con_regla")


# --------------------------------------------------------------------------- #
# Lectura de los resultados
# --------------------------------------------------------------------------- #
def _hay(*valores) -> bool:
    """True si todos los valores son números publicables (ni texto ni NaN)."""
    return all(isinstance(v, (int, float, np.integer, np.floating)) and np.isfinite(v)
               for v in valores)


def _pct(valor: float, decimales: int = 0) -> str:
    return f"{numero(100 * valor, decimales)} %"


def _diferencia(a: float, b: float) -> int:
    """Diferencia en puntos porcentuales entre dos tasas, tal como se leen ya redondeadas."""
    return int(round(100 * a)) - int(round(100 * b))


def _enumerar(partes: list[str]) -> str:
    return partes[0] if len(partes) == 1 else ", ".join(partes[:-1]) + " y " + partes[-1]


def conclusiones(desglose: pd.DataFrame, por_k: pd.DataFrame, semanal: pd.DataFrame,
                 estrategias: pd.DataFrame) -> dict[str, list[str]]:
    """Frases que resumen cada análisis, escritas a partir de las cifras (fila «Todas»).

    Una frase solo se escribe si todas sus cifras son publicables, y las comparaciones dicen
    «más», «menos» o «igual» según el signo de la diferencia.
    """
    textos: dict[str, list[str]] = {"desglose": [], "por_k": [], "semanal": [], "campana": []}

    total = desglose[desglose["cohorte"] == TODAS].iloc[0]
    frases = {"tardia": ("pagaron todo después del 30 de abril", "pagan tarde"),
              "parcial": ("pagaron por unos estudiantes y no por otros", "pagan en parte"),
              "sin_pago": ("no registran ningún pago", "no registran ningún pago")}
    visibles = [t for t in TIPOS if _hay(total[t])]
    if not visibles:
        textos["desglose"].append("Las celdas del desglose tienen menos casos que el mínimo "
                                  "publicable; no se muestra.")
    else:
        partes = [f"{int(total[t])} ({_pct(total[f'pct_{t}'])}) {frases[t][0]}"
                  for t in visibles]
        frase = (f"De {int(total['eventos'])} familias que no pagaron en plazo, "
                 f"{_enumerar(partes)}.")
        ocultos = [t for t in TIPOS if t not in visibles]
        if ocultos:
            resto = int(total["eventos"]) - sum(int(total[t]) for t in visibles)
            frase += (f" Las otras {resto} se reparten entre las que "
                      f"{_enumerar([frases[t][1] for t in ocultos])}; el detalle no se publica "
                      f"porque alguna celda es menor que el mínimo.")
        textos["desglose"].append(frase)
        partes = [f"al {_pct(total[f'recall_{t}'])} de las que {frases[t][1]}"
                  for t in TIPOS if _hay(total[f"recall_{t}"])]
        if partes:
            textos["desglose"].append("La lista alcanza " + _enumerar(partes) + ".")
        if _hay(total["mediana_dias_tarde"]):
            frase = (f"Quienes pagan tarde lo hacen a una mediana de "
                     f"{int(total['mediana_dias_tarde'])} días después del 30 de abril")
            if _hay(total["pct_tardia_hasta_30_dias"]):
                frase += (f"; el {_pct(total['pct_tardia_hasta_30_dias'])} paga dentro de los "
                          "30 días siguientes")
            textos["desglose"].append(frase + ".")

    k_total = por_k[por_k["cohorte"] == TODAS].set_index("multiplicador")
    actual, doble, todas = k_total.loc[1.0], k_total.loc[2.0], k_total.loc["todas"]
    if _hay(actual["recall"], actual["recall_azar"]):
        textos["por_k"].append(
            f"Con el k aprobado se contacta al {_pct(actual['pct_familias'])} de las familias "
            f"y se alcanza al {_pct(actual['recall'])} de los casos (al azar: "
            f"{_pct(actual['recall_azar'])}).")
    if _hay(doble["recall"], doble["precision"], actual["precision"]):
        textos["por_k"].append(
            f"Con el doble de contactos ({_pct(doble['pct_familias'])} de las familias) se "
            f"alcanza al {_pct(doble['recall'])} (al azar: {_pct(doble['recall_azar'])}); la "
            f"precisión pasa de {numero(actual['precision'])} a {numero(doble['precision'])}.")
    lifts = pd.to_numeric(por_k[(por_k["cohorte"] != TODAS)
                                & (por_k["multiplicador"].astype(str) == "1.0")]["lift"],
                          errors="coerce").dropna()
    if len(lifts) > 1:
        textos["por_k"].append(
            f"Con el k aprobado, el Lift de la lista va de {numero(lifts.min(), 2)} a "
            f"{numero(lifts.max(), 2)} según la cohorte.")
    if "contactos_por_persona_semana" in k_total:
        textos["por_k"].append(
            f"Contactar a todas las familias equivale a "
            f"{numero(todas['contactos_por_persona_semana'], 1)} contactos por persona y semana; "
            f"con el k aprobado son {numero(actual['contactos_por_persona_semana'], 1)}.")

    foto = semanal[semanal["cohorte"] == TODAS].set_index("semana")
    foto = foto[[_hay(*fila) for fila in foto[["tasa_base", "recall", "recall_azar"]].to_numpy()]]
    if len(foto) >= 3:
        primera, mitad, ultima = foto.iloc[0], foto.iloc[len(foto) // 2], foto.iloc[-1]
        textos["semanal"].append(
            f"En la semana {int(mitad.name)} sigue sin pagar el {_pct(mitad['pct_pendientes'])} "
            f"de las familias, y en la {int(ultima.name)} el {_pct(ultima['pct_pendientes'])}. "
            f"La proporción de casos entre las pendientes pasa de {_pct(primera['tasa_base'], 1)} "
            f"en la semana {int(primera.name)} a {_pct(mitad['tasa_base'], 1)} y "
            f"{_pct(ultima['tasa_base'], 1)}.")
        textos["semanal"].append(
            f"Una lista de k familias hecha en la semana {int(mitad.name)} contendría al "
            f"{_pct(mitad['recall'])} de los casos, frente al {_pct(primera['recall'])} de la "
            f"semana {int(primera.name)}. Elegir al azar entre las pendientes daría "
            f"{_pct(mitad['recall_azar'])}: la mayor parte de la diferencia viene de saber "
            f"quién sigue sin pagar, no de la regla.")

        parcial = (pd.to_numeric(foto["contactos"], errors="coerce")
                   < pd.to_numeric(foto["pendientes"], errors="coerce"))   # la lista no cubre todo
        mejor_azar = foto[parcial & (pd.to_numeric(foto["lift"], errors="coerce") <= 1.0)]
        if len(mejor_azar) and int(mejor_azar.index[0]) > int(primera.name):
            semana = int(mejor_azar.index[0])
            textos["semanal"].append(
                f"Desde la semana {semana}, la regla ya no ordena mejor que el azar entre las "
                f"familias que siguen sin pagar: su ventaja está al principio de la campaña.")
        if _hay(mitad.get("pendientes_por_campana"), mitad.get("veces_k")):
            textos["semanal"].append(
                f"En la semana {int(mitad.name)} quedan unas "
                f"{int(mitad['pendientes_por_campana'])} familias pendientes por año "
                f"({numero(mitad['veces_k'], 1)} veces el k aprobado) y el "
                f"{_pct(mitad['tasa_base'])} son casos. Contactarlas a todas alcanzaría a todos "
                f"los casos con {int(mitad['dias_ventana_restante'])} días de margen.")

    camp = estrategias[estrategias["cohorte"] == TODAS].set_index("estrategia")
    inicio, repartida, movil = (camp.loc[c] for c in ("fija_inicio_d2", "fija_repartida_d2",
                                                      "semanal_d2"))
    azar_inicio, azar_movil = camp.loc["fija_inicio_azar"], camp.loc["semanal_azar"]
    if _hay(inicio["recall"], inicio["recall_min"], inicio["recall_max"],
            inicio["recall_medio"]):
        textos["campana"].append(
            f"La lista fija llamada entera en la primera semana alcanza al "
            f"{_pct(inicio['recall'])} de los casos, todos con el margen completo. Según cómo "
            f"caiga el sorteo entre familias empatadas, va de {_pct(inicio['recall_min'])} a "
            f"{_pct(inicio['recall_max'])} (media: {_pct(inicio['recall_medio'])}).")
    if _hay(repartida["cupos_sin_usar"], repartida["recall"]) and repartida["cupos"]:
        textos["campana"].append(
            f"Si esa misma lista se reparte en la campaña, el "
            f"{_pct(repartida['cupos_sin_usar'] / repartida['cupos'])} de sus familias ya habrá "
            f"pagado cuando le llegue el turno. Esos cupos quedan sin usar.")
    if _hay(movil["recall"], movil["recall_primera_mitad"], inicio["recall"],
            azar_movil["recall"], movil["margen_medio_dias"]):
        textos["campana"].append(
            f"La lista semanal da esos cupos a las siguientes familias pendientes y alcanza al "
            f"{_pct(movil['recall'])} en toda la campaña. Hay que leerlo con cuidado: cerca del "
            f"30 de abril casi todas las pendientes son casos (sin regla se llega al "
            f"{_pct(azar_movil['recall'])}) y el margen medio de un acierto baja a "
            f"{numero(movil['margen_medio_dias'], 0)} días.")
        diferencia = _diferencia(movil["recall_primera_mitad"], inicio["recall"])
        if diferencia == 0:
            comparacion = "lo mismo que"
        else:
            comparacion = f"{abs(diferencia)} puntos {'más' if diferencia > 0 else 'menos'} que"
        textos["campana"].append(
            f"En la primera mitad de las semanas, la lista semanal alcanza al "
            f"{_pct(movil['recall_primera_mitad'])} de los casos: {comparacion} la lista fija "
            f"llamada al inicio ({_pct(inicio['recall'])}).")
    if _hay(movil["recall_primera_mitad"], azar_movil["recall_primera_mitad"]):
        aporte = _diferencia(movil["recall_primera_mitad"], azar_movil["recall_primera_mitad"])
        if aporte > 0:
            lectura = f"la regla añade {aporte} puntos"
        elif aporte < 0:
            lectura = f"la regla queda {abs(aporte)} puntos por debajo del azar"
        else:
            lectura = "la regla no añade nada apreciable"
        textos["campana"].append(
            f"Aporte de la regla en la lista semanal, medido en la primera mitad: sin regla "
            f"se alcanza al {_pct(azar_movil['recall_primera_mitad'])} y con ella al "
            f"{_pct(movil['recall_primera_mitad'])}; {lectura}.")
    if _hay(azar_inicio["recall"], inicio["recall"]):
        textos["campana"].append(
            f"En la lista fija, sin regla se alcanza al {_pct(azar_inicio['recall'])} y con "
            f"ella al {_pct(inicio['recall'])}.")
    return textos
