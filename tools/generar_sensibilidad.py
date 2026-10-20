"""
Análisis de sensibilidad de hiperparámetros (Workshop S5, D58).

Lee solo `results/metrics/optuna_historial_<fuente>.csv` (hiperparámetros y PR-AUC de las
180 pruebas de Optuna; sin datos de estudiantes) y guarda:

- `results/metrics/sensibilidad_importancia_<fuente>.csv`: importancia por fANOVA e impureza,
- `results/metrics/sensibilidad_dependencia_<fuente>.csv`: dependencia parcial,
- `results/metrics/sensibilidad_interacciones_<fuente>.csv`: H² de Friedman por par,
- `results/metrics/sensibilidad_uno_a_la_vez_<fuente>.csv`: rango de PR-AUC por hiperparámetro,
- `results/metrics/sensibilidad_antes_despues_<fuente>.csv` y `sensibilidad_<fuente>.json`,
- `results/figures/<fuente>_31_importancia_hiperparametros.png`,
  `<fuente>_32_dependencia_parcial.png` y `<fuente>_33_interacciones.png`.

No entrena modelos del proyecto ni usa C4 o C5.

    python tools/generar_sensibilidad.py --fuente real
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src import graficos_sensibilidad as gs  # noqa: E402
from src import sensibilidad as se  # noqa: E402

METRICAS = RAIZ / "results" / "metrics"
FIGURAS = RAIZ / "results" / "figures"


def _tasa_interna(fuente: str) -> float | None:
    ruta = METRICAS / f"diagnostico_semana3_{fuente}.json"
    if not ruta.exists():
        return None
    for particion in json.loads(ruta.read_text(encoding="utf-8")).get("particiones", []):
        if particion.get("particion") == "interna":
            return float(particion["tasa_validacion"])
    return None


def generar(fuente: str) -> dict:
    historial = pd.read_csv(METRICAS / f"optuna_historial_{fuente}.csv")
    tasa = _tasa_interna(fuente)
    imps, deps, inters, sens, antes, mapas, pares, pruebas = [], [], [], [], [], {}, {}, {}
    for tipo in ("logistica", "arboles", "hibrido"):
        p = se.pruebas_de(historial, tipo)
        nombre = se.NOMBRES[tipo]
        pruebas[nombre] = p
        imp = se.importancias(p, tipo)
        imps.append(imp)
        sustituto = se.ajustar_sustituto(p, tipo)
        orden = (
            imp[imp["metodo"] == "fANOVA"]
            .sort_values("importancia", ascending=False)["hiperparametro"]
            .tolist()
        )
        deps.extend(se.dependencia_parcial(sustituto, n) for n in orden)
        inter = se.interacciones(sustituto)
        inters.append(inter)
        sens.append(se.sensibilidad(sustituto, p))
        antes.append(se.antes_despues(p, tipo, tasa))
        if tipo != "hibrido" or len(sustituto.columnas) > 1:
            a, b = inter.iloc[0]["a"], inter.iloc[0]["b"]
            mapas[nombre] = se.dependencia_2d(sustituto, a, b)
            pares[nombre] = (a, b)
    imp, dep = pd.concat(imps, ignore_index=True), pd.concat(deps, ignore_index=True)
    inter, sen = pd.concat(inters, ignore_index=True), pd.concat(sens, ignore_index=True)
    ant = pd.DataFrame(antes)
    imp.to_csv(METRICAS / f"sensibilidad_importancia_{fuente}.csv", index=False)
    dep.to_csv(
        METRICAS / f"sensibilidad_dependencia_{fuente}.csv", index=False, float_format="%.6f"
    )
    inter.to_csv(METRICAS / f"sensibilidad_interacciones_{fuente}.csv", index=False)
    sen.to_csv(METRICAS / f"sensibilidad_uno_a_la_vez_{fuente}.csv", index=False)
    ant.to_csv(METRICAS / f"sensibilidad_antes_despues_{fuente}.csv", index=False)
    textos = se.conclusiones(imp, inter, sen, ant)
    resumen = {
        "fuente": fuente,
        "pruebas_por_modelo": 60,
        "validacion": "C2 → C3",
        "tasa_validacion": tasa,
        "semillas_importancia": list(se.SEMILLAS),
        "conclusiones": textos,
    }
    (METRICAS / f"sensibilidad_{fuente}.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    gs.guardar(gs.figura_importancia(imp), FIGURAS / f"{fuente}_31_importancia_hiperparametros.png")
    gs.guardar(
        gs.figura_dependencia(dep, pruebas, tasa), FIGURAS / f"{fuente}_32_dependencia_parcial.png"
    )
    gs.guardar(
        gs.figura_interacciones(inter, mapas, pares), FIGURAS / f"{fuente}_33_interacciones.png"
    )
    return resumen


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--fuente", choices=["real", "sintetica"], default="sintetica")
    args = parser.parse_args()
    for texto in generar(args.fuente)["conclusiones"]:
        print("-", texto)


if __name__ == "__main__":
    main()
