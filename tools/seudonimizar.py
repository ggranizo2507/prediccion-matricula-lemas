"""
Seudonimización reversible solo dentro de LEMAS.

Técnica: HMAC-SHA256 con clave secreta (seudonimización con clave).
- Hacia afuera: el seudónimo es indescifrable. Sin la clave no se puede
  recalcular ni probar por fuerza bruta, aunque la cédula tenga solo 10 dígitos.
- Hacia adentro: quien tiene la clave recalcula el seudónimo sobre el padrón
  institucional y ubica al estudiante o familia (reidentificación).
- Es determinista: el mismo estudiante recibe el mismo código en las cinco
  cohortes, lo que permite enlazar registros sin guardar la cédula.

No existe tabla de correspondencia que proteger: la "información adicional"
que exige la seudonimización es únicamente la clave, custodiada por LEMAS.

Uso (en el entorno autorizado de LEMAS):
    python seudonimizar.py generar-clave --salida C:/custodio/clave_lemas.key
    python seudonimizar.py seudonimizar --entrada base_lemas.xlsx --salida base_seud.csv \
        --clave C:/custodio/clave_lemas.key \
        --col-estudiante CI --col-familia cedulap \
        --derivar-anio-ingreso --col-codigo Codigo \
        --eliminar Codigo Orden "Nombre Completo" "Nombres completos padre de familia" \
                   saldo deuda statusp
    La llave del estudiante es la cédula (no cambia con reingresos ni cambios de sede);
    el código interno solo aporta el año de ingreso y luego se elimina.
    python seudonimizar.py reidentificar --entrada top_k.csv --padron padron.xlsx \
        --clave C:/custodio/clave_lemas.key --col-seudonimo id_familia_seudonimo \
        --col-padron cedula_representante --tipo FAM --salida top_k_interno.csv
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import io
import json
import logging
import secrets
import sys
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("seudonimizar")

LONGITUD_CODIGO = 12  # 12 caracteres base32 = 60 bits; colisiones despreciables
DOMINIOS = {"EST": "estudiante", "FAM": "familia"}


# --------------------------------------------------------------------------- #
# Clave
# --------------------------------------------------------------------------- #
def generar_clave(ruta: Path) -> None:
    """Crea una clave aleatoria de 256 bits. Nunca debe entrar al repositorio."""
    if ruta.exists():
        raise FileExistsError(f"Ya existe {ruta}. No se sobrescribe una clave.")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(nueva_clave(), encoding="utf-8")
    log.info("Clave creada en %s. Guárdela con respaldo cifrado: "
             "si se pierde, no se podrá reidentificar a nadie.", ruta)


def nueva_clave() -> str:
    """Clave aleatoria de 256 bits en hexadecimal (contenido de clave_lemas.key)."""
    return secrets.token_hex(32)


def clave_desde_texto(texto: str | bytes) -> bytes:
    """Convierte el contenido de un archivo de clave (hexadecimal) y valida su longitud."""
    try:
        if isinstance(texto, bytes):
            texto = texto.decode("utf-8-sig")
        clave = bytes.fromhex(texto.strip())
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError("El archivo no contiene una clave válida (hexadecimal).") from exc
    if len(clave) < 32:
        raise ValueError("La clave debe tener al menos 256 bits.")
    return clave


def huella_clave(clave: bytes) -> str:
    """Huella corta para comprobar que se usa la misma clave de siempre.

    No permite recuperar la clave ni recalcular seudónimos: es un SHA-256 truncado.
    """
    digest = hashlib.sha256(b"huella-clave-lemas|" + clave).hexdigest()
    return f"{digest[:4]}-{digest[4:8]}"


def cargar_clave(ruta: Path) -> bytes:
    """Lee la clave hexadecimal y valida su longitud."""
    try:
        return clave_desde_texto(ruta.read_bytes())
    except (OSError, ValueError) as exc:
        raise ValueError(f"No se pudo leer una clave válida en {ruta}") from exc


# --------------------------------------------------------------------------- #
# Núcleo
# --------------------------------------------------------------------------- #
def normalizar(valor: object) -> str | None:
    """Normaliza el identificador para que '0912345678' y 912345678 coincidan."""
    if pd.isna(valor):
        return None
    texto = str(valor).strip().upper()
    if texto.endswith(".0"):  # Excel convierte códigos numéricos en float
        texto = texto[:-2]
    if texto.isdigit() and len(texto) == 9:  # cédula que perdió el cero inicial
        texto = "0" + texto
    return texto or None


def validar_cedula_ec(cedula: str) -> bool:
    """Dígito verificador (módulo 10) de la cédula ecuatoriana."""
    if not (cedula.isdigit() and len(cedula) == 10):
        return False
    provincia = int(cedula[:2])
    if not (1 <= provincia <= 24 or provincia == 30) or int(cedula[2]) >= 6:
        return False
    suma = 0
    for i, digito in enumerate(cedula[:9]):
        producto = int(digito) * (2 if i % 2 == 0 else 1)
        suma += producto - 9 if producto > 9 else producto
    return (10 - suma % 10) % 10 == int(cedula[9])


def seudonimo(valor: object, clave: bytes, tipo: str) -> str | None:
    """Devuelve p. ej. 'EST-K3M9QX2PLA7R'. El prefijo separa dominios:
    el mismo número usado como estudiante y como familia da códigos distintos."""
    if tipo not in DOMINIOS:
        raise ValueError(f"Tipo desconocido: {tipo}")
    texto = normalizar(valor)
    if texto is None:
        return None
    mensaje = f"{tipo}|{texto}".encode()
    digest = hmac.new(clave, mensaje, hashlib.sha256).digest()
    codigo = base64.b32encode(digest).decode("ascii")[:LONGITUD_CODIGO]
    return f"{tipo}-{codigo}"


def anio_ingreso(codigo: object) -> int | None:
    """Los dos primeros dígitos del código interno indican el año de ingreso
    (p. ej. 21xxx -> 2021). Se deriva ANTES de reemplazar el código."""
    texto = normalizar(codigo)
    if not texto or len(texto) < 3 or not texto[:2].isdigit():
        return None
    yy = int(texto[:2])
    return 2000 + yy if yy <= 50 else 1900 + yy


def _verificar_colisiones(originales: pd.Series, codigos: pd.Series, tipo: str) -> None:
    pares = pd.DataFrame({"o": originales.map(normalizar), "c": codigos}).dropna()
    conflictos = pares.drop_duplicates().groupby("c")["o"].nunique()
    if (conflictos > 1).any():
        raise RuntimeError(f"Colisión de seudónimos en {tipo}. Aumente LONGITUD_CODIGO.")


def _clave_encabezado(texto: str) -> str:
    """'Anoa ', 'ANOA' y 'anoa' se tratan como el mismo encabezado."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.lower().split())


