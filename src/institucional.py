"""
Modo institucional · Del Excel de LEMAS a la lista con nombres (D45).

Permite que el personal de LEMAS use la aplicación sin Colab ni línea de comandos:

1. **Seudonimizar en memoria** el Excel institucional (una hoja por ciclo) con la clave
   del custodio. Reutiliza ``tools/seudonimizar.py``: la misma técnica HMAC-SHA256 del
   cuaderno 00a, así que los seudónimos coinciden.
2. **Reidentificar** la lista de contactos para uso interno (nombres del representante
   y de sus estudiantes).

Reglas de seguridad:
- Solo se usa en modo institucional y en el mismo equipo (``localhost``).
- Nada se guarda en disco: el Excel, la clave y el padrón viven en la memoria de la
  sesión y se descartan al cerrar la aplicación o al pulsar «Borrar datos de la sesión».
- El modelo y la priorización siguen recibiendo solo la base seudonimizada.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.data_processing import anio_de_ciclo
from src.inferencia import PATRON_IDENTIFICADOR, ErrorEntrada
from src.utils import completar_anoa_desde_hoja, unificar_alias
from tools import seudonimizar as seud

EXTENSIONES_EXCEL = (".xlsx", ".xls")
EQUIPOS_LOCALES = ("localhost", "127.0.0.1", "[::1]")


def es_equipo_local(host: str | None) -> bool:
    """True si la aplicación se abrió en el mismo equipo donde se ejecuta.

    `host` es la cabecera Host del navegador (p. ej. ``localhost:8501``). Si no hay
    cabecera (pruebas automáticas) se considera local.
    """
    if not host:
        return True
    nombre = host.strip().lower()
    if nombre.startswith("["):                       # IPv6: [::1]:8501
        nombre = nombre.split("]")[0] + "]"
    else:
        nombre = nombre.split(":")[0]
    return nombre in EQUIPOS_LOCALES


@dataclass
class BaseInstitucional:
    """Resultado de seudonimizar el Excel. `padron` contiene datos personales:
    nunca se guarda, se descarga ni se pasa al modelo."""

    base: pd.DataFrame        # base seudonimizada (equivale a base_seud.csv)
    csv: bytes                # la misma base lista para descargar o procesar
    acta: dict                # acta de extracción (sin datos personales)
    padron: pd.DataFrame      # seudónimo -> nombres y cédulas, solo en memoria
    resumen: dict             # cifras para mostrar al usuario


def nueva_clave() -> str:
    """Clave nueva (solo la primera vez que LEMAS usa el sistema)."""
    return seud.nueva_clave()


def leer_clave(contenido: bytes) -> bytes:
    """Valida el archivo de clave subido por el custodio."""
    try:
        return seud.clave_desde_texto(contenido)
    except ValueError as error:
        raise ErrorEntrada(
            "El archivo de clave no es válido. Debe ser el archivo clave_lemas.key que "
            "guarda el custodio de datos, sin modificar.") from error


def seudonimizar_excel(contenido: bytes, nombre: str, clave: bytes, config: dict
                       ) -> BaseInstitucional:
    """Convierte el Excel institucional en la base seudonimizada, todo en memoria."""
    reglas = config["seudonimizacion"]
    try:
        bruto = seud.leer_tabla(contenido, nombre)
    except Exception as error:   # archivo dañado, con contraseña o que no es Excel
        raise ErrorEntrada(
            "No se pudo leer el Excel. Verifique que sea el archivo institucional (.xlsx), "
            "que no tenga contraseña y que no esté abierto en otro programa.") from error
    if bruto.empty:
        raise ErrorEntrada("El Excel no tiene filas.")

    obligatorias = [reglas["col_estudiante"], reglas["col_familia"], reglas["col_codigo"]]
    faltan = [c for c in obligatorias if c not in bruto.columns]
    if faltan:
        raise ErrorEntrada(
            f"Al Excel le faltan columnas obligatorias: {', '.join(faltan)}. Revise que los "
            "encabezados sean los acordados (ver manual de usuario).")

    # Además de las columnas acordadas, se elimina cualquier otra que parezca un
    # identificador directo (teléfono, correo, dirección, apellidos...).
    extra = [c for c in bruto.columns
             if PATRON_IDENTIFICADOR.match(str(c).strip()) and c not in obligatorias]
    eliminar = list(dict.fromkeys([*reglas["eliminar"], *extra]))
    try:
        base, eliminadas = seud.seudonimizar_tabla(
            bruto, clave, reglas["col_estudiante"], reglas["col_familia"], eliminar,
            derivar_anio_ingreso=True, col_codigo=reglas["col_codigo"])
    except (KeyError, RuntimeError) as error:
        raise ErrorEntrada(f"No se pudo seudonimizar el Excel: {error}") from error

    restantes = seud.columnas_identificatorias(base)
    if restantes:
        raise ErrorEntrada(
            "Por seguridad no se continúa: después de seudonimizar aún hay columnas con "
            f"nombres o cédulas ({', '.join(restantes)}). Elimínelas del Excel o avise al "
            "responsable de datos.")

    csv = base.to_csv(index=False).encode("utf-8")
    salida = "base_seud.csv"
    acta = seud.construir_acta(base, csv, nombre, salida, eliminadas,
                               reglas["col_estudiante"], clave)
    resumen = {
        "filas": len(base),
        "hojas": bruto["hoja"].value_counts().sort_index().to_dict() if "hoja" in bruto else {},
        "estudiantes": int(base["id_seudonimo"].nunique()),
        "familias": int(base["id_familia_seudonimo"].nunique()),
        "sin_cedula_estudiante": int(base["id_seudonimo"].isna().sum()),
        "sin_cedula_representante": int(base["id_familia_seudonimo"].isna().sum()),
        "columnas_eliminadas": eliminadas,
        "huella_clave": seud.huella_clave(clave),
    }
    return BaseInstitucional(base, csv, acta, _padron(bruto, base, config), resumen)


def _padron(bruto: pd.DataFrame, base: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Tabla interna seudónimo -> persona. Las filas de `base` conservan el orden de
    `bruto`, así que se alinean por posición."""
    reglas = config["seudonimizacion"]
    con_anio = completar_anoa_desde_hoja(unificar_alias(bruto, config.get("alias_columnas", {})))
    columnas = config["columnas"]

    def columna(nombre: str) -> pd.Series:
        if nombre in con_anio.columns:
            return con_anio[nombre].astype("string").str.strip()
        return pd.Series(pd.NA, index=con_anio.index, dtype="string")

    return pd.DataFrame({
        "id_estudiante": base["id_seudonimo"].to_numpy(),
        "anio": anio_de_ciclo(columna(columnas["anio_origen"])).to_numpy(),
        "estudiante": columna(reglas["nombre_estudiante"]).to_numpy(),
        "cedula_estudiante": columna(reglas["col_estudiante"]).to_numpy(),
        "representante": columna(reglas["nombre_representante"]).to_numpy(),
        "cedula_representante": columna(reglas["col_familia"]).to_numpy(),
        "curso": columna(columnas["nivel"]).to_numpy(),
        "paralelo": columna(columnas["paralelo"]).to_numpy(),
    }).dropna(subset=["id_estudiante"])


