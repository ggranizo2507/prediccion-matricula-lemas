"""
Generador de datos SINTÉTICOS con la misma estructura que la base seudonimizada
de LEMAS (una fila por estudiante y ciclo lectivo).

Propósito: que el repositorio público, los tests y la app funcionen sin datos
reales. Las relaciones entre variables son supuestos plausibles; solo los
totales se calibran con el perfil agregado (perfil_lemas.json). Las métricas
obtenidas con estos datos NO son evidencia sobre LEMAS.

Uso:
    python -m src.synthetic                       # valores por defecto
    python -m src.synthetic --perfil perfil_lemas.json
"""

from __future__ import annotations

import argparse
import json
import logging
import string
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils import RAIZ, cargar_config, configurar_logging

log = logging.getLogger("lemas.sintetico")

GRADOS = [
    ("Inicial 1", "Inicial"), ("Inicial 2", "Inicial"),
    ("1ro EGB", "Preparatoria"),
    ("2do EGB", "Básica Elemental"), ("3ro EGB", "Básica Elemental"),
    ("4to EGB", "Básica Elemental"),
    ("5to EGB", "Básica Media"), ("6to EGB", "Básica Media"), ("7mo EGB", "Básica Media"),
    ("8vo EGB", "Básica Superior"), ("9no EGB", "Básica Superior"),
    ("10mo EGB", "Básica Superior"),
    ("1ro BGU", "BGU"), ("2do BGU", "BGU"), ("3ro BGU", "BGU"),
]
ULTIMO_GRADO = len(GRADOS) - 1
# Grados donde entran más estudiantes nuevos (pesos relativos)
PESO_INGRESO = np.array([8, 3, 5, 1, 1, 1, 1, 1, 1, 3, 1, 1, 2, 0.5, 0.2])

PARAMETROS_BASE = {
    "sedes": {"Mucho Lote 1": 0.6, "Mucho Lote 2": 0.4},
    "tasa_beca": 0.15,
    "promedio_media": 8.7, "promedio_desv": 0.6,
    "conducta_letras": {"A": 0.55, "B": 0.30, "C": 0.11, "D": 0.03, "E": 0.01},
    "atrasos_media": 1.5,
}


def _codigo(rng: np.random.Generator, prefijo: str) -> str:
    alfabeto = np.array(list(string.ascii_uppercase + "234567"))
    return f"{prefijo}-" + "".join(rng.choice(alfabeto, 12))


def _nota(media: float, desv: float, z: float) -> float:
    """Nota en escala 0-10 recortada a [4, 10] con dos decimales."""
    return round(float(np.clip(media + desv * z, 4, 10)), 2)


def _letra_conducta(z: float, proporciones: dict) -> str:
    """Convierte un puntaje latente normal en letra A-E respetando las proporciones."""
    from statistics import NormalDist

    acumulada = 0.0
    for letra in "ABCDE":
        acumulada += proporciones.get(letra, 0.0)
        if z >= NormalDist().inv_cdf(max(min(1 - acumulada, 1 - 1e-9), 1e-9)):
            return letra
    return "E"