def leer_tabla(origen: Path | bytes, nombre: str | None = None) -> pd.DataFrame:
    """Lee CSV o Excel desde una ruta o desde bytes en memoria (aplicación).

    En Excel une todas las hojas (una por ciclo lectivo) y agrega la columna 'hoja'
    para conservar su origen. `nombre` indica la extensión cuando `origen` son bytes.
    """
    if isinstance(origen, bytes):
        sufijo = Path(nombre or "").suffix.lower()
        origen = io.BytesIO(origen)
    else:
        sufijo = Path(origen).suffix.lower()
    if sufijo in {".xlsx", ".xls"}:
        hojas = pd.read_excel(origen, sheet_name=None, dtype=str)
        partes = []
        canonicas: dict[str, str] = {}   # encabezado normalizado -> nombre de la 1.ª hoja
        for nombre, df in hojas.items():
            df = df.dropna(how="all")
            nombres = []
            for c in df.columns:
                limpio = " ".join(str(c).split())
                clave = _clave_encabezado(limpio)
                nombres.append(canonicas.setdefault(clave, limpio))
            df.columns = nombres
            df.insert(0, "hoja", str(nombre))
            partes.append(df)
            log.info("Hoja '%s': %d filas", nombre, len(df))
        todas = set().union(*(set(p.columns) for p in partes))
        for p in partes:
            faltan = sorted(todas - set(p.columns))
            vacias = [c for c in p.columns if c != "hoja" and p[c].isna().all()]
            if faltan:
                log.warning("Hoja '%s': no tiene las columnas %s", p["hoja"].iloc[0], faltan)
            if vacias:
                log.warning("Hoja '%s': columnas completamente vacías %s",
                            p["hoja"].iloc[0], vacias)
        return pd.concat(partes, ignore_index=True)
    return pd.read_csv(origen, dtype=str)


