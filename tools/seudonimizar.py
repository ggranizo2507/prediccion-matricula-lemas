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
        --col-estudiante Codigo --col-familia cedulap \
        --eliminar CI "Nombre Completo" "Nombres completos padre de familia" Orden \
        --derivar-anio-ingreso
    python seudonimizar.py reidentificar --entrada top_k.csv --padron padron.xlsx \
        --clave C:/custodio/clave_lemas.key --col-seudonimo id_familia_seudonimo \
        --col-padron cedula_representante --tipo FAM --salida top_k_interno.csv
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import logging
import secrets
import sys
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
    ruta.write_text(secrets.token_hex(32), encoding="utf-8")
    log.info("Clave creada en %s. Guárdela con respaldo cifrado: "
             "si se pierde, no se podrá reidentificar a nadie.", ruta)


def cargar_clave(ruta: Path) -> bytes:
    """Lee la clave hexadecimal y valida su longitud."""
    try:
        clave = bytes.fromhex(ruta.read_text(encoding="utf-8").strip())
    except (OSError, ValueError) as exc:
        raise ValueError(f"No se pudo leer una clave válida en {ruta}") from exc
    if len(clave) < 32:
        raise ValueError("La clave debe tener al menos 256 bits.")
    return clave


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


def _leer(ruta: Path) -> pd.DataFrame:
    """Lee CSV o Excel. En Excel une todas las hojas (una por ciclo lectivo)
    y agrega la columna 'hoja' para conservar su origen."""
    if ruta.suffix.lower() in {".xlsx", ".xls"}:
        hojas = pd.read_excel(ruta, sheet_name=None, dtype=str)
        partes = []
        for nombre, df in hojas.items():
            df = df.dropna(how="all")
            df.columns = [str(c).strip() for c in df.columns]
            df.insert(0, "hoja", str(nombre))
            partes.append(df)
            log.info("Hoja '%s': %d filas", nombre, len(df))
        columnas = {tuple(p.columns) for p in partes}
        if len(columnas) > 1:
            log.warning("Las hojas no tienen exactamente las mismas columnas; "
                        "se unen igual y las faltantes quedan vacías.")
        return pd.concat(partes, ignore_index=True)
    return pd.read_csv(ruta, dtype=str)


def _huella(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Comandos
# --------------------------------------------------------------------------- #
def cmd_seudonimizar(args: argparse.Namespace) -> None:
    clave = cargar_clave(Path(args.clave))
    df = _leer(Path(args.entrada))
    columnas = {args.col_estudiante: ("EST", "id_seudonimo")}
    if args.col_familia:
        columnas[args.col_familia] = ("FAM", "id_familia_seudonimo")

    faltantes = [c for c in [*columnas, *args.eliminar] if c not in df.columns]
    if faltantes:
        raise KeyError(f"Columnas inexistentes en la entrada: {faltantes}")

    if args.derivar_anio_ingreso:
        df["anio_ingreso"] = df[args.col_estudiante].map(anio_ingreso)
        log.info("anio_ingreso derivado; %d filas sin valor.", df["anio_ingreso"].isna().sum())

    for col, (tipo, destino) in columnas.items():
        if args.validar_cedula:
            invalidas = (~df[col].map(lambda v: validar_cedula_ec(normalizar(v) or ""))).sum()
            if invalidas:
                log.warning("%s: %d valores no son cédulas válidas.", col, invalidas)
        df[destino] = df[col].map(lambda v, t=tipo: seudonimo(v, clave, t))
        _verificar_colisiones(df[col], df[destino], tipo)
        nulos = df[destino].isna().sum()
        if nulos:
            log.warning("%s: %d filas sin identificador (quedan sin seudónimo).", col, nulos)

    # Se eliminan los identificadores originales y los campos directos pedidos.
    df = df.drop(columns=list({*columnas, *args.eliminar}))
    salida = Path(args.salida)
    df.to_csv(salida, index=False, encoding="utf-8")

    acta = {
        "fecha_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "archivo_entrada": Path(args.entrada).name,
        "archivo_salida": salida.name,
        "sha256_salida": _huella(salida),
        "filas": len(df),
        "estudiantes_unicos": int(df["id_seudonimo"].nunique()),
        "familias_unicas": int(df["id_familia_seudonimo"].nunique())
        if "id_familia_seudonimo" in df else None,
        "columnas_eliminadas": sorted({*columnas, *args.eliminar}),
        "tecnica": "HMAC-SHA256 con clave secreta, truncado a 60 bits, base32",
    }
    salida.with_suffix(".acta.json").write_text(
        json.dumps(acta, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Listo: %s (%d filas). Acta de extracción: %s",
             salida, len(df), salida.with_suffix(".acta.json").name)


def cmd_reidentificar(args: argparse.Namespace) -> None:
    """Solo para personal autorizado de LEMAS: une seudónimos con el padrón."""
    clave = cargar_clave(Path(args.clave))
    entrada = _leer(Path(args.entrada))
    padron = _leer(Path(args.padron))
    if args.col_seudonimo not in entrada.columns or args.col_padron not in padron.columns:
        raise KeyError("Revise --col-seudonimo y --col-padron.")

    padron[args.col_seudonimo] = padron[args.col_padron].map(
        lambda v: seudonimo(v, clave, args.tipo))
    resultado = entrada.merge(padron, on=args.col_seudonimo, how="left")
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