def _sigmoide(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def calibrar_con_perfil(ruta: str | Path) -> dict:
    """Toma del perfil agregado solo los totales que existan; el resto queda por defecto."""
    parametros = dict(PARAMETROS_BASE)
    perfil = json.loads(Path(ruta).read_text(encoding="utf-8"))
    columnas = next(iter(perfil["tablas"].values()))["columnas"]

    def frecuencias(nombre):
        info = columnas.get(nombre, {})
        return {k: v for k, v in info.get("frecuencias", {}).items() if isinstance(v, int)}

    sedes = frecuencias("Sede")
    if sedes:
        total = sum(sedes.values())
        parametros["sedes"] = {k: v / total for k, v in sedes.items()}
    becas = frecuencias("beca")
    if becas:
        si = sum(v for k, v in becas.items() if k.upper() in {"SI", "1"})
        parametros["tasa_beca"] = si / sum(becas.values())
    atrasos = frecuencias("# meses caído")
    if atrasos:
        total = sum(atrasos.values())
        parametros["atrasos_media"] = sum(float(k) * v for k, v in atrasos.items()) / total
    info = columnas.get("P.Académico", {})
    if "media" in info:
        parametros["promedio_media"], parametros["promedio_desv"] = info["media"], info["desv"]
    letras = {k: v for k, v in frecuencias("P.Conducta").items() if k.upper() in "ABCDE"}
    if letras:
        total = sum(letras.values())
        parametros["conducta_letras"] = {k.upper(): v / total for k, v in letras.items()}
    log.info("Parámetros calibrados con %s: %s", ruta, parametros)
    return parametros


def generar(
    config: dict, parametros: dict | None = None, semilla: int | None = None
) -> pd.DataFrame:
    """Simula la historia de estudiantes y familias año por año."""
    p = parametros or PARAMETROS_BASE
    rng = np.random.default_rng(config["proyecto"]["semilla"] if semilla is None else semilla)
    cfg = config["sintetico"]
    anios, n_anio, tasa_obj = cfg["anios"], cfg["estudiantes_por_anio"], cfg["tasa_no_matricula"]
    sedes, pesos_sede = list(p["sedes"]), list(p["sedes"].values())
    estres_escala = p["atrasos_media"] / 10

    familias: dict[str, dict] = {}
    estudiantes: list[dict] = []

    def nueva_familia() -> str:
        fid = _codigo(rng, "FAM")
        familias[fid] = {
            "estres": float(np.clip(rng.beta(1.2, 5) * estres_escala / 0.19, 0, 0.95)),
            "beca": int(rng.random() < p["tasa_beca"]),
            "sede": rng.choice(sedes, p=pesos_sede),
        }
        return fid

    def nuevo_estudiante(anio: int, grado: int | None = None) -> dict:
        if familias and rng.random() < 0.2:
            fid = rng.choice(list(familias))
        else:
            fid = nueva_familia()
        if grado is None:
            grado = int(rng.choice(len(GRADOS), p=PESO_INGRESO / PESO_INGRESO.sum()))
        return {"id": _codigo(rng, "EST"), "familia": fid, "grado": grado,
                "ingreso": anio, "habilidad": rng.normal(), "paralelo": rng.choice(["A", "B"])}

    # Población inicial: estudiantes que ya estaban antes de 2021
    for _ in range(n_anio):
        est = nuevo_estudiante(anios[0], int(rng.integers(0, len(GRADOS))))
        est["ingreso"] = int(anios[0] - rng.integers(0, est["grado"] + 1))
        estudiantes.append(est)

    filas = []
    deriva = {a: rng.normal(0, 0.15) for a in anios}   # variación entre cohortes
    # C1 menos comparable (pospandemia): más atrasos en pensiones en el primer año
    factor_c1 = 1 + cfg.get("desplazamiento_c1", 0.0)
    for i, anio in enumerate(anios):
        registros = []
        for est in estudiantes:
            fam = familias[est["familia"]]
            nuevo = est["ingreso"] == anio
            if nuevo:
                pago = pd.Timestamp(anio - 1, 11, 1) + pd.Timedelta(days=int(rng.integers(0, 90)))
            else:
                pago = pd.Timestamp(anio, 2, 20) + pd.Timedelta(days=int(rng.exponential(12)))
                if est.get("tardio"):
                    pago = pd.Timestamp(anio, 5, 1) + pd.Timedelta(days=int(rng.integers(0, 40)))
            factor = factor_c1 if anio == anios[0] else 1.0
            atrasos = int(rng.binomial(10, min(fam["estres"] * factor, 0.95)))
            reserva = rng.random() < 0.97 - 0.5 * fam["estres"]
            u = rng.random()
            estado = ("En proceso" if u < 0.03 + 0.3 * fam["estres"] else
                      "Aprobar extraordinaria" if u < 0.08 + 0.3 * fam["estres"] else "Aprobar")
            extra = rng.random() < 0.10 + 0.4 * fam["estres"]
            inicio = pd.Timestamp(anio, 11, 1) if extra else pd.Timestamp(anio, 9, 15)
            fecha_reserva = inicio + pd.Timedelta(days=int(rng.integers(0, 30)),
                                                  hours=int(rng.integers(7, 19)))
            if rng.random() < 0.01:
                fecha_reserva = pd.Timestamp(anio + 1, 3, 1)   # activación tardía
            curso, subnivel = GRADOS[est["grado"]]
            registros.append({
                "anoa": anio, "anos": anio + 1, "Sede": fam["sede"],
                "Nivel": f"{curso} {est['paralelo']} - {subnivel}", "Paralelo": est["paralelo"],
                "P.Académico": _nota(p["promedio_media"], p["promedio_desv"],
                                     0.8 * est["habilidad"] + 0.6 * rng.normal()),
                "P.Conducta": _letra_conducta(0.53 * est["habilidad"] + 0.85 * rng.normal(),
                                              p["conducta_letras"]),
                "fecha_pago_matricula": pago.strftime("%Y-%m-%d"),
                "Reserva": "SI" if reserva else "NO", "RColegio": estado if reserva else "",
                "Fecha Reserva": fecha_reserva.strftime("%Y-%m-%d %H:%M") if reserva else "",
                "Tiempo": ("EXTRAORDINARIA" if extra else "ORDINARIA") if reserva else "",
                "beca": "SI" if fam["beca"] else "NO", "# meses caído": atrasos,
                "anio_ingreso": est["ingreso"], "id_seudonimo": est["id"],
                "id_familia_seudonimo": est["familia"],
                # Riesgo latente: supuesto plausible, NO estimado de datos reales
                "_logit": (3.25 * (atrasos / 10 - estres_escala) - 0.45 * est["habilidad"]
                           - 0.3 * fam["beca"] - 0.25 * min(anio - est["ingreso"], 6) / 6
                           + (1.2 if estado == "En proceso" else 0) + deriva[anio]),
                "_reserva": reserva, "_terminal": est["grado"] == ULTIMO_GRADO,
            })
        tabla = pd.DataFrame(registros)
        filas.append(tabla)
        if i == len(anios) - 1:
            break

        # Decisión de continuidad para el año siguiente, calibrada a la tasa objetivo
        elegibles = tabla["_reserva"] & ~tabla["_terminal"]
        bajo, alto = -8.0, 4.0
        for _ in range(40):
            intercepto = (bajo + alto) / 2
            media = _sigmoide(intercepto + tabla.loc[elegibles, "_logit"]).mean()
            bajo, alto = (intercepto, alto) if media < tasa_obj else (bajo, intercepto)
        prob_salida = np.where(tabla["_reserva"], _sigmoide(intercepto + tabla["_logit"]), 0.9)
        # Las familias tienden a decidir en bloque
        choque_familiar = tabla.groupby("id_familia_seudonimo")["_logit"].transform(
            lambda s: rng.normal(0, 0.8))
        prob_salida = np.clip(prob_salida + 0.08 * choque_familiar, 0, 1)
        sale = rng.random(len(tabla)) < prob_salida

        siguientes = []
        for est, sale_i, terminal in zip(estudiantes, sale, tabla["_terminal"], strict=False):
            if terminal:
                continue
            tardio = sale_i and rng.random() < 0.15      # parte de las "salidas" son tardías
            if sale_i and not tardio:
                continue
            est = dict(est, grado=est["grado"] + 1, tardio=tardio)
            siguientes.append(est)
        faltan = max(n_anio - len(siguientes), 0)
        siguientes += [nuevo_estudiante(anios[i + 1]) for _ in range(faltan)]
        estudiantes = siguientes

    base = pd.concat(filas, ignore_index=True).drop(columns=["_logit", "_reserva", "_terminal"])
    base.insert(0, "hoja", base["anoa"].astype(str) + "-" + base["anos"].astype(str))
    base["origen_datos"] = "SINTETICO"
    # Suciedad realista para probar la limpieza
    base.loc[rng.random(len(base)) < 0.01, "P.Académico"] = np.nan
    return base


def main(argv: list[str] | None = None) -> int:
    configurar_logging()
    parser = argparse.ArgumentParser(description="Genera la base sintética de LEMAS")
    parser.add_argument("--perfil", help="perfil_lemas.json para calibrar totales")
    parser.add_argument("--salida", help="Ruta del CSV (por defecto la de config.yaml)")
    args = parser.parse_args(argv)

    config = cargar_config()
    parametros = calibrar_con_perfil(args.perfil) if args.perfil else None
    base = generar(config, parametros)
    salida = Path(args.salida) if args.salida else RAIZ / config["rutas"]["base_sintetica"]
    salida.parent.mkdir(parents=True, exist_ok=True)
    base.to_csv(salida, index=False, encoding="utf-8")
    log.info("Base sintética: %s (%d filas, %d años).", salida, len(base), base["anoa"].nunique())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