def lista_con_nombres(lista: pd.DataFrame, padron: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Lista de contactos con los datos del representante y de sus estudiantes.

    Uso interno de LEMAS. Para cada estudiante se toma su fila del ciclo `anio`; si no
    existe, la más reciente. Una familia marcada ``IND-`` usa una cédula de representante
    compartida (genérica): se avisa para que Secretaría confirme el contacto.
    """
    if lista.empty:
        return pd.DataFrame()
    orden = padron.assign(_del_ciclo=(padron["anio"] == anio).astype(int)).sort_values(
        ["_del_ciclo", "anio"], ascending=False, na_position="last")
    por_estudiante = orden.drop_duplicates("id_estudiante").set_index("id_estudiante")

    filas = []
    for _, familia in lista.iterrows():
        ids = [i.strip() for i in str(familia["estudiantes_ids"]).split(",") if i.strip()]
        personas = por_estudiante.reindex(ids)
        encontrados = personas.dropna(subset=["estudiante", "representante"], how="all")
        nombres = [
            f"{p.estudiante} ({p.curso})" if pd.notna(p.curso) else str(p.estudiante)
            for p in encontrados.itertuples() if pd.notna(p.estudiante)]
        representantes = encontrados["representante"].dropna()
        cedulas = encontrados["cedula_representante"].dropna()
        generica = str(familia["id_familia"]).startswith("IND-")
        observacion = []
        if generica:
            observacion.append("cédula de representante compartida: confirmar el contacto")
        if len(encontrados) < len(ids):
            observacion.append("estudiante no encontrado en el Excel")
        filas.append({
            "puesto": familia["puesto"],
            "sede": familia["sede"],
            "representante": representantes.iloc[0] if len(representantes) else pd.NA,
            "cedula_representante": cedulas.iloc[0] if len(cedulas) else pd.NA,
            "estudiantes": "; ".join(nombres),
            "motivo": familia["motivo"],
            "observacion": "; ".join(observacion),
            "id_familia": familia["id_familia"],
        })
    return pd.DataFrame(filas)