def _leer(ruta: Path) -> pd.DataFrame:
    return leer_tabla(ruta)


def seudonimizar_tabla(
    df: pd.DataFrame,
    clave: bytes,
    col_estudiante: str,
    col_familia: str | None = None,
    eliminar: list[str] | tuple[str, ...] = (),
    derivar_anio_ingreso: bool = False,
    col_codigo: str | None = None,
    validar_cedula: bool = False,
) -> tuple[pd.DataFrame, list[str]]:
    """Reemplaza identificadores por seudónimos. No lee ni escribe archivos.

    Devuelve la tabla seudonimizada (mismo orden de filas que la entrada) y la lista
    de columnas eliminadas. La usan la línea de comandos y la aplicación.
    """
    df = df.copy()
    columnas = {col_estudiante: ("EST", "id_seudonimo")}
    if col_familia:
        columnas[col_familia] = ("FAM", "id_familia_seudonimo")

    col_codigo = col_codigo or col_estudiante
    requeridas = [*columnas, *([col_codigo] if derivar_anio_ingreso else [])]
    faltantes = [c for c in requeridas if c not in df.columns]
    if faltantes:
        raise KeyError(f"Columnas inexistentes en la entrada: {faltantes}")
    # Las columnas a eliminar son opcionales: si ya no existen, solo se avisa.
    ausentes = [c for c in eliminar if c not in df.columns]
    if ausentes:
        log.info("Columnas a eliminar que no están en el archivo (se omiten): %s", ausentes)
    eliminar = [c for c in eliminar if c in df.columns]

    if derivar_anio_ingreso:
        # El código interno solo se usa para el año de ingreso (2 primeros dígitos).
        df["anio_ingreso"] = df[col_codigo].map(anio_ingreso)
        log.info("anio_ingreso derivado de %s; %d filas sin valor.",
                 col_codigo, df["anio_ingreso"].isna().sum())

    for col, (tipo, destino) in columnas.items():
        if validar_cedula:
            invalidas = (~df[col].map(lambda v: validar_cedula_ec(normalizar(v) or ""))).sum()
            if invalidas:
                log.warning("%s: %d valores no son cédulas válidas.", col, invalidas)
        df[destino] = df[col].map(lambda v, t=tipo: seudonimo(v, clave, t))
        _verificar_colisiones(df[col], df[destino], tipo)
        nulos = df[destino].isna().sum()
        if nulos:
            log.warning("%s: %d filas sin identificador (quedan sin seudónimo).", col, nulos)

    # Se eliminan los identificadores originales y los campos directos pedidos.
    eliminadas = sorted({*columnas, *eliminar})
    return df.drop(columns=eliminadas), eliminadas


def columnas_identificatorias(df: pd.DataFrame, muestra: int = 300) -> list[str]:
    """Columnas que aún parecen identificadores: nombres o cédulas válidas."""
    problemas = [c for c in df.columns if "nombre" in str(c).lower()]
    for col in df.columns:
        valores = df[col].dropna().head(muestra)
        if len(valores) and valores.map(
                lambda v: validar_cedula_ec(normalizar(v) or "")).mean() > 0.5:
            problemas.append(col)
    return sorted(set(problemas))


def construir_acta(df: pd.DataFrame, csv: bytes, entrada: str, salida: str,
                   eliminadas: list[str], col_estudiante: str,
                   clave: bytes | None = None) -> dict:
    """Acta de extracción: qué se generó, cuándo y con qué huella (sin datos personales)."""
    acta = {
        "fecha_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "archivo_entrada": entrada,
        "archivo_salida": salida,
        "sha256_salida": hashlib.sha256(csv).hexdigest(),
        "filas": len(df),
        "estudiantes_unicos": int(df["id_seudonimo"].nunique()),
        "familias_unicas": int(df["id_familia_seudonimo"].nunique())
        if "id_familia_seudonimo" in df else None,
        "columnas_eliminadas": eliminadas,
        "llave_estudiante": col_estudiante,
        "tecnica": "HMAC-SHA256 con clave secreta, truncado a 60 bits, base32",
    }
    if clave is not None:
        acta["huella_clave"] = huella_clave(clave)
    return acta


