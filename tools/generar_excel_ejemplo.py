"""
Genera un Excel de EJEMPLO con la estructura institucional de LEMAS (una hoja por
ciclo, con cédulas y nombres FICTICIOS) y una clave de práctica.

Sirve para capacitar al personal y para probar el modo institucional de la aplicación
sin usar datos reales:

    python tools/generar_excel_ejemplo.py --salida ejemplo_lemas

Crea `ejemplo_lemas/ejemplo_institucional.xlsx` y `ejemplo_lemas/clave_ejemplo.key`.
Las personas no existen: los nombres son «Estudiante 0001», «Representante 0001»…
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BASE_SINTETICA = RAIZ / "data/synthetic/base_sintetica.csv"
CLAVE_EJEMPLO = "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"
COLUMNAS = ["anoa", "anos", "Sede", "Orden", "Nombre Completo", "CI", "Codigo", "Nivel",
            "Paralelo", "cedulap", "Nombres completos padre de familia", "P.Académico",
            "P.Conducta", "saldo", "deuda", "statusp", "fecha_pago", "Reserva", "RColegio",
            "Fecha Reserva", "Tiempo", "beca", "# meses caído"]


def cedula_ficticia(numero: int) -> str:
    """Cédula con formato y dígito verificador válidos, de una provincia inexistente
    en la práctica para este uso (prefijo 30) y numeración consecutiva."""
    cuerpo = f"30{numero:07d}"
    suma = 0
    for i, digito in enumerate(cuerpo):
        producto = int(digito) * (2 if i % 2 == 0 else 1)
        suma += producto - 9 if producto > 9 else producto
    return cuerpo + str((10 - suma % 10) % 10)


def tabla_ejemplo(base: pd.DataFrame | None = None) -> pd.DataFrame:
    """Convierte la base sintética seudonimizada en una tabla con identificadores
    ficticios, como la que exporta el sistema académico."""
    if base is None:
        base = pd.read_csv(BASE_SINTETICA, dtype=str)
    estudiantes = {s: i for i, s in enumerate(base["id_seudonimo"].dropna().unique(), start=1)}
    familias = {f: i for i, f in enumerate(base["id_familia_seudonimo"].dropna().unique(),
                                           start=1)}
    num_est = base["id_seudonimo"].map(estudiantes)
    num_fam = base["id_familia_seudonimo"].map(familias)
    ingreso = pd.to_numeric(base["anio_ingreso"], errors="coerce")

    datos = base.copy()
    datos["CI"] = num_est.map(lambda n: cedula_ficticia(int(n)) if pd.notna(n) else None)
    datos["Nombre Completo"] = num_est.map(
        lambda n: f"Estudiante {int(n):04d}" if pd.notna(n) else None)
    datos["cedulap"] = num_fam.map(
        lambda n: cedula_ficticia(5_000_000 + int(n)) if pd.notna(n) else None)
    datos["Nombres completos padre de familia"] = num_fam.map(
        lambda n: f"Representante {int(n):04d}" if pd.notna(n) else None)
    datos["Codigo"] = [
        f"{int(a) % 100:02d}{int(n):04d}" if pd.notna(a) and pd.notna(n) else None
        for a, n in zip(ingreso, num_est, strict=True)]
    datos["Orden"] = datos.groupby("hoja").cumcount() + 1
    for vacia in ("saldo", "deuda", "statusp"):
        datos[vacia] = None
    return datos[["hoja", *COLUMNAS]]


def excel_ejemplo(tabla: pd.DataFrame | None = None) -> bytes:
    """Excel en memoria con una hoja por ciclo."""
    tabla = tabla_ejemplo() if tabla is None else tabla
    memoria = io.BytesIO()
    with pd.ExcelWriter(memoria, engine="openpyxl") as escritor:
        for hoja, grupo in tabla.groupby("hoja", sort=True):
            grupo.drop(columns="hoja").to_excel(escritor, sheet_name=str(hoja)[:31], index=False)
    return memoria.getvalue()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--salida", default="ejemplo_lemas", help="Carpeta de destino")
    args = parser.parse_args(argv)
    carpeta = Path(args.salida)
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "ejemplo_institucional.xlsx").write_bytes(excel_ejemplo())
    (carpeta / "clave_ejemplo.key").write_text(CLAVE_EJEMPLO, encoding="utf-8")
    print(f"Ejemplo creado en {carpeta.resolve()} (datos ficticios; clave solo de práctica).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