def reidentificar_tabla(entrada: pd.DataFrame, padron: pd.DataFrame, clave: bytes,
                        col_seudonimo: str, col_padron: str, tipo: str) -> pd.DataFrame:
    """Une seudónimos con el padrón institucional. Solo para personal autorizado."""
    if col_seudonimo not in entrada.columns or col_padron not in padron.columns:
        raise KeyError("Revise --col-seudonimo y --col-padron.")
    padron = padron.copy()
    padron[col_seudonimo] = padron[col_padron].map(lambda v: seudonimo(v, clave, tipo))
    return entrada.merge(padron, on=col_seudonimo, how="left")


# --------------------------------------------------------------------------- #
# Comandos
# --------------------------------------------------------------------------- #
def cmd_seudonimizar(args: argparse.Namespace) -> None:
    clave = cargar_clave(Path(args.clave))
    df, eliminadas = seudonimizar_tabla(
        _leer(Path(args.entrada)), clave, args.col_estudiante, args.col_familia,
        args.eliminar, args.derivar_anio_ingreso, args.col_codigo, args.validar_cedula)
    salida = Path(args.salida)
    df.to_csv(salida, index=False, encoding="utf-8")

    acta = construir_acta(df, salida.read_bytes(), Path(args.entrada).name, salida.name,
                          eliminadas, args.col_estudiante)
    salida.with_suffix(".acta.json").write_text(
        json.dumps(acta, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Listo: %s (%d filas). Acta de extracción: %s",
             salida, len(df), salida.with_suffix(".acta.json").name)


def cmd_reidentificar(args: argparse.Namespace) -> None:
    """Solo para personal autorizado de LEMAS: une seudónimos con el padrón."""
    clave = cargar_clave(Path(args.clave))
    resultado = reidentificar_tabla(_leer(Path(args.entrada)), _leer(Path(args.padron)),
                                    clave, args.col_seudonimo, args.col_padron, args.tipo)
    sin_match = resultado[args.col_padron].isna().sum()
    if sin_match:
        log.warning("%d registros no se encontraron en el padrón.", sin_match)
    resultado.to_csv(args.salida, index=False, encoding="utf-8")
    log.info("Archivo interno generado: %s. No debe salir del entorno de LEMAS.",
             args.salida)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)

    p_clave = sub.add_parser("generar-clave", help="Crea la clave secreta del custodio")
    p_clave.add_argument("--salida", required=True)

    p_seud = sub.add_parser("seudonimizar", help="Reemplaza identificadores por seudónimos")
    p_seud.add_argument("--entrada", required=True)
    p_seud.add_argument("--salida", required=True)
    p_seud.add_argument("--clave", required=True)
    p_seud.add_argument("--col-estudiante", required=True)
    p_seud.add_argument("--col-familia")
    p_seud.add_argument("--eliminar", nargs="*", default=[],
                        help="Columnas identificatorias adicionales a borrar")
    p_seud.add_argument("--derivar-anio-ingreso", action="store_true",
                        help="Crea anio_ingreso con los 2 primeros dígitos del código")
    p_seud.add_argument("--col-codigo",
                        help="Columna del código interno para el año de ingreso "
                             "(por defecto, la misma de --col-estudiante)")
    p_seud.add_argument("--validar-cedula", action="store_true",
                        help="Advierte si la columna no contiene cédulas válidas")

    p_reid = sub.add_parser("reidentificar", help="Uso interno: seudónimo -> padrón")
    p_reid.add_argument("--entrada", required=True)
    p_reid.add_argument("--padron", required=True)
    p_reid.add_argument("--clave", required=True)
    p_reid.add_argument("--col-seudonimo", required=True)
    p_reid.add_argument("--col-padron", required=True)
    p_reid.add_argument("--tipo", choices=list(DOMINIOS), required=True)
    p_reid.add_argument("--salida", required=True)

    args = parser.parse_args(argv)
    try:
        {"generar-clave": lambda a: generar_clave(Path(a.salida)),
         "seudonimizar": cmd_seudonimizar,
         "reidentificar": cmd_reidentificar}[args.comando](args)
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        log.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
